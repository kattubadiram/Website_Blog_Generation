# create_overlay_cutaway_video.py

import os
import numpy as np
from datetime import datetime
from zoneinfo import ZoneInfo
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip
from PIL import Image, ImageDraw, ImageFont

# -------------------------
# Configuration constants
# -------------------------
AVATAR_VIDEO = 'avatar_video.mp4'
IMAGES_FOLDER = 'ai_images/'
FINAL_VIDEO = 'video_output_shorts.mp4'

FRAME_RATE = 24
SHOW_IMAGE_EVERY = 6        # Seconds between image overlays
IMAGE_DURATION = 3          # Duration each image stays on screen
IMAGE_FADE = 0.5            # Duration of fade in/out for each image
SHORTS_WIDTH = 1080
SHORTS_HEIGHT = 1920
MAX_DURATION = 60           # Shorts must be less than or equal to 60s

# -------------------------
# Create a transparent image with timestamp text
# -------------------------
def create_text_overlay(text, width, height):
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    font_size = 36
    font = ImageFont.truetype(font_path, font_size)

    text_width, text_height = draw.textsize(text, font=font)
    x = width - text_width - 40
    y = 40

    draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))
    return np.array(img)

# -------------------------
# Create final video with image overlays and timestamp
# -------------------------
def create_overlay_cutaway_video():
    # Load avatar video
    avatar_clip = VideoFileClip(AVATAR_VIDEO).resize((SHORTS_WIDTH, SHORTS_HEIGHT))
    
    # Limit duration to 60 seconds (Shorts requirement)
    avatar_duration = min(avatar_clip.duration, MAX_DURATION)
    avatar_clip = avatar_clip.subclip(0, avatar_duration)

    # Collect overlay images
    images = sorted([
        f for f in os.listdir(IMAGES_FOLDER)
        if f.lower().endswith(('.png', '.jpg', '.jpeg'))
    ])
    if not images:
        raise Exception("No images found in 'ai_images/' folder.")

    # Schedule overlay image times
    overlay_times = list(range(SHOW_IMAGE_EVERY, int(avatar_duration), SHOW_IMAGE_EVERY))
    extended_images = (images * ((len(overlay_times) // len(images)) + 1))[:len(overlay_times)]

    # Create overlay image clips
    overlays = []
    for time_sec, img_file in zip(overlay_times, extended_images):
        img_path = os.path.join(IMAGES_FOLDER, img_file)
        img_clip = (
            ImageClip(img_path)
            .resize((SHORTS_WIDTH, SHORTS_HEIGHT))
            .set_start(time_sec)
            .set_duration(IMAGE_DURATION)
            .crossfadein(IMAGE_FADE)
            .crossfadeout(IMAGE_FADE)
        )
        overlays.append(img_clip)

    # Create timestamp overlay in Eastern Time
    now = datetime.now(ZoneInfo("America/New_York"))
    datetime_text = now.strftime("%A, %B %d, %Y %I:%M %p ET")
    text_image_array = create_text_overlay(datetime_text, SHORTS_WIDTH, SHORTS_HEIGHT)
    text_image_clip = ImageClip(text_image_array, ismask=False).set_duration(avatar_duration)

    # Combine everything into one composite clip
    final = CompositeVideoClip(
        [avatar_clip, text_image_clip] + overlays,
        size=(SHORTS_WIDTH, SHORTS_HEIGHT)
    ).set_audio(avatar_clip.audio)

    # Export the final video
    final.write_videofile(
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
