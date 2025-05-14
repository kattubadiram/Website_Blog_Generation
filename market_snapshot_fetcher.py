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
        summary_dict = {
            "timestamp": ts,
            "headline": "",
            "indices": "",
            "bonds": "",
            "currencies": "",
            "commodities": "",
            "etfs": "",
            "stocks": "",
            "tech_focus": "",
            "global_insights": "",
            "analyst_angle": "",
            "sector_spotlight": "",
            "risks_and_opportunities": ""
        }

        def format_category(category_data, label):
            lines = []
            for symbol, data in category_data.items():
                if isinstance(data, dict):
                    price = data.get("price", "N/A")
                    pct = data.get("percent_change", "N/A")
                    lines.append(f"{symbol}: {price} ({pct}%)")
            return f"{label}:\n" + "\n".join(lines) if lines else f"{label}: No data available."

        summary_dict["headline"] = (
            "Markets showed mixed momentum today with tech leading gains and global uncertainties keeping investors alert. "
            "Major indices reflected optimism, while commodities and currencies moved in response to broader geopolitical cues."
        )

        summary_dict["indices"] = format_category(snapshot.get("indices", {}), "Major Indices")
        summary_dict["bonds"] = format_category(snapshot.get("bonds", {}), "Bond Yields")
        summary_dict["currencies"] = format_category(snapshot.get("currencies", {}), "Currency Exchange Rates")
        summary_dict["commodities"] = format_category(snapshot.get("commodities", {}), "Commodities")
        summary_dict["etfs"] = format_category(snapshot.get("etfs", {}), "Sector ETFs")
        summary_dict["stocks"] = format_category(snapshot.get("stocks", {}), "Top Movers")
        summary_dict["tech_focus"] = format_category(snapshot.get("tech_focus", {}), "Tech & AI Stocks")

        summary_dict["global_insights"] = (
            "Asian markets closed mixed while European indices struggled to gain ground. The global macro landscape, "
            "influenced by central bank policy, oil supply shifts, and geopolitical tension, continues to affect sentiment."
        )

        summary_dict["analyst_angle"] = (
            "Financial analysts are split on short-term direction. While some highlight strong consumer data and robust tech earnings, "
            "others caution against overheated valuations and rising treasury yields."
        )

        summary_dict["sector_spotlight"] = (
            "Technology remained the star sector today, with AI-related stocks showing resilience. Energy also gained as oil prices edged higher, "
            "while Healthcare saw select inflows amid earnings announcements."
        )

        summary_dict["risks_and_opportunities"] = (
            "Investors are eyeing inflation reports, interest rate signals, and global commodity supply issues. Risks include tightening liquidity, "
            "while opportunities remain in innovation-driven sectors and select undervalued ETFs."
        )

        return summary_dict

    except Exception as e:
        return {"error": f"Summary generation failed: {e}"}

if __name__ == "__main__":
    snapshot = get_market_snapshot()
    append_snapshot_to_log(snapshot)
    summary = summarize_market_snapshot(snapshot)
    print("\nMarket Summary (Structured):\n")
    for key, value in summary.items():
        if key != "timestamp":
            print(f"\n=== {key.upper()} ===\n{value}")
