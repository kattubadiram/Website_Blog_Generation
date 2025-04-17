import os
import json
import openai
import requests
import pytz
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAIError

# Load environment vars
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WP_USERNAME     = os.getenv("WP_USERNAME")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")
WP_SITE_URL     = os.getenv("WP_SITE_URL")

# Init clients
client = openai.OpenAI(api_key=OPENAI_API_KEY)

def log_blog_to_history(blog_content: str):
    LOG_FILE = "blog_history.txt"
    ts = datetime.now(pytz.utc)\
         .astimezone(pytz.timezone('America/New_York'))\
         .strftime("%Y-%m-%d %H:%M:%S %Z")
    divider = "="*80
    entry = f"\n\n{divider}\nBLOG ENTRY - {ts}\n{divider}\n\n{blog_content}\n"
    with open(LOG_FILE, 'a') as f:
        f.write(entry)
    print(f"📋 Logged to {LOG_FILE}")

def generate_blog():
    system_msg = {
        "role": "system",
        "content": (
            "You are a top‑tier financial intelligence writer. "
            "Output strict JSON with 3 fields:\n"
            "  • \"blog\": a 250‑word market‑moving news post\n"
            "  • \"summary\": a 100‑word brief prefixed with 'SUMMARY:'\n"
            "  • \"title\": a click‑worthy headline (no timestamp)\n"
        )
    }
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[system_msg, {"role":"user","content":""}],
        temperature=0.7
    )
    data    = json.loads(resp.choices[0].message.content)
    blog    = data["blog"].strip()
    summary = data["summary"].strip()
    title   = data["title"].strip()
    log_blog_to_history(blog)
    return blog, summary, title

def generate_header_image(prompt_text: str) -> str:
    """
    Try DALL·E at 1024×1024; if it fails, fall back to Unsplash.
    """
    dalle_prompt = f"Professional, high‑resolution financial markets illustration for: {prompt_text}"
    print(f"[DEBUG] DALL·E prompt: {dalle_prompt!r}")

    try:
        resp = client.images.generate(
            prompt=dalle_prompt,
            n=1,
            size="1024x1024"     # supported square size
        )
        return resp.data[0].url
    except OpenAIError as e:
        print("❌ DALL·E failed, using Unsplash fallback:", e)
        # random finance image from Unsplash (no API key needed)
        return "https://source.unsplash.com/1024x1024/?finance,stock-market"

def upload_image_to_wordpress(image_url: str) -> dict:
    img_data = requests.get(image_url).content
    filename = "header_image.png"
    media = requests.post(
        f"{WP_SITE_URL}/wp-json/wp/v2/media",
        auth=(WP_USERNAME, WP_APP_PASSWORD),
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        files={"file": (filename, img_data, "image/png")}
    )
    media.raise_for_status()
    return media.json()

def save_local(blog: str, summary: str):
    with open("blog_summary.txt","w") as f: f.write(summary)
    with open("blog_post.txt","w") as f: f.write(blog+"\n\n"+summary)
    print("📝 Saved blog and summary locally")

def post_to_wordpress(title: str, content: str, featured_media: int):
    payload = {
        "title": title,
        "content": content,
        "status": "publish",
        "featured_media": featured_media
    }
    resp = requests.post(
        f"{WP_SITE_URL}/wp-json/wp/v2/posts",
        auth=(WP_USERNAME, WP_APP_PASSWORD),
        json=payload
    )
    resp.raise_for_status()
    print(f"📤 Published (status {resp.status_code})")

if __name__ == "__main__":
    # 1) Generate blog + summary + title
    blog_text, summary_text, base_title = generate_blog()

    # 2) Generate & upload header image
    image_url = generate_header_image(base_title)
    media_obj = upload_image_to_wordpress(image_url)
    media_id  = media_obj["id"]
    media_src = media_obj["source_url"]

    # 3) Save locally
    save_local(blog_text, summary_text)

    # 4) Build timestamp + flex header
    est_now     = datetime.now(pytz.utc)\
                   .astimezone(pytz.timezone('America/New_York'))
    ts_readable = est_now.strftime("%B %d, %Y %H:%M")
    header_html = (
        '<div style="display:flex; justify-content:space-between; '
        'align-items:center; margin-bottom:20px;">'
        f'<span style="color:#666; font-size:12px;">{ts_readable} EST</span>'
        # vertical separator + some padding
        '<div style="width:1px; background:#ccc; height:24px;"></div>'
        f'<h1 style="margin:0; padding-left:10px;">{base_title}</h1>'
        '</div>'
    )

    # 5) Embed the featured image + inline after first paragraph
    paragraphs = blog_text.split("\n\n", 1)
    first_para = paragraphs[0]
    rest       = paragraphs[1] if len(paragraphs)>1 else ""
    inline_img = (
        f'\n\n<img src="{media_src}" '
        'style="max-width:100%; display:block; margin:20px 0;" />\n\n'
    )
    blog_with_inline = first_para + inline_img + rest

    # 6) Compose full post HTML
    post_body = (
        f'<img src="{media_src}" '
        'style="max-width:100%; display:block; margin-bottom:20px;" />\n'
        + header_html +
        f'<p><em>{summary_text}</em></p>\n\n'
        + blog_with_inline
    )

    # 7) Publish with featured image
    post_to_wordpress(base_title, post_body, featured_media=media_id)
