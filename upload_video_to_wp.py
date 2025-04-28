import requests
import base64
import os
from dotenv import load_dotenv

# ——— Load credentials from .env ———————————————————————
load_dotenv()
WP_USERNAME = os.getenv("WP_USERNAME")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")
WP_SITE_URL = os.getenv("WP_SITE_URL")
VIDEO_FILE = "video_output.mp4"
VIDEO_TITLE = "AI-Generated Market News Video"

# ——— Upload video to WordPress Media Library ——————————
def upload_video():
    media_endpoint = f"{WP_SITE_URL}/wp-json/wp/v2/media"
    auth = base64.b64encode(f"{WP_USERNAME}:{WP_APP_PASSWORD}".encode()).decode()

    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Disposition": f'attachment; filename="{VIDEO_FILE}"',
        "Content-Type": "video/mp4"
    }

    try:
        with open(VIDEO_FILE, "rb") as f:
            response = requests.post(media_endpoint, headers=headers, data=f)

        if response.status_code == 201:
            video_url = response.json()["source_url"]
            print(f"✅ Uploaded video to WordPress: {video_url}")
            return video_url
        else:
            print(f"❌ Failed to upload video: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error opening video file: {e}")
        return None

# ——— Embed video into latest blog post ——————————————————
def embed_video(video_url):
    auth = base64.b64encode(f"{WP_USERNAME}:{WP_APP_PASSWORD}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/json"
    }

    try:
        # Get most recent post
        posts_resp = requests.get(f"{WP_SITE_URL}/wp-json/wp/v2/posts", headers=headers)
        posts = posts_resp.json()

        if not posts:
            print("❌ No posts found.")
            return

        post_id = posts[0]['id']
        content = posts[0]['content']['rendered']

        # Append styled vertical video embed
        embed_html = f"""
<div style="display: flex; justify-content: flex-end; margin-bottom: 20px;">
  <video controls playsinline style="max-width: 320px; width: 100%; height: auto; border-radius: 8px;">
    <source src="{video_url}" type="video/mp4">
    Your browser does not support the video tag.
  </video>
</div>
"""

        new_content = f"{embed_html.strip()}\n\n{content}"  # Video first, then content
        payload = {"content": new_content}

        update_resp = requests.post(
            f"{WP_SITE_URL}/wp-json/wp/v2/posts/{post_id}",
            headers=headers,
            json=payload
        )

        if update_resp.status_code == 200:
            print("✅ Video embedded successfully into the latest post.")
        else:
            print(f"❌ Failed to embed video: {update_resp.status_code} - {update_resp.text}")

    except Exception as e:
        print(f"❌ Error embedding video: {e}")

# ——— Main ————————————————————————————————————————————————
if __name__ == "__main__":
    video_url = upload_video()
    if video_url:
        embed_video(video_url)
