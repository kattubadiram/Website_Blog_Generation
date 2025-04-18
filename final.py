import os
import json
import openai
import requests
import pytz
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAIError

# Import our modular image utilities
import image_utils

# ——— Load credentials —————————————————————————————
load_dotenv()
OPENAI_API_KEY   = os.getenv("OPENAI_API_KEY")
WP_USERNAME     = os.getenv("WP_USERNAME")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")
WP_SITE_URL     = os.getenv("WP_SITE_URL")

# ——— Initialize OpenAI —————————————————————————————
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# ——— Helper Functions ———————————————————————————————

def log_blog_to_history(blog_content: str):
    """Append blog content to history file with timestamp"""
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
        # Request JSON format specifically to ensure proper response format
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[system, {"role":"user","content":""}],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        # Parse the JSON response
        try:
            data = json.loads(resp.choices[0].message.content)
            blog = data["blog"].strip()
            summary = data["summary"].strip()
            title = data["title"].strip()
        except (json.JSONDecodeError, KeyError) as e:
            # Fallback if JSON parsing fails or expected keys are missing
            print(f"⚠️ Error processing AI response: {e}")
            print(f"Raw content received: {resp.choices[0].message.content[:100]}...")
            
            # Create fallback content
            content = resp.choices[0].message.content
            blog = content if len(content) > 100 else "Recent market movements indicate volatility across multiple sectors. Investors are closely monitoring central bank policies and geopolitical developments. Financial analysts recommend diversified portfolios as a hedge against uncertainty. Market indicators suggest cautious optimism for the coming quarter, with selective opportunities in technology and sustainable energy sectors."
            summary = "SUMMARY: Financial markets are experiencing volatility influenced by monetary policy shifts and global events. Diversification strategies are recommended while selective sectors offer potential despite broader uncertainty."
            title = "Market Analysis: Navigating Volatility in Today's Financial Landscape"
            
        # Log the blog content to history file
        log_blog_to_history(blog)
        return blog, summary, title
        
    except OpenAIError as e:
        # Handle OpenAI API errors
        print(f"❌ OpenAI API error: {e}")
        # Return emergency fallback content
        emergency_blog = "Markets continue to adapt to changing economic conditions. Investors should stay informed about central bank policies and global developments that may impact various sectors. Maintaining a balanced portfolio remains advisable in the current climate."
        emergency_summary = "SUMMARY: Current market conditions require vigilant monitoring and balanced investment strategies."
        emergency_title = "Market Update: Strategic Positioning in Current Economic Climate"
        log_blog_to_history(emergency_blog)
        return emergency_blog, emergency_summary, emergency_title


def save_local(blog: str, summary: str):
    """Save blog content and summary to local files"""
    try:
        with open("blog_summary.txt","w") as f: f.write(summary)
        with open("blog_post.txt","w") as f:
            f.write(blog + "\n\n" + summary)
        print("📝 Saved locally")
    except IOError as e:
        print(f"❌ Failed to save local files: {e}")


def post_to_wordpress(title: str, content: str, featured_media: int):
    """Publish post to WordPress with featured image"""
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
        # 1) Create blog
        print("Generating blog content...")
        blog_text, summary_text, base_title = generate_blog()

        # 2) Get content-aware image and upload using the modular utilities
        print("Selecting and uploading relevant header image...")
        img_url = image_utils.get_advanced_content_aware_image(blog_text, summary_text, base_title)
        media_obj = image_utils.upload_image_to_wordpress(
            img_url, 
            WP_USERNAME, 
            WP_APP_PASSWORD, 
            WP_SITE_URL
        )
        media_id = media_obj.get("id", 0)
        media_src = media_obj.get("source_url", "")

        # 3) Save drafts locally
        print("Saving content locally...")
        save_local(blog_text, summary_text)

        # 4) Timestamp & title string
        print("Formatting post elements...")
        est_now = datetime.now(pytz.utc).astimezone(pytz.timezone('America/New_York'))
        ts_readable = est_now.strftime("%B %d, %Y %H:%M")
        final_title = f"{ts_readable} EST  |  {base_title}"

        # 5) Build header block: image left, date & title right
        header_html = (
            '<div style="display:flex; align-items:center; margin-bottom:20px;">'
            f'<div style="flex:1;"><img src="{media_src}" style="width:100%; height:auto;" /></div>'
            '<div style="flex:1; display:flex; flex-direction:column; justify-content:center; padding-left:20px;">'
            f'<div style="color:#666; font-size:12px; margin-bottom:8px;">{ts_readable} EST</div>'
            f'<h1 style="margin:0; font-size:24px;">{base_title}</h1>'
            '</div>'
            '</div>'
        )

        # 6) Assemble post body
        post_body = (
            header_html +
            f'<p><em>{summary_text}</em></p>\n\n'
            + f'<div>{blog_text}</div>'
        )

        # 7) Publish!
        print("Publishing to WordPress...")
        post_to_wordpress(final_title, post_body, featured_media=media_id)
        
        print("✅ Process completed successfully!")
        
    except Exception as e:
        print(f"❌ Unexpected error in main process: {e}")
