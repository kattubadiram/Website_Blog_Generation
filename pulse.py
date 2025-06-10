import datetime as dt
import json
import pathlib
import time
import os
import base64
from typing import Dict, List

import importlib.util
import pandas as pd
import requests
import feedparser
import yfinance as yf
import pytz                       # ← NEW
from transformers import logging as tf_logging, pipeline, Pipeline

from article_extractor import extract_article_text

# Optional RAG ingestion
try:
    from rag_layer.ingest import ingest_section
except ImportError:
    ingest_section = lambda *_a, **_kw: None

# ── Timezones & Dates ───────────────────────────
EST    = pytz.timezone("America/New_York")
TODAY  = dt.datetime.now(dt.timezone.utc).astimezone(EST).date()
DATA_DIR = pathlib.Path("data") / TODAY.isoformat()
DATA_DIR.mkdir(parents=True, exist_ok=True)

# 1.1 · Symbols we track
INDICES = {
    "S&P 500":               "^GSPC",
    "Dow Jones Industrial":  "^DJI",
    "Nasdaq Composite":      "^IXIC",
    "10-Year Treasury Yield": "^TNX",
    "U.S. Dollar Index":     "DX-Y.NYB",
    "CBOE VIX":              "^VIX"
}

COMMODITIES = {
    "WTI Crude Oil": "CL=F",
    "Brent Crude":   "BZ=F",
    "Gold":          "GC=F",
    "Silver":        "SI=F",
    "Natural Gas":   "NG=F"
}

SYMBOLS = {**INDICES, **COMMODITIES}  # merged dict

# Summariser pipeline setup
tf_logging.set_verbosity_error()
MODEL_NAME = "sshleifer/distilbart-cnn-12-6"
summariser: Pipeline = pipeline(
    "summarization",
    model=MODEL_NAME,
    tokenizer=MODEL_NAME,
    framework="pt",
    truncation=True,
    token=None  # anonymous → avoids 401
)

# STEP 3 · Pull latest quotes
def fetch_quotes(symbol_map: Dict[str, str]) -> Dict[str, Dict]:
    tickers = list(symbol_map.values())
    df = yf.download(
        tickers,
        period="5d",
        interval="1d",
        auto_adjust=False,
        threads=False,
        progress=False
    )["Close"]

    latest = df.iloc[-1]
    prev   = df.iloc[-2]

    out: Dict[str, Dict] = {}
    for name, sym in symbol_map.items():
        try:
            last = float(latest[sym])
            prev_close = float(prev[sym])
            pct = round((last - prev_close) / prev_close * 100, 2)
            out[name] = {
                "symbol": sym,
                "last_close": last,
                "prev_close": prev_close,
                "pct_change": pct
            }
        except Exception as exc:
            print(f"[Quote error] {name} ({sym}): {exc}")
            out[name] = {"symbol": sym, "last_close": None, "prev_close": None, "pct_change": None}
    return out

# STEP 4 · Fetch up to 10 RSS headlines
def yahoo_rss(symbol: str, pause: float = 1.0) -> List[Dict]:
    url = (
        f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}"
        "&region=US&lang=en-US"
    )
    time.sleep(pause)
    parsed = feedparser.parse(url)
    if parsed.bozo:
        raise RuntimeError(parsed.bozo_exception)
    out = []
    for e in parsed.entries[:10]:
        out.append({
            "title":     e.get("title", "").strip(),
            "summary":   e.get("summary", "").strip(),
            "link":      e.get("link", "").strip(),
            "published": e.get("published", "").strip()
        })
    return out

# STEP 5 · Summarise entries
def summarise_entries(entries: List[Dict]) -> List[str]:
    lines: List[str] = []
    for e in entries:
        art_text = extract_article_text(e["link"])
        src_text = art_text if art_text else e["title"] + ". " + e.get("summary", "")
        line = summariser(src_text, max_length=60, min_length=15, do_sample=False)[0]["summary_text"]
        lines.append(line.strip())
    return lines

# STEP 6 · Build pulse blob
def build_pulse_blob(pause: float = 1.0) -> Dict:
    quote_data = fetch_quotes(SYMBOLS)
    entities: List[Dict] = []
    for name, sym in SYMBOLS.items():
        try:
            rss_items = yahoo_rss(sym, pause=pause)
            summaries = summarise_entries(rss_items)
        except Exception as exc:
            print(f"[RSS error] {name} ({sym}): {exc}")
            summaries = []
        entities.append({
            "ticker": sym,
            "label": name,
            "data": quote_data.get(name, {}),
            "summaries": summaries
        })

    return {
        "meta": {"section": "pulse", "generated_at": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z", "source": "yfinance + yahoo_rss"},
        "entities": entities
    }

# GitHub persistence helper
def push_to_github(file_path: pathlib.Path):
    token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPO")  # 'owner/repo'
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

    payload = {"message": f"Add pulse data for {TODAY.isoformat()}", "content": content_b64, "branch": branch}
    if sha:
        payload["sha"] = sha
    put_resp = requests.put(url, headers=headers, json=payload)
    if put_resp.status_code in (200, 201):
        print(f"✔ Pushed to GitHub: {repo}/{api_path}@{branch}")
    else:
        print(f"✖ GitHub push failed: {put_resp.status_code} - {put_resp.text}")

# STEP 7 · Persist + optional vector-ingest
def main():
    blob = build_pulse_blob()
    out_file = DATA_DIR / "pulse.json"
    out_file.write_text(json.dumps(blob, indent=2))
    print(f"✔ Saved pulse JSON → {out_file}")

    try:
        ingest_section(blob)
        print("✔ Ingested pulse section into FAISS")
    except Exception as exc:
        print(f"Vector-ingest skipped – {exc}")

    # Persist to GitHub
    push_to_github(out_file)

    print(f"⏱ Total runtime: {round(time.time() - T0, 2)} seconds")

if __name__ == "__main__":
    main()
