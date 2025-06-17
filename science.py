#!/usr/bin/env python3
"""
Daily Science & Technology Blog Generator
(LLM-only – no scraping, same workflow & naming as financial_blog.py)

• GPT-4o picks today’s most impactful Sci-Tech headline, avoiding repeats
• Writes multi-section article (~250-350 words each)
• Creates summary + title, stores history, saves local files
• Generates 2-sentence video narration prompt
• Uploads poster image via `image_utils`
• Publishes to WordPress
"""

import os, json, pytz, requests, re
from datetime import datetime
from dotenv import load_dotenv
from typing import Set
import openai
from openai import OpenAIError

# ─── Custom utilities (unchanged) ────────────────────────────────────────
import image_utils
# If you don’t need a market snapshot for science posts, remove these lines.
from market_snapshot_fetcher import get_market_snapshot, append_snapshot_to_log, summarize_market_snapshot
# ─────────────────────────────────────────────────────────────────────────

# ─── ENVIRONMENT ─────────────────────────────────────────────────────────
load_dotenv()
OPENAI_API_KEY  = os.getenv("OPENAI_API_KEY")
WP_USERNAME     = os.getenv("WP_USERNAME")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD")
WP_SITE_URL     = os.getenv("WP_SITE_URL")

client = openai.OpenAI(api_key=OPENAI_API_KEY)

# ─── CONSTANTS / FILES ───────────────────────────────────────────────────
TOPIC_HISTORY_FILE = "topic_history_science.json"
LOG_FILE           = "blog_history_science.txt"
MAX_TOPIC_ATTEMPTS = 5       # retries if GPT repeats a topic

# ─── HELPERS ─────────────────────────────────────────────────────────────
def ordinal(n: int) -> str:
    if 11 <= n % 100 <= 13:
        return f"{n}th"
    return f"{n}{ {1:'st',2:'nd',3:'rd'}.get(n%10,'th') }"

def load_topic_history() -> Set[str]:
    if os.path.exists(TOPIC_HISTORY_FILE):
        try:
            return set(json.load(open(TOPIC_HISTORY_FILE)))
        except json.JSONDecodeError:
            pass
    return set()

def save_topic_history(history: Set[str]):
    with open(TOPIC_HISTORY_FILE, "w") as f:
        json.dump(sorted(history), f, indent=2)

# ─── LLM-based topic picker ──────────────────────────────────────────────
def get_new_topic_via_llm(history: Set[str]) -> str:
    """Ask GPT-4o for a fresh Sci-Tech headline not in history."""
    attempts = 0
    latest_list = ', '.join(list(history)[-50:]) or '(none)'
    while attempts < MAX_TOPIC_ATTEMPTS:
        attempts += 1
        try:
            resp = client.chat.completions.create(
                model="gpt-4o",
                messages=[{
                    "role": "system",
                    "content":(
                        "You are a science & technology news curator.\n"
                        "Step 1 – Mentally review today’s front pages or RSS feeds of:\n"
                        "• Scientific American (News)  • ScienceDaily (Top Science)\n"
                        "• Ars Technica – Science      • TechCrunch (General Feed)\n"
                        "Scan stories published within the last 48 hours.\n\n"
                        "Step 2 – Choose ONE headline that is specific, impactful, and easy to verify "
                        "(breakthrough, release, discovery, or policy change; no vague trend pieces).\n\n"
                        f"Step 3 – Compare against this list of USED topics: {latest_list}\n"
                        "If your headline appears (case-insensitive), pick another.\n"
                        "Return ONLY valid JSON like: {\"topic\": \"<headline>\"}"
                    )
                }],
                temperature=0.3,
            )
            topic = json.loads(resp.choices[0].message.content)["topic"].strip()
            if topic.lower() not in {t.lower() for t in history}:
                history.add(topic)
                save_topic_history(history)
                return topic
            print("[⚠] GPT chose a repeat, retrying …")
        except (OpenAIError, KeyError, json.JSONDecodeError) as e:
            print(f"[!] Topic selection error ({attempts}):", e)
    # fallback
    return topic if 'topic' in locals() else "A recent breakthrough in science and technology"

# ─── LOGGING ─────────────────────────────────────────────────────────────
def log_blog_to_history(content: str):
    ts = datetime.now(pytz.utc).astimezone(
         pytz.timezone('America/New_York')).strftime("%Y-%m-%d %H:%M:%S %Z")
    divider = "="*80
    with open(LOG_FILE, "a") as f:
        f.write(f"\n\n{divider}\nBLOG ENTRY – {ts}\n{divider}\n\n{content}\n")
    print("Logged to", LOG_FILE)

# ─── BLOG GENERATION ─────────────────────────────────────────────────────
def generate_blog(topic: str, section_count: int = 3):
    est = pytz.timezone("America/New_York")
    now = datetime.now(pytz.utc).astimezone(est)
    intro = (
        f"Today is {now.strftime('%A')}, {ordinal(now.day)} of "
        f"{now.strftime('%B')} {now.year} Eastern Time | "
        "This science & technology update is brought to you by "
        "Preeti Capital, your trusted source for intelligent insights."
    )

    # Optional: predefined section titles
    default_titles = [
        "Background", "Key Findings", "Implications",
        "Expert Insights", "Future Outlook", "Broader Impact"
    ]
    blog_sections = []

    for i in range(section_count):
        title = default_titles[i] if i < len(default_titles) else f"Section {i+1}"
        sys_msg = (
            f"You are a senior science & technology journalist.\n"
            f"Write the section titled '{title}' (~250-350 words) about **{topic}**.\n"
            "• Strictly factual and analytical (no speculation or unsupported claims)\n"
            "• Professional tone, avoid repetition, no headings inside text, "
            "no emojis or caret symbols.\n"
            f"{'Begin the first paragraph exactly with: '+intro if i==0 else ''}"
        )
        try:
            text = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": sys_msg},
                    {"role": "user",   "content": "Write the section now."}
                ],
                temperature=0.7
            ).choices[0].message.content.strip()
        except OpenAIError as e:
            print(f"[!] Section '{title}' error:", e)
            text = "Content temporarily unavailable."
        blog_sections.append(text)

    full_blog = "\n\n".join(blog_sections)

    # ── summary + headline ────────────────────────────────────────────
    try:
        meta = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role":"system",
                 "content":"You are a Sci-Tech editor. Summarise (~100 words, start with 'SUMMARY:') "
                           "and craft a catchy headline (no dates). Return JSON {'summary','title'}."},
                {"role":"user", "content":full_blog}
            ],
            temperature=0.0,
            response_format={"type":"json_object"}
        ).choices[0].message.content
        meta_json = json.loads(meta)
        summary, title = meta_json["summary"].strip(), meta_json["title"].strip()
    except Exception as e:
        print("[!] Meta generation failed:", e)
        summary = "SUMMARY: Overview of a recent science & technology development."
        title   = f"Insight: {topic}"

    log_blog_to_history(full_blog)
    return full_blog, summary, title

# ─── LOCAL SAVE ─────────────────────────────────────────────────────────
def save_local(blog: str, summary: str):
    open("blog_post_science.txt","w").write(blog + "\n\n" + summary)
    open("blog_summary_science.txt","w").write(summary)
    print("Saved blog_post_science.txt & blog_summary_science.txt")

# ─── VIDEO PROMPT ───────────────────────────────────────────────────────
def generate_video_prompt(summary_text: str) -> str:
    try:
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role":"system",
                 "content":"You are a scriptwriter for short Sci-Tech videos. "
                           "Write exactly 2 punchy sentences based on the summary."},
                {"role":"user","content":summary_text}
            ],
            temperature=0.6
        )
        narration_core = resp.choices[0].message.content.strip()
        narration = ("This update is brought to you by Preeti Capital, your trusted "
                     f"source for intelligent insights. {narration_core}")
        open("video_prompt_science.txt","w").write(narration)
        print("Saved video_prompt_science.txt")
        return narration
    except Exception as e:
        print("Video prompt error:", e)
        return ""

# ─── WORDPRESS UPLOAD ───────────────────────────────────────────────────
def post_to_wordpress(title: str, content: str, featured_media: int):
    try:
        payload = {
            "title": title,
            "content": content,
            "status": "publish",
            "featured_media": featured_media
        }
        r = requests.post(
            f"{WP_SITE_URL}/wp-json/wp/v2/posts",
            auth=(WP_USERNAME, WP_APP_PASSWORD),
            json=payload
        )
        r.raise_for_status()
        print("Published post (HTTP", r.status_code, ")")
    except requests.RequestException as e:
        print("WordPress post failed:", e)

# ─── MAIN WORKFLOW ──────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        # Optional: financial snapshot reuse
        snapshot = get_market_snapshot()
        append_snapshot_to_log(snapshot)
        _ = summarize_market_snapshot(snapshot)

        history = load_topic_history()
        topic = get_new_topic_via_llm(history)
        print("Chosen topic:", topic)

        section_count = 3   # change 1-6 as needed
        blog_text, summary_text, base_title = generate_blog(topic, section_count)

        print("Fetching and uploading poster image …")
        media_obj = image_utils.fetch_and_upload_blog_poster(blog_text)
        media_id  = media_obj.get("id", 0)
        media_src = media_obj.get("source_url", "")

        save_local(blog_text, summary_text)
        _ = generate_video_prompt(summary_text)

        est_now = datetime.now(pytz.utc).astimezone(pytz.timezone('America/New_York'))
        ts_readable = est_now.strftime("%A, %B %d, %Y %H:%M")
        final_title = f"{ts_readable} EST  |  {base_title}"

        header_html = (
            '<div style="display:flex;align-items:center;margin-bottom:20px;">'
            f'<div style="flex:1;"><img src="{media_src}" style="width:100%;height:auto;" /></div>'
            '<div style="flex:1;display:flex;flex-direction:column;justify-content:center;padding-left:20px;">'
            f'<div style="color:#666;font-size:12px;margin-bottom:8px;">{ts_readable} EST</div>'
            f'<h1 style="margin:0;font-size:24px;">{base_title}</h1>'
            '</div></div>'
        )
        post_body = header_html + f"<div>{blog_text}</div>"

        print("Publishing to WordPress …")
        post_to_wordpress(final_title, post_body, featured_media=media_id)

        print("Done ✅")
    except Exception as e:
        print("Unexpected error:", e)
