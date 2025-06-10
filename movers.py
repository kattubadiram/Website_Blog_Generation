import datetime as dt
import json
import pathlib
import time
import os
import base64
from typing import Dict, List

import requests
import pandas as pd
import feedparser
import pytz
from transformers import logging as tf_logging, pipeline, Pipeline
from article_extractor import extract_article_text

# Optional RAG ingestion
try:
    from rag_layer.ingest import ingest_section
except ImportError:
    ingest_section = lambda *_a, **_kw: None

# ── Timezones & Dates ───────────────────────────
EST      = pytz.timezone("America/New_York")
DATE_STR = dt.datetime.now(dt.timezone.utc).astimezone(EST).date().isoformat()
DATA_DIR = pathlib.Path("data") / DATE_STR
DATA_DIR.mkdir(parents=True, exist_ok=True)

URLS = {
    "most_active": "https://finance.yahoo.com/most-active",
    "gainers":     "https://finance.yahoo.com/gainers",
    "losers":      "https://finance.yahoo.com/losers",
    "52w_high":    "https://finance.yahoo.com/markets/stocks/52-week-gainers/",
    "52w_low":     "https://finance.yahoo.com/markets/stocks/52-week-losers/",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121 Safari/537.36"
    )
}

# Summariser pipeline setup
tf_logging.set_verbosity_error()
MODEL_NAME = "sshleifer/distilbart-cnn-12-6"
summariser: Pipeline = pipeline(
    "summarization",
    model=MODEL_NAME,
    tokenizer=MODEL_NAME,
    framework="pt",
    truncation=True,
    token=None
)

# STEP 3 · Scrape top-5 tickers per category
def top5_symbols(category: str, pause: float = 1.5) -> List[str]:
    time.sleep(pause)
    html = requests.get(URLS[category], headers=HEADERS, timeout=12).text
    tables = pd.read_html(html, flavor="lxml")
    if not tables:
        return []
    df = tables[0]
    return df.get("Symbol", [])[:5].tolist()

# STEP 4 · Fetch RSS headlines
def yahoo_rss(symbol: str, pause: float = 1.0) -> List[Dict]:
    url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}&region=US&lang=en-US"
    time.sleep(pause)
    parsed = feedparser.parse(url)
    if parsed.bozo:
        raise RuntimeError(parsed.bozo_exception)
    return [{
        "title":     e.get("title", "").strip(),
        "summary":   e.get("summary", "").strip(),
        "link":      e.get("link", "").strip(),
        "published": e.get("published", "").strip()
    } for e in parsed.entries[:10]]

# STEP 5 · Summarise headlines
def summarise_headlines(entries: List[Dict]) -> List[str]:
    lines: List[str] = []
    for e in entries:
        art_text = extract_article_text(e["link"])
        src_text = art_text if art_text else e["title"] + ". " + e.get("summary", "")
        line = summariser(src_text, max_length=60, min_length=15, do_sample=False)[0]["summary_text"]
        lines.append(line.strip())
    return lines

# STEP 6 · Build movers blob
def build_movers_blob(pause: float = 1.0) -> Dict:
    symbols_by_cat: Dict[str, List[str]] = {}
    for cat in URLS:
        try:
            symbols_by_cat[cat] = top5_symbols(cat, pause=pause)
        except Exception as exc:
            print(f"[Scrape error] {cat}: {exc}")
            symbols_by_cat[cat] = []

    entities: List[Dict] = []
    for cat, tickers in symbols_by_cat.items():
        for sym in tickers:
            try:
                rss_items = yahoo_rss(sym, pause=pause)
                summaries = summarise_headlines(rss_items)
                entities.append({
                    "ticker":    sym,
                    "label":     sym,
                    "data":      {"category": cat},
                    "summaries": summaries
                })
            except Exception as exc:
                print(f"[RSS error] {sym}: {exc}")

    return {
        "meta": {"section": "movers", "generated_at": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z", "source": "yahoo_rss"},
        "entities": entities
    }

# GitHub persistence helper
def push_to_github(file_path: pathlib.Path):
    token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPO")
    branch = os.getenv("GITHUB_BRANCH", "main")
    if not token or not repo:
        print("✔ GitHub persistence skipped: set GITHUB_TOKEN and GITHUB_REPO env vars.")
        return

    with open(file_path, "rb") as f:
        content_b64 = base64.b64encode(f.read()).decode()
    api_path = file_path.as_posix()
    url = f"https://api.github.com/repos/{repo}/contents/{api_path}"
    headers = {"Authorization": f"token {token}"}

    resp = requests.get(url, headers=headers)
    sha = resp.json().get("sha") if resp.status_code == 200 else None

    payload = {"message": f"Add movers data for {DATE_STR}", "content": content_b64, "branch": branch}
    if sha:
        payload["sha"] = sha

    put_resp = requests.put(url, headers=headers, json=payload)
    if put_resp.status_code in (200, 201):
        print(f"✔ Pushed to GitHub: {repo}/{api_path}@{branch}")
    else:
        print(f"✖ GitHub push failed: {put_resp.status_code} - {put_resp.text}")

# STEP 7 · Persist + vector-ingest
def main():
    blob = build_movers_blob()
    out_file = DATA_DIR / "movers.json"
    out_file.write_text(json.dumps(blob, indent=2))
    print(f"✔ Saved movers JSON → {out_file}")

    try:
        ingest_section(blob)
        print("✔ Ingested movers section into FAISS")
    except Exception as exc:
        print(f"Vector-ingest skipped – {exc}")

    # Persist to GitHub
    push_to_github(out_file)

    print(f"⏱ Total runtime: {round(time.time() - T0, 2)} seconds")

if __name__ == "__main__":
    main()
