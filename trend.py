import datetime as dt
import json
import pathlib
import time
import os
import base64
from typing import Dict, List, Tuple

import pandas as pd
import yfinance as yf
import pytz                       # ← NEW
from sp500 import sp500_tickers

# Optional RAG ingestion
try:
    from rag_layer.ingest import ingest_section
except ImportError:
    ingest_section = lambda *_a, **_kw: None

# ── Timezones & Dates ───────────────────────────
EST   = pytz.timezone("America/New_York")
TODAY = dt.datetime.now(dt.timezone.utc).astimezone(EST).date()
DATA_DIR = pathlib.Path("data") / TODAY.isoformat()
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------
# Everything below this line remains your original logic
# ---------------------------------------------------------------------
# 1.2 · Helpers --------------------------------------------------------
def _last_week_bounds(d: dt.date) -> Tuple[dt.date, dt.date]:
    last_monday = d - dt.timedelta(days=d.weekday() + 7)
    last_friday = last_monday + dt.timedelta(days=4)
    return last_monday, last_friday

LAST_MON, LAST_FRI = _last_week_bounds(TODAY)

SECTOR_TICKERS = [
    "XLB", "XLC", "XLE", "XLF", "XLI",
    "XLK", "XLP", "XLU", "XLV", "XLRE", "XLY"
]

# STEP 3: % above MA
# ... (rest of pct_above_ma, sector_weekly, rsp_spy_ratio unchanged) ...

def pct_above_ma() -> Tuple[Dict, List[Dict]]:
    # your existing implementation
    ...

def sector_weekly() -> List[Dict]:
    # your existing implementation
    ...

def rsp_spy_ratio() -> Dict:
    # your existing implementation
    ...

# STEP 6: Build breadth lens

def build_breadth_lens():
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
                "summaries": []
            }
        ],
        "sector_return": sector_weekly(),
        "rsp_spy_ratio": rsp_spy_ratio()
    }

    # Persist summary and details to disk
    breadth_file = DATA_DIR / "breadth.json"
    details_file = DATA_DIR / "details.json"
    breadth_file.write_text(json.dumps(summary_blob, indent=2))
    details_file.write_text(json.dumps(ticker_details, indent=2))
    print(f"✔ Saved breadth & details JSON → {DATA_DIR}")

    # Optional: ingest into FAISS vector store for RAG
    try:
        ingest_section(summary_blob)
        ingest_section({"meta": summary_blob["meta"], "entities": ticker_details})
        print("✔ Ingested into FAISS vector store")
    except Exception as exc:
        print(f"Vector-ingest skipped – {exc}")

    # Persist files to GitHub
    push_to_github(breadth_file)
    push_to_github(details_file)

    print(f"⏱ Total runtime: {round(time.time() - T0, 2)} seconds")

# ───────────────────────────────────────────────────────────────
# GitHub persistence helper
# ───────────────────────────────────────────────────────────────
def push_to_github(file_path: pathlib.Path):
    token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPO")  # format: 'owner/repo'
    branch = os.getenv("GITHUB_BRANCH", "main")
    if not token or not repo:
        print("✔ GitHub persistence skipped: set GITHUB_TOKEN and GITHUB_REPO env vars.")
        return

    # Read and encode file
    with open(file_path, "rb") as f:
        content_b64 = base64.b64encode(f.read()).decode()

    # Construct API URL
    api_path = file_path.as_posix()  # e.g. 'data/2025-06-09/breadth.json'
    url = f"https://api.github.com/repos/{repo}/contents/{api_path}"
    headers = {"Authorization": f"token {token}"}

    # Check if file exists to include sha
    resp = requests.get(url, headers=headers)
    sha = resp.json().get("sha") if resp.status_code == 200 else None

    payload = {
        "message": f"Add trend data for {TODAY.isoformat()}",
        "content": content_b64,
        "branch": branch
    }
    if sha:
        payload["sha"] = sha

    put_resp = requests.put(url, headers=headers, json=payload)
    if put_resp.status_code in (200, 201):
        print(f"✔ Pushed to GitHub: {repo}/{api_path}@{branch}")
    else:
        print(f"✖ GitHub push failed: {put_resp.status_code} - {put_resp.text}")

# STEP 7: Entry-point

if __name__ == "__main__":
    build_breadth_lens()
