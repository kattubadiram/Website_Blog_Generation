import requests
import base64
import os
from dotenv import load_dotenv

# ——— Load credentials —————————————————————————
load_dotenv()
WP_USERNAME = os.getenv("WP_USERNAME")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")
WP_SITE_URL = os.getenv("WP_SITE_URL")
VIDEO_FILE = "video_output.mp4"
VIDEO_TITLE = "AI-Generated Market News Video"

# ——— Upload video to WordPress Media ——————————————
def upload_video():
    media_endpoint = f"{WP_SITE_URL}/wp-json/wp/v2/media"
    auth = base64.b64encode(f"{WP_USERNAME}:{WP_APP_PASSWORD}".encode()).decode()

    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Disposition": f'attachment; filename="{VIDEO_FILE}"',
        "Content-Type": "video/mp4"
    }

    with open(VIDEO_FILE, "rb") as f:
        response = requests.post(media_endpoint, headers=headers, data=f)

    if response.status_code == 201:
        video_url = response.json()["source_url"]
        print(f"✅ Uploaded video to WordPress: {video_url}")
        return video_url
    else:
        print(f"❌ Failed to upload video: {response.text}")
        return None

# ——— Embed video in latest blog post ——————————————————
def embed_video(video_url):
    auth = base64.b64encode(f"{WP_USERNAME}:{WP_APP_PASSWORD}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/json"
    }

    # Get most recent post
    posts = requests.get(f"{WP_SITE_URL}/wp-json/wp/v2/posts", headers=headers).json()
    if not posts:
        print("❌ No posts found.")
        return

    post_id = posts[0]['id']
    content = posts[0]['content']['rendered']  # ✅ FIXED

    # ✅ Place video at the end of the post
    new_content = f'{content}\n\n<video controls width="100%">\n  <source src="{video_url}" type="video/mp4">\n</video>'
    payload = {"content": new_content}

    resp = requests.post(f"{WP_SITE_URL}/wp-json/wp/v2/posts/{post_id}", headers=headers, json=payload)

    if resp.status_code == 200:
        print("✅ Video embedded successfully.")
    else:
        print(f"❌ Failed to embed video: {resp.text}")

# ——— Main Execution ————————————————————————————
if __name__ == "__main__":
    video_url = upload_video()
    if video_url:
        embed_video(video_url)
