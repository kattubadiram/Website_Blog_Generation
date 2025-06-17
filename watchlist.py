"""
watchlist.py  ·  Morning Market Primer – Section 4
---------------------------------------------------
Builds tomorrow’s earnings/dividends calendar and a
“tickers-to-watch” list, enriched with headline summaries.

Outputs:
  • watchlist_log.jsonl
  • watchlist_latest.json
"""
import datetime as dt
import json
import pathlib
import time
from typing import Dict, List, Optional

import pandas as pd
import requests
import yfinance as yf
import feedparser
import pytz
from transformers import logging as tf_logging, pipeline, Pipeline

from article_extractor import extract_article_text

try:
    from rag_layer.ingest import ingest_section
except ImportError:
    ingest_section = lambda *_a, **_kw: None

# ─── Setup & Constants ───────────────────────────────────────────
EST       = pytz.timezone("America/New_York")
TODAY     = dt.datetime.now(dt.timezone.utc).astimezone(EST).date()
TOMORROW  = TODAY + dt.timedelta(days=1)
LOOKAHEAD_DAYS = {TOMORROW.isoformat()}

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://www.nasdaq.com",
    "Referer": "https://www.nasdaq.com/",
}

EARN_URL = "https://api.nasdaq.com/api/calendar/earnings?date={d}"
DIV_URL = "https://api.nasdaq.com/api/calendar/dividends?date={d}"

MODEL_NAME = "sshleifer/distilbart-cnn-12-6"
tf_logging.set_verbosity_error()

summariser: Pipeline = pipeline(
    "summarization",
    model=MODEL_NAME,
    tokenizer=MODEL_NAME,
    framework="pt",
    truncation=True,
    token=None
)

LOG_FILE    = pathlib.Path("watchlist_log.jsonl")
LATEST_FILE = pathlib.Path("watchlist_latest.json")


# ─── Option-Implied Move % ───────────────────────────────────────
def implied_move_pct(tkr: yf.Ticker) -> Optional[float]:
    try:
        exp = tkr.options[0]
        chain = tkr.option_chain(exp)
        spot = tkr.fast_info["last_price"]
        calls = chain.calls.to_dict("records")
        puts = chain.puts.to_dict("records")
        nearest_call = min(calls, key=lambda r: abs(r["strike"] - spot))
        nearest_put = min(puts, key=lambda r: abs(r["strike"] - spot))
        return round((nearest_call["lastPrice"] + nearest_put["lastPrice"]) / spot * 100, 2)
    except Exception:
        return None


# ─── Nasdaq Calendar Queries ─────────────────────────────────────
def fetch_earnings(top_n: int = 5) -> Dict[str, Dict]:
    def get_mcap(sym: str) -> int:
        try:
            return yf.Ticker(sym).info.get("marketCap", 0) or 0
        except:
            return 0

    day = TOMORROW.isoformat()
    all_rows = []
    try:
        response = requests.get(EARN_URL.format(d=day), headers=HEADERS, timeout=10)
        rows = response.json().get("data", {}).get("rows", []) or []
        for row in rows:
            row["earn_date"] = day
            all_rows.append(row)
    except:
        pass

    with_caps = [(row, get_mcap(row.get("symbol", "").upper())) for row in all_rows]
    with_caps.sort(key=lambda x: x[1], reverse=True)
    top_rows = with_caps[:top_n]

    return {
        row.get("symbol", "").upper(): {
            "ticker": row.get("symbol", "").upper(),
            "event": "earnings",
            "date": row["earn_date"],
            "time": row.get("time"),
            "eps_estimate": row.get("epsestimate"),
            "revenue_estimate": row.get("revestimate"),
        }
        for row, _ in top_rows
    }


def fetch_dividends(top_n: int = 5) -> Dict[str, Dict]:
    def get_mcap(sym: str) -> int:
        try:
            return yf.Ticker(sym).info.get("marketCap", 0) or 0
        except:
            return 0

    day = TOMORROW.isoformat()
    try:
        response = requests.get(DIV_URL.format(d=day), headers=HEADERS, timeout=10)
        rows = (
            response.json().get("data", {}).get("calendar", {}).get("rows", [])
            or response.json().get("data", {}).get("rows", [])
            or []
        )
    except:
        rows = []

    with_caps = [(row, get_mcap(row.get("symbol", "").upper())) for row in rows]
    with_caps.sort(key=lambda x: x[1], reverse=True)

    return {
        row.get("symbol", "").upper(): {
            "ticker": row.get("symbol", "").upper(),
            "event": "dividend",
            "date": day,
            "amount": row.get("amount") or row.get("dividend_Rate"),
            "pay_date": row.get("paymentDate") or row.get("payment date"),
        }
        for row, _ in with_caps[:top_n]
    }


# ─── RSS Summarization ───────────────────────────────────────────
def rss_summaries(sym: str, pause: float = 1.0) -> List[str]:
    url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={sym}&region=US&lang=en-US"
    time.sleep(pause)
    parsed = feedparser.parse(url)
    if parsed.bozo:
        return []
    lines = []
    for entry in parsed.entries[:10]:
        art_text = extract_article_text(entry.get("link", ""), pause=0.5)
        src = art_text or entry.get("title", "").strip() + ". " + entry.get("summary", "").strip()
        summary = summariser(src, max_length=60, min_length=15, do_sample=False)[0]["summary_text"]
        lines.append(summary.strip())
    return lines


# ─── Main Blob Builder ───────────────────────────────────────────
def build_watchlist_blob() -> Dict:
    earnings = fetch_earnings()
    dividends = fetch_dividends()
    universe = {**earnings, **dividends}

    entities: List[Dict] = []
    for sym, base_info in universe.items():
        try:
            summaries = rss_summaries(sym)
        except:
            summaries = []

        if base_info["event"] == "earnings":
            base_info["implied_move_pct"] = implied_move_pct(yf.Ticker(sym))
        else:
            base_info["implied_move_pct"] = None

        try:
            label = yf.Ticker(sym).info.get("shortName", sym)
        except:
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


# ─── Persistence & Entrypoint ────────────────────────────────────
def save_to_log(blob: Dict):
    with LOG_FILE.open("a") as f:
        f.write(json.dumps(blob) + "\n")
    LATEST_FILE.write_text(json.dumps(blob, indent=2))
    print("✔ Saved to watchlist_log.jsonl and watchlist_latest.json")

def main():
    blob = build_watchlist_blob()
    save_to_log(blob)

    try:
        ingest_section(blob)
        print("✔ Ingested into FAISS")
    except Exception as exc:
        print(f"Vector ingest skipped – {exc}")


if __name__ == "__main__":
    main()
