import requests
import datetime
import base64
import os
from dotenv import load_dotenv
import ollama

# Load WordPress credentials
load_dotenv()

# WordPress environment variables
WP_USERNAME = os.getenv("WP_USERNAME")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")
WP_SITE_URL = os.getenv("WP_SITE_URL")

# Blog prompt
PROMPT = "Write a 250-word news-style blog post about the latest in business news. Make it informative, engaging, and easy to understand."

# Step 1: Generate content from local LLaMA 2 (via Ollama)
def generate_blog_locally(prompt):
    response = ollama.chat(model='llama2', messages=[
        {"role": "user", "content": prompt}
    ])
    return response['message']['content']

# Step 2: Publish to WordPress via REST API
def post_to_wordpress(title, content):
    auth = base64.b64encode(f"{WP_USERNAME}:{WP_APP_PASSWORD}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth}",
        "Content-Type": "application/json"
    }
    data = {
        "title": title,
        "content": content,
        "status": "publish"
    }
    response = requests.post(f"{WP_SITE_URL}/wp-json/wp/v2/posts", headers=headers, json=data)
    response.raise_for_status()
    return response.json()

# Main routine
if __name__ == "__main__":
    blog_content = generate_blog_locally(PROMPT)
    today_title = datetime.date.today().strftime("%Y-%m-%d") + " - Daily Business News"
    result = post_to_wordpress(today_title, blog_content)
    print("✅ Blog posted at:", result['link'])