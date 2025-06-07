"""
movers.py  ·  Morning Market Primer  – Section 3
------------------------------------------------
Scrapes Yahoo Finance mover lists (most-active, gainers, losers,
52-week highs/lows), grabs recent RSS headlines, summarises them,
and writes a consolidated JSON blob.
"""
import datetime as dt
import json
import pathlib
import time
from typing import Dict, List

import datetime as dt
import importlib.util
import json
import pathlib
import time
from typing import Dict, List
import time
T0 = time.time()
import requests
import pandas as pd
import feedparser
from transformers import logging as tf_logging, pipeline, Pipeline
from article_extractor import extract_article_text


import feedparser
import pandas as pd
import requests
import pytz                       # ← NEW
T0 = time.time()

try:
    from rag_layer.ingest import ingest_section
except ImportError:
    ingest_section = lambda *_a, **_kw: None

# ── New EST-aware folder ───────────────────────────
EST       = pytz.timezone("America/New_York")
DATE_STR  = dt.datetime.now(dt.timezone.utc).astimezone(EST).date().isoformat()
DATA_DIR  = pathlib.Path("data") / DATE_STR
DATA_DIR.mkdir(parents=True, exist_ok=True)

# (all other code is exactly as before)
DATA_DIR = pathlib.Path("data") / dt.date.today().isoformat()
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

# ────────────────────────────────────────────────────────────────
# STEP 2 · Summariser pipeline (backend guard & anonymous download)
# ────────────────────────────────────────────────────────────────
if not any(importlib.util.find_spec(x) for x in ("torch", "tensorflow", "jax")):
    raise RuntimeError(
        "No deep-learning backend detected. "
        "Install CPU PyTorch:\n"
        "    pip install torch --index-url https://download.pytorch.org/whl/cpu torch"
    )

MODEL_NAME = "sshleifer/distilbart-cnn-12-6"  # ≈480 MB

summariser: Pipeline = pipeline(
    "summarization",
    model=MODEL_NAME,
    tokenizer=MODEL_NAME,
    framework="pt",
    truncation=True,
    token=None  # anonymous → avoids 401
)

# ────────────────────────────────────────────────────────────────
# STEP 3 · Scrape top-5 tickers per category
# ────────────────────────────────────────────────────────────────
def top5_symbols(category: str, pause: float = 1.5) -> List[str]:
    """
    Fetches the first five ticker symbols from the Yahoo Finance page for the given category.
    """
    if category not in URLS:
        raise KeyError(category)
    time.sleep(pause)
    html = requests.get(URLS[category], headers=HEADERS, timeout=12).text
    tables = pd.read_html(html, flavor="lxml")
    if not tables:
        return []
    df = tables[0]
    return df.get("Symbol", [])[:5].tolist()

# ────────────────────────────────────────────────────────────────
# STEP 4 · Fetch RSS headlines for a ticker
# ────────────────────────────────────────────────────────────────
def yahoo_rss(symbol: str, pause: float = 1.0) -> List[Dict]:
    """
    Queries Yahoo’s RSS feed for the given symbol.
    Returns a list of up to 10 dicts: {title, summary, link, published}.
    """
    url = (
        f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}"
        "&region=US&lang=en-US"
    )
    time.sleep(pause)
    parsed = feedparser.parse(url)
    if parsed.bozo:
        raise RuntimeError(parsed.bozo_exception)
    out: List[Dict] = []
    for e in parsed.entries[:10]:
        out.append({
            "title":     e.get("title", "").strip(),
            "summary":   e.get("summary", "").strip(),
            "link":      e.get("link", "").strip(),
            "published": e.get("published", "").strip(),
        })
    return out

# ────────────────────────────────────────────────────────────────
# STEP 5 · Condense headlines into one line
# ────────────────────────────────────────────────────────────────
def summarise_headlines(entries: List[Dict]) -> List[str]:
    lines: List[str] = []
    for e in entries:
        art_text = extract_article_text(e["link"])
        src_text = art_text if art_text else e["title"] + ". " + e.get("summary", "")
        line = summariser(src_text, max_length=60, min_length=15, do_sample=False)[0]["summary_text"]
        lines.append(line.strip())
    return lines


# ────────────────────────────────────────────────────────────────
# STEP 6 · Build canonical JSON blob
# ────────────────────────────────────────────────────────────────
def build_movers_blob(pause: float = 1.0) -> Dict:
    """
    1) Fetch top-5 symbols for each mover category.
    2) Fetch up to 10 RSS headlines and summarise each.
    3) Construct the JSON in our agreed schema.
    """
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
                    "label":     sym,         # can map to company name later
                    "data":      {"category": cat},
                    "summaries": summaries
                })
            except Exception as exc:
                print(f"[RSS error] {sym}: {exc}")

    return {
        "meta": {
            "section": "movers",
            "generated_at": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "source": "yahoo_rss"
        },
        "entities": entities
    }

# ────────────────────────────────────────────────────────────────
# STEP 7 · Persist + vector-ingest
# ────────────────────────────────────────────────────────────────
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

    print(f"⏱ Total runtime: {round(time.time() - T0, 2)} seconds")
    
if __name__ == "__main__":
    main()
