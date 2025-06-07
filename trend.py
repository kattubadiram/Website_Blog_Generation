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
