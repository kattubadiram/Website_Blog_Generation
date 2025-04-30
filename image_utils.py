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

def generate_prompt_from_blog(blog_text):
    """Generate a deeply symbolic, context-driven poster prompt using GPT-4o."""
    prompt_template = f"""
You are an expert prompt engineer specializing in poster generation with DALL·E. 
Your job is to extract the underlying sentiment and market context from the following financial blog and generate a modern, cinematic-style image prompt. Avoid referencing people unless essential. Prioritize:
- Symbolism (e.g., red charts, coins, screens, scale, buildings)
- Environment (e.g., trading floor, data center, lab, desk scene)
- Lighting/mood (e.g., dim, dramatic, cold, energetic, warm)
- Objects/labels (e.g., 'Dow +0.95%', 'UNH -2.16%', 'Gold ▼')

Return a DALL·E 3–compatible image prompt that evokes the blog’s emotional tone and economic event.

Blog Content:
{blog_text}
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You generate cinematic DALL·E image prompts for blog posters."},
            {"role": "user", "content": prompt_template}
        ],
        temperature=0.7
    )
    return response.choices[0].message.content.strip()


def generate_dalle_image(prompt, output_path="blog_poster.png"):
    """Generate image using DALL·E and save to disk."""
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
    return output_path


def upload_image_to_wp(image_path):
    """Upload an image to WordPress and return the media object JSON."""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    media_endpoint = f"{WP_SITE_URL}/wp-json/wp/v2/media"

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
        return response.json()
    else:
        raise Exception(f"Upload failed: {response.status_code} - {response.text}")


# ——— Combined Utility Function ————————————————————————
def fetch_and_upload_blog_poster(blog_text, output_path="blog_poster.png"):
    """End-to-end: Generate DALL·E image and upload to WordPress."""
    try:
        print("🧠 Generating enhanced DALL·E prompt...")
        prompt = generate_prompt_from_blog(blog_text)
        print(f"🎯 Generated Prompt:\n{prompt}\n")

        print("🎨 Generating poster image...")
        image_path = generate_dalle_image(prompt, output_path)
        print(f"✅ Poster saved to: {image_path}")

        print("☁️ Uploading image to WordPress...")
        media_info = upload_image_to_wp(image_path)
        print("✅ Uploaded Successfully:", media_info.get("source_url"))
        return media_info

    except Exception as e:
        print(f"❌ Error in poster generation/upload: {e}")
        return {}
