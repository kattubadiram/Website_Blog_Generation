#!/usr/bin/env python3
"""
modular_blog.py – four-section (≈250-300 words each) market blog builder
Reads   data/<DATE>/{breadth,pulse,movers,watchlist}.json
Writes  blog_post.txt, blog_summary.txt, video_prompt.txt
Publishes to WordPress via post_to_wordpress() imported from final.py
"""

import json, os, sys
from pathlib import Path
from datetime import datetime, timezone

import pytz, openai
from dotenv import load_dotenv
from openai import OpenAIError

# ───── env ─────────────────────────────────────────────────────────────
load_dotenv()                              # harmless if .env is absent
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# WordPress helpers live in final.py – import without running its main()
from final import generate_video_prompt, post_to_wordpress   # noqa: E402

EST = pytz.timezone("America/New_York")
TODAY_EST = datetime.now(timezone.utc).astimezone(EST).date()

SECTIONS = [
    ("Trend Check",   "breadth.json"),
    ("Market Pulse",  "pulse.json"),
    ("Top Movers",    "movers.json"),
    ("Stocks to Watch", "watchlist.json"),
]

# ───── helpers ─────────────────────────────────────────────────────────
def ordinal(n: int) -> str:
    return f"{n}{'th' if 11<=n%100<=13 else {1:'st',2:'nd',3:'rd'}.get(n%10,'th')}"

def banner() -> str:
    now = datetime.now(timezone.utc).astimezone(EST)
    return (f"Today is {now:%A}, {ordinal(now.day)} of {now:%B} {now.year} Eastern Time | "
            "This news is brought to you by Preeti Capital, your trusted source for financial insights.")

def load_blob(path: Path) -> dict:
    if not path.exists():
        print(f"[!] Missing {path}")
        return {}
    return json.loads(path.read_text(encoding="utf-8"))

def write(path: str, txt: str) -> None:
    Path(path).write_text(txt, encoding="utf-8")

# ───── main ────────────────────────────────────────────────────────────
def main(date_iso: str | None = None) -> None:
    folder = Path("data") / (date_iso or str(TODAY_EST))
    folder.mkdir(parents=True, exist_ok=True)

    # build each section
    sections_out = []
    for idx, (title, fname) in enumerate(SECTIONS):
        raw = json.dumps(load_blob(folder / fname))
        sys_prompt = (
            f"You are a senior financial journalist. Write a {title} section, "
            "professional and analytical, 250–300 words, using ONLY this JSON. "
            "Avoid repetition, no headings or ticker symbols."
        )
        # first section must start with banner
        if idx == 0:
            sys_prompt += f"\nBegin the output with this exact sentence:\n{banner()}"
        try:
            resp = client.chat.completions.create(
                model="gpt-4o",
                temperature=0.7,
                messages=[{"role":"system","content":sys_prompt},
                          {"role":"user","content":raw}]
            )
            sections_out.append(resp.choices[0].message.content.strip())
        except OpenAIError as e:
            print(f"[!] Section {title} failed:", e)
            sections_out.append("Content temporarily unavailable.")

    full_blog = "\n\n".join(sections_out)

    # summary + headline
    try:
        meta = client.chat.completions.create(
            model="gpt-4o",
            temperature=0.6,
            response_format={"type":"json_object"},
            messages=[
                {"role":"system","content":
                 "You are a financial editor. Summarize the blog in ≈100 words "
                 "starting with 'SUMMARY:'. Then craft a compelling headline (no timestamps). "
                 "Return JSON with 'summary' and 'title'."},
                {"role":"user","content":full_blog}
            ]
        )
        meta_json = json.loads(meta.choices[0].message.content)
        summary = meta_json["summary"].strip()
        title   = meta_json["title"].strip()
    except Exception as e:
        print("[!] Metadata generation failed:", e)
        summary = "SUMMARY: Financial markets are in motion..."
        title   = "Market Commentary: Key Takeaways from Global Moves"

    # local artefacts
    write("blog_post.txt", full_blog)
    write("blog_summary.txt", summary)
    video_prompt = generate_video_prompt(summary)   # writes video_prompt.txt inside
    write("video_prompt.txt", video_prompt)         # just in case helper didn’t
    (folder / "article.md").write_text(full_blog, encoding="utf-8")
    print("✅ Local files saved")

    # try optional featured image
    media_id = 0
    try:
        import image_utils                              # optional helper
        media_id = image_utils.fetch_and_upload_blog_poster(full_blog).get("id", 0)
    except ModuleNotFoundError:
        pass

    # publish
    ts = datetime.now(timezone.utc).astimezone(EST).strftime("%A, %B %d, %Y %H:%M")
    final_title = f"{ts} EST | {title}"
    post_to_wordpress(final_title, f"<div>{full_blog}</div>", media_id)

    print("✅ Blog generation & publish complete\nTitle →", final_title)

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv)==2 else None)
