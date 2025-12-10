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

def process_and_save_video(input_path: str, output_path: str, data: tuple, progress_callback=None):
    """
    Reads video, resizes if needed, burns overlay, and saves compressed.
    """
    
    # 1. Resize if too large (e.g. 4K) to save time/space
    try:
        clip = VideoFileClip(input_path)
    except Exception as e:
        if "moov atom not found" in str(e) or "Invalid data found" in str(e):
            raise ValueError(f"The video file appears to be corrupted or incomplete.\n"
                             f"If this is in OneDrive/Dropbox, ensure it is fully downloaded.\n"
                             f"Try copying the file to a local folder (e.g. Desktop) and try again.\n\n"
                             f"Details: {e}")
        raise e
    
    # Downscale to 1080p width if larger, maintaining aspect ratio
    if clip.w > 1920:
        clip = clip.resized(width=1920)
    
    # Create overlay image matching (possibly resized) video size
    overlay_img = create_overlay_image(clip.size, data)
    
    # Create ImageClip
    overlay_clip = (ImageClip(np.array(overlay_img))
                   .with_duration(clip.duration)
                   .with_position(("left", "bottom")))
    
    # Composite
    final = CompositeVideoClip([clip, overlay_clip])
    
    # Logger
    my_logger = EncodeLogger(progress_callback) if progress_callback else None

    # Write
    # Attempt 1: Try NVIDIA GPU (h264_nvenc)
    # Fast, efficient, uses hardware.
    try:
        final.write_videofile(
            output_path, 
            codec='h264_nvenc', 
            audio_codec='aac', 
            preset='p4', # p1=fastest, p7=slowest (highest quality). p4 is medium/balanced.
            ffmpeg_params=['-rc:v', 'vbr', '-cq:v', '28'], # Constant Quality for NVENC
            logger=my_logger,
            threads=os.cpu_count() # Threads for audio/muxing
        )
    except Exception as gpu_error:
        print(f"GPU Encoding failed, falling back to CPU: {gpu_error}")
        
        # Attempt 2: Fallback to CPU (libx264)
        # Using preset='veryfast' for speed and max threads
        final.write_videofile(
            output_path, 
            codec='libx264', 
            audio_codec='aac', 
            preset='veryfast',
            ffmpeg_params=['-crf', '28'],
            logger=my_logger,
            threads=os.cpu_count() or 4 # Use all cores
        )
    
    clip.close()
    final.close()
