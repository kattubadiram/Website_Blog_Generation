import openai
import requests
import os
import base64
from dotenv import load_dotenv

# ——— Load credentials —————————————————————————————
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WP_USERNAME = os.getenv("WP_USERNAME")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")
WP_SITE_URL = os.getenv("WP_SITE_URL")

client = openai.OpenAI(api_key=OPENAI_API_KEY)

# ——— Step 1: Generate visual prompt from blog content ——————————
def generate_blog_poster_from_text(blog_text, output_path="blog_poster.png"):
    """Generate a blog poster image from blog content using DALL·E."""
    try:
        print("🧠 Generating poster prompt...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You write creative visual prompts for DALL·E to generate blog posters."
                },
                {
                    "role": "user",
                    "content": (
                        f"Write a modern, visually engaging poster prompt for a blog post with this content:\n\n{blog_text}"
                    )
                }
            ],
            temperature=0.7
        )
        prompt = response.choices[0].message.content.strip()
        print(f"🎯 Prompt: {prompt}")

        print("🎨 Generating poster image via DALL·E...")
        image_response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size="1792x1024"  # ✅ WIDE landscape for blog posters
        )

        image_url = image_response.data[0].url
        img_data = requests.get(image_url).content

        with open(output_path, "wb") as f:
            f.write(img_data)

        print(f"✅ Poster saved to {output_path}")
        return output_path

    except Exception as e:
        print(f"❌ Failed to generate poster from blog text: {e}")
        return None

# ——— Step 2: Upload poster image to WordPress ———————————————
def upload_image_to_wp(image_path):
    """Upload an image to WordPress and return the media object JSON."""
    if not os.path.exists(image_path):
        print("❌ Image not found:", image_path)
        return {}

    try:
        media_endpoint = f"{WP_SITE_URL}/wp-json/wp/v2/media"

        # Safely handle token or basic auth
        env_token = os.environ.get("WP_AUTH_HEADER")
        if env_token:
            auth_header = "Basic " + env_token
        else:
            token = base64.b64encode(f"{WP_USERNAME}:{WP_APP_PASSWORD}".encode()).decode()
            auth_header = f"Basic {token}"

        headers = {
            "Authorization": auth_header,
            "Content-Disposition": f'attachment; filename="{os.path.basename(image_path)}"',
            "Content-Type": "image/png"
        }

        with open(image_path, "rb") as img:
            response = requests.post(media_endpoint, headers=headers, data=img)

        if response.status_code == 201:
            print("✅ Uploaded poster to WordPress")
            return response.json()
        else:
            print(f"❌ Failed to upload poster: {response.status_code} - {response.text}")
            return {}

    except Exception as e:
        print(f"❌ Upload error: {e}")
        return {}
