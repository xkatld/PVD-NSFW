import os
import re
import subprocess
import shutil

class VideoProcessor:
    @staticmethod
    def merge_ts_files(ts_dir, output_file):
        raw_files = os.listdir(ts_dir)
        ts_files = [f for f in raw_files if f not in ["filelist.txt", "merged.mp4"]]
        
        if not ts_files:
            return 0
            
        def get_index(name):
            match = re.search(r"(\d+)", name)
            return int(match.group(1)) if match else 0
            
        ts_files.sort(key=get_index)
        
        filelist_path = os.path.join(ts_dir, "filelist.txt")
        with open(filelist_path, "w", encoding="utf-8") as f:
            for ts_file in ts_files:
                escaped_name = ts_file.replace("'", "'\\''")
                f.write(f"file '{escaped_name}'\n")
        
        try:
            cmd = [
                "ffmpeg", "-f", "concat", "-safe", "0",
                "-i", "filelist.txt", "-c", "copy",
                "-movflags", "+faststart", "-y", "merged.mp4"
            ]
            subprocess.run(cmd, cwd=ts_dir, capture_output=True, check=True)
            
            tmp_output = os.path.join(ts_dir, "merged.mp4")
            if os.path.exists(tmp_output):
                if os.path.exists(output_file):
                    os.remove(output_file)
                shutil.move(tmp_output, output_file)
                return len(ts_files)
        except:
            pass
            
        return 0

    @staticmethod
    def rclone_move(local_file, remote_dest, **kwargs):
        if not os.path.exists(local_file):
            return False
            
        try:
            cmd = [
                'rclone', 'move', local_file, remote_dest, 
                '-P', '--stats', '1s',
                '--onedrive-chunk-size', '240M'
            ]
            subprocess.run(cmd, check=True)
            return True
        except subprocess.CalledProcessError:
            return False
        except:
            return False
