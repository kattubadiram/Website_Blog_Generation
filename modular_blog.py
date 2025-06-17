#!/usr/bin/env python3
"""
modular_blog.py – four-section (≈250-300 words each) market blog builder

Reads  latest snapshots by default:
  breadth_latest.json, pulse_latest.json, movers_latest.json, watchlist_latest.json

If the script is called with a date argument (YYYY-MM-DD), it will pull the
matching snapshot out of each *_log.jsonl file instead.

Writes  blog_post.txt, blog_summary.txt, video_prompt.txt
Publishes to WordPress via post_to_wordpress() imported from final.py
"""
import json, os, sys, gzip
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict

import pytz, openai
from dotenv import load_dotenv
from openai import OpenAIError

# ─── env ───────────────────────────────────────────────────────────
load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# WordPress helpers live in final.py – import without running its main()
from final import generate_video_prompt, post_to_wordpress   # noqa: E402

EST        = pytz.timezone("America/New_York")
TODAY_EST  = datetime.now(timezone.utc).astimezone(EST).date()

LATEST_FILES = {
    "breadth":   Path("breadth_latest.json"),
    "pulse":     Path("pulse_latest.json"),
    "movers":    Path("movers_latest.json"),
    "watchlist": Path("watchlist_latest.json"),
}

LOG_FILES = {
    "breadth":   Path("breadth_log.jsonl"),
    "pulse":     Path("pulse_log.jsonl"),
    "movers":    Path("movers_log.jsonl"),
    "watchlist": Path("watchlist_log.jsonl"),
}

SECTIONS = [
    ("Trend Check",    "breadth"),    # maps to breadth_latest.json
    ("Market Pulse",   "pulse"),
    ("Top Movers",     "movers"),
    ("Stocks to Watch","watchlist"),
]

# ─── helpers ──────────────────────────────────────────────────────
def ordinal(n: int) -> str:
    return f"{n}{'th' if 11<=n%100<=13 else {1:'st',2:'nd',3:'rd'}.get(n%10,'th')}"

def banner() -> str:
    now = datetime.now(timezone.utc).astimezone(EST)
    return (f"Today is {now:%A}, {ordinal(now.day)} of {now:%B} {now.year} Eastern Time | "
            "This news is brought to you by Preeti Capital, your trusted source for financial insights.")

def load_latest_blob(key: str) -> Dict:
    path = LATEST_FILES[key]
    if not path.exists():
        print(f"[!] Missing {path}")
        return {}
    return json.loads(path.read_text(encoding="utf-8"))

def load_blob_for_date(key: str, date_iso: str) -> Dict:
    """
    Scans the *_log.jsonl file for the first blob whose meta.run_date matches date_iso.
    Returns {} if not found.
    """
    log_path = LOG_FILES[key]
    if not log_path.exists():
        print(f"[!] Missing {log_path}")
        return {}
    with log_path.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                blob = json.loads(line)
                if blob.get("meta", {}).get("run_date") == date_iso:
                    return blob
            except Exception:
                continue
    print(f"[!] No {key} entry for {date_iso} found in {log_path}")
    return {}

def write(path: str | Path, txt: str) -> None:
    Path(path).write_text(txt, encoding="utf-8")

# ─── main ────────────────────────────────────────────────────────
def main(date_iso: str | None = None) -> None:
    # 1) Load all four blobs
    blobs = {}
    for title, key in SECTIONS:
        if date_iso:
            blobs[key] = load_blob_for_date(key, date_iso)
        else:
            blobs[key] = load_latest_blob(key)

    # 2) Generate each section via GPT
    sections_out = []
    for idx, (title, key) in enumerate(SECTIONS):
        raw_json = json.dumps(blobs.get(key, {}))
        sys_prompt = (
            f"You are a senior financial journalist. Write a {title} section, "
            "professional and analytical, 250–300 words, using ONLY this JSON. "
            "Avoid repetition, no headings or ticker symbols."
        )
        if idx == 0:
            sys_prompt += f"\nBegin the output with this exact sentence:\n{banner()}"

        try:
            resp = client.chat.completions.create(
                model="gpt-4o",
                temperature=0.7,
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user",   "content": raw_json}
                ]
            )
            sections_out.append(resp.choices[0].message.content.strip())
        except OpenAIError as e:
            print(f"[!] Section {title} failed:", e)
            sections_out.append("Content temporarily unavailable.")

    full_blog = "\n\n".join(sections_out)

    # 3) Generate summary + headline
    try:
        meta = client.chat.completions.create(
            model="gpt-4o",
            temperature=0.6,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system",
                 "content": "You are a financial editor. Summarize the blog in ≈100 words "
                            "starting with 'SUMMARY:'. Then craft a compelling headline (no timestamps). "
                            "Return JSON with 'summary' and 'title'."},
                {"role": "user", "content": full_blog}
            ]
        )
        meta_json = json.loads(meta.choices[0].message.content)
        summary = meta_json["summary"].strip()
        title   = meta_json["title"].strip()
    except Exception as e:
        print("[!] Metadata generation failed:", e)
        summary = "SUMMARY: Financial markets are in motion..."
        title   = "Market Commentary: Key Takeaways from Global Moves"

    # 4) Local artefacts
    write("blog_post.txt",      full_blog)
    write("blog_summary.txt",   summary)
    video_prompt = generate_video_prompt(summary)
    write("video_prompt.txt",   video_prompt)

    # Optionally store article.md under data/<DATE>/ for archival
    article_folder = Path("data") / (date_iso or str(TODAY_EST))
    article_folder.mkdir(parents=True, exist_ok=True)
    (article_folder / "article.md").write_text(full_blog, encoding="utf-8")
    print("✅ Local files saved")

    # 5) Try featured image
    media_id = 0
    try:
        import image_utils
        media_id = image_utils.fetch_and_upload_blog_poster(full_blog).get("id", 0)
    except ModuleNotFoundError:
        pass

    # 6) Publish to WordPress
    ts_est = datetime.now(timezone.utc).astimezone(EST).strftime("%A, %B %d, %Y %H:%M")
    final_title = f"{ts_est} EST | {title}"
    post_to_wordpress(final_title, f"<div>{full_blog}</div>", media_id)
    print("✅ Blog generation & publish complete\nTitle →", final_title)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) == 2 else None)
