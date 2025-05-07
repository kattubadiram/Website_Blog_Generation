import ffmpeg
import os
from glob import glob
from natsort import natsorted

IMG_DIR = "ai_images"
AUDIO_FILE = "video_voiceover.mp3"
OUTPUT = "video_output.mp4"
TEMP_DIR = "temp_frames"

# ——— Create individual videos from each image ——————————————————
def create_video_from_images(image_files, slide_duration=5):
    os.makedirs(TEMP_DIR, exist_ok=True)

    for i, img_path in enumerate(image_files):
        output_path = os.path.join(TEMP_DIR, f"slide_{i:03d}.mp4")
        (
            ffmpeg
            .input(img_path, loop=1, t=slide_duration)
            .filter('scale', 1080, -1)
            .output(output_path, vcodec='libx264', pix_fmt='yuv420p', movflags='faststart')
            .overwrite_output()
            .run()
        )
        print(f" Created slide video: {output_path}")
    return sorted(glob(f"{TEMP_DIR}/slide_*.mp4"))

# ——— Concatenate all slide videos ————————————————————————
def concatenate_videos(video_files):
    list_file = "concat_list.txt"
    with open(list_file, "w") as f:
        for file in video_files:
            f.write(f"file '{file}'\n")

    output_path = "slides_combined.mp4"
    (
        ffmpeg
        .input(list_file, format='concat', safe=0)
        .output(output_path, c='copy')
        .overwrite_output()
        .run()
    )
    return output_path

# ——— Merge concatenated video with audio ————————————————————
def add_audio_to_video(video_path, audio_path, output_path):
    video_input = ffmpeg.input(video_path)
    audio_input = ffmpeg.input(audio_path).filter("atempo", 1.25)  # ⚡ ADJUST AUDIO SPEED HERE

    (
        ffmpeg
        .output(video_input, audio_input, output_path, vcodec='libx264', acodec='aac', strict='experimental')
        .overwrite_output()
        .run()
    )
    print(f" Final video with audio saved to {output_path}")

# ——— Main workflow ————————————————————————————————————————
if __name__ == "__main__":
    image_files = natsorted(glob(f"{IMG_DIR}/scene_*.png"))
    if not image_files:
        print(" No images found in ai_images/. Cannot generate video.")
        exit(1)

    slide_videos = create_video_from_images(image_files, slide_duration=5)
    merged_video = concatenate_videos(slide_videos)
    add_audio_to_video(merged_video, AUDIO_FILE, OUTPUT)
