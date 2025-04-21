import os
import base64
import requests
import openai
from dotenv import load_dotenv

# Load credentials from .env file
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WP_USERNAME = os.getenv("WP_USERNAME")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")
WP_SITE_URL = os.getenv("WP_SITE_URL")

# Initialize OpenAI client
client = openai.OpenAI(api_key=OPENAI_API_KEY)


def generate_blog_poster_from_text(blog_text, output_path="blog_poster.png"):
    """
    Generate a DALL·E blog poster image from blog content and save to file.
    Returns the image path if successful, None otherwise.
    """
    try:
        print("🧠 Generating DALL·E prompt from blog content...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You write creative visual prompts for DALL·E to generate blog posters."},
                {"role": "user", "content": f"Write a modern, visually engaging poster prompt for a blog post with this content:\n\n{blog_text}"}
            ],
            temperature=0.7
        )
        prompt = response.choices[0].message.content.strip()
        print(f"🎯 Generated Prompt: {prompt}")

        print("🎨 Generating image using DALL·E...")
        image_response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size="1792x1024"
        )
        image_url = image_response.data[0].url
        img_data = requests.get(image_url).content

        with open(output_path, "wb") as f:
            f.write(img_data)

        print(f"✅ Poster image saved at: {output_path}")
        return output_path

    except Exception as e:
        print(f"❌ Error generating blog poster: {e}")
        return None


def upload_image_to_wp(image_path):
    """
    Uploads an image file to WordPress and returns the media JSON object.
    """
    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return {}

    try:
        media_endpoint = f"{WP_SITE_URL}/wp-json/wp/v2/media"

        # Use either predefined auth header or base64 encode user:password
        env_token = os.getenv("WP_AUTH_HEADER")
        if env_token:
            auth_header = "Basic " + env_token
        else:
            credentials = f"{WP_USERNAME}:{WP_APP_PASSWORD}"
            token = base64.b64encode(credentials.encode()).decode()
            auth_header = f"Basic {token}"

        headers = {
            "Authorization": auth_header,
            "Content-Disposition": f'attachment; filename="{os.path.basename(image_path)}"',
            "Content-Type": "image/png"
        }

        with open(image_path, "rb") as img_file:
            response = requests.post(media_endpoint, headers=headers, data=img_file)

        if response.status_code == 201:
            print("✅ Poster uploaded to WordPress.")
            return response.json()
        else:
            print(f"❌ WordPress upload failed: {response.status_code} - {response.text}")
            return {}

    except Exception as e:
        print(f"❌ Error during upload: {e}")
        return {}
