#!/usr/bin/env python3
"""
modular_science_blog.py – multi-section (~250–300 words each) science & technology
blog builder

👟 Runtime footsteps mirror **modular_blog.py** (financial flow):
  1. Pick a fresh science/tech headline via GPT-4o (deduplicated).
  2. Generate three analytical sections (titles in `SECTION_TITLES`).
  3. Produce summary & headline (JSON), save local artefacts.
  4. Create 2-sentence video prompt through shared helper in `final.py`.
  5. Upload poster image (if `image_utils` available).
  6. Publish to WordPress via `post_to_wordpress` from `final.py`.

Every helper, constant, and file-naming convention intentionally parallels the
financial script so downstream orchestration stays identical.
"""

from __future__ import annotations

import json, os, sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Set

import pytz, openai
from dotenv import load_dotenv
from openai import OpenAIError

# ─── environment ──────────────────────────────────────────────────────
load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Import shared publishing helpers (same as modular_blog.py)
from final import generate_video_prompt, post_to_wordpress  # noqa: E402
import image_utils  # poster uploader (optional)

# ─── time & paths ─────────────────────────────────────────────────────
EST = pytz.timezone("America/New_York")
TODAY_EST = datetime.now(timezone.utc).astimezone(EST).date()

TOPIC_HISTORY_FILE = Path("topic_history_science.json")  # JSON list
ARCHIVE_ROOT = Path("data")  # mirrors finance script

SECTION_TITLES = [
    "Background & Context",
    "Key Findings",
    "Broader Implications",
]
MAX_TOPIC_ATTEMPTS = 5

# ─── helpers ──────────────────────────────────────────────────────────
def ordinal(n: int) -> str:
    return f"{n}{'th' if 11 <= n % 100 <= 13 else {1:'st',2:'nd',3:'rd'}.get(n%10,'th')}"  # noqa: E501

def banner() -> str:
    now = datetime.now(timezone.utc).astimezone(EST)
    return (
        f"Today is {now:%A}, {ordinal(now.day)} of {now:%B} {now.year} Eastern Time | "
        "This science & technology update is brought to you by Preeti Capital, your trusted source for intelligent insights."
    )

# ––– topic history ----------------------------------------------------

def _load_topic_history() -> Set[str]:
    if TOPIC_HISTORY_FILE.exists():
        try:
            return set(json.loads(TOPIC_HISTORY_FILE.read_text()))
        except json.JSONDecodeError:
            pass
    return set()


def _save_topic_history(hist: Set[str]):
    TOPIC_HISTORY_FILE.write_text(json.dumps(sorted(hist), indent=2))

# ––– LLM topic picker --------------------------------------------------

def pick_new_topic(hist: Set[str]) -> str:
    """Ask GPT-4o for a headline not present in *hist*."""
    attempts, latest_list = 0, ", ".join(list(hist)[-50:]) or "(none)"
    topic: str | None = None
    while attempts < MAX_TOPIC_ATTEMPTS:
        attempts += 1
        try:
            completion = client.chat.completions.create(
                model="gpt-4o",
                temperature=0.3,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a science & technology news curator.\n"
                            "Step 1 – Mentally scan today’s front pages or RSS feeds of: Scientific American (News), ScienceDaily (Top Science), Ars Technica – Science, TechCrunch (General).\n"
                            "Step 2 – Pick ONE specific, impactful headline (within last 48 h).\n"
                            f"Step 3 – Avoid repeats; here are USED topics: {latest_list}.\n"
                            "Return ONLY JSON like {\"topic\":\"<headline>\"}."
                        ),
                    }
                ],
            )
            topic = json.loads(completion.choices[0].message.content)["topic"].strip()
            if topic.lower() not in {t.lower() for t in hist}:
                hist.add(topic)
                _save_topic_history(hist)
                return topic
            print("[⚠] GPT produced a repeat; retrying …")
        except (OpenAIError, KeyError, json.JSONDecodeError) as exc:
            print(f"[!] Topic selection error ({attempts}):", exc)
    return topic or "A recent breakthrough in science and technology"

# ––– local IO ----------------------------------------------------------

def _write(path: str | Path, text: str):
    Path(path).write_text(text, encoding="utf-8")

# ─── main workflow ────────────────────────────────────────────────────

def main():
    # 1. Topic selection ------------------------------------------------
    history = _load_topic_history()
    topic = pick_new_topic(history)
    print("Chosen topic →", topic)

    # 2. Section generation -------------------------------------------
    sections_out: list[str] = []
    for idx, title in enumerate(SECTION_TITLES):
        sys_prompt = (
            f"You are a senior science & technology journalist. Write the section titled '{title}' "
            "(professional, analytical, 250–300 words) about the topic below. Avoid repetition, no sub-headings inside text."
        )
        if idx == 0:
            sys_prompt += f"\nBegin the output with this exact sentence:\n{banner()}"
        try:
            resp = client.chat.completions.create(
                model="gpt-4o",
                temperature=0.7,
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": topic},
                ],
            )
            sections_out.append(resp.choices[0].message.content.strip())
        except OpenAIError as exc:
            print(f"[!] Section '{title}' failed:", exc)
            sections_out.append("Content temporarily unavailable.")

    full_blog = "\n\n".join(sections_out)

    # 3. Summary + headline -------------------------------------------
    try:
        meta_resp = client.chat.completions.create(
            model="gpt-4o",
            temperature=0.6,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a science editor. Summarize the blog in ≈100 words starting with 'SUMMARY:'. "
                        "Then craft a compelling headline (no dates). Return JSON with 'summary' & 'title'."
                    ),
                },
                {"role": "user", "content": full_blog},
            ],
        )
        meta = json.loads(meta_resp.choices[0].message.content)
        summary, title = meta["summary"].strip(), meta["title"].strip()
    except Exception as exc:
        print("[!] Metadata generation failed:", exc)
        summary = "SUMMARY: Overview of a recent science & technology development."
        title = f"Insight: {topic}"

    # 4. Local artefacts ----------------------------------------------
    _write("blog_post.txt", full_blog)
    _write("blog_summary.txt", summary)
    video_prompt = generate_video_prompt(summary)
    _write("video_prompt.txt", video_prompt)

    archive_dir = ARCHIVE_ROOT / "science" / str(TODAY_EST)
    archive_dir.mkdir(parents=True, exist_ok=True)
    (archive_dir / "article.md").write_text(full_blog, encoding="utf-8")
    print("✅ Local files saved →", archive_dir)

    # 5. Featured image (optional) ------------------------------------
    media_id = 0
    try:
        media_id = image_utils.fetch_and_upload_blog_poster(full_blog).get("id", 0)
    except ModuleNotFoundError:
        pass

    # 6. Publish to WordPress -----------------------------------------
    ts_est = datetime.now(timezone.utc).astimezone(EST).strftime("%A, %B %d, %Y %H:%M")
    final_title = f"{ts_est} EST | {title}"
    post_to_wordpress(final_title, f"<div>{full_blog}</div>", media_id)
    print("✅ Blog generation & publish complete\nTitle →", final_title)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
