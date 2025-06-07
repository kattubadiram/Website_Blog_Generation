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
TODAY      = dt.date.today()
DATA_DIR   = pathlib.Path("data") / TODAY.isoformat()
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

SYMBOLS = {**INDICES, **COMMODITIES}           # merged dict

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
        "No deep-learning backend detected.  Install CPU PyTorch:\n"
        "    pip install torch --index-url https://download.pytorch.org/whl/cpu torch"
    )

MODEL_NAME = "sshleifer/distilbart-cnn-12-6"              # ≈480 MB

summariser: Pipeline = pipeline(
    "summarization",
    model=MODEL_NAME,
    tokenizer=MODEL_NAME,
    framework="pt",
    truncation=True,
    token=None                                            # anonymous → avoids 401
)

# ────────────────────────────────────────────────────────────────
# STEP 3 · Pull latest quotes (one batched yfinance call)
# ────────────────────────────────────────────────────────────────
def fetch_quotes(symbol_map: Dict[str, str]) -> Dict[str, Dict]:
    """
    Returns a dict mapping each name → {last_close, prev_close, pct_change}.
    Uses a 5-day window to grab yesterday’s and today’s closes.
    """
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
            out[name] = {
                "symbol": sym,
                "last_close": None,
                "prev_close": None,
                "pct_change": None
            }
    return out

# ────────────────────────────────────────────────────────────────
# STEP 4 · Fetch up to 10 RSS headlines for a symbol
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
    out = []
    for e in parsed.entries[:10]:
        out.append({
            "title":     e.get("title", "").strip(),
            "summary":   e.get("summary", "").strip(),
            "link":      e.get("link", "").strip(),
            "published": e.get("published", "").strip()
        })
    return out

# ────────────────────────────────────────────────────────────────
# STEP 5 · Condense each headline into one line (FULL-ARTICLE MODE)
# ────────────────────────────────────────────────────────────────

def summarise_entries(entries: List[Dict]) -> List[str]:
    lines: List[str] = []
    for e in entries:
        # 5.1  try full-article extraction
        art_text = extract_article_text(e["link"])
        src_text = art_text if art_text else e["title"] + ". " + e.get("summary", "")
        # 5.2  summarise
        line = summariser(
            src_text,
            max_length=60,
            min_length=15,
            do_sample=False
        )[0]["summary_text"]
        lines.append(line.strip())
    return lines

# ────────────────────────────────────────────────────────────────
# STEP 6 · Build canonical JSON blob
# ────────────────────────────────────────────────────────────────
def build_pulse_blob(pause: float = 1.0) -> Dict:
    """
    1) Fetch latest quotes for all indices and commodities.
    2) For each symbol, fetch up to 10 RSS headlines and summarise each.
    3) Construct the JSON in our agreed schema.
    """
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
            "ticker":    sym,
            "label":     name,
            "data":      quote_data.get(name, {}),
            "summaries": summaries
        })

    return {
        "meta": {
            "section": "pulse",
            "generated_at": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
            "source": "yfinance + yahoo_rss"
        },
        "entities": entities
    }

# ────────────────────────────────────────────────────────────────
# STEP 7 · Persist + optional vector-ingest
# ────────────────────────────────────────────────────────────────
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

    print(f"⏱ Total runtime: {round(time.time() - T0, 2)} seconds")
    
if __name__ == "__main__":
    main()
