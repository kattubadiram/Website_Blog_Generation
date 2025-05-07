# upload_video_to_wp.py

import os
import requests
import base64
from dotenv import load_dotenv

# -------------------------
# Load WordPress credentials
# -------------------------
load_dotenv()
WP_USERNAME     = os.getenv("WP_USERNAME")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")
WP_SITE_URL     = os.getenv("WP_SITE_URL")

# -------------------------
# Load latest audio URL from file (if available)
# -------------------------
AUDIO_FILE = "latest_audio_url.txt"
AUDIO_URL = None
if os.path.exists(AUDIO_FILE):
    with open(AUDIO_FILE, "r", encoding="utf-8") as f:
        AUDIO_URL = f.read().strip()
    print(f"Loaded audio URL: {AUDIO_URL}")
else:
    print("No audio URL file found; continuing without audio.")

# -------------------------
# Upload local video to WordPress Media Library
# -------------------------
def upload_video():
    media_endpoint = f"{WP_SITE_URL}/wp-json/wp/v2/media"
    auth_header = base64.b64encode(f"{WP_USERNAME}:{WP_APP_PASSWORD}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Disposition": 'attachment; filename="video_output.mp4"',
        "Content-Type": "video/mp4"
    }

    try:
        with open("video_output.mp4", "rb") as f:
            resp = requests.post(media_endpoint, headers=headers, data=f)
        resp.raise_for_status()
        video_url = resp.json().get("source_url")
        print(f"Uploaded video: {video_url}")
        return video_url
    except Exception as e:
        print(f"Video upload failed: {e}")
        return None

# -------------------------
# Embed video, title, and optional audio into latest post
# -------------------------
def embed_video(video_url, audio_url=None):
    if not video_url:
        print("No video URL provided, cannot embed.")
        return False

    auth_header = base64.b64encode(f"{WP_USERNAME}:{WP_APP_PASSWORD}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/json"
    }

    try:
        # Get latest post
        resp = requests.get(f"{WP_SITE_URL}/wp-json/wp/v2/posts", headers=headers)
        resp.raise_for_status()
        posts = resp.json()
        if not posts:
            print("No posts found.")
            return False

        latest = posts[0]
        post_id      = latest["id"]
        title_html   = latest["title"]["rendered"]
        content_html = latest["content"]["rendered"]

        # Build embed layout with video and optional audio
        embed_parts = [
            '<div style="display:flex; align-items:center; justify-content:center; gap:40px; margin-bottom:30px;">',
            '  <div style="flex:0 0 320px;">',
            f'    <video controls playsinline style="width:100%; height:auto; border-radius:12px;">',
            f'      <source src="{video_url}" type="video/mp4">',
            '      Your browser does not support the video tag.',
            '    </video>',
            '  </div>',
            '  <div style="flex:1; max-width:600px;">',
            f'    <h1 style="margin:0 0 20px; font-size:28px; text-align:center;">{title_html}</h1>',
        ]

        if audio_url:
            embed_parts += [
                '    <p style="text-align:center;"><strong>Prefer to listen?</strong></p>',
                '    <audio controls style="width:100%; margin-top:10px;">',
                f'      <source src="{audio_url}" type="audio/mpeg">',
                '      Your browser does not support the audio element.',
                '    </audio>',
            ]

        embed_parts += [
            '  </div>',
            '</div>'
        ]

        embed_html = "\n".join(embed_parts)
        new_content = embed_html + "\n\n" + content_html

        # Update post with embedded media
        update_resp = requests.post(
            f"{WP_SITE_URL}/wp-json/wp/v2/posts/{post_id}",
            headers=headers,
            json={"content": new_content}
        )
        update_resp.raise_for_status()
        print("Embedded video, title, and audio successfully.")
        return True

    except Exception as e:
        print(f"Embedding failed: {e}")
        return False

# -------------------------
# Main execution
# -------------------------
if __name__ == "__main__":
    print("Running upload_video_to_wp.py")
    vid_url = upload_video()
    result = embed_video(vid_url, AUDIO_URL)
    print("Done embedding media." if result else "Done with errors.")
