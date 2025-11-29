import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from moviepy import ColorClip
from services.video_processor import process_and_save_video

def create_dummy_video(path):
    # Create a 2 second red video
    # MoviePy 2.0+ might require duration set separately or different init
    clip = ColorClip(size=(640, 480), color=(255, 0, 0))
    clip = clip.with_duration(2)
    clip.write_videofile(path, fps=24)

def test_overlay():
    src = "test_src.mp4"
    dst = "test_dst.mp4"
    
    try:
        print("Creating dummy video...")
        create_dummy_video(src)
        
        print("Processing video...")
        data = ("BAT-001", "12345", "John Doe")
        process_and_save_video(src, dst, data)
        
        if os.path.exists(dst):
            print("Success: Output video created.")
            # Clean up
            os.remove(src)
            os.remove(dst)
        else:
            print("Error: Output video not found.")
    except Exception:
        import traceback
        with open("error.log", "w") as f:
            traceback.print_exc(file=f)
        traceback.print_exc()

if __name__ == "__main__":
    test_overlay()
