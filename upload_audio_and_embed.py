import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

WP_USERNAME    = os.getenv("WP_USERNAME")
WP_APP_PASSWORD= os.getenv("WP_APP_PASSWORD")
WP_SITE_URL    = os.getenv("WP_SITE_URL")

def upload_audio_to_wp(file_path):
    media_url = f"{WP_SITE_URL}/wp-json/wp/v2/media"
    filename  = os.path.basename(file_path)
    headers = {
        'Content-Disposition': f'attachment; filename={filename}',
        'Content-Type': 'audio/mpeg'
    }
    with open(file_path, 'rb') as f:
        response = requests.post(media_url, headers=headers, data=f,
                                 auth=(WP_USERNAME, WP_APP_PASSWORD))
    response.raise_for_status()
    audio_url = response.json()["source_url"]
    print("✅ Uploaded to media:", audio_url)
    return audio_url

def embed_audio_in_latest_post(audio_url):
    posts_url = f"{WP_SITE_URL}/wp-json/wp/v2/posts"
    posts     = requests.get(posts_url, auth=(WP_USERNAME, WP_APP_PASSWORD)).json()
    if not posts:
        raise Exception("❌ No posts found to update.")

    latest_post = sorted(posts, key=lambda p: p['date'], reverse=True)[0]
    post_id      = latest_post["id"]
    current_content = latest_post["content"]["rendered"]

    # Embed audio at the very top
    audio_embed = (
        '<p>If you’d rather listen, hit play below:</p>\n'
        f'<audio controls><source src="{audio_url}" type="audio/mpeg"></audio>'
    )
    updated_content = audio_embed + "\n\n" + current_content

    update_url = f"{WP_SITE_URL}/wp-json/wp/v2/posts/{post_id}"
    update_response = requests.post(update_url,
                                    json={"content": updated_content},
                                    auth=(WP_USERNAME, WP_APP_PASSWORD))
    update_response.raise_for_status()
    print(f"🔗 Audio embedded at top of post ID {post_id}")

if __name__ == "__main__":
    mp3_url = upload_audio_to_wp("blog_voiceover.mp3")
    embed_audio_in_latest_post(mp3_url)
