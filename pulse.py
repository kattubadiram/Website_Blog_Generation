"""
pulse.py  ·  Morning Market Primer  – Section 2
------------------------------------------------
Captures “market pulse” stats: indices, bonds, vol, FX,
commodities, crypto, and macro calendar.

Output
  • data/YYYY-MM-DD/pulse.json
"""
import datetime as dt
import json
import pathlib
import time
from typing import Dict

import pandas as pd
import yfinance as yf
import pytz                       # ← NEW
T0 = time.time()

try:
    from rag_layer.ingest import ingest_section
except ImportError:
    ingest_section = lambda *_a, **_kw: None

# ── New EST-aware folder ───────────────────────────
EST   = pytz.timezone("America/New_York")
TODAY = dt.datetime.now(dt.timezone.utc).astimezone(EST).date()
DATA_DIR = pathlib.Path("data") / TODAY.isoformat()
DATA_DIR.mkdir(parents=True, exist_ok=True)

# (rest of your original pulse-gathering logic remains unchanged)
