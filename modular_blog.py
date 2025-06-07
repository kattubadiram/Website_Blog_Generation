#!/usr/bin/env python3
"""
modular_blog.py  –  Generate a single-section (250-350 words) financial blog
from the four data feeds produced by trend.py, pulse.py, movers.py, watchlist.py.

• Keeps the **identical first sentence** format you already use.
• Writes   blog_post.txt, blog_summary.txt, video_prompt.txt   so the
  downstream audio/video steps keep working unchanged.
"""

import json, os, re, pytz, sys
from datetime import datetime, timezone
from pathlib   import Path
from dotenv    import load_dotenv
import openai, requests
from openai import OpenAIError

# ─────────────────────────── ENV & CONSTANTS ────────────────────────────
load_dotenv()
OPENAI_API_KEY   = os.getenv("OPENAI_API_KEY")
WP_USERNAME      = os.getenv("WP_USERNAME")      # only used for poster upload
WP_APP_PASSWORD  = os.getenv("WP_APP_PASSWORD")
WP_SITE_URL      = os.getenv("WP_SITE_URL")
client           = openai.OpenAI(api_key=OPENAI_API_KEY)

EST  = pytz.timezone("America/New_York")
TODAY_EST = datetime.now(timezone.utc).astimezone(EST).date()

# ─────────────────────────── HELPERS ────────────────────────────────────
def ordinal(n: int) -> str:
    return f"{n}{'th' if 11<=n%100<=13 else {1:'st',2:'nd',3:'rd'}.get(n%10,'th')}"

def load_json(path: Path) -> dict:
    if not path.is_file():
        print(f"[!] Missing {path}")
        return {}
    return json.loads(path.read_text(encoding="utf-8"))

def first_line() -> str:
    now = datetime.now(timezone.utc).astimezone(EST)
    weekday, month, year, day = now.strftime("%A"), now.strftime("%B"), now.year, now.day
    return (f"Today is {weekday}, {ordinal(day)} of {month} {year} Eastern Time | "
            "This news is brought to you by Preeti Capital, your trusted source for financial insights.")

def save_local(blog: str, summary: str):
    Path("blog_post.txt").write_text(blog, encoding="utf-8")
    Path("blog_summary.txt").write_text(summary, encoding="utf-8")
    print("✅ Saved blog_post.txt & blog_summary.txt")

def save_video_prompt(summary: str):
    system = ("You are a professional scriptwriter for short financial news videos targeted at investors. "
              "Write exactly 2 short, impactful sentences summarizing the financial situation based on the given summary. "
              "Do NOT include any introduction like 'This news is brought to you by Preeti Capital'.")
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role":"system","content":system},
                  {"role":"user","content":summary}],
        temperature=0.6
    )
    narration = ( "This news is brought to you by Preeti Capital, your trusted source for financial insights. "
                  + resp.choices[0].message.content.strip())
    Path("video_prompt.txt").write_text(narration, encoding="utf-8")
    print("✅ Saved video_prompt.txt")

# ─────────────────────────── MAIN ───────────────────────────────────────
def main(date_iso: str|None = None):
    # pick folder  data/YYYY-MM-DD/   (default = today EST)
    folder_date = date_iso or str(TODAY_EST)
    data_dir = Path("data") / folder_date
    trend     = load_json(data_dir / "breadth.json")
    pulse     = load_json(data_dir / "pulse.json")
    movers    = load_json(data_dir / "movers.json")
    watchlist = load_json(data_dir / "watchlist.json")

    # Concatenate raw content for the LLM
    raw = {
        "trend"    : json.dumps(trend),
        "pulse"    : json.dumps(pulse),
        "movers"   : json.dumps(movers),
        "watchlist": json.dumps(watchlist),
    }
    combined_text = "\n\n".join(f"{k.upper()}:\n{v}" for k,v in raw.items())

    # ── Compose single 250-350 word section ────────────────────────────
    section_title = "Market Overview"
    sys_prompt = (f"You are a senior financial journalist. Write a {section_title} section around 250-350 words, "
                  "professional and analytical, based ONLY on the provided JSON-like data. "
                  "Avoid repetition. Do not include headings or ticker symbols in the output.")
    messages = [{"role":"system","content":sys_prompt},
                {"role":"user","content":combined_text}]
    try:
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.7
        )
        section_text = resp.choices[0].message.content.strip()
    except OpenAIError as e:
        print(f"[!] Blog generation failed: {e}")
        section_text = "Content temporarily unavailable."

    full_blog = first_line() + "\n\n" + section_text

    # ── Metadata (summary + headline) ──────────────────────────────────
    meta_prompt = ("You are a financial editor. Summarize the blog in ≈100 words "
                   "starting with 'SUMMARY:'. Then generate a compelling headline "
                   "(no timestamps). Return JSON with 'summary' and 'title'.")
    try:
        meta_resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role":"system","content":meta_prompt},
                      {"role":"user","content":full_blog}],
            temperature=0.6,
            response_format={"type":"json_object"}
        )
        meta = json.loads(meta_resp.choices[0].message.content)
        summary, title = meta["summary"].strip(), meta["title"].strip()
    except Exception as e:
        print(f"[!] Metadata generation failed: {e}")
        summary = "SUMMARY: Financial markets are in motion..."
        title   = "Market Commentary: Key Takeaways from Global Moves"

    # ── Save files for downstream steps ────────────────────────────────
    save_local(full_blog, summary)
    save_video_prompt(summary)

    # extra copy in dated folder (article.md) for archive
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "article.md").write_text(full_blog, encoding="utf-8")

    print("✅ Blog generation complete.")
    print("Title →", title)

if __name__ == "__main__":
    # optional CLI arg  YYYY-MM-DD  to target a past date
    main(sys.argv[1] if len(sys.argv) == 2 else None)
