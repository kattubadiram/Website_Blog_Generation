# create_overlay_cutaway_video.py

import os
from moviepy.editor import VideoFileClip
from datetime import datetime
from zoneinfo import ZoneInfo

# -------------------------
# Configuration constants
# (kept unchanged for workflow compatibility)
# -------------------------
AVATAR_VIDEO = 'avatar_video.mp4'
IMAGES_FOLDER = 'ai_images/'         # no longer used, left for compatibility
FINAL_VIDEO  = 'video_output.mp4'

FRAME_RATE   = 24
SHOW_IMAGE_EVERY = 6                 # unused
IMAGE_DURATION   = 3                 # unused
IMAGE_FADE       = 0.5               # unused
SHORTS_WIDTH  = 1080
SHORTS_HEIGHT = 1920
MAX_DURATION  = 60                   # Shorts must be ≤ 60 s

# -------------------------
# Main function — converts avatar video to portrait
# -------------------------
def create_overlay_cutaway_video():
    # Load avatar video
    avatar_clip = VideoFileClip(AVATAR_VIDEO)

    # Trim to Shorts-legal length
    avatar_duration = min(avatar_clip.duration, MAX_DURATION)
    avatar_clip = avatar_clip.subclip(0, avatar_duration)

    # Resize so the smaller dimension fits, then crop center to 1080 × 1920
    scale_factor = max(SHORTS_WIDTH / avatar_clip.w, SHORTS_HEIGHT / avatar_clip.h)
    resized_clip = avatar_clip.resize(scale_factor)
    portrait_clip = resized_clip.crop(
        x_center=resized_clip.w / 2,
        y_center=resized_clip.h / 2,
        width=SHORTS_WIDTH,
        height=SHORTS_HEIGHT
    )

    # Preserve original audio (if any)
    final_clip = portrait_clip.set_audio(avatar_clip.audio)

    # Export
    final_clip.write_videofile(
        FINAL_VIDEO,
        fps=FRAME_RATE,
        codec="libx264",
        audio_codec="aac",
        preset="ultrafast",
        threads=4
    )
    print(f"Shorts-ready video created: {FINAL_VIDEO}")

# -------------------------
# Entry point
# -------------------------
if __name__ == "__main__":
    create_overlay_cutaway_video()
