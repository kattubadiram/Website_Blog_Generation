import datetime as dt
import json
import pathlib
import time
import os
import base64
from typing import Dict, List, Optional

import feedparser
import pandas as pd
import requests
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
EST      = pytz.timezone("America/New_York")
TODAY    = dt.datetime.now(dt.timezone.utc).astimezone(EST).date()
TOMORROW = TODAY + dt.timedelta(days=1)

# Data directory for today's run
DATA_DIR = pathlib.Path("data") / TODAY.isoformat()
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Nasdaq API endpoints
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://www.nasdaq.com",
    "Referer": "https://www.nasdaq.com/",
}
EARN_URL = "https://api.nasdaq.com/api/calendar/earnings?date={d}"
DIV_URL   = "https://api.nasdaq.com/api/calendar/dividends?date={d}"

# Summarizer setup
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

# Helper: implied move % from options
def implied_move_pct(tkr: yf.Ticker) -> Optional[float]:
    try:
        exp = tkr.options[0]
        chain = tkr.option_chain(exp)
        spot = tkr.fast_info["last_price"]
        calls = chain.calls.to_dict("records")
        puts = chain.puts.to_dict("records")
        nearest_call = min(calls, key=lambda r: abs(r["strike"] - spot))
        nearest_put  = min(puts,  key=lambda r: abs(r["strike"] - spot))
        return round(
            (nearest_call["lastPrice"] + nearest_put["lastPrice"]) / spot * 100,
            2
        )
    except Exception:
        return None

# Fetch earnings for tomorrow
def fetch_earnings(top_n: int = 5) -> Dict[str, Dict]:
    def get_mcap(sym: str) -> int:
        try:
            return yf.Ticker(sym).info.get("marketCap", 0) or 0
        except Exception:
            return 0

    all_rows = []
    day = TOMORROW.isoformat()
    try:
        resp = requests.get(EARN_URL.format(d=day), headers=HEADERS, timeout=10)
        data = resp.json()
        rows = data.get("data", {}).get("rows", []) or []
        for row in rows:
            row["earn_date"] = day
        all_rows.extend(rows)
    except Exception:
        pass

    # Sort by market cap
    with_caps = [(row, get_mcap(row.get("symbol", "").upper())) for row in all_rows]
    with_caps.sort(key=lambda x: x[1], reverse=True)

    earnings_info: Dict[str, Dict] = {}
    for row, _ in with_caps[:top_n]:
        sym = row.get("symbol", "").upper()
        earnings_info[sym] = {
            "ticker": sym,
            "event": "earnings",
            "date": row["earn_date"],
            "time": row.get("time"),
            "eps_estimate": row.get("epsestimate"),
            "revenue_estimate": row.get("revestimate"),
        }

    return earnings_info

# Fetch dividends for tomorrow
def fetch_dividends(top_n: int = 5) -> Dict[str, Dict]:
    def get_mcap(sym: str) -> int:
        try:
            return yf.Ticker(sym).info.get("marketCap", 0) or 0
        except Exception:
            return 0

    day = TOMORROW.isoformat()
    try:
        resp = requests.get(DIV_URL.format(d=day), headers=HEADERS, timeout=10)
        data = resp.json()
        rows = (
            data.get("data", {}).get("calendar", {}).get("rows", [])
            or data.get("data", {}).get("rows", [])
            or []
        )
    except Exception:
        rows = []

    with_caps = [(row, get_mcap(row.get("symbol", "").upper())) for row in rows]
    with_caps.sort(key=lambda x: x[1], reverse=True)

    dividends_info: Dict[str, Dict] = {}
    for row, _ in with_caps[:top_n]:
        sym = row.get("symbol", "").upper()
        dividends_info[sym] = {
            "ticker": sym,
            "event": "dividend",
            "date": day,
            "amount": row.get("amount") or row.get("dividend_Rate"),
            "pay_date": row.get("paymentDate") or row.get("payment date"),
        }

    return dividends_info

# Fetch and summarize RSS articles
def rss_summaries(sym: str, pause: float = 1.0) -> List[str]:
    url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={sym}&region=US&lang=en-US"
    time.sleep(pause)
    parsed = feedparser.parse(url)
    if parsed.bozo:
        return []
    lines: List[str] = []
    for entry in parsed.entries[:10]:
        art_text = extract_article_text(entry.get("link", ""), pause=0.5)
        src = art_text or (entry.get("title", "").strip() + ". " + entry.get("summary", "").strip())
        summary = summariser(src, max_length=60, min_length=15, do_sample=False)[0]["summary_text"]
        lines.append(summary.strip())
    return lines

# Build watchlist blob
def build_watchlist_blob() -> Dict:
    earnings  = fetch_earnings()
    dividends = fetch_dividends()
    universe  = {**earnings, **dividends}

    entities: List[Dict] = []
    for sym, base_info in universe.items():
        summaries = []
        try:
            summaries = rss_summaries(sym)
        except Exception:
            pass

        if base_info["event"] == "earnings":
            tkr = yf.Ticker(sym)
            base_info["implied_move_pct"] = implied_move_pct(tkr)
        else:
            base_info["implied_move_pct"] = None

        try:
            label = yf.Ticker(sym).info.get("shortName", sym)
        except Exception:
            label = sym

        entities.append({
            "ticker": sym,
            "label": label,
            "data": base_info,
            "summaries": summaries
        })

    return {
        "meta": {
            "section": "watchlist",
            "generated_at": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "source": "nasdaq_api + yahoo_rss",
            "target_date": TOMORROW.isoformat()
        },
        "entities": entities
    }

# Push file to GitHub repo via REST API
def push_to_github(file_path: pathlib.Path):
    token = os.getenv("GITHUB_TOKEN")
    repo  = os.getenv("GITHUB_REPO")  # format: 'owner/repo'
    branch = os.getenv("GITHUB_BRANCH", "main")
    if not token or not repo:
        print("✔ GitHub persistence skipped: set GITHUB_TOKEN and GITHUB_REPO env vars.")
        return

    # Relative path in the repo
    repo_path = file_path.as_posix()
    with open(file_path, "rb") as f:
        content_b64 = base64.b64encode(f.read()).decode()

    url = f"https://api.github.com/repos/{repo}/contents/{repo_path}"
    headers = {"Authorization": f"token {token}"}

    # Check if file exists to get 'sha'
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        sha = resp.json().get("sha")
    else:
        sha = None

    payload = {
        "message": f"Add watchlist data for {TOMORROW.isoformat()}",
        "content": content_b64,
        "branch": branch
    }
    if sha:
        payload["sha"] = sha

    put_resp = requests.put(url, headers=headers, json=payload)
    if put_resp.status_code in (200, 201):
        print(f"✔ Pushed to GitHub: {repo}/{repo_path}@{branch}")
    else:
        print(f"✖ GitHub push failed: {put_resp.status_code} - {put_resp.text}")

# Main entrypoint
def main():
    blob = build_watchlist_blob()
    out_file = DATA_DIR / "watchlist.json"
    out_file.write_text(json.dumps(blob, indent=2))
    print(f"✔ Saved → {out_file}")

    # Attempt RAG ingestion
    try:
        ingest_section(blob)
        print("✔ Ingested into FAISS")
    except Exception as exc:
        print(f"Vector ingest skipped – {exc}")

    # Persist to GitHub
    push_to_github(out_file)

    print(f"✔ Total time: {time.perf_counter() - time.perf_counter():.2f}s")

if __name__ == "__main__":
    main()
