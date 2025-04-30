import os
import time
import json
import random
import requests
from datetime import datetime

# ------------------ CONFIG -------------------
HEYGEN_API_KEY = os.environ.get('HEYGEN_API_KEY')  # <-- from GitHub Secret
SCRIPT_FILE = 'video_prompt.txt'
AVATAR_OUTPUT = 'avatar_video.mp4'

VIDEO_WIDTH = 1280
VIDEO_HEIGHT = 720
SPEAK_SPEED = 1.0

# ------------------ FUNCTIONS -------------------
def download_json(url, file_name):
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        with open(file_name, "w") as f:
            json.dump(response.json(), f, indent=2)
        print(f"✅ Saved {file_name}")
    else:
        print(f"❌ Failed to fetch {url}: {response.status_code}")

def load_json(file_name):
    with open(file_name, "r") as f:
        return json.load(f)

def select_random_avatar(data):
    avatars = data.get("data", {}).get("avatars", [])
    if not avatars:
        raise Exception("No avatars found.")
    return random.choice(avatars)

def get_voice_id_by_first_name(first_name, voices_data):
    voices = voices_data.get("data", {}).get("voices", [])
    for voice in voices:
        if first_name.lower() in voice.get("name", "").lower():
            return voice.get("voice_id"), voice.get("name")
    return None, None

def read_script(script_file):
    with open(script_file, 'r', encoding='utf-8') as f:
        return f.read()

def generate_avatar_video(script_text, avatar_id, voice_id):
    url = "https://api.heygen.com/v2/video/generate"
    headers = {
        "X-Api-Key": HEYGEN_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "video_inputs": [
            {
                "character": {
                    "type": "avatar",
                    "avatar_id": avatar_id,
                    "avatar_style": "normal"
                },
                "voice": {
                    "type": "text",
                    "input_text": script_text,
                    "voice_id": voice_id,
                    "speed": SPEAK_SPEED
                }
            }
        ],
        "dimension": {
            "width": VIDEO_WIDTH,
            "height": VIDEO_HEIGHT
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()

    video_id = response.json()["data"]["video_id"]
    return wait_for_video_ready(video_id)

def wait_for_video_ready(video_id):
    headers = { "X-Api-Key": HEYGEN_API_KEY }
    status_url = f"https://api.heygen.com/v1/video_status.get?video_id={video_id}"

    while True:
        response = requests.get(status_url, headers=headers)
        response.raise_for_status()
        data = response.json()["data"]

        if data["status"] == "completed":
            print("✅ Video is ready!")
            return data["video_url"]
        elif data["status"] == "failed":
            raise Exception("❌ Video generation failed.")
        
        print("⏳ Waiting for video to finish rendering...")
        time.sleep(10)

def download_video(video_url, output_path=AVATAR_OUTPUT):
    r = requests.get(video_url)
    with open(output_path, 'wb') as f:
        f.write(r.content)
    print(f"📥 Avatar video saved as {output_path}")

# ------------------ MAIN -------------------
if __name__ == "__main__":
    if not HEYGEN_API_KEY:
        raise ValueError("❌ Missing HEYGEN_API_KEY environment variable")

    HEADERS = { "X-Api-Key": HEYGEN_API_KEY }

    # Download and load avatar/voice data
    download_json("https://api.heygen.com/v2/avatars", "avatars.json")
    download_json("https://api.heygen.com/v2/voices", "voices.json")

    avatars_data = load_json("avatars.json")
    voices_data = load_json("voices.json")

    # Pick a random avatar
    avatar = select_random_avatar(avatars_data)
    avatar_id = avatar.get("avatar_id")
    avatar_name = avatar.get("name")
    print(f"\n🎭 Selected Avatar: {avatar_name}")
    print(f"🧍 Avatar ID: {avatar_id}")

    # Match voice by avatar's first name
    first_name = avatar_name.split()[0] if avatar_name else ""
    voice_id, voice_name = get_voice_id_by_first_name(first_name, voices_data)

    if not voice_id:
        raise Exception(f"❌ No matching voice found for avatar first name: {first_name}")

    print(f"🗣️ Matched Voice: {voice_name} (ID: {voice_id})")

    # Generate video
    script_text = read_script(SCRIPT_FILE)
    avatar_video_url = generate_avatar_video(script_text, avatar_id, voice_id)
    download_video(avatar_video_url)
