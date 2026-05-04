#!/usr/bin/env python3
import sys
import json
import argparse
import pandas as pd

try:
    import yfinance as yf
except ImportError:
    print(json.dumps({"error": "yfinance not installed. Please run: pip install yfinance"}))
    sys.exit(1)

def convert_timestamps(obj):
    """Recursively convert pandas Timestamps to strings and clean NaNs for JSON serialization."""
    if isinstance(obj, dict):
        return {str(k): convert_timestamps(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_timestamps(i) for i in obj]
    elif isinstance(obj, pd.Timestamp):
        return str(obj.date())
    elif pd.isna(obj):
        return None
    return obj

def fetch_short_interest_data(ticker_symbol):
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        
        data = {
            "ticker": ticker_symbol,
            "data_timeliness": "Latest reporting period available from Yahoo Finance",
            "missing_data_note": "Borrow rate and daily short volume are not natively available via yfinance. Do NOT make up missing data, proceed with available metrics.",
            "price_data": {
                "current_price": info.get("currentPrice", info.get("regularMarketPrice")),
                "fiftyDayAverage": info.get("fiftyDayAverage"),
                "twoHundredDayAverage": info.get("twoHundredDayAverage"),
            },
            "short_metrics": {
                "shortPercentOfFloat": info.get("shortPercentOfFloat"),
                "shortRatio": info.get("shortRatio"), # Days to cover
                "sharesShort": info.get("sharesShort"),
                "sharesShortPriorMonth": info.get("sharesShortPriorMonth"),
                "sharesOutstanding": info.get("sharesOutstanding", info.get("impliedSharesOutstanding")),
                "floatShares": info.get("floatShares"),
            },
            "options_data": {
                "put_call_open_interest_ratio": None,
                "implied_volatility_note": "yfinance options chains can be sparse, IV data not reliably aggregated."
            }
        }
        
        # Try to get nearest option chain for put/call open interest ratio
        try:
            expirations = ticker.options
            if expirations:
                nearest_expiry = expirations[0]
                chain = ticker.option_chain(nearest_expiry)
                total_call_oi = chain.calls['openInterest'].sum()
                total_put_oi = chain.puts['openInterest'].sum()
                if total_call_oi > 0:
                    data["options_data"]["put_call_open_interest_ratio"] = float(total_put_oi / total_call_oi)
                    data["options_data"]["nearest_expiration_date"] = nearest_expiry
        except Exception as e:
            data["options_data"]["error"] = f"Could not fetch options data: {str(e)}"
            
        print(json.dumps(convert_timestamps(data), indent=2))
        
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch Short Interest data for LLM agents")
    parser.add_argument("ticker", help="Stock ticker symbol (e.g., GME)")
    args = parser.parse_args()
    
    fetch_short_interest_data(args.ticker)
