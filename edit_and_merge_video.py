import os
import numpy as np
from datetime import datetime
from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip
from PIL import Image, ImageDraw, ImageFont

# ------------ CONFIG ------------
AVATAR_VIDEO = 'avatar_video.mp4'
IMAGES_FOLDER = 'ai_images/'   # Folder with images
FINAL_VIDEO = 'video_output.mp4'

FRAME_RATE = 24
PORTRAIT_WIDTH = 720
PORTRAIT_HEIGHT = 1280

SHOW_IMAGE_EVERY = 6
IMAGE_DURATION = 3
IMAGE_FADE = 0.5

def create_text_overlay(text, width, height):
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Use a common font available on Linux runners
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    font_size = 24
    font = ImageFont.truetype(font_path, font_size)

    text_width, text_height = draw.textsize(text, font=font)
    x = width - text_width - 20  # 20px right margin
    y = 20  # 20px top margin

    draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))  # White text

    return np.array(img)

def create_overlay_cutaway_video():
    avatar_clip = VideoFileClip(AVATAR_VIDEO).resize(width=PORTRAIT_WIDTH)
    avatar_clip = avatar_clip.resize(height=PORTRAIT_HEIGHT).set_position(("center", "center"))
    avatar_duration = avatar_clip.duration

    images = sorted([
        f for f in os.listdir(IMAGES_FOLDER)
        if f.lower().endswith(('.png', '.jpg', '.jpeg'))
    ])
    if not images:
        raise Exception("❌ No images found in 'ai_images/' folder.")

    overlay_times = list(range(SHOW_IMAGE_EVERY, int(avatar_duration), SHOW_IMAGE_EVERY))
    extended_images = (images * ((len(overlay_times) // len(images)) + 1))[:len(overlay_times)]

    overlays = []
    for time_sec, img_file in zip(overlay_times, extended_images):
        img_path = os.path.join(IMAGES_FOLDER, img_file)
        img_clip = (
            ImageClip(img_path)
            .resize((PORTRAIT_WIDTH, PORTRAIT_HEIGHT))
            .set_start(time_sec)
            .set_duration(IMAGE_DURATION)
            .crossfadein(IMAGE_FADE)
            .crossfadeout(IMAGE_FADE)
        )
        overlays.append(img_clip)

    # ➡️ Add datetime text overlay
    now = datetime.now()
    datetime_text = now.strftime("%A, %B %d, %Y %I:%M %p")

    text_image_array = create_text_overlay(datetime_text, PORTRAIT_WIDTH, PORTRAIT_HEIGHT)
    text_image_clip = (
        ImageClip(text_image_array, ismask=False)
        .set_duration(avatar_duration)
    )

    final = CompositeVideoClip(
        [avatar_clip, text_image_clip] + overlays,
        size=(PORTRAIT_WIDTH, PORTRAIT_HEIGHT)
    ).set_audio(avatar_clip.audio)

    final.write_videofile(FINAL_VIDEO, fps=FRAME_RATE, codec="libx264", audio_codec="aac")
    print(f"✅ Final video created: {FINAL_VIDEO}")

if __name__ == "__main__":
    create_overlay_cutaway_video()
