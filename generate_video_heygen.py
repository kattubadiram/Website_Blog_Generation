import os
import time
import requests
from datetime import datetime

# ------------------ CONFIG -------------------
HEYGEN_API_KEY = os.environ.get('HEYGEN_API_KEY')  # <-- from GitHub Secret
SCRIPT_FILE = 'video_prompt.txt'
AVATAR_OUTPUT = 'avatar_video.mp4'

VIDEO_WIDTH = 1280
VIDEO_HEIGHT = 720
SPEAK_SPEED = 1.0

# Avatars and their corresponding voices
AVATAR_VOICE_PAIRS = [
    {
        "avatar_id": "Gala_sitting_businesssofa_front",
        "voice_id": "35b75145af9041b298c720f23375f578",  # Gala - Lifelike
        "name": "Gala"
    },
    {
        "avatar_id": "Piper_sitting_businesssofa_side",
        "voice_id": "aeeb145b5a2f418d8f41456f79644f33",  # Piper - Lifelike
        "name": "Piper Business Sofa Front"
    },
    {
        "avatar_id": "Masha Office Front",
        "voice_id": "72a90016199b4a31bd6d8a003eef8ee2",  # Masha - Lifelike
        "name": "Masha"
    },
    {
        "avatar_id": "Georgia_expressive_2024112701",
        "voice_id": "511ffd086a904ef593b608032004112c",  # Sabine - Lifelike (Closest match for Georgia)
        "name": "Georgia (Upper Body)"
    },
    {
        "avatar_id": "Georgia_standing_casual_side",
        "voice_id": "511ffd086a904ef593b608032004112c",  # Sabine - Lifelike (Closest match for Georgia)
        "name": "Georgia Office Front"
    },
    {
        "avatar_id": "June_HR_public",
        "voice_id": "387ec7c290324b55a6bb6ab654f016ef",  # Aubrey - Lifelike
        "name": "Aubrey"
    }
]

# ------------------ STEP 1: Read Script -------------------
def read_script(script_file):
    with open(script_file, 'r', encoding='utf-8') as f:
        return f.read()

# ------------------ STEP 2: Pick Today's Avatar and Voice -------------------
def get_today_avatar_and_voice():
    today = datetime.now().weekday()  # Monday=0, Sunday=6
    avatar_voice = AVATAR_VOICE_PAIRS[today % len(AVATAR_VOICE_PAIRS)]
    print(f"🎭 Today's avatar: {avatar_voice['name']}")
    print(f"🗣️ Today's voice ID: {avatar_voice['voice_id']}")
    return avatar_voice["avatar_id"], avatar_voice["voice_id"]

# ------------------ STEP 3: Generate Avatar Video -------------------
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

# ------------------ STEP 4: Download Video -------------------
def download_video(video_url, output_path=AVATAR_OUTPUT):
    r = requests.get(video_url)
    with open(output_path, 'wb') as f:
        f.write(r.content)
    print(f"📥 Avatar video saved as {output_path}")

# ------------------ MAIN -------------------
if __name__ == "__main__":
    if not HEYGEN_API_KEY:
        raise ValueError("❌ Missing HEYGEN_API_KEY environment variable")
    
    script_text = read_script(SCRIPT_FILE)
    today_avatar, today_voice = get_today_avatar_and_voice()
    avatar_video_url = generate_avatar_video(script_text, today_avatar, today_voice)
    download_video(avatar_video_url)
