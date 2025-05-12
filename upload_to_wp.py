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
# Embed YouTube video and audio into latest post
# -------------------------
def embed_youtube_video(youtube_url, audio_url=None):
    if not youtube_url:
        print("No YouTube URL provided, cannot embed.")
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

        # Build embed layout with YouTube and optional audio
        embed_parts = [
            '<div style="display:flex; align-items:center; justify-content:center; gap:40px; margin-bottom:30px;">',
            '  <div style="flex:0 0 320px;">',
            f'    <iframe width="100%" height="215" src="{youtube_url}" '
            'frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" '
            'allowfullscreen style="border-radius:12px;"></iframe>',
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
        print("Embedded YouTube video, title, and audio successfully.")
        return True

    except Exception as e:
        print(f"Embedding failed: {e}")
        return False

# -------------------------
# Main execution
# -------------------------
if __name__ == "__main__":
    print("Running upload_video_to_wp.py")
    YOUTUBE_VIDEO_URL = "https://www.youtube.com/embed/YOUTUBE ID HERE"  # Use embed format
    result = embed_youtube_video(YOUTUBE_VIDEO_URL, AUDIO_URL)
    print("Done embedding media." if result else "Done with errors.")
