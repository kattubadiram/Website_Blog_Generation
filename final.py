import os
import json
import re
import openai
import requests
import pytz
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAIError

# ——— Load credentials —————————————————————————————
load_dotenv()
OPENAI_API_KEY   = os.getenv("OPENAI_API_KEY")
WP_USERNAME      = os.getenv("WP_USERNAME")
WP_APP_PASSWORD  = os.getenv("WP_APP_PASSWORD")
WP_SITE_URL      = os.getenv("WP_SITE_URL")

# ——— Initialize OpenAI —————————————————————————————
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# ——— Helpers ———————————————————————————————————————

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
            "You are a top‑tier financial intelligence writer. "
            "Output strict JSON with three fields:\n"
            "  • \"blog\": a 250‑word market‑moving news post\n"
            "  • \"summary\": a 100‑word brief prefixed with 'SUMMARY:'\n"
            "  • \"title\": a click‑worthy headline (no timestamp)"
        )
    }
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[system, {"role":"user","content":""}],
        temperature=0.7
    )
    data    = json.loads(resp.choices[0].message.content)
    blog    = data["blog"].strip()
    summary = data["summary"].strip()
    title   = data["title"].strip()
    log_blog_to_history(blog)
    return blog, summary, title

def create_image_prompt(summary: str) -> str:
    system = {
        "role":"system",
        "content":(
            "You are an expert prompt engineer for DALL·E. "
            "Given a short finance article summary, produce a single-sentence, "
            "highly descriptive, poster‑style image prompt suitable for DALL·E. "
            "Do NOT include any text overlays in the image."
        )
    }
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[system, {"role":"user","content": summary}],
        temperature=0.8
    )
    prompt_text = resp.choices[0].message.content.strip().strip('"')
    print("[DEBUG] Generated DALL·E prompt:", prompt_text)
    return prompt_text

def generate_header_image(image_prompt: str) -> str:
    try:
        resp = client.images.generate(
            model="dall-e-2",
            prompt=image_prompt,
            n=1,
            size="1024x1024"
        )
        return resp.data[0].url
    except OpenAIError as e:
        print("❌ DALL·E failed, falling back to Unsplash:", e)
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
    with open("blog_summary.txt","w") as f:
        f.write(summary)
    with open("blog_post.txt","w") as f:
        f.write(blog + "\n\n" + summary)
    print("📝 Saved locally")

# ——— Main Execution ——————————————————————————————

if __name__ == "__main__":
    # 1) Generate the blog, ignore summary, and get base title
    blog_text, summary_text, base_title = generate_blog()

    # 2) Create & upload header image
    img_prompt = create_image_prompt(summary_text)
    img_url    = generate_header_image(img_prompt)
    media_obj  = upload_image_to_wordpress(img_url)
    media_id   = media_obj["id"]
    media_src  = media_obj["source_url"]

    # 3) (Optional) TTS step → obtain audio_url
    # Replace this stub with your own TTS/upload logic:
    # audio_url = upload_and_get_audio_url(blog_text)
    audio_url = "https://your-cdn.com/path/to/generated-audio.mp3"

    # 4) Save drafts locally
    save_local(blog_text, summary_text)

    # 5) Build timestamped title string
    est_now     = datetime.now(pytz.utc).astimezone(pytz.timezone('America/New_York'))
    ts_readable = est_now.strftime("%B %d, %Y %H:%M")
    final_title = f"{ts_readable} EST  |  {base_title}"

    # 6) Compose header block: image left; date & title right (no stub audio)
    header_html = (
        '<div style="display:flex; align-items:flex-start; margin-bottom:20px;">'
        f'<div style="flex:0 0 200px; margin-right:20px;">'
        f'<img src="{media_src}" style="width:100%; height:auto;" />'
        '</div>'
        '<div style="flex:1; display:flex; flex-direction:column;">'
        f'<div style="color:#666; font-size:12px; margin-bottom:8px;">{ts_readable} EST</div>'
        f'<h1 style="margin:0 0 12px 0; font-size:24px;">{base_title}</h1>'
        '</div>'
        '</div>'
    )

    # 7) Initial publish: header + blog body (no audio)
    publish_resp = requests.post(
        f"{WP_SITE_URL}/wp-json/wp/v2/posts",
        auth=(WP_USERNAME, WP_APP_PASSWORD),
        json={
            "title": final_title,
            "content": header_html + f"\n<div>{blog_text}</div>",
            "status": "publish",
            "featured_media": media_id
        }
    )
    publish_resp.raise_for_status()
    post = publish_resp.json()
    post_id = post["id"]
    print(f"📤 Published post ID {post_id}")

    # 8) Fetch rendered content (with bottom audio from your TTS/upload plugin)
    rendered = requests.get(
        f"{WP_SITE_URL}/wp-json/wp/v2/posts/{post_id}?_fields=content",
        auth=(WP_USERNAME, WP_APP_PASSWORD)
    ).json()["content"]["rendered"]

    # 9) Extract the bottom <audio> block
    audio_match = re.findall(r'(<audio[\s\S]*?</audio>)', rendered)
    if audio_match:
        bottom_audio = audio_match[-1]
        # Remove all audio blocks
        cleaned = re.sub(r'<audio[\s\S]*?</audio>', '', rendered)
        # Prepend the real audio to the top
        updated_content = bottom_audio + cleaned

        # 10) Update the post with the moved audio
        update_resp = requests.post(
            f"{WP_SITE_URL}/wp-json/wp/v2/posts/{post_id}",
            auth=(WP_USERNAME, WP_APP_PASSWORD),
            json={"content": updated_content}
        )
        update_resp.raise_for_status()
        print("🔄 Moved bottom audio to top and removed duplicate.")
    else:
        print("⚠️ No audio block found to move.")
