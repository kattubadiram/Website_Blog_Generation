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
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WP_USERNAME = os.getenv("WP_USERNAME")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")
WP_SITE_URL = os.getenv("WP_SITE_URL")

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
        "role": "system",
        "content": (
            "You are a senior science and technology journalist at a globally respected publication like Nature, Science, or The New York Times Science section. "
            "Your expertise lies in delivering deeply researched, factually accurate, and technically rigorous news and analysis across emerging technologies, scientific breakthroughs, and their broader societal implications. "
            "Write in a clear, authoritative, and intellectually engaging tone suitable for professionals, researchers, policymakers, and serious technologists. "
            "Your reporting must be based on current, peer-reviewed research, press releases from reputable institutions, and credible mainstream science journalism. Always triple-check facts with recent, verifiable sources. "
            "Distinguish speculative developments from validated findings. Provide context, citations, and potential impact, both immediate and long-term.\n\n"
            "Output strict JSON with three fields:\n"
            "  • \"blog\": a 250-word science and tech news analysis that blends breaking developments with historical and technical context. "
            "Include named institutions (e.g., MIT, NASA, OpenAI), reference specific technologies or studies (e.g., CRISPR, quantum computing, GPT-5), and maintain a balanced tone that highlights both promise and uncertainty. "
            "Explain why this matters to the scientific community, industry, or public policy. Always cite your factual sources from live news or scientific publications.\n"
            "  • \"summary\": a 100-word executive brief prefixed with 'SUMMARY:' that distills the significance of the development for professionals in science, R&D, or tech policy.\n"
            "  • \"title\": a precise, informative headline that reflects scientific accuracy and avoids hype or oversimplification (no timestamp)."
        )
    }

    try:
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[system, {"role": "user", "content": ""}],
            temperature=0.7,
            response_format="json"
        )
        data = json.loads(resp.choices[0].message.content)
        blog = data["blog"].strip()
        summary = data["summary"].strip()
        title = data["title"].strip()
    except Exception as e:
        print(f"⚠️ Error processing AI response: {e}")
        blog = "Recent developments in science and technology remain underreported."
        summary = "SUMMARY: Stay informed on key breakthroughs across global scientific and tech institutions."
        title = "Science & Tech Update: Critical Developments in Research and Innovation"

    log_blog_to_history(blog)
    return blog, summary, title

def save_local(blog: str, summary: str):
    try:
        with open("blog_summary.txt", "w") as f:
            f.write(summary)
        with open("blog_post.txt", "w") as f:
            f.write(blog + "\n\n" + summary)
        print("📝 Saved locally")
    except IOError as e:
        print(f"❌ Failed to save local files: {e}")

def generate_video_prompt(summary_text):
    try:
        print("🎙️ Generating video narration prompt from blog summary...")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You write concise, 2-sentence narrations for science and tech shorts videos."
                },
                {
                    "role": "user",
                    "content": f"Write a 2-sentence narration suitable for a science or tech short video based on this summary:\n\n{summary_text}"
                }
            ],
            temperature=0.6
        )
        narration = response.choices[0].message.content.strip()
        with open("video_prompt.txt", "w") as f:
            f.write(narration)
        print("✅ Saved video narration to video_prompt.txt")
        return narration
    except Exception as e:
        print(f"❌ Failed to generate video narration prompt: {e}")
        return ""

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
        print("📝 Generating blog content...")
        blog_text, summary_text, base_title = generate_blog()

        print("🎨 Fetching and uploading blog poster via Unsplash...")
        media_obj = image_utils.fetch_and_upload_blog_poster(blog_text)
        media_id = media_obj.get("id", 0)
        media_src = media_obj.get("source_url", "")

        save_local(blog_text, summary_text)
        video_prompt = generate_video_prompt(summary_text)

        est_now = datetime.now(pytz.utc).astimezone(pytz.timezone('America/New_York'))
        ts_readable = est_now.strftime("%B %d, %Y %H:%M")
        final_title = f"{ts_readable} EST  |  {base_title}"

        header_html = (
            '<div style="display:flex; align-items:center; margin-bottom:20px;">'
            f'<div style="flex:1;"><img src="{media_src}" style="width:100%; height:auto;" /></div>'
            '<div style="flex:1; display:flex; flex-direction:column; justify-content:center; padding-left:20px;">'
            f'<div style="color:#666; font-size:12px; margin-bottom:8px;">{ts_readable} EST</div>'
            f'<h1 style="margin:0; font-size:24px;">{base_title}</h1>'
            '</div>'
            '</div>'
        )

        post_body = (
            header_html +
            f'<p><em>{summary_text}</em></p>\n\n'
            f'<div>{blog_text}</div>'
        )

        print("📤 Publishing to WordPress...")
        post_to_wordpress(final_title, post_body, featured_media=media_id)

        print("✅ Done!")

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
