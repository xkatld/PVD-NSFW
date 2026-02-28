let video_items = [];
const container = document.getElementById('video-container');
let current_speed = parseFloat(localStorage.getItem('video_speed') || '1.0');

async function fetch_videos() {
    const res = await fetch('/api/videos');
    if (res.status === 401) {
        const pass = prompt('请输入访问密码:');
        if (pass) {
            const login_res = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ password: pass })
            });
            if (login_res.ok) {
                location.reload();
            } else {
                alert('密码错误');
            }
        }
        return;
    }
    const data = await res.json();
    for (let i = data.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [data[i], data[j]] = [data[j], data[i]];
    }
    video_items = data;
    render_videos();
}

function setup_video_pitch(v) {
    v.preservesPitch = true;
    if ('webkitPreservesPitch' in v) {
        v.webkitPreservesPitch = true;
    }
}

function render_videos() {
    container.innerHTML = '';
    video_items.forEach((video, index) => {
        const card = document.createElement('div');
        card.className = 'video-card';
        card.dataset.index = index;
        card.innerHTML = `
            <video loop playsinline preload="metadata" data-src="${video.url}"></video>
            <div class="controls-overlay">
                <div class="play-pause-btn"><div class="play-icon"></div></div>
                <div class="info-overlay">
                    <div class="video-title">@${video.title}</div>
                    <div class="video-labels">
                        ${video.labels.map((l) => `<span class="label-tag">#${l.name || l}</span>`).join('')}
                    </div>
                </div>
                <div class="player-ui">
                    <div class="progress-container">
                        <div class="progress-bar">
                            <div class="progress-filled"></div>
                        </div>
                    </div>
                    <div class="speed-ctrl">${current_speed}x</div>
                </div>
            </div>
        `;

        const v = card.querySelector('video');
        const speed_btn = card.querySelector('.speed-ctrl');
        const progress_filled = card.querySelector('.progress-filled');
        const progress_container = card.querySelector('.progress-container');

        setup_video_pitch(v);

        let is_dragging = false;

        card.onclick = (e) => {
            if (e.target.closest('.player-ui')) return;
            if (v.paused) v.play(); else v.pause();
        };

        v.onplay = () => card.querySelector('.play-pause-btn').classList.remove('visible');
        v.onpause = () => card.querySelector('.play-pause-btn').classList.add('visible');

        v.ontimeupdate = () => {
            if (!is_dragging) {
                const pct = (v.currentTime / v.duration) * 100;
                progress_filled.style.width = `${pct}%`;
            }
        };

        const update_progress = (e) => {
            const rect = progress_container.getBoundingClientRect();
            const client_x = e.touches ? e.touches[0].clientX : e.clientX;
            const pos = Math.max(0, Math.min(1, (client_x - rect.left) / rect.width));
            progress_filled.style.width = `${pos * 100}%`;
            return pos;
        };

        progress_container.onmousedown = (e) => {
            is_dragging = true;
            v.currentTime = update_progress(e) * v.duration;
        };

        window.addEventListener('mousemove', (e) => {
            if (is_dragging) update_progress(e);
        });

        window.addEventListener('mouseup', (e) => {
            if (is_dragging) {
                is_dragging = false;
                v.currentTime = update_progress(e) * v.duration;
            }
        });

        progress_container.ontouchstart = (e) => {
            is_dragging = true;
            update_progress(e);
        };

        progress_container.ontouchmove = (e) => {
            if (is_dragging) update_progress(e);
        };

        progress_container.ontouchend = (e) => {
            if (is_dragging) {
                is_dragging = false;
                const pos = parseFloat(progress_filled.style.width) / 100;
                v.currentTime = pos * v.duration;
            }
        };

        speed_btn.onclick = (e) => {
            e.stopPropagation();
            const speeds = [0.5, 1.0, 1.5, 2.0, 3.0, 5.0];
            let current_idx = speeds.indexOf(current_speed);
            if (current_idx === -1) current_idx = 1;
            let next_idx = (current_idx + 1) % speeds.length;
            current_speed = speeds[next_idx];
            localStorage.setItem('video_speed', current_speed.toString());
            update_all_speeds();
        };

        container.appendChild(card);
    });
    init_intersection_observer();
}

function update_all_speeds() {
    document.querySelectorAll('video').forEach(v => {
        setup_video_pitch(v);
        v.playbackRate = current_speed;
    });
    document.querySelectorAll('.speed-ctrl').forEach(btn => btn.textContent = `${current_speed}x`);
}

function update_video_resources(current_index) {
    const cards = document.querySelectorAll('.video-card');
    cards.forEach((card) => {
        const index = parseInt(card.dataset.index);
        const video = card.querySelector('video');

        if (Math.abs(index - current_index) <= 1) {
            if (!video.src && video.dataset.src) {
                video.src = video.dataset.src;
            }
            if (index === current_index) {
                setup_video_pitch(video);
                video.playbackRate = current_speed;
                video.play().catch(() => { });
            } else {
                video.pause();
            }
        } else {
            video.pause();
            video.removeAttribute('src');
            video.load();
        }
    });
}

function init_intersection_observer() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const index = parseInt(entry.target.dataset.index || '0');
                update_video_resources(index);
            }
        });
    }, { threshold: 0.6 });
    document.querySelectorAll('.video-card').forEach(card => observer.observe(card));
}

fetch_videos();
