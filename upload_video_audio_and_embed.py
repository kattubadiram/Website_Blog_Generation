import os
import requests
from dotenv import load_dotenv

# Load env
load_dotenv() 

WP_USERNAME = os.getenv("WP_USERNAME")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")
WP_SITE_URL = os.getenv("WP_SITE_URL")

# Upload voiceover
def upload_audio(file_path="voiceover.mp3"):
    file_name = os.path.basename(file_path)
    media_url = f"{WP_SITE_URL}/wp-json/wp/v2/media"
    headers = {
        "Content-Disposition": f"attachment; filename={file_name}",
        "Content-Type": "audio/mpeg"
    }

    with open(file_path, 'rb') as f:
        response = requests.post(
            media_url,
            headers=headers,
            data=f,
            auth=(WP_USERNAME, WP_APP_PASSWORD)
        )

    if response.status_code in [200, 201]:
        print("✅ Audio uploaded")
        return response.json()["source_url"]
    else:
        raise Exception(f"Upload failed: {response.status_code}\n{response.text}")

# Update latest post to embed audio
def embed_audio_in_latest_post(audio_url):
    # Get latest post
    posts_url = f"{WP_SITE_URL}/wp-json/wp/v2/posts?per_page=1"
    res = requests.get(posts_url, auth=(WP_USERNAME, WP_APP_PASSWORD))

    if res.status_code != 200:
        raise Exception(f"Failed to fetch post: {res.text}")

    post = res.json()[0]
    post_id = post["id"]
    old_content = post["content"]["rendered"]

    # Embed audio
    audio_embed = f"""
    <h3>🎧 Listen to the Voiceover</h3>
    <audio controls>
      <source src="{audio_url}" type="audio/mpeg">
      Your browser does not support the audio tag.
    </audio>
    """
    new_content = old_content + audio_embed

    update_url = f"{WP_SITE_URL}/wp-json/wp/v2/posts/{post_id}"
    update_res = requests.post(
        update_url,
        auth=(WP_USERNAME, WP_APP_PASSWORD),
        headers={"Content-Type": "application/json"},
        json={"content": new_content}
    )

    if update_res.status_code in [200, 201]:
        print("✅ Post updated with audio player")
    else:
        raise Exception(f"Failed to update post: {update_res.text}")

# Run
if __name__ == "__main__":
    audio_url = upload_audio()
    embed_audio_in_latest_post(audio_url)
