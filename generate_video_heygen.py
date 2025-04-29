import os
import time
import requests
import random
from datetime import datetime
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# ------------------ CONFIG -------------------
HEYGEN_API_KEY = os.environ.get('HEYGEN_API_KEY')  # <-- Set this in GitHub Secrets or local env
SCRIPT_FILE = 'video_prompt.txt'
AVATAR_OUTPUT = 'avatar_video.mp4'

VIDEO_WIDTH = 1280
VIDEO_HEIGHT = 720
SPEAK_SPEED = 1.0
VIDEO_TIMEOUT = 300  # seconds (5 minutes)

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

# ------------------ AVATAR / VOICE PAIRS -------------------
AVATAR_VOICE_PAIRS = [
    {
        "avatar_id": "Gala_sitting_businesssofa_front",
        "voice_id": "35b75145af9041b298c720f23375f578",  # Gala - Lifelike
        "name": "Gala"
    },
    {
        "avatar_id": "Masha_standing_office_front",
        "voice_id": "72a90016199b4a31bd6d8a003eef8ee2",  # Masha - Lifelike
        "name": "Masha"
    },
    {
        "avatar_id": "Georgia_expressive_2024112701",
        "voice_id": "511ffd086a904ef593b608032004112c",  # Georgia (Sabine matching voice)
        "name": "Georgia (Upper Body)"
    },
    {
        "avatar_id": "Georgia_standing_casual_side",
        "voice_id": "511ffd086a904ef593b608032004112c",  # Georgia Office
        "name": "Georgia Office Front"
    },
    {
        "avatar_id": "Adriana_BizTalk_Front_public",
        "voice_id": "387ec7c290324b55a6bb6ab654f016ef",  # Aubrey - Lifelike
        "name": "Adriana"
    },
    {
        "avatar_id": "Amanda_in_Blue_Shirt_Front",
        "voice_id": "387ec7c290324b55a6bb6ab654f016ef",  # Aubrey - Lifelike
        "name": "Amanda"
    },
    {
        "avatar_id": "Amelia_standing_business_training_front",
        "voice_id": "387ec7c290324b55a6bb6ab654f016ef",  # Aubrey - Lifelike
        "name": "Amelia"
    },
    {
        "avatar_id": "Annie_expressive2_public",
        "voice_id": "387ec7c290324b55a6bb6ab654f016ef",  # Aubrey - Lifelike
        "name": "Annie"
    },
    {
        "avatar_id": "Carlotta_Business_Front_public",
        "voice_id": "387ec7c290324b55a6bb6ab654f016ef",  # Aubrey - Lifelike
        "name": "Carlotta"
    },
    {
        "avatar_id": "Caroline_Business_Sitting_Front_public",
        "voice_id": "387ec7c290324b55a6bb6ab654f016ef",  # Aubrey - Lifelike
        "name": "Caroline"
    },
    {
        "avatar_id": "Chloe_standing_lounge_side",
        "voice_id": "387ec7c290324b55a6bb6ab654f016ef",  # Aubrey - Lifelike
        "name": "Chloe"
    },
    {
        "avatar_id": "Violante_Business_Sitting_Front_public",
        "voice_id": "387ec7c290324b55a6bb6ab654f016ef",  # Aubrey - Lifelike
        "name": "Violante"
    },
    {
        "avatar_id": "Elenora_Casual_Front_public",
        "voice_id": "387ec7c290324b55a6bb6ab654f016ef",  # Aubrey - Lifelike
        "name": "Elenora"
    },
    {
        "avatar_id": "Fina_Casual_Side_public",
        "voice_id": "387ec7c290324b55a6bb6ab654f016ef",  # Aubrey - Lifelike
        "name": "Fina"
    },
    {
        "avatar_id": "Jin_Suit_Front_public",
        "voice_id": "387ec7c290324b55a6bb6ab654f016ef",  # Aubrey - Lifelike
        "name": "Jin"
    },
    {
        "avatar_id": "Yola_Casual_Side_public",
        "voice_id": "387ec7c290324b55a6bb6ab654f016ef",  # Aubrey - Lifelike
        "name": "Yola"
    },
    {
        "avatar_id": "Zara_Business_Sitting_Front_public",
        "voice_id": "387ec7c290324b55a6bb6ab654f016ef",  # Aubrey - Lifelike
        "name": "Zara"
    },
    {
        "avatar_id": "Artur_sitting_office_front",
        "voice_id": "e5f89518d5564535885cb6d674e57173",  # Aubrey - Lifelike
        "name": "Artur"
    },
    {
        "avatar_id": "Berat_standing_office_side",
        "voice_id": "e5f89518d5564535885cb6d674e57173",  # Aubrey - Lifelike
        "name": "Berat"
    },
    {
        "avatar_id": "Bojan_standing_businesstraining_side",
        "voice_id": "e5f89518d5564535885cb6d674e57173",  # Aubrey - Lifelike
        "name": "Bojan"
    },
    {
        "avatar_id": "Brandon_Business_Sitting_Front_public",
        "voice_id": "e5f89518d5564535885cb6d674e57173",  # Aubrey - Lifelike
        "name": "Brandon"
    },
    {
        "avatar_id": "Brent_standing_sofa_side",
        "voice_id": "e5f89518d5564535885cb6d674e57173",  # Aubrey - Lifelike
        "name": "Brent"
    },
    {
        "avatar_id": "Byron_Jacket_Side_public",
        "voice_id": "e5f89518d5564535885cb6d674e57173",  # Aubrey - Lifelike
        "name": "Byron"
    },
    {
        "avatar_id": "Chad_in_Blue_Shirt_Left",
        "voice_id": "e5f89518d5564535885cb6d674e57173",  # Aubrey - Lifelike
        "name": "Chad"
    },
    {
        "avatar_id": "Conrad_standing_house_front",
        "voice_id": "e5f89518d5564535885cb6d674e57173",  # Aubrey - Lifelike
        "name": "Conrad"
    },
    {
        "avatar_id": "Darnell_Blue_Shirt_Left",
        "voice_id": "e5f89518d5564535885cb6d674e57173",  # Aubrey - Lifelike
        "name": "Darnell"
    }
]

# ------------------ STEP 1: Read Script -------------------
def read_script(script_file):
    with open(script_file, 'r', encoding='utf-8') as f:
        return f.read()

# ------------------ STEP 2: Pick Avatar and Voice -------------------
def get_random_avatar_and_voice():
    avatar_voice = random.choice(AVATAR_VOICE_PAIRS)
    print(f"🎭 Selected avatar: {avatar_voice['name']}")
    print(f"🧍 Avatar ID: {avatar_voice['avatar_id']}")
    print(f"🗣️ Voice ID: {avatar_voice['voice_id']}")
    return avatar_voice["avatar_id"], avatar_voice["voice_id"], avatar_voice["name"]

# ------------------ STEP 3: Generate Video -------------------
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

# ------------------ STEP 4: Wait for Video -------------------
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

# ------------------ STEP 5: Download Video -------------------
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
    today_avatar, today_voice, today_name = get_random_avatar_and_voice()
    avatar_video_url = generate_avatar_video(script_text, today_avatar, today_voice)
    download_video(avatar_video_url)
