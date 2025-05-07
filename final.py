import os
import json
import openai
import requests
import pytz
import re
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAIError

# Custom utilities
import image_utils
from market_snapshot_fetcher import get_market_snapshot, append_snapshot_to_log, summarize_market_snapshot

# Load credentials
load_dotenv()
OPENAI_API_KEY   = os.getenv("OPENAI_API_KEY")
WP_USERNAME     = os.getenv("WP_USERNAME")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")
WP_SITE_URL     = os.getenv("WP_SITE_URL")

client = openai.OpenAI(api_key=OPENAI_API_KEY)

def ordinal(n: int) -> str:
    if 11 <= (n % 100) <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"

def log_blog_to_history(blog_content: str):
    LOG_FILE = "blog_history.txt"
    ts = datetime.now(pytz.utc).astimezone(pytz.timezone('America/New_York')) \
             .strftime("%Y-%m-%d %H:%M:%S %Z")
    divider = "=" * 80
    entry = f"\n\n{divider}\nBLOG ENTRY - {ts}\n{divider}\n\n{blog_content}\n"
    with open(LOG_FILE, "a") as f:
        f.write(entry)
    print("Logged to", LOG_FILE)

def generate_blog(market_summary: str):
    est = pytz.timezone("America/New_York")
    now_est = datetime.now(pytz.utc).astimezone(est)
    weekday    = now_est.strftime("%A")
    day_number = now_est.day
    month_name = now_est.strftime("%B")
    year       = now_est.year
    day_ord    = ordinal(day_number)

    today_line = f"Today is {weekday}, {day_ord} of {month_name} {year} Eastern Time | This news is brought to you by Preeti Capital, your trusted source for financial insights."

    system = {
        "role": "system",
        "content": (
            f"You are a senior financial journalist writing for institutional investors.\n\n"
            f"Start the blog post with this exact sentence:\n"
            f"{today_line}\n\n"
            "Then, write a 5000 - word analysis of today's global market based strictly on the provided summary. "
            "Do not fabricate or add any external data. Maintain a professional, analytical tone.\n\n"
            "IMPORTANT FORMATTING:\n"
            "- Use only the full names of indices and companies (e.g., 'S&P 500' instead of '^GSPC').\n"
            "- Do NOT include symbols inside brackets like (^IXIC).\n\n"
            "Return the result as strict JSON with exactly three fields:\n"
            "- 'blog': full post starting with the exact opening sentence provided above.\n"
            "- 'summary': a 100-word executive brief starting with 'SUMMARY:'.\n"
            "- 'title': a strong headline without timestamps."
        )
    }

    clean_summary = re.sub(r'\(\^[A-Z0-9\.\-]+\)', '', market_summary)

    messages = [
        system,
        {"role": "user", "content": clean_summary}
    ]

    try:
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        data    = json.loads(resp.choices[0].message.content)
        blog    = data["blog"].strip()
        summary = data["summary"].strip()
        title   = data["title"].strip()
    except OpenAIError as e:
        print(f"Error processing AI response: {e}")
        blog    = "Markets continue to adapt..."
        summary = "SUMMARY: Financial markets are experiencing..."
        title   = "Market Update: Strategic Positioning in Current Economic Climate"

    log_blog_to_history(blog)
    return blog, summary, title

def save_local(blog: str, summary: str):
    try:
        with open("blog_summary.txt", "w") as f:
            f.write(summary)
        with open("blog_post.txt", "w") as f:
            f.write(blog + "\n\n" + summary)
        print("Saved locally")
    except IOError as e:
        print(f"Failed to save local files: {e}")

def generate_video_prompt(summary_text):
    try:
        print("Generating video narration prompt from blog summary...")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional scriptwriter for short financial news videos targeted at investors. "
                        "Write exactly 2 short, impactful sentences summarizing the financial situation based on the given summary. "
                        "Be clear, objective, and slightly urgent if market moves are significant. "
                        "Do NOT include any introduction like 'This news is brought to you by Preeti Capital' — only focus on the financial content."
                    )
                },
                {
                    "role": "user",
                    "content": f"Write a concise 2-sentence financial short video narration based on this summary:\n\n{summary_text}"
                }
            ],
            temperature=0.6
        )
        pure_narration = response.choices[0].message.content.strip()

        fixed_intro = "This news is brought to you by Preeti Capital, your trusted source for financial insights."
        narration  = f"{fixed_intro} {pure_narration}"

        with open("video_prompt.txt", "w") as f:
            f.write(narration)
        print("Saved video narration to video_prompt.txt")
        return narration
    except Exception as e:
        print(f"Failed to generate video narration prompt: {e}")
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
        print("Published post (status", resp.status_code, ")")
    except requests.RequestException as e:
        print(f"Failed to post to WordPress: {e}")

if __name__ == "__main__":
    try:
        print("Fetching market snapshot...")
        snapshot        = get_market_snapshot()
        append_snapshot_to_log(snapshot)
        market_summary  = summarize_market_snapshot(snapshot)

        print("Generating blog content...")
        blog_text, summary_text, base_title = generate_blog(market_summary)

        print("Fetching and uploading blog poster via Unsplash...")
        media_obj  = image_utils.fetch_and_upload_blog_poster(blog_text)
        media_id   = media_obj.get("id", 0)
        media_src  = media_obj.get("source_url", "")

        save_local(blog_text, summary_text)

        video_prompt = generate_video_prompt(summary_text)

        est_now      = datetime.now(pytz.utc).astimezone(pytz.timezone('America/New_York'))
        ts_readable  = est_now.strftime("%A, %B %d, %Y %H:%M")
        final_title  = f"{ts_readable} EST  |  {base_title}"

        header_html = (
            '<div style="display:flex; align-items:center; margin-bottom:20px;">'
            f'<div style="flex:1;"><img src="{media_src}" style="width:100%; height:auto;" /></div>'
            '<div style="flex:1; display:flex; flex-direction:column; justify-content:center; padding-left:20px;">'
            f'<div style="color:#666; font-size:12px; margin-bottom:8px;">{ts_readable} EST</div>'
            f'<h1 style="margin:0; font-size:24px;">{base_title}</h1>'
            '</div>'
            '</div>'
        )

        post_body = f'<div>{blog_text}</div>'

        print("Publishing to WordPress...")
        post_to_wordpress(final_title, post_body, featured_media=media_id)

        print("Done")

    except Exception as e:
        print(f"Unexpected error: {e}")
