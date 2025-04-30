import os
import time
import random
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# ------------------ CONFIG -------------------
HEYGEN_API_KEY = os.environ.get('HEYGEN_API_KEY')
SCRIPT_FILE = 'video_prompt.txt'
AVATAR_OUTPUT = 'avatar_video.mp4'
VIDEO_WIDTH = 1280
VIDEO_HEIGHT = 720
SPEAK_SPEED = 1.0
VIDEO_TIMEOUT = 300  # seconds

# ------------------ RETRY SESSION -------------------
def get_retry_session(retries=3, backoff_factor=0.5):
    session = requests.Session()
    retry = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET", "POST"]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

session = get_retry_session()

# ------------------ STEP 1: Read Script -------------------
def read_script(script_file):
    with open(script_file, 'r', encoding='utf-8') as f:
        return f.read()

# ------------------ STEP 2: Get Live Avatars -------------------
def fetch_avatars():
    url = "https://api.heygen.com/v2/avatars"
    headers = {
        "Accept": "application/json",
        "X-Api-Key": HEYGEN_API_KEY
    }
    response = session.get(url, headers=headers)
    response.raise_for_status()
    avatars = response.json().get("data", {}).get("avatars", [])
    return avatars

# ------------------ STEP 3: Random Avatar + Its Default Voice -------------------
def select_avatar_with_voice(avatars):
    valid_avatars = [a for a in avatars if a.get("default_voice_id")]
    if not valid_avatars:
        raise Exception("❌ No avatars with default_voice_id found.")

    selected = random.choice(valid_avatars)
    avatar_id = selected.get("avatar_id")
    voice_id = selected.get("default_voice_id")
    print(f"🎭 Selected avatar: {selected.get('avatar_name')}")
    print(f"🧍 Avatar ID: {avatar_id}")
    print(f"🗣️ Voice ID (default): {voice_id}")
    return avatar_id, voice_id

# ------------------ STEP 4: Generate Video -------------------
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

    response = session.post(url, headers=headers, json=payload)
    response.raise_for_status()
    video_id = response.json().get("data", {}).get("video_id")
    if not video_id:
        raise Exception("❌ Failed to retrieve video_id from HeyGen response.")

    return wait_for_video_ready(video_id)

# ------------------ STEP 5: Wait for Video -------------------
def wait_for_video_ready(video_id):
    headers = { "X-Api-Key": HEYGEN_API_KEY }
    status_url = f"https://api.heygen.com/v2/video/status?video_id={video_id}"

    start_time = time.time()
    while True:
        response = session.get(status_url, headers=headers)
        response.raise_for_status()
        data = response.json().get("data", {})

        if data.get("status") == "completed":
            print("✅ Video is ready!")
            return data["video_url"]
        elif data.get("status") == "failed":
            raise Exception("❌ Video generation failed.")

        if time.time() - start_time > VIDEO_TIMEOUT:
            raise TimeoutError("⏳ Video generation timed out.")

        print("⏳ Waiting for video to finish rendering...")
        time.sleep(10)

# ------------------ STEP 6: Download Video -------------------
def download_video(video_url, output_path=AVATAR_OUTPUT):
    r = session.get(video_url)
    r.raise_for_status()
    with open(output_path, 'wb') as f:
        f.write(r.content)
    print(f"📥 Avatar video saved as {output_path}")

# ------------------ MAIN -------------------
if __name__ == "__main__":
    if not HEYGEN_API_KEY:
        raise ValueError("❌ Missing HEYGEN_API_KEY environment variable")

    script_text = read_script(SCRIPT_FILE)
    avatars = fetch_avatars()
    if not avatars:
        raise Exception("❌ Could not fetch avatars.")

    avatar_id, voice_id = select_avatar_with_voice(avatars)
    avatar_video_url = generate_avatar_video(script_text, avatar_id, voice_id)
    download_video(avatar_video_url)
