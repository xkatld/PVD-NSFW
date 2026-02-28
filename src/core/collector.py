import os
import json
import shutil
import time
import random
from pathlib import Path
from src.api.client import ApiClient
from src.core.downloader import HLSDownloader
from src.utils.processor import VideoProcessor
from src.core.db_manager import DbManager
from rich.console import Console
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import yaml

class VideoCollector:
    def __init__(self, config_path="config.yaml", is_local=False):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
            
        self.is_local = is_local
        self.output_dir = Path(self.config['storage']['output_dir'])
        self.staging_dir = Path(self.config['storage']['staging_dir'])
        self.output_dir.mkdir(exist_ok=True)
        self.staging_dir.mkdir(exist_ok=True)
        
        self.db = DbManager(str(self.output_dir / self.config['storage']['db_name']))
        self.api = ApiClient(self.config['api'])
        self.downloader = HLSDownloader(
            max_workers=self.config['concurrency']['max_segment_tasks']
        )
        self.metadata = self.db.get_all_metadata()
        self.console = Console()
        self.max_workers = self.config['concurrency']['max_video_tasks']
        self.rclone_remote = self.config['rclone']['remote_dest']
        self.lock = threading.Lock()
        self.merge_lock = threading.Lock()
        self.processing_ids = set()
        self._migrate_json_to_db()

    def _migrate_json_to_db(self):
        json_file = self.output_dir / "metadata.json"
        if json_file.exists():
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    old_data = json.load(f)
                for vid, info in old_data.items():
                    if vid not in self.metadata:
                        self.db.save_video(vid, info)
                self.metadata = self.db.get_all_metadata()
                json_file.rename(self.output_dir / "metadata.json.bak")
            except:
                pass

    def save_metadata(self, video_id, info):
        with self.lock:
            self.db.save_video(video_id, info)
            self.metadata[str(video_id)] = info

    def process_video(self, video_id):
        vid_str = str(video_id)
        with self.lock:
            if vid_str in self.metadata and self.metadata[vid_str].get('file_name'):
                return True
            if vid_str in self.processing_ids:
                return True
            self.processing_ids.add(vid_str)

        try:
            time.sleep(random.uniform(1.0, 5.0))
            info_res = self.api.get_video_info(video_id)
            if not info_res or info_res.get('code') != 200:
                return False
                
            vod = info_res['data']
            info = {
                'id': video_id,
                'title': vod.get('title') or vod.get('vod_name'),
                'labels': vod.get('labels', [])
            }
            
            self.console.print(f"[bold magenta][INFO][/bold magenta] 正在处理 ID: [bold white]{video_id}[/bold white] | 标题: [cyan]{info['title']}[/cyan]")
            
            m3u8_url, key_url = self.api.get_play_urls(video_id)
            temp_dir = f"temp_{video_id}"
            file_name = f"{video_id}.mp4"
            staging_file = str(self.staging_dir / file_name)
            
            if self.downloader.run(m3u8_url, key_url, temp_dir):
                with self.merge_lock:
                    merge_res = VideoProcessor.merge_ts_files(temp_dir, staging_file)
                
                if merge_res > 0:
                    shutil.rmtree(temp_dir)
                    
                    if self.is_local:
                        self.console.print(f"[bold yellow][MOVE][/bold yellow] 正在移动至本地: {file_name}")
                        dest_path = self.output_dir / file_name
                        shutil.move(staging_file, dest_path)
                        success = True
                    else:
                        self.console.print(f"[bold yellow][SYNC][/bold yellow] 正在同步至 Rclone: {file_name}")
                        success = VideoProcessor.rclone_move(
                            staging_file, 
                            self.rclone_remote,
                            transfers=str(self.config['rclone']['transfers']),
                            buffer_size=self.config['rclone']['buffer_size'],
                            chunk_size=self.config['rclone']['chunk_size']
                        )
                    
                    if success:
                        info['file_name'] = file_name
                        self.save_metadata(video_id, info)
                        self.console.print(f"[正确] 视频 {video_id} 处理成功")
                        return True
                    else:
                        self.console.print(f"[错误] 视频 {video_id} 搬运/同步失败")
                        if os.path.exists(staging_file): os.remove(staging_file)
                        return False
                else:
                    self.console.print(f"[错误] 视频 {video_id} 本地合并失败")
                    return False
            else:
                self.console.print(f"[错误] 视频 {video_id} 下载失败")
                return False
        finally:
            with self.lock:
                self.processing_ids.discard(vid_str)

    def batch_process(self, start_id, end_id):
        vids = list(range(start_id, end_id + 1))
        self.list_process(vids)
            
    def list_process(self, id_list):
        unique_ids = []
        seen = set()
        for vid in id_list:
            if vid and vid not in seen:
                unique_ids.append(vid)
                seen.add(vid)

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(self.process_video, vid) for vid in unique_ids]
            for future in as_completed(futures):
                try:
                    future.result()
                except:
                    pass

    def search_and_batch_process(self, keyword):
        page = 1
        while True:
            res = self.api.search_videos(keyword, page)
            if not res or res.get('code') != 200:
                break
            
            data_list = res.get('data', {}).get('list', [])
            if not data_list:
                break
            
            vids = [item.get('id') or item.get('vod_id') for item in data_list]
            self.list_process(vids)
            page += 1
            time.sleep(random.uniform(3.0, 6.0))
