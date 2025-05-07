import os
import json
import openai
import requests
import pytz
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAIError
import re

# Custom utilities
import image_utils

# Load environment
load_dotenv()
OPENAI_API_KEY   = os.getenv("OPENAI_API_KEY")
WP_USERNAME     = os.getenv("WP_USERNAME")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")
WP_SITE_URL     = os.getenv("WP_SITE_URL")
NEWS_API_KEY    = os.getenv("NEWS_API_KEY")  # Add this to your .env

client = openai.OpenAI(api_key=OPENAI_API_KEY)

def fetch_latest_science_news():
    url = f"https://newsapi.org/v2/top-headlines?category=technology&q=science&language=en&pageSize=3&apiKey={NEWS_API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        articles = response.json().get("articles", [])
        if not articles:
            raise ValueError("No news articles found.")
        summary = "\n\n".join([f"Title: {a['title']}\nDescription: {a['description']}" for a in articles if a['description']])
        return summary
    except Exception as e:
        print(f"Error fetching news: {e}")
        return "No significant science or technology news was retrieved today."

def generate_blog(news_summary: str):
    est = pytz.timezone("America/New_York")
    now_est = datetime.now(pytz.utc).astimezone(est)
    today_line = f"Today is {now_est.strftime('%A, %B %d, %Y')} Eastern Time | Brought to you by Preeti Capital — decoding innovation for the future."

    system = {
        "role": "system",
        "content": (
            f"You are a senior science and technology journalist writing for a broad audience.\n\n"
            f"Start the blog post with this exact sentence:\n{today_line}\n\n"
            "Then, write a 250-word blog about the latest science and tech developments based on the provided summary. "
            "Do not fabricate facts. Be analytical and forward-looking.\n\n"
            "Return the result as strict JSON with exactly three fields:\n"
            "- 'blog': full post starting with the exact opening sentence provided above.\n"
            "- 'summary': a 100-word executive brief starting with 'SUMMARY:'.\n"
            "- 'title': a compelling headline."
        )
    }

    messages = [
        system,
        {"role": "user", "content": news_summary}
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
        print(f"OpenAI error: {e}")
        blog = "Exciting developments are shaping the future of science and technology."
        summary = "SUMMARY: Breakthroughs in innovation and research continue to gain momentum across the tech world."
        title = "Today in Tech: Emerging Trends and Discoveries"

    return blog, summary, title

def generate_video_prompt(summary_text):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a scriptwriter for science and tech short videos. Write 2 compelling sentences "
                        "summarizing the news for curious minds. No intros, no sponsor lines."
                    )
                },
                {
                    "role": "user",
                    "content": f"Summarize this in 2 exciting, digestible sentences:\n\n{summary_text}"
                }
            ],
            temperature=0.6
        )
        narration = response.choices[0].message.content.strip()
        narration_final = f"This news is brought to you by Preeti Capital. {narration}"
        with open("video_prompt.txt", "w") as f:
            f.write(narration_final)
        return narration_final
    except Exception as e:
        print(f"Failed to generate video prompt: {e}")
        return ""

def post_to_wordpress(title, content, featured_media):
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
        print("Published blog to WordPress")
    except requests.RequestException as e:
        print(f"WordPress post failed: {e}")

if __name__ == "__main__":
    try:
        print("Fetching latest science/technology news...")
        news_summary = fetch_latest_science_news()

        print("Generating blog content...")
        blog_text, summary_text, base_title = generate_blog(news_summary)

        print("Fetching and uploading blog poster via Unsplash...")
        media_obj = image_utils.fetch_and_upload_blog_poster(blog_text)
        media_id  = media_obj.get("id", 0)
        media_src = media_obj.get("source_url", "")

        # ✅ Save in original filenames for compatibility
        with open("blog_post.txt", "w") as f:
            f.write(blog_text + "\n\n" + summary_text)

        with open("blog_summary.txt", "w") as f:
            f.write(summary_text)

        print("Saved blog and summary to local files.")

        video_prompt = generate_video_prompt(summary_text)
        with open("video_prompt.txt", "w") as f:
            f.write(video_prompt)

        now_est = datetime.now(pytz.utc).astimezone(pytz.timezone("America/New_York"))
        ts_str  = now_est.strftime("%A, %B %d, %Y %H:%M")
        final_title = f"{ts_str} EST | {base_title}"

        header_html = (
            '<div style="display:flex; align-items:center; margin-bottom:20px;">'
            f'<img src="{media_src}" style="width:100%; height:auto;" />'
            '</div>'
        )
        post_body = f"{header_html}<div>{blog_text}</div>"

        print("Posting science blog to WordPress...")
        post_to_wordpress(final_title, post_body, media_id)

        # ✅ Also log to history (optional)
        log_blog_to_history(blog_text)

        print("Done.")

    except Exception as e:
        print(f"Unexpected error in science blog flow: {e}")
