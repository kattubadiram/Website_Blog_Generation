import os
import json
import requests
import pytz
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI, OpenAIError
from gtts import gTTS

# ——— Load credentials —————————————————————————————
load_dotenv()
OPENAI_API_KEY  = os.getenv("OPENAI_API_KEY")
WP_USERNAME     = os.getenv("WP_USERNAME")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")
WP_SITE_URL     = os.getenv("WP_SITE_URL")

# ——— Initialize OpenAI —————————————————————————————
client = OpenAI(api_key=OPENAI_API_KEY)

# ——— Helpers ———————————————————————————————————————

def log_blog_to_history(blog_content: str):
    LOG_FILE = "blog_history.txt"
    ts = datetime.now(pytz.utc)\
             .astimezone(pytz.timezone("America/New_York"))\
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
            "You are a top‑tier financial intelligence writer. "
            "Output strict JSON with three fields:\n"
            "  • \"blog\": a 250‑word market‑moving news post\n"
            "  • \"summary\": a 100‑word brief prefixed with 'SUMMARY:'\n"
            "  • \"title\": a click‑worthy headline (no timestamp)"
        )
    }
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[system, {"role": "user", "content": ""}],
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
        "role": "system",
        "content": (
            "You are an expert prompt engineer for DALL·E. "
            "Given a short finance article summary, produce a single-sentence, "
            "highly descriptive, poster‑style image prompt suitable for DALL·E. "
            "Do NOT include any text overlays in the image."
        )
    }
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[system, {"role": "user", "content": summary}],
        temperature=0.8
    )
    prompt_text = resp.choices[0].message.content.strip().strip('"')
    print("[DEBUG] DALL·E prompt:", prompt_text)
    return prompt_text

def generate_header_image(prompt: str) -> str:
    try:
        resp = client.images.generate(
            model="dall-e-2",
            prompt=prompt,
            n=1,
            size="1024x1024"
        )
        return resp.data[0].url
    except OpenAIError as e:
        print("❌ DALL·E failed, falling back to Unsplash:", e)
        return "https://source.unsplash.com/1024x1024/?finance,stock-market"

def upload_image_to_wordpress(url: str) -> dict:
    data = requests.get(url).content
    filename = "header.png"
    resp = requests.post(
        f"{WP_SITE_URL}/wp-json/wp/v2/media",
        auth=(WP_USERNAME, WP_APP_PASSWORD),
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        files={"file": (filename, data, "image/png")}
    )
    resp.raise_for_status()
    return resp.json()  # contains id & source_url

def generate_and_upload_audio(text: str) -> str:
    # 1) generate MP3 via gTTS
    tts = gTTS(text=text, lang="en")
    local_mp3 = "voiceover.mp3"
    tts.save(local_mp3)
    print("✅ TTS audio saved to", local_mp3)
    # 2) upload to WP media
    media_url = f"{WP_SITE_URL}/wp-json/wp/v2/media"
    with open(local_mp3, "rb") as f:
        resp = requests.post(
            media_url,
            auth=(WP_USERNAME, WP_APP_PASSWORD),
            headers={
                "Content-Disposition": f'attachment; filename="{local_mp3}"',
                "Content-Type": "audio/mpeg"
            },
            data=f
        )
    resp.raise_for_status()
    audio_url = resp.json()["source_url"]
    print("✅ Uploaded audio to", audio_url)
    return audio_url

def post_to_wordpress(title: str, content: str, featured_media: int) -> dict:
    resp = requests.post(
        f"{WP_SITE_URL}/wp-json/wp/v2/posts",
        auth=(WP_USERNAME, WP_APP_PASSWORD),
        json={
            "title": title,
            "content": content,
            "status": "publish",
            "featured_media": featured_media
        }
    )
    resp.raise_for_status()
    print("📤 Published post:", resp.status_code)
    return resp.json()

def embed_audio_in_post_top(audio_url: str, post_id: int):
    # fetch raw content
    resp = requests.get(
        f"{WP_SITE_URL}/wp-json/wp/v2/posts/{post_id}?_fields=content",
        auth=(WP_USERNAME, WP_APP_PASSWORD)
    )
    resp.raise_for_status()
    raw_content = resp.json()["content"]["raw"]
    # build embed tag
    embed = (
        '<p>If you’d rather listen, hit play below:</p>\n'
        f'<audio controls src="{audio_url}" style="width:100%; max-width:400px;"></audio>\n\n'
    )
    updated = embed + raw_content
    # update post
    upd = requests.post(
        f"{WP_SITE_URL}/wp-json/wp/v2/posts/{post_id}",
        auth=(WP_USERNAME, WP_APP_PASSWORD),
        json={"content": updated}
    )
    upd.raise_for_status()
    print("🔄 Audio embedded at top of post")

# ——— Main —————————————————————————————————————————

if __name__ == "__main__":
    # 1) Generate blog + summary + title
    blog_text, summary_text, base_title = generate_blog()

    # 2) Make image
    img_prompt = create_image_prompt(summary_text)
    img_url    = generate_header_image(img_prompt)
    img_media  = upload_image_to_wordpress(img_url)
    img_id     = img_media["id"]
    img_src    = img_media["source_url"]

    # 3) Make audio & upload
    audio_url = generate_and_upload_audio(blog_text)

    # 4) Save drafts
    with open("blog_post.txt","w") as f: f.write(blog_text)
    with open("blog_summary.txt","w") as f: f.write(summary_text)

    # 5) Build title + header HTML
    est = datetime.now(pytz.utc).astimezone(pytz.timezone("America/New_York"))\
            .strftime("%B %d, %Y %H:%M")
    full_title = f"{est} EST  |  {base_title}"
    header_html = (
        '<div style="display:flex; align-items:center; margin-bottom:20px;">'
        f'<div style="flex:0 0 200px; margin-right:20px;">'
        f'<img src="{img_src}" style="width:100%; height:auto;" />'
        '</div>'
        '<div style="flex:1; display:flex; flex-direction:column;">'
        f'<div style="color:#666; font-size:12px; margin-bottom:8px;">{est} EST</div>'
        f'<h1 style="margin:0 0 12px 0; font-size:24px;">{base_title}</h1>'
        '</div>'
        '</div>'
    )

    # 6) Publish without audio
    post = post_to_wordpress(
        full_title,
        header_html + "\n<div>" + blog_text + "</div>",
        img_id
    )
    post_id = post["id"]

    # 7) Embed audio at very top
    embed_audio_in_post_top(audio_url, post_id)
