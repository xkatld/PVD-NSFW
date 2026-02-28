import requests
import random
import ua_generator

class ApiClient:
    def __init__(self, api_config):
        self.api_base = api_config['api_base']
        self.play_base = api_config['play_base']
        self.token = api_config['token']
        self.session = requests.Session()

    def get_headers(self):
        ua = ua_generator.generate(device='mobile', platform='android')
        return {
            "User-Agent": ua.text,
            "Accept": "application/json",
            "x-token": self.token
        }

    def get_video_info(self, video_id):
        url = f"{self.api_base}/api/vod/info?id={video_id}"
        try:
            response = self.session.get(url, headers=self.get_headers(), timeout=10)
            response.raise_for_status()
            return response.json()
        except:
            return None

    def get_play_urls(self, video_id):
        m3u8_url = f"{self.play_base}/play/{video_id}/1/newvod.plist.m3u8"
        key_url = f"{self.play_base}/play/{video_id}/1/newvod.enc"
        return m3u8_url, key_url

    def search_videos(self, keyword, page=1):
        url = f"{self.api_base}/api/vod/clever?limit=20&page={page}&wd={keyword}"
        try:
            response = self.session.get(url, headers=self.get_headers(), timeout=10)
            response.raise_for_status()
            return response.json()
        except:
            return None
