import os
import requests
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
WP_USERNAME = os.getenv("WP_USERNAME")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")
WP_SITE_URL = os.getenv("WP_SITE_URL")

# Step 1: Upload MP3 to WordPress Media Library
def upload_audio_to_wp(file_path):
    if not os.path.exists(file_path):
        print(f"❌ Error: Audio file {file_path} not found")
        return None
        
    try:
        media_url = f"{WP_SITE_URL}/wp-json/wp/v2/media"
        filename = os.path.basename(file_path)
        headers = {
            'Content-Disposition': f'attachment; filename={filename}',
            'Content-Type': 'audio/mpeg'
        }
        with open(file_path, 'rb') as f:
            response = requests.post(media_url, headers=headers, data=f, auth=(WP_USERNAME, WP_APP_PASSWORD))
        
        response.raise_for_status()
        audio_url = response.json()["source_url"]
        print("✅ Uploaded to media:", audio_url)
        return audio_url
    except Exception as e:
        print(f"❌ Failed to upload audio: {e}")
        return None

# Step 2: Embed audio right after the title in the latest published post
def embed_audio_in_latest_post(audio_url):
    if not audio_url:
        print("❌ No audio URL provided, cannot embed")
        return False
        
    try:
        # Get the latest post
        posts_url = f"{WP_SITE_URL}/wp-json/wp/v2/posts"
        posts_response = requests.get(posts_url, auth=(WP_USERNAME, WP_APP_PASSWORD))
        posts_response.raise_for_status()
        posts = posts_response.json()
        
        if not posts:
            print("❌ No posts found to update.")
            return False
            
        # Sort posts by date to find the latest one
        latest_post = sorted(posts, key=lambda p: p['date'], reverse=True)[0]
        post_id = latest_post["id"]
        
        # Get the current content
        try:
            current_content = latest_post["content"]["rendered"]
        except KeyError:
            print("⚠️ Could not access rendered content, using fallback")
            current_content = latest_post.get("content", {}).get("raw", "")
            if not current_content:
                print("⚠️ No content found in the post")
                current_content = "<p>Financial market update.</p>"
        
        # Create audio embed HTML with introduction text
        audio_embed = '<p><strong>Prefer to listen? Here\'s an audio version of this article:</strong></p>'
        audio_embed += f'<p><audio controls><source src="{audio_url}" type="audio/mpeg">Your browser does not support the audio element.</audio></p>'
        
        # Find the position after the title (h1)
        # This pattern looks for the closing </h1> tag
        title_pattern = r'</h1>'
        match = re.search(title_pattern, current_content)
        
        if match:
            # Insert audio player right after the </h1> tag
            insert_position = match.end()
            updated_content = current_content[:insert_position] + "\n\n" + audio_embed + "\n\n" + current_content[insert_position:]
            print("🎯 Inserting audio after the title (h1 tag)")
        else:
            # Fallback - insert after the header div if title not found
            header_div_pattern = r'</div>\s*</div>\s*</div>'
            match = re.search(header_div_pattern, current_content)
            
            if match:
                insert_position = match.end()
                updated_content = current_content[:insert_position] + "\n\n" + audio_embed + "\n\n" + current_content[insert_position:]
                print("🎯 Inserting audio after the header div")
            else:
                # Last resort - insert at the beginning
                updated_content = audio_embed + "\n\n" + current_content
                print("⚠️ Could not find title or header position, adding audio at the beginning")
        
        # Update the post
        update_payload = {"content": updated_content}
        update_url = f"{WP_SITE_URL}/wp-json/wp/v2/posts/{post_id}"
        update_response = requests.post(update_url, json=update_payload, auth=(WP_USERNAME, WP_APP_PASSWORD))
        update_response.raise_for_status()
        print(f"🔗 Audio embedded in post ID {post_id}")
        return True
    except Exception as e:
        print(f"❌ Failed to embed audio: {e}")
        return False

# Main execution
if __name__ == "__main__":
    try:
        print("Starting audio upload process...")
        mp3_path = "blog_voiceover.mp3"
        mp3_url = upload_audio_to_wp(mp3_path)
        
        if mp3_url:
            success = embed_audio_in_latest_post(mp3_url)
            if success:
                print("✅ Audio successfully uploaded and embedded")
            else:
                print("⚠️ Failed to embed audio, but upload was successful")
        else:
            print("⚠️ Process completed with errors")
    except Exception as e:
        print(f"❌ Unexpected error in main process: {e}")
