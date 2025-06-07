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
