# upload_audio_and_embed.py

import os
import requests
from dotenv import load_dotenv

# ——— Load environment variables —————————————————————————————
load_dotenv()
WP_USERNAME     = os.getenv("WP_USERNAME")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")
WP_SITE_URL     = os.getenv("WP_SITE_URL")

# Step 1: Upload MP3 to WordPress Media Library
def upload_audio_to_wp(file_path):
    if not os.path.exists(file_path):
        print(f"❌ Error: Audio file {file_path} not found")
        return None
        
    try:
        media_url = f"{WP_SITE_URL}/wp-json/wp/v2/media"
        filename = os.path.basename(file_path)
        headers = {
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": "audio/mpeg"
        }
        with open(file_path, "rb") as f:
            response = requests.post(
                media_url,
                headers=headers,
                data=f,
                auth=(WP_USERNAME, WP_APP_PASSWORD)
            )
        response.raise_for_status()
        audio_url = response.json()["source_url"]
        print("✅ Uploaded to media:", audio_url)

        # ——— Save the uploaded audio URL for later embedding by another script ———
        with open("latest_audio_url.txt", "w", encoding="utf-8") as ff:
            ff.write(audio_url)

        return audio_url

    except Exception as e:
        print(f"❌ Failed to upload audio: {e}")
        return None

# ——— Main execution ————————————————————————————————
if __name__ == "__main__":
    print("▶️ Starting upload_audio_and_embed.py")
    mp3_path = "blog_voiceover.mp3"
    mp3_url = upload_audio_to_wp(mp3_path)
    
    if mp3_url:
        print("✅ Audio uploaded successfully. Ready for embedding with video.")
    else:
        print("⚠️ Audio upload failed.")
