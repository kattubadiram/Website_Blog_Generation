"""
trend.py  ·  Morning Market Primer
----------------------------------
Computes S&P 500 breadth (50- & 200-day SMA %),
sector ETF moves, and the RSP/SPY ratio.

Outputs:
  • breadth_log.jsonl              (append-only snapshot)
  • breadth_latest.json            (latest aggregate)
  • breadth_details_latest.json    (per-ticker metrics)
"""
import datetime as dt
import json
import pathlib
import time
from typing import Dict, List, Tuple

import pandas as pd
import yfinance as yf
import pytz

from sp500 import sp500_tickers
try:
    from rag_layer.ingest import ingest_section
except ImportError:
    ingest_section = lambda *_a, **_kw: None

T0 = time.time()

# ─── Constants ───────────────────────────────────────
EST       = pytz.timezone("America/New_York")
TODAY     = dt.datetime.now(dt.timezone.utc).astimezone(EST).date()
RUN_DATE  = TODAY.isoformat()

SECTOR_TICKERS = [
    "XLB", "XLC", "XLE", "XLF", "XLI",
    "XLK", "XLP", "XLU", "XLV", "XLRE", "XLY"
]

# ─── File targets ─────────────────────────────────────
LOG_FILE_BREADTH = pathlib.Path("breadth_log.jsonl")
LATEST_BREADTH   = pathlib.Path("breadth_latest.json")
LATEST_DETAILS   = pathlib.Path("breadth_details_latest.json")

# ─── Date anchors ─────────────────────────────────────
def _last_week_bounds(today: dt.date) -> Tuple[dt.date, dt.date]:
    this_monday = today - dt.timedelta(days=today.weekday())
    last_monday = this_monday - dt.timedelta(days=7)
    last_friday = last_monday + dt.timedelta(days=4)
    return last_monday, last_friday

LAST_MON, LAST_FRI = _last_week_bounds(TODAY)

# ─── SMA Breadth Calculation ──────────────────────────
def pct_above_ma() -> Tuple[Dict, List[Dict]]:
    print("▶ Computing SMA breadth for all S&P 500 constituents …")
    above_50 = above_200 = valid = 0
    details: List[Dict] = []

    for idx, symbol in enumerate(sp500_tickers, 1):
        try:
            hist = yf.Ticker(symbol).history(period="1y", auto_adjust=False)
            time.sleep(0.3)

            closes = hist["Close"]
            if len(closes) < 200:
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
                "summaries": []
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

# ─── Sector Returns ───────────────────────────────────
def sector_weekly() -> List[Dict]:
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

# ─── RSP/SPY Ratio ────────────────────────────────────
def rsp_spy_ratio() -> Dict:
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

# ─── Core snapshot builder ─────────────────────────────
def build_breadth_lens():
    aggregate, ticker_details = pct_above_ma()

    summary_blob = {
        "meta": {
            "section": "trend",
            "generated_at": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "run_date": RUN_DATE,
            "source": "yfinance",
            "notes": "S&P 500 breadth vs 50/200-day SMA"
        },
        "entities": [
            {
                "ticker": "^GSPC",
                "label": "S&P 500",
                "data": aggregate,
                "summaries": []
            }
        ],
        "sector_return": sector_weekly(),
        "rsp_spy_ratio": rsp_spy_ratio()
    }

    # Save to files
    with LOG_FILE_BREADTH.open("a") as f:
        f.write(json.dumps(summary_blob) + "\n")
    LATEST_BREADTH.write_text(json.dumps(summary_blob, indent=2))
    LATEST_DETAILS.write_text(json.dumps(ticker_details, indent=2))
    print("✔ Saved breadth_log.jsonl, breadth_latest.json, and breadth_details_latest.json")

    # Optional: Ingest into FAISS
    try:
        ingest_section(summary_blob)
        ingest_section({
            "meta": summary_blob["meta"],
            "entities": ticker_details
        })
        print("✔ Ingested into FAISS vector store")
    except Exception as exc:
        print(f"Vector-ingest skipped – {exc}")

    print(f"⏱ Total runtime: {round(time.time() - T0, 2)} seconds")

# ─── Entrypoint ───────────────────────────────────────
if __name__ == "__main__":
    build_breadth_lens()
