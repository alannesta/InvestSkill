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
    """Recursively convert pandas Timestamps to strings for JSON serialization."""
    if isinstance(obj, dict):
        return {str(k): convert_timestamps(v) for k, v in obj.items()}
    elif isinstance(obj, pd.Timestamp):
        return str(obj.date())
    return obj

def fetch_data(ticker_symbol):
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        
        # 1. Extract core metrics for Fundamental, DCF, and Short Interest
        keys_of_interest = [
            'shortRatio', 'shortPercentOfFloat', 'sharesShort', 
            'sharesOutstanding', 'impliedSharesOutstanding', 'floatShares',
            'beta', 'trailingPE', 'forwardPE', 'priceToBook', 'enterpriseToEbitda',
            'returnOnEquity', 'returnOnAssets', 'grossMargins', 'operatingMargins', 'profitMargins',
            'totalDebt', 'totalCash', 'freeCashflow', 'operatingCashflow',
            'fiftyDayAverage', 'twoHundredDayAverage'
        ]
        
        data = {
            "ticker": ticker_symbol,
            "metrics": {k: info.get(k) for k in keys_of_interest if k in info},
            "financials": {},
            "options": {}
        }
        
        # 2. Fetch Financial Statements (Income, Balance Sheet, Cash Flow)
        if ticker.income_stmt is not None and not ticker.income_stmt.empty:
            data["financials"]["income_statement"] = ticker.income_stmt.fillna(0).to_dict()
            
        if ticker.balance_sheet is not None and not ticker.balance_sheet.empty:
            data["financials"]["balance_sheet"] = ticker.balance_sheet.fillna(0).to_dict()
            
        if ticker.cashflow is not None and not ticker.cashflow.empty:
            data["financials"]["cashflow"] = ticker.cashflow.fillna(0).to_dict()
            
        # Clean up timestamps
        data["financials"] = convert_timestamps(data["financials"])
        
        # 3. Basic Options Data (Implied Volatility Summary)
        try:
            opts = ticker.options
            if opts:
                closest_expiry = opts[0]
                chain = ticker.option_chain(closest_expiry)
                # Just get aggregate metrics so we don't blow up the LLM token context
                data["options"]["closest_expiry"] = closest_expiry
                data["options"]["calls_volume"] = float(chain.calls['volume'].sum())
                data["options"]["puts_volume"] = float(chain.puts['volume'].sum())
                data["options"]["avg_call_iv"] = float(chain.calls['impliedVolatility'].mean())
                data["options"]["avg_put_iv"] = float(chain.puts['impliedVolatility'].mean())
        except Exception as e:
            data["options"]["error"] = str(e)
            
        print(json.dumps(data, indent=2))
        
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch financial data for LLM agents")
    parser.add_argument("ticker", help="Stock ticker symbol (e.g., AAPL)")
    args = parser.parse_args()
    
    fetch_data(args.ticker)
