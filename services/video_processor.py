import os
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import VideoFileClip, ImageClip, CompositeVideoClip

def create_overlay_image(size, data):
    """
    Creates a transparent image with the text overlay.
    data: tuple of (battery_code, battery_no, operator_name)
    """
    w, h = size
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Try to load a nice font, fallback to default
    try:
        font = ImageFont.truetype("arial.ttf", 24)
        bold_font = ImageFont.truetype("arialbd.ttf", 24)
    except IOError:
        font = ImageFont.load_default()
        bold_font = font

    lines = [
        f"Battery code : {data[0]}",
        f"Battery Number : {data[1]}",
        f"Operator Name : {data[2]}"
    ]
    
    # Bottom left position
    # 20px padding from bottom/left
    line_height = 30
    start_y = h - (len(lines) * line_height) - 20
    x = 20
    
    for i, line in enumerate(lines):
        y = start_y + (i * line_height)
        
        # Draw shadow
        draw.text((x+2, y+2), line, font=bold_font, fill=(0, 0, 0, 200))
        # Draw text
        draw.text((x, y), line, font=bold_font, fill=(255, 255, 255, 255))
        
    return img

from proglog import ProgressBarLogger
import time

class EncodeLogger(ProgressBarLogger):
    def __init__(self, callback=None):
        super().__init__()
        self._progress_cb = callback
        self.start_time = None

    def bars_callback(self, bar, attr, value, old_value=None):
        if not self._progress_cb: return
        
        if self.start_time is None:
            self.start_time = time.time()
            
        total = self.bars[bar]['total']
        if total > 0:
            progress = (value / total) * 100
            
            # Calculate ETA
            elapsed = time.time() - self.start_time
            if progress > 0:
                eta_seconds = (elapsed / progress) * (100 - progress)
                # Format ETA
                if eta_seconds < 60:
                    eta_str = f"{int(eta_seconds)}s"
                else:
                    eta_str = f"{int(eta_seconds//60)}m {int(eta_seconds%60)}s"
            else:
                eta_str = "..."
                
            self._progress_cb(int(progress), eta_str)

import subprocess
import re
from imageio_ffmpeg import get_ffmpeg_exe

def get_video_metadata(path):
    clip = VideoFileClip(path)
    w, h = clip.w, clip.h
    duration = clip.duration
    clip.close()
    return w, h, duration

def process_and_save_video(input_path: str, output_path: str, data: tuple, progress_callback=None):
    """
    Uses direct FFmpeg command for maximum speed.
    Bypasses Python-side frame processing.
    """
    # 1. Get metadata
    w, h, duration = get_video_metadata(input_path)
    
    # 2. Calculate target size (limit to 1080p width)
    target_w = w
    target_h = h
    if w > 1920:
        ratio = 1920 / w
        target_w = 1920
        target_h = int(h * ratio)
        # Ensure even dimensions for encoding
        if target_h % 2 != 0: target_h -= 1
    
    # 3. Create overlay image at TARGET size
    overlay_img = create_overlay_image((target_w, target_h), data)
    
    # Save overlay to temp file
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tf:
        overlay_img.save(tf, format="PNG")
        overlay_path = tf.name
        
    ffmpeg_exe = get_ffmpeg_exe()
    
    # 4. Construct FFmpeg command
    # Filter: Scale input -> Overlay PNG on top
    # Note: We must scale input video to match the overlay size we just created
    filter_complex = f"[0:v]scale={target_w}:{target_h}[bg];[bg][1:v]overlay=0:0"
    
    # Common args
    cmd_base = [
        ffmpeg_exe, '-y',
        '-i', input_path,
        '-i', overlay_path,
        '-filter_complex', filter_complex,
        '-c:a', 'aac'
    ]
    
    # Encoder args (Try NVENC first)
    # Using 'g' (GoP size) optimization often helps seeking/speed too
    nvenc_args = ['-c:v', 'h264_nvenc', '-preset', 'p4', '-rc:v', 'vbr', '-cq:v', '28']
    cpu_args = ['-c:v', 'libx264', '-preset', 'veryfast', '-crf', '28', '-threads', str(os.cpu_count() or 4)]
    
    def run_ffmpeg(args):
        # Merge base + encoder + output
        full_cmd = cmd_base + args + [output_path]
        
        process = subprocess.Popen(
            full_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True, # text mode
            encoding='utf-8',
            errors='replace' 
        )
        
        # Parse progress from stderr
        # Duration format in stderr: Duration: 00:00:30.50
        # Progress format: time=00:00:15.20
        
        while True:
            line = process.stderr.readline()
            if not line and process.poll() is not None:
                break
                
            if line and progress_callback:
                # Naive parsing
                if "time=" in line:
                    # extract time
                    match = re.search(r"time=(\d{2}):(\d{2}):(\d{2}\.\d{2})", line)
                    if match:
                        h_val, m_val, s_val = map(float, match.groups())
                        current_seconds = h_val*3600 + m_val*60 + s_val
                        percent = min(100, int((current_seconds / duration) * 100))
                        
                        # ETA calculation is tricky without stored start time in this scope
                        # Simpler: just show percent and 'Processing...'
                        # Or pass simple "..." as ETA for now
                        progress_callback(percent, "...")

        if process.returncode != 0:
            raise Exception("FFmpeg failed")

    try:
        try:
            run_ffmpeg(nvenc_args)
        except Exception as e:
            print(f"NVENC failed ({e}), falling back to CPU...")
            run_ffmpeg(cpu_args)
    finally:
        # Cleanup temp overlay
        if os.path.exists(overlay_path):
            os.remove(overlay_path)
