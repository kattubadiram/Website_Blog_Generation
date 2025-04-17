import os
import json
import openai
import requests
import pytz
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Credentials
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WP_USERNAME     = os.getenv("WP_USERNAME")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")
WP_SITE_URL     = os.getenv("WP_SITE_URL")

# Initialize OpenAI client
client = openai.OpenAI(api_key=OPENAI_API_KEY)

def log_blog_to_history(blog_content: str):
    """
    Append the raw blog content to blog_history.txt with timestamp.
    """
    LOG_FILE = "blog_history.txt"
    est_now = datetime.now(pytz.utc).astimezone(pytz.timezone('America/New_York'))
    ts = est_now.strftime("%Y-%m-%d %H:%M:%S %Z")
    divider = "=" * 80
    entry = f"\n\n{divider}\nBLOG ENTRY - {ts}\n{divider}\n\n{blog_content}\n"
    with open(LOG_FILE, 'a') as f:
        f.write(entry)
    print(f"📋 Blog content logged to {LOG_FILE}")

def generate_blog():
    """
    Ask the model to emit a JSON object with keys:
      - blog   : 250‑word market‑moving news post
      - summary: 100‑word SUMMARY:...
      - title  : click‑worthy title (no timestamp)
    """
    system_msg = {
        "role": "system",
        "content": (
            "You are a top‑tier financial intelligence writer. "
            "Respond in strict JSON with three fields: "
            "1) \"blog\": a 250‑word post on the latest, trending news that could move markets, "
            "including emerging themes, macro factors, and risk management insights; "
            "2) \"summary\": a 100‑word brief preﬁxed with 'SUMMARY:'; "
            "3) \"title\": an engaging, click‑worthy headline (without timestamp)."
        )
    }
    user_msg = {
        "role": "user",
        "content": ""
    }

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[system_msg, user_msg],
        temperature=0.7
    )

    # Parse JSON output
    data = json.loads(response.choices[0].message.content)
    blog    = data["blog"].strip()
    summary = data["summary"].strip()
    title   = data["title"].strip()
    
    # Log for history
    log_blog_to_history(blog)
    return blog, summary, title

def save_summary(summary: str):
    with open("blog_summary.txt", "w") as f:
        f.write(summary)
    print("📝 Summary saved to blog_summary.txt")

def save_blog(blog: str, summary: str):
    with open("blog_post.txt", "w") as f:
        f.write(blog + "\n\n" + summary)
    print("📝 Blog + summary saved to blog_post.txt")

def post_to_wordpress(title: str, content: str):
    url     = f"{WP_SITE_URL}/wp-json/wp/v2/posts"
    headers = {"Content-Type": "application/json"}
    payload = {"title": title, "content": content, "status": "publish"}
    resp = requests.post(url, headers=headers, json=payload, auth=(WP_USERNAME, WP_APP_PASSWORD))
    resp.raise_for_status()
    print(f"📤 Published post: {resp.status_code}")

if __name__ == "__main__":
    # Generate content
    blog_text, summary_text, base_title = generate_blog()
    
    # Save locally
    save_summary(summary_text)
    save_blog(blog_text, summary_text)
    
    # Build timestamped title
    est_now      = datetime.now(pytz.utc).astimezone(pytz.timezone('America/New_York'))
    ts_readable  = est_now.strftime("%B %d, %Y %H:%M")
    final_title  = f"{base_title} — {ts_readable} EST"
    
    # Prepare post body (you can include the summary in the post if you like)
    post_body = f"<p><em>{ts_readable} EST</em></p>\n\n{blog_text}"
    
    # Publish
    post_to_wordpress(final_title, post_body)
