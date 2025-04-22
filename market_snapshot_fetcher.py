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


def summarize_market_snapshot(snapshot):
    """
    Generates a detailed textual summary of the market snapshot using all major categories.
    """
    try:
        ts = snapshot['timestamp']
        s = [f"Market Snapshot Summary as of {ts}:"]

        # Summarize indices
        if snapshot.get("indices"):
            s.append("\nMajor Indices:")
            for k, v in snapshot["indices"].items():
                if isinstance(v, dict):
                    s.append(f"- {k}: {v.get('price', 'N/A')} ({v.get('percent_change', 'N/A')}%)")

        # Summarize bonds
        if snapshot.get("bonds"):
            s.append("\nBond Yields:")
            for k, v in snapshot["bonds"].items():
                if isinstance(v, dict):
                    s.append(f"- {k}: {v.get('price', 'N/A')} ({v.get('percent_change', 'N/A')}%)")

        # Summarize currencies
        if snapshot.get("currencies"):
            s.append("\nCurrency Rates:")
            for k, v in snapshot["currencies"].items():
                if isinstance(v, dict):
                    s.append(f"- {k}: {v.get('price', 'N/A')} ({v.get('percent_change', 'N/A')}%)")

        # Summarize commodities
        if snapshot.get("commodities"):
            s.append("\nCommodities:")
            for k, v in snapshot["commodities"].items():
                if isinstance(v, dict):
                    s.append(f"- {k}: {v.get('price', 'N/A')} ({v.get('percent_change', 'N/A')}%)")

        # Summarize key ETFs
        if snapshot.get("etfs"):
            s.append("\nSector ETFs:")
            for k, v in snapshot["etfs"].items():
                if isinstance(v, dict):
                    s.append(f"- {k}: {v.get('price', 'N/A')} ({v.get('percent_change', 'N/A')}%)")

        # Summarize select stocks (top 5 movers by % change)
        if snapshot.get("stocks"):
            s.append("\nTop Movers (Selected Stocks):")
            sorted_stocks = sorted(
                [(k, v) for k, v in snapshot["stocks"].items() if isinstance(v, dict) and v.get("percent_change") is not None],
                key=lambda x: abs(x[1]["percent_change"]),
                reverse=True
            )[:5]
            for k, v in sorted_stocks:
                s.append(f"- {k}: {v.get('price', 'N/A')} ({v.get('percent_change', 'N/A')}%)")

        return "\n".join(s)
    except Exception as e:
        return f"Summary generation failed: {e}"


if __name__ == "__main__":
    snapshot = get_market_snapshot()
    append_snapshot_to_log(snapshot)
    summary = summarize_market_snapshot(snapshot)
    print("\n📋 Market Summary:\n" + summary)
