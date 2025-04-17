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

# Init OpenAI client
client = openai.OpenAI(api_key=OPENAI_API_KEY)


def log_blog_to_history(blog_content: str):
    """Append the raw blog content to blog_history.txt with timestamp."""
    LOG_FILE = "blog_history.txt"
    ts = datetime.now(pytz.utc) \
             .astimezone(pytz.timezone('America/New_York')) \
             .strftime("%Y-%m-%d %H:%M:%S %Z")
    divider = "=" * 80
    entry = f"\n\n{divider}\nBLOG ENTRY - {ts}\n{divider}\n\n{blog_content}\n"
    with open(LOG_FILE, 'a') as f:
        f.write(entry)
    print("📋 Logged to", LOG_FILE)


def generate_blog():
    """
    Ask the LLM to emit a JSON object with:
      - blog   : 250‑word market‑moving news post
      - summary: 100‑word brief prefixed with 'SUMMARY:'
      - title  : click‑worthy headline (no timestamp)
    """
    system_msg = {
        "role": "system",
        "content": (
            "You are a top‑tier financial intelligence writer. "
            "Output strict JSON with three fields:\n"
            "  • \"blog\": a 250‑word market‑moving news post\n"
            "  • \"summary\": a 100‑word brief prefixed with 'SUMMARY:'\n"
            "  • \"title\": a click‑worthy headline (no timestamp)\n"
        )
    }
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[system_msg, {"role": "user", "content": ""}],
        temperature=0.7
    )
    data = json.loads(resp.choices[0].message.content)
    blog = data["blog"].strip()
    summary = data["summary"].strip()
    title = data["title"].strip()
    log_blog_to_history(blog)
    return blog, summary, title


def extract_keywords(text: str) -> list[str]:
    """
    Use the LLM to extract the top three keywords/phrases
    from the blog text. Returns a list of up to 3 strings.
    Falls back to a default if parsing fails.
    """
    prompt = (
        "Extract the top three most important keywords or phrases "
        "from the following finance article. "
        "Respond in JSON as {\"keywords\": [\"kw1\",\"kw2\",\"kw3\"]} and NOTHING else.\n\n"
        + text
    )
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a keyword extractor. Output ONLY JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.0
    )
    raw = resp.choices[0].message.content.strip()
    try:
        data = json.loads(raw)
        return data.get("keywords", [])[:3]
    except json.JSONDecodeError:
        # log the malformed output for debugging, and fall back
        print("⚠️ Keyword extraction returned invalid JSON:")
        print(raw)
        return ["finance", "markets", "investment"]


def generate_header_image(keywords: list[str]) -> str:
    """
    Build a poster‑style prompt around the top keywords,
    generate via DALL·E-2 (1024×1024), or fall back to Unsplash.
    """
    dalle_prompt = (
        "A poster‑style, high‑impact cover illustration for a finance article, "
        "featuring " + ", ".join(keywords) +
        ". Vibrant, professional, modern design."
    )
    print("[DEBUG] DALL·E prompt:", dalle_prompt)
    try:
        resp = client.images.generate(
            model="dall-e-2",
            prompt=dalle_prompt,
            n=1,
            size="1024x1024"
        )
        return resp.data[0].url
    except OpenAIError as e:
        print("❌ DALL·E failed, falling back to Unsplash:", e)
        return "https://source.unsplash.com/1024x1024/?finance,stock-market"


def upload_image_to_wordpress(image_url: str) -> dict:
    """Download an image from a URL and upload it to WP media library."""
    img_data = requests.get(image_url).content
    filename = "header_image.png"
    media = requests.post(
        f"{WP_SITE_URL}/wp-json/wp/v2/media",
        auth=(WP_USERNAME, WP_APP_PASSWORD),
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        files={"file": (filename, img_data, "image/png")}
    )
    media.raise_for_status()
    return media.json()  # contains "id" and "source_url"


def save_local(blog: str, summary: str):
    """Save summary and blog+summary to local files."""
    with open("blog_summary.txt", "w") as f:
        f.write(summary)
    with open("blog_post.txt", "w") as f:
        f.write(blog + "\n\n" + summary)
    print("📝 Saved locally")


def post_to_wordpress(title: str, content: str, featured_media: int):
    """Publish a new post to WordPress with featured image."""
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
    print("📤 Published post (status", resp.status_code, ")")


if __name__ == "__main__":
    # 1) Generate the blog, summary, and base title
    blog_text, summary_text, base_title = generate_blog()

    # 2) Extract top keywords & generate header image
    keywords = extract_keywords(blog_text)
    image_url = generate_header_image(keywords)
    media_obj = upload_image_to_wordpress(image_url)
    media_id = media_obj["id"]
    media_src = media_obj["source_url"]

    # 3) Save files locally
    save_local(blog_text, summary_text)

    # 4) Build the EST timestamp and combined title
    est_now = datetime.now(pytz.utc).astimezone(pytz.timezone('America/New_York'))
    ts_readable = est_now.strftime("%B %d, %Y %H:%M")
    final_title = f"{ts_readable} EST  |  {base_title}"

    # 5) Create the in‑post header (optional)
    header_html = (
        '<div style="display:flex; justify-content:space-between; '
        'align-items:center; margin-bottom:20px;">'
        f'<span style="color:#666; font-size:12px;">{ts_readable} EST</span>'
        '<div style="width:1px; background:#ccc; height:24px;"></div>'
        f'<h1 style="margin:0; padding-left:10px;">{base_title}</h1>'
        '</div>'
    )

    # 6) Compose the post body: image on top, then header, then summary, then full blog
    post_body = (
        f'<img src="{media_src}" '
        'style="max-width:100%; display:block; margin-bottom:20px;" />\n'
        + header_html +
        f'<p><em>{summary_text}</em></p>\n\n'
        + f'<div>{blog_text}</div>'
    )

    # 7) Publish with timestamped title
    post_to_wordpress(final_title, post_body, featured_media=media_id)
