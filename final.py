import os
import openai
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Credentials
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WP_USERNAME = os.getenv("WP_USERNAME")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")
WP_SITE_URL = os.getenv("WP_SITE_URL")

# Initialize OpenAI client (new SDK format)
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Step 1: Generate blog + summary
def generate_blog():
    prompt = (
        "Write a 250-word blog post on the latest trending news in the stock market and hedge fund world, "
        "presented from the perspective of a hedge fund manager. Discuss key market trends, emerging investment strategies, "
        "and risk management tactics, while providing a thoughtful analysis of the current financial landscape and its macroeconomic implications. "
        "Then write a 100-word summary starting with 'SUMMARY:' that encapsulates the main insights and strategic takeaways from the post."
    )

    response = client.chat.completions.create(
        model="gpt-4.1-nano",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that writes blog content."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )

    full_text = response.choices[0].message.content
    blog, summary = full_text.split("SUMMARY:", 1)
    return blog.strip(), summary.strip()

# Step 2: Post blog to WordPress
def post_to_wordpress(title, content):
    post_url = f"{WP_SITE_URL}/wp-json/wp/v2/posts"
    headers = {"Content-Type": "application/json"}
    payload = {
        "title": title,
        "content": content,
        "status": "publish"
    }

    response = requests.post(post_url, headers=headers, json=payload, auth=(WP_USERNAME, WP_APP_PASSWORD))
    print("📤 WordPress Response:", response.status_code, response.text)
    response.raise_for_status()

# Step 3: Save summary to file
def save_summary(summary_text):
    with open("blog_summary.txt", "w") as f:
        f.write(summary_text)
    print("📝 Summary saved to blog_summary.txt")

# Step 4: Save blog to text file (for audio later)
def save_blog(blog_text):
    with open("blog_post.txt", "w") as f:
        f.write(blog_text)
    print("📝 Blog saved to blog_post.txt")

# Main Execution
if __name__ == "__main__":
    blog_text, summary_text = generate_blog()
    save_summary(summary_text)
    save_blog(blog_text)

    # Get current date and time
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M")  # Format: YYYY-MM-DD HH:MM

    # Create the blog title with the timestamp
    blog_title = f"Today's Business Insights - {timestamp}"

    post_to_wordpress(blog_title, blog_text)
