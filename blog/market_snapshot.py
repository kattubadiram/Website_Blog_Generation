import yfinance as yf
import datetime
import json

def get_market_snapshot():
    snapshot = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "indices": {},
        "bonds": {},
        "currencies": {},
        "commodities": {},
        "etfs": {},
        "stocks": {},
        "tech_focus": {},
    }

    tickers = {
        "indices": ["^GSPC", "^IXIC", "^DJI", "^RUT", "^VIX", "^FTSE", "^GDAXI", "^N225", "^HSI", "000001.SS"],
        "bonds": ["^TNX", "^IRX", "^TYX"],
        "currencies": ["DX-Y.NYB", "EURUSD=X", "JPY=X", "GBPUSD=X"],
        "commodities": ["GC=F", "SI=F", "CL=F", "BZ=F", "NG=F", "HG=F"],
        "etfs": ["SPY", "QQQ", "IWM", "XLF", "XLV", "XLE", "XLK", "ARKK"],
        "stocks": [
            "AAPL", "MSFT", "NVDA", "ORCL", "INTC", "JPM", "GS", "BAC", "AXP", "BLK",
            "XOM", "CVX", "SLB", "FANG", "GE", "CAT", "BA", "DE",
            "TSLA", "HD", "NKE", "MCD", "SBUX", "JNJ", "PFE", "UNH", "MRK", "CVS",
            "NEE", "PLD", "PG", "KO"
        ],
        "tech_focus": [
            "NVDA", "AMD", "TSLA", "AAPL", "MSFT", "GOOGL", "AMZN", "META",
            "ASML", "INTC", "TSM", "CRM", "SNOW", "PLTR", "ZM", "ROKU",
            "DOCU", "ABNB", "UBER", "AI"
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
    try:
        with open(filepath, "a") as f:
            f.write(json.dumps(snapshot) + "\n")
        print(f"Appended market snapshot to {filepath}")
    except IOError as e:
        print(f"Failed to write snapshot log: {e}")

def summarize_market_snapshot(snapshot):
    try:
        ts = snapshot['timestamp']
        s = [f"Market Snapshot Summary as of {ts}:"]

        if snapshot.get("indices"):
            s.append("\nMajor Indices:")
            for k, v in snapshot["indices"].items():
                if isinstance(v, dict):
                    s.append(f"- {k}: {v.get('price', 'N/A')} ({v.get('percent_change', 'N/A')}%)")

        if snapshot.get("bonds"):
            s.append("\nBond Yields:")
            for k, v in snapshot["bonds"].items():
                if isinstance(v, dict):
                    s.append(f"- {k}: {v.get('price', 'N/A')} ({v.get('percent_change', 'N/A')}%)")

        if snapshot.get("currencies"):
            s.append("\nCurrency Rates:")
            for k, v in snapshot["currencies"].items():
                if isinstance(v, dict):
                    s.append(f"- {k}: {v.get('price', 'N/A')} ({v.get('percent_change', 'N/A')}%)")

        if snapshot.get("commodities"):
            s.append("\nCommodities:")
            for k, v in snapshot["commodities"].items():
                if isinstance(v, dict):
                    s.append(f"- {k}: {v.get('price', 'N/A')} ({v.get('percent_change', 'N/A')}%)")

        if snapshot.get("etfs"):
            s.append("\nSector ETFs:")
            for k, v in snapshot["etfs"].items():
                if isinstance(v, dict):
                    s.append(f"- {k}: {v.get('price', 'N/A')} ({v.get('percent_change', 'N/A')}%)")

        if snapshot.get("stocks"):
            s.append("\nTop Movers (Selected Stocks):")
            sorted_stocks = sorted(
                [(k, v) for k, v in snapshot["stocks"].items() if isinstance(v, dict) and v.get("percent_change") is not None],
                key=lambda x: abs(x[1]["percent_change"]),
                reverse=True
            )[:5]
            for k, v in sorted_stocks:
                s.append(f"- {k}: {v.get('price', 'N/A')} ({v.get('percent_change', 'N/A')}%)")

        if snapshot.get("tech_focus"):
            s.append("\nScience & Tech Focused Stocks:")
            sorted_tech = sorted(
                [(k, v) for k, v in snapshot["tech_focus"].items() if isinstance(v, dict) and v.get("percent_change") is not None],
                key=lambda x: abs(x[1]["percent_change"]),
                reverse=True
            )[:5]
            for k, v in sorted_tech:
                s.append(f"- {k}: {v.get('price', 'N/A')} ({v.get('percent_change', 'N/A')}%)")

        return "\n".join(s)
    except Exception as e:
        return f"Summary generation failed: {e}"

if __name__ == "__main__":
    snapshot = get_market_snapshot()
    append_snapshot_to_log(snapshot)
    summary = summarize_market_snapshot(snapshot)
    print("\nMarket Summary:\n" + summary)
