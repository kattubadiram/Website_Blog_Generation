"""
watchlist.py  ·  Morning Market Primer  – Section 4
---------------------------------------------------
Builds tomorrow’s earnings/dividends calendar and a
“tickers-to-watch” list, enriched with headline summaries.
"""
import datetime as dt
import json
import pathlib
import time
from typing import Dict, List, Optional

import datetime as dt
import importlib.util
import json
import pathlib
import time
from typing import Dict, List, Optional

import feedparser
import pandas as pd
import requests
import yfinance as yf
from transformers import logging as tf_logging, pipeline, Pipeline

from article_extractor import extract_article_text

import feedparser
import pandas as pd
import requests
import yfinance as yf
import pytz                       # ← NEW

from article_extractor import extract_article_text
try:
    from rag_layer.ingest import ingest_section
except ImportError:
    ingest_section = lambda *_a, **_kw: None

# ── New EST-aware dates ───────────────────────────
EST      = pytz.timezone("America/New_York")
TODAY    = dt.datetime.now(dt.timezone.utc).astimezone(EST).date()
TOMORROW = TODAY + dt.timedelta(days=1)

DATA_DIR = pathlib.Path("data") / TODAY.isoformat()
DATA_DIR.mkdir(parents=True, exist_ok=True)

# (the remainder of your NASDAQ-query & RSS-summary code is unchanged)
# watchlist.py (updated to fetch only tomorrow’s data, with timing logs)

# Calculate “tomorrow” and set DATA_DIR accordingly
TODAY = dt.date.today()
TOMORROW = TODAY + dt.timedelta(days=1)
DATA_DIR = pathlib.Path("data") / TODAY.isoformat()
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Only look up TOMORROW’s date
LOOKAHEAD_DAYS = {TOMORROW.isoformat()}

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://www.nasdaq.com",
    "Referer": "https://www.nasdaq.com/",
}

EARN_URL = "https://api.nasdaq.com/api/calendar/earnings?date={d}"
DIV_URL = "https://api.nasdaq.com/api/calendar/dividends?date={d}"

# ───────────────────────────────────────────────
# Summarizer setup
# ───────────────────────────────────────────────
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


# ───────────────────────────────────────────────
# Helper to compute implied move %
# ───────────────────────────────────────────────
def implied_move_pct(tkr: yf.Ticker) -> Optional[float]:
    try:
        exp = tkr.options[0]
        chain = tkr.option_chain(exp)
        spot = tkr.fast_info["last_price"]
        calls = chain.calls.to_dict("records")
        puts = chain.puts.to_dict("records")
        nearest_call = min(calls, key=lambda r: abs(r["strike"] - spot))
        nearest_put = min(puts, key=lambda r: abs(r["strike"] - spot))
        return round(
            (nearest_call["lastPrice"] + nearest_put["lastPrice"]) / spot * 100,
            2
        )
    except Exception:
        return None


# ───────────────────────────────────────────────
# Fetch earnings for TOMORROW only
# ───────────────────────────────────────────────
def fetch_earnings(top_n: int = 5) -> Dict[str, Dict]:
    """
    Fetch earnings for TOMORROW via Nasdaq API.
    Returns a dict mapping ticker → earnings info (top-N by market cap).
    """
    def get_mcap(sym: str) -> int:
        try:
            return yf.Ticker(sym).info.get("marketCap", 0) or 0
        except Exception:
            return 0

    all_rows = []
    day = TOMORROW.isoformat()
    try:
        response = requests.get(EARN_URL.format(d=day), headers=HEADERS, timeout=10)
        data = response.json()
        rows = data.get("data", {}).get("rows", []) or []
        for row in rows:
            row["earn_date"] = day
        all_rows.extend(rows)
    except Exception:
        pass

    # Sort by market cap
    with_caps = []
    for row in all_rows:
        sym = row.get("symbol", "").upper()
        cap = get_mcap(sym)
        with_caps.append((row, cap))
    with_caps.sort(key=lambda x: x[1], reverse=True)

    # Select top-N by market cap
    top_rows = with_caps[:top_n]

    earnings_info: Dict[str, Dict] = {}
    for row, _ in top_rows:
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


# ───────────────────────────────────────────────
# Fetch dividends for TOMORROW only
# ───────────────────────────────────────────────
def fetch_dividends(top_n: int = 5) -> Dict[str, Dict]:
    """
    Fetch dividends for TOMORROW via Nasdaq API.
    Returns a dict mapping ticker → dividend info (top-N by market cap).
    """
    start = time.perf_counter()

    def get_mcap(sym: str) -> int:
        try:
            return yf.Ticker(sym).info.get("marketCap", 0) or 0
        except:
            return 0

    dividends_info: Dict[str, Dict] = {}
    day = TOMORROW.isoformat()
    try:
        response = requests.get(DIV_URL.format(d=day), headers=HEADERS, timeout=10)
        data = response.json()
        # Some endpoints use “calendar” → “rows”; others use “rows” directly
        rows = (
            data.get("data", {}).get("calendar", {}).get("rows", [])
            or data.get("data", {}).get("rows", [])
            or []
        )
    except Exception:
        rows = []

    with_caps = [(row, get_mcap(row.get("symbol", "").upper())) for row in rows]
    with_caps.sort(key=lambda x: x[1], reverse=True)

    for row, _ in with_caps[:top_n]:
        sym = row.get("symbol", "").upper()
        dividends_info[sym] = {
            "ticker": sym,
            "event": "dividend",
            "date": day,
            "amount": row.get("amount") or row.get("dividend_Rate"),
            "pay_date": row.get("paymentDate") or row.get("payment date"),
        }

    print(f"✔ Dividends fetched in {time.perf_counter() - start:.2f}s")
    return dividends_info


# ───────────────────────────────────────────────
# Fetch and summarize RSS articles for a symbol
# ───────────────────────────────────────────────
def rss_summaries(sym: str, pause: float = 1.0) -> List[str]:
    url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={sym}&region=US&lang=en-US"
    time.sleep(pause)
    parsed = feedparser.parse(url)
    if parsed.bozo:
        return []
    lines: List[str] = []
    for entry in parsed.entries[:10]:
        art_text = extract_article_text(entry.get("link", ""), pause=0.5)
        src = (
            art_text
            or entry.get("title", "").strip() + ". " + entry.get("summary", "").strip()
        )
        summary = summariser(src, max_length=60, min_length=15, do_sample=False)[0][
            "summary_text"
        ]
        lines.append(summary.strip())
    return lines


# ───────────────────────────────────────────────
# Build the watchlist blob using TOMORROW only
# ───────────────────────────────────────────────
def build_watchlist_blob() -> Dict:
    start = time.perf_counter()
    earnings = fetch_earnings()
    dividends = fetch_dividends()
    universe = {**earnings, **dividends}

    entities: List[Dict] = []
    for sym, base_info in universe.items():
        rss_start = time.perf_counter()
        try:
            summaries = rss_summaries(sym)
        except Exception:
            summaries = []
        print(f"RSS+summary for {sym} → {time.perf_counter() - rss_start:.2f}s")

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

    print(f"✔ Watchlist blob built in {time.perf_counter() - start:.2f}s")
    return {
        "meta": {
            "section": "watchlist",
            "generated_at": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "source": "nasdaq_api + yahoo_rss",
            "target_date": TOMORROW.isoformat()
        },
        "entities": entities
    }


# ───────────────────────────────────────────────
# Main entrypoint
# ───────────────────────────────────────────────
def main():
    total_start = time.perf_counter()
    blob = build_watchlist_blob()

    out_file = DATA_DIR / "watchlist.json"
    out_file.write_text(json.dumps(blob, indent=2))
    print(f"✔ Saved → {out_file}")

    try:
        ingest_section(blob)
        print("✔ Ingested into FAISS")
    except Exception as exc:
        print(f"Vector ingest skipped – {exc}")

    print(f"✔ Total time: {time.perf_counter() - total_start:.2f}s")


if __name__ == "__main__":
    main()
