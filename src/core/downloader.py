import requests
import re
import os
import time
import random
from urllib.parse import urljoin
from Crypto.Cipher import AES
from concurrent.futures import ThreadPoolExecutor, as_completed

from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn

class HLSDownloader:
    def __init__(self, max_workers=4, ua_list=None):
        self.max_workers = max_workers
        self.ua_list = ua_list or ["okhttp/3.12.0"]
        self.session = requests.Session()

    def download_file(self, url, max_retries=3):
        for attempt in range(max_retries):
            try:
                headers = {
                    "User-Agent": random.choice(self.ua_list),
                    "Accept-Encoding": "gzip",
                }
                response = self.session.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                return response.content
            except Exception:
                if attempt < max_retries - 1:
                    time.sleep(1)
        return None

    def parse_m3u8(self, m3u8_content, m3u8_url):
        lines = m3u8_content.decode('utf-8').split('\n')
        ts_list = []
        key_uri = None
        ts_base_url = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('#EXT-X-KEY:'):
                match = re.search(r'URI="([^"]+)"', line)
                if match:
                    key_uri = match.group(1)
            elif line and not line.startswith('#'):
                if line.startswith('http'):
                    if not ts_base_url:
                        ts_base_url = line.rsplit('/', 1)[0] + '/'
                    ts_list.append(line.split('/')[-1])
                else:
                    ts_list.append(line.split('/')[-1])
        
        if not ts_base_url:
            ts_base_url = m3u8_url.rsplit('/', 1)[0] + '/'
        return ts_list, key_uri, ts_base_url

    def decrypt_ts(self, ts_data, key):
        cipher = AES.new(key, AES.MODE_CBC, key)
        decrypted = cipher.decrypt(ts_data)
        pad_len = decrypted[-1]
        if pad_len <= 16:
            return decrypted[:-pad_len]
        return decrypted

    def download_segment(self, args):
        time.sleep(random.uniform(0.1, 0.5))
        ts_url, ts_name, key = args
        ts_data = self.download_file(ts_url)
        if ts_data:
            try:
                decrypted = self.decrypt_ts(ts_data, key)
                return ts_name, decrypted, True
            except:
                return ts_name, ts_data, True
        return ts_name, None, False

    def run(self, m3u8_url, key_url, temp_dir):
        m3u8_content = self.download_file(m3u8_url)
        if not m3u8_content:
            return False
        
        ts_list, key_uri, ts_base_url = self.parse_m3u8(m3u8_content, m3u8_url)
        actual_key_url = urljoin(m3u8_url, key_uri) if key_uri else key_url
        key = self.download_file(actual_key_url)
        
        if not key or len(key) != 16:
            key = b'\x00' * 16

        os.makedirs(temp_dir, exist_ok=True)
        tasks = [(urljoin(ts_base_url, ts), ts, key) for ts in ts_list]
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("[bold white]{task.completed}/{task.total} [cyan]分片[/cyan]"),
            TimeRemainingColumn(),
        ) as progress:
            task = progress.add_task("[cyan]正在获取分片", total=len(ts_list))
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_task = {executor.submit(self.download_segment, task): task for task in tasks}
                for future in as_completed(future_to_task):
                    ts_name, data, success = future.result()
                    if data:
                        with open(os.path.join(temp_dir, ts_name), 'wb') as f:
                            f.write(data)
                    progress.update(task, advance=1)
        return True
