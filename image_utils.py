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
    """Generate a cinematic and realistic DALL·E-style poster prompt from blog content using GPT-4o, with few-shot examples."""
    few_shot_intro = (
        "You are a professional visual prompt engineer working for a top-tier editorial image agency. "
        "Your task is to translate financial or news blog content into detailed, cinematic prompts for realistic poster generation using AI (like DALL·E). "
        "Use a storytelling approach — frame the scene as if it's a real photo taken in a financial newsroom or trading floor. "
        "Incorporate human emotion, natural lighting, symbolic props, and accurate workplace settings. "
        "Avoid any text overlays in the image. Focus on the mood, sector, and specific events mentioned. "
        "The final prompt should feel like a single frame from a high-end documentary or editorial magazine cover."
    )

    few_shot_examples = (
        "Example 1:\n"
        "Blog: Healthcare stocks dropped, with UNH down 2.16% amid claim policy uncertainties.\n"
        "Prompt: A somber analyst sits at a dimly lit desk in a high-rise office, surrounded by red graphs on monitors. A stethoscope rests on a folder labeled 'Policy Review' as tension hangs in the air.\n\n"

        "Example 2:\n"
        "Blog: Tesla surged 4.7% leading a bullish market as tech rebounded strongly.\n"
        "Prompt: A modern trading floor bathed in golden light, a glowing Tesla logo on a digital board. A bronze bull sculpture stands beside it, symbolizing strength and momentum.\n\n"

        "Example 3:\n"
        "Blog: Markets closed mixed ahead of the Fed meeting; energy stocks climbed while tech lagged.\n"
        "Prompt: In a low-lit trading hub, an investor looks at diverging green and red charts. An oil barrel icon glows faintly on one screen while others show tumbling tech indices. The mood is uncertain, reflective of split market sentiment.\n\n"
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": few_shot_intro
            },
            {
                "role": "user",
                "content": (
                    few_shot_examples +
                    f"Now based on the following blog, generate a cinematic, photorealistic DALL·E poster prompt using a white, blue, and grey color palette that is friendly for light mode screens.:\n\n{blog_text}"
                )
            }
        ],
        temperature=0.8
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
        print("🧠 Generating DALL·E prompt...")
        prompt = generate_prompt_from_blog(blog_text)
        print(f"🎯 Prompt: {prompt}")

        print("🎨 Generating poster image...")
        image_path = generate_dalle_image(prompt, output_path)
        print(f"✅ Poster saved: {image_path}")

        print("☁️ Uploading to WordPress...")
        media_info = upload_image_to_wp(image_path)
        print("✅ Uploaded:", media_info.get("source_url"))
        return media_info

    except Exception as e:
        print(f"❌ Error in poster generation/upload: {e}")
        return {}
