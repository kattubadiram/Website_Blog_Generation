"""
trend.py  ·  Morning Market Primer
----------------------------------
Computes S&P 500 breadth (50- & 200-day SMA %),
sector ETF moves, and the RSP/SPY ratio.

Outputs
  • data/YYYY-MM-DD/breadth.json   (aggregate snapshot)
  • data/YYYY-MM-DD/details.json   (per-ticker metrics)
"""
# STEP 1 ─────────────────────────────────────────────
import datetime as dt
import json
import pathlib
import time
from typing import Dict, List, Tuple

import pandas as pd
import yfinance as yf
import pytz                       # ← NEW
T0 = time.time()

# local modules
from sp500 import sp500_tickers
try:
    from rag_layer.ingest import ingest_section   # optional
except ImportError:
    ingest_section = lambda *_a, **_kw: None

# ── New EST-aware folder ───────────────────────────
EST   = pytz.timezone("America/New_York")
TODAY = dt.datetime.now(dt.timezone.utc).astimezone(EST).date()
DATA_DIR = pathlib.Path("data") / TODAY.isoformat()   # e.g. data/2025-06-07
DATA_DIR.mkdir(parents=True, exist_ok=True)

# (rest of the original code is unchanged)
# ---------------------------------------------------------------------
# … EVERYTHING BELOW THIS LINE IS IDENTICAL TO YOUR ORIGINAL SCRIPT …
# ---------------------------------------------------------------------

# 1.2 · Helpers --------------------------------------------------------
def _last_week_bounds(d: dt.date) -> Tuple[dt.date, dt.date]:
    last_monday = d - dt.timedelta(days=d.weekday() + 7)
    last_friday = last_monday + dt.timedelta(days=4)
    return last_monday, last_friday

LAST_MON, LAST_FRI = _last_week_bounds(TODAY)

# … keep the remainder of your logic intact …
TODAY = dt.date.today()
DATA_DIR = pathlib.Path("data") / TODAY.isoformat()  # e.g. data/2025-06-04
DATA_DIR.mkdir(parents=True, exist_ok=True)

SECTOR_TICKERS = [
    "XLB", "XLC", "XLE", "XLF", "XLI",
    "XLK", "XLP", "XLU", "XLV", "XLRE", "XLY"
]


# STEP 2 ────────────────────────────────────────────────────────────
# Helper: calculate date anchors (last Monday / Friday of prior week)
def _last_week_bounds(today: dt.date) -> Tuple[dt.date, dt.date]:
    this_monday = today - dt.timedelta(days=today.weekday())
    last_monday = this_monday - dt.timedelta(days=7)
    last_friday = last_monday + dt.timedelta(days=4)
    return last_monday, last_friday


LAST_MON, LAST_FRI = _last_week_bounds(TODAY)


# STEP 3 ────────────────────────────────────────────────────────────
# % of constituents above 50- & 200-day SMAs
def pct_above_ma() -> Tuple[Dict, List[Dict]]:
    """
    Fetch one year of daily closes for each S&P 500 ticker, compute:
      - latest 50-day SMA
      - latest 200-day SMA
      - whether current price is above each SMA

    Returns:
      aggregate (dict):
        {
          "50d": <percent above 50-day SMA>,
          "200d": <percent above 200-day SMA>,
          "sample_size": <number of symbols included>
        }
      details (list[dict]): per-ticker:
        {
          "ticker": <symbol>,
          "current": <latest close>,
          "sma50": <latest 50-day SMA>,
          "sma200": <latest 200-day SMA>,
          "above50": <True/False>,
          "above200": <True/False>,
          "summaries": []   # Trend has no text to summarise, but field must exist
        }
    """
    print("▶ Computing SMA breadth for all S&P 500 constituents …")
    above_50 = above_200 = valid = 0
    details: List[Dict] = []

    for idx, symbol in enumerate(sp500_tickers, 1):
        try:
            hist = yf.Ticker(symbol).history(period="1y", auto_adjust=False)
            time.sleep(0.3)  # throttle politely

            closes = hist["Close"]
            if len(closes) < 200:
                # Skip tickers without sufficient history
                continue

            sma50 = closes.rolling(window=50).mean().iloc[-1]
            sma200 = closes.rolling(window=200).mean().iloc[-1]
            price = closes.iloc[-1]

            above50_flag = price > sma50
            above200_flag = price > sma200

            if above50_flag:
                above_50 += 1
            if above200_flag:
                above_200 += 1
            valid += 1

            details.append({
                "ticker": symbol,
                "current": round(float(price), 2),
                "sma50": round(float(sma50), 2),
                "sma200": round(float(sma200), 2),
                "above50": bool(above50_flag),
                "above200": bool(above200_flag),
                "summaries": []  # no text to summarise for Trend
            })

            print(f"{idx:>3}/{len(sp500_tickers)}  {symbol}: ok")

        except Exception as exc:
            print(f"{idx:>3}/{len(sp500_tickers)}  {symbol}: error – {exc}")

    pct50 = round(above_50 / valid * 100, 1) if valid else 0.0
    pct200 = round(above_200 / valid * 100, 1) if valid else 0.0

    aggregate = {
        "50d": pct50,
        "200d": pct200,
        "sample_size": valid
    }
    return aggregate, details


# STEP 4 ────────────────────────────────────────────────────────────
# 1-week sector ETF percentage moves
def sector_weekly() -> List[Dict]:
    """
    Download daily 'Close' prices for sector ETFs between LAST_MON and LAST_FRI.
    Compute the percentage change from Monday’s close to Friday’s close.
    Returns a list of dicts:
      { "sector": <ticker>, "w_change": <pct change> }
    """
    price_df = yf.download(
        SECTOR_TICKERS,
        start=str(LAST_MON),
        end=str(LAST_FRI + dt.timedelta(days=1)),
        progress=False,
        auto_adjust=False
    )["Close"]

    mon_close = price_df.iloc[0]
    fri_close = price_df.iloc[-1]
    pct = ((fri_close - mon_close) / mon_close * 100).round(2)

    return [{"sector": t, "w_change": float(pct[t])} for t in pct.index]


# STEP 5 ────────────────────────────────────────────────────────────
# RSP / SPY ratio change over two consecutive Fridays
def rsp_spy_ratio() -> Dict:
    """
    Download daily 'Close' for RSP & SPY from the previous Friday to LAST_FRI.
    Compute:
      - prev = RSP/SPY ratio on the prior Friday
      - curr = RSP/SPY ratio on LAST_FRI
      - pct_chg = (curr - prev)/prev * 100
    """
    prev_friday = LAST_FRI - dt.timedelta(days=7)
    df = yf.download(
        ["RSP", "SPY"],
        start=str(prev_friday),
        end=str(LAST_FRI + dt.timedelta(days=1)),
        progress=False,
        auto_adjust=False
    )["Close"]

    prev_ratio = float(df.iloc[0]["RSP"] / df.iloc[0]["SPY"])
    curr_ratio = float(df.iloc[-1]["RSP"] / df.iloc[-1]["SPY"])
    pct_chg = round((curr_ratio - prev_ratio) / prev_ratio * 100, 2)

    return {
        "prev": round(prev_ratio, 3),
        "curr": round(curr_ratio, 3),
        "pct_chg": pct_chg
    }


# STEP 6 ────────────────────────────────────────────────────────────
# Build canonical JSON snapshot + optional vector ingest
def build_breadth_lens():
    """
    1. Compute pct_above_ma() → aggregate stats & per-ticker details
    2. Build summary_blob with:
         • meta: {section: "trend", generated_at, source, notes}
         • entities: [one dict for “S&P 500” with aggregate data; Summaries field empty]
         • sector_return: output of sector_weekly()
         • rsp_spy_ratio: output of rsp_spy_ratio()
    3. Persist to:
         data/YYYY-MM-DD/breadth.json
         data/YYYY-MM-DD/details.json
    4. If rag_layer.ingest is available, ingest both blobs into FAISS.
    """
    aggregate, ticker_details = pct_above_ma()

    summary_blob = {
        "meta": {
            "section": "trend",
            "generated_at": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "source": "yfinance",
            "notes": "S&P 500 breadth vs 50/200-day SMA"
        },
        "entities": [
            {
                "ticker": "^GSPC",
                "label": "S&P 500",
                "data": aggregate,
                "summaries": []  # no text for Trend, but field must exist
            }
        ],
        "sector_return": sector_weekly(),
        "rsp_spy_ratio": rsp_spy_ratio()
    }

    # Persist summary and details to disk
    (DATA_DIR / "breadth.json").write_text(json.dumps(summary_blob, indent=2))
    (DATA_DIR / "details.json").write_text(json.dumps(ticker_details, indent=2))
    print(f"✔ Saved breadth & details JSON → {DATA_DIR}")

    # Optional: ingest into FAISS vector store for RAG
    try:
        ingest_section(summary_blob)                  # aggregate doc
        ingest_section({
            "meta": summary_blob["meta"],
            "entities": ticker_details               # per-ticker docs
        })
        print("✔ Ingested into FAISS vector store")
    except Exception as exc:
        print(f"Vector-ingest skipped – {exc}")

    print(f"⏱ Total runtime: {round(time.time() - T0, 2)} seconds")

# STEP 7 ────────────────────────────────────────────────────────────
# Entry-point
if __name__ == "__main__":
    build_breadth_lens()
