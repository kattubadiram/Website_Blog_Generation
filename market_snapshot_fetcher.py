import yfinance as yf
import datetime
import json


def get_market_snapshot():
    """
    Fetches real-time market indicators from Yahoo Finance across multiple categories.
    Returns a structured dictionary with 80+ indicators.
    """
    snapshot = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "indices": {},
        "bonds": {},
        "currencies": {},
        "commodities": {},
        "etfs": {},
        "stocks": {},
    }

    # Define tickers for each category
    tickers = {
        "indices": ["^GSPC", "^IXIC", "^DJI", "^RUT", "^VIX", "^FTSE", "^GDAXI", "^N225", "^HSI", "000001.SS"],
        "bonds": ["^TNX", "^IRX", "^TYX"],
        "currencies": ["DX-Y.NYB", "EURUSD=X", "JPY=X", "GBPUSD=X"],
        "commodities": ["GC=F", "SI=F", "CL=F", "BZ=F", "NG=F", "HG=F"],
        "etfs": ["SPY", "QQQ", "IWM", "XLF", "XLV", "XLE", "XLK", "ARKK"],
        "stocks": [
            # Tech
            "AAPL", "MSFT", "NVDA", "ORCL", "INTC",
            # Financials
            "JPM", "GS", "BAC", "AXP", "BLK",
            # Energy
            "XOM", "CVX", "SLB", "FANG",
            # Industrials
            "GE", "CAT", "BA", "DE",
            # Consumer Discretionary
            "TSLA", "HD", "NKE", "MCD", "SBUX",
            # Healthcare
            "JNJ", "PFE", "UNH", "MRK", "CVS",
            # Staples, Utilities, Real Estate
            "NEE", "PLD", "PG", "KO"
        ]
    }

    for category, symbols in tickers.items():
        for symbol in symbols:
            try:
                data = yf.Ticker(symbol).info
                snapshot[category][symbol] = {
                    "price": data.get("regularMarketPrice"),
                    "change": data.get("regularMarketChange"),
                    "percent_change": data.get("regularMarketChangePercent"),
                    "market_cap": data.get("marketCap")
                }
            except Exception as e:
                snapshot[category][symbol] = {"error": str(e)}

    return snapshot


def append_snapshot_to_log(snapshot, filepath="market_snapshot_log.jsonl"):
    """
    Appends a single market snapshot JSON object to a log file (one line per snapshot).
    """
    try:
        with open(filepath, "a") as f:
            f.write(json.dumps(snapshot) + "\n")
        print(f"\U0001F4E6 Appended market snapshot to {filepath}")
    except IOError as e:
        print(f"❌ Failed to write snapshot log: {e}")


if __name__ == "__main__":
    snapshot = get_market_snapshot()
    append_snapshot_to_log(snapshot)
