import os
import json
import openai
import requests
import pytz
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAIError

# Import updated image utilities
import image_utils

# ——— Load credentials —————————————————————————————
load_dotenv()
OPENAI_API_KEY   = os.getenv("OPENAI_API_KEY")
WP_USERNAME     = os.getenv("WP_USERNAME")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")
WP_SITE_URL     = os.getenv("WP_SITE_URL")

client = openai.OpenAI(api_key=OPENAI_API_KEY)

# ——— Helper Functions ———————————————————————————————

def log_blog_to_history(blog_content: str):
    LOG_FILE = "blog_history.txt"
    ts = datetime.now(pytz.utc)\
             .astimezone(pytz.timezone('America/New_York'))\
             .strftime("%Y-%m-%d %H:%M:%S %Z")
    divider = "=" * 80
    entry = f"\n\n{divider}\nBLOG ENTRY - {ts}\n{divider}\n\n{blog_content}\n"
    with open(LOG_FILE, "a") as f:
        f.write(entry)
    print("📋 Logged to", LOG_FILE)

def generate_blog():
    system = {
        "role":"system",
        "content":(
            "You are a senior financial journalist at a top-tier global financial news organization like Bloomberg. "
            "Your expertise is in delivering authoritative, data-driven analysis of market movements and economic trends. "
            "Write in a precise, sophisticated tone that financial professionals and serious investors expect. "
            "Include specific figures, expert perspectives, and nuanced market insights. "
            "Analyze both immediate market reactions and potential longer-term implications. "
            "Focus on institutional investor concerns rather than retail trading tips. "
        
            "Output strict JSON with three fields:\n"
            "  • \"blog\": a 250-word sophisticated market analysis that blends breaking news with contextual insights. "
            "Include relevant market data points (indices, yields, currency movements) and reference specific financial "
            "institutions or analysts where appropriate. Maintain balanced perspective while highlighting key risk factors. "
            "Connect current events to broader economic narratives.\n"
            "  • \"summary\": a 100-word executive brief prefixed with 'SUMMARY:' that distills the core market "
            "implications for institutional investors\n"
            "  • \"title\": a precise, authoritative headline that signals depth and sophistication rather than "
            "sensationalism (no timestamp)"
        )
    }
    
    try:
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[system, {"role":"user","content":""}],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        data = json.loads(resp.choices[0].message.content)
        blog = data["blog"].strip()
        summary = data["summary"].strip()
        title = data["title"].strip()

    except Exception as e:
        print(f"⚠️ Error processing AI response: {e}")
        blog = "Markets continue to adapt..."
        summary = "SUMMARY: Financial markets are experiencing..."
        title = "Market Update: Strategic Positioning in Current Economic Climate"

    log_blog_to_history(blog)
    return blog, summary, title

def save_local(blog: str, summary: str):
    try:
        with open("blog_summary.txt","w") as f: f.write(summary)
        with open("blog_post.txt","w") as f: f.write(blog + "\n\n" + summary)
        print("📝 Saved locally")
    except IOError as e:
        print(f"❌ Failed to save local files: {e}")

def post_to_wordpress(title: str, content: str, featured_media: int):
    try:
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
    except requests.RequestException as e:
        print(f"❌ Failed to post to WordPress: {e}")

# ——— Main Execution ——————————————————————————————

if __name__ == "__main__":
    try:
        # 1) Create blog content
        print("📝 Generating blog content...")
        blog_text, summary_text, base_title = generate_blog()

        # 2) Generate poster image from blog content using updated utils
        print("🎨 Generating and uploading blog poster...")
        poster_path = image_utils.generate_blog_poster_from_text(blog_text)
        media_obj = image_utils.upload_image_to_wp(poster_path)
        media_id = media_obj.get("id", 0)
        media_src = media_obj.get("source_url", "")

        # 3) Save blog and summary locally
        save_local(blog_text, summary_text)

        # 4) Build final post title with timestamp
        est_now = datetime.now(pytz.utc).astimezone(pytz.timezone('America/New_York'))
        ts_readable = est_now.strftime("%B %d, %Y %H:%M")
        final_title = f"{ts_readable} EST  |  {base_title}"

        # 5) Build HTML header
        header_html = (
            '<div style="display:flex; align-items:center; margin-bottom:20px;">'
            f'<div style="flex:1;"><img src="{media_src}" style="width:100%; height:auto;" /></div>'
            '<div style="flex:1; display:flex; flex-direction:column; justify-content:center; padding-left:20px;">'
            f'<div style="color:#666; font-size:12px; margin-bottom:8px;">{ts_readable} EST</div>'
            f'<h1 style="margin:0; font-size:24px;">{base_title}</h1>'
            '</div>'
            '</div>'
        )

        # 6) Final blog body
        post_body = (
            header_html +
            f'<p><em>{summary_text}</em></p>\n\n'
            f'<div>{blog_text}</div>'
        )

        # 7) Post to WordPress
        print("📤 Publishing to WordPress...")
        post_to_wordpress(final_title, post_body, featured_media=media_id)

        print("✅ Done!")

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
