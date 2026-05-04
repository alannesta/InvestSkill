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

def fetch_dcf_data(ticker_symbol):
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        
        # 10Y Treasury (Risk-Free Rate)
        try:
            tnx = yf.Ticker("^TNX")
            # Using fast_info to avoid slow/failing info calls on indices
            risk_free_rate = tnx.fast_info.last_price / 100.0
        except Exception:
            risk_free_rate = 0.04  # Fallback to 4% if ^TNX fails
            
        data = {
            "ticker": ticker_symbol,
            "data_timeliness": "Real-time or latest available from Yahoo Finance",
            "current_price": info.get("currentPrice", info.get("regularMarketPrice")),
            "freeCashflow": info.get("freeCashflow"),
            "totalRevenue": info.get("totalRevenue"),
            "sharesOutstanding": info.get("sharesOutstanding", info.get("impliedSharesOutstanding")),
            "totalDebt": info.get("totalDebt"),
            "totalCash": info.get("totalCash"),
            "beta": info.get("beta", 1.0),
            "risk_free_rate": risk_free_rate,
            "wacc_components": {},
            "historical_revenue": {}
        }
        
        # Calculate Net Debt if both are present
        if data["totalDebt"] is not None and data["totalCash"] is not None:
            data["netDebt"] = data["totalDebt"] - data["totalCash"]
        
        # Extract from financials (Income Statement)
        inc = ticker.income_stmt
        if inc is not None and not inc.empty:
            # We want the most recent available annual column
            latest_date = inc.columns[0]
            data["latest_fiscal_date"] = str(latest_date.date()) if isinstance(latest_date, pd.Timestamp) else str(latest_date)
            
            tax_provision = inc.loc["Tax Provision", latest_date] if "Tax Provision" in inc.index else 0
            pretax_income = inc.loc["Pretax Income", latest_date] if "Pretax Income" in inc.index else 1
            
            tax_provision = tax_provision if not pd.isna(tax_provision) else 0
            pretax_income = pretax_income if not pd.isna(pretax_income) else 1
            
            tax_rate = tax_provision / pretax_income if pretax_income > 0 else 0.21
            data["wacc_components"]["effective_tax_rate"] = float(tax_rate)
            
            interest_expense = inc.loc["Interest Expense", latest_date] if "Interest Expense" in inc.index else 0
            interest_expense = interest_expense if not pd.isna(interest_expense) else 0
            data["wacc_components"]["interest_expense"] = float(abs(interest_expense))
            
            # Historical revenues for CAGR (Up to 4 years from yfinance)
            if "Total Revenue" in inc.index:
                revs = inc.loc["Total Revenue"].dropna()
                data["historical_revenue"] = {str(d.date()) if hasattr(d, 'date') else str(d): float(v) for d, v in revs.items()}
                
        # Clean up any potential numpy types
        def sanitize_floats(obj):
            if isinstance(obj, dict):
                return {k: sanitize_floats(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [sanitize_floats(i) for i in obj]
            elif pd.isna(obj):
                return None
            return obj

        print(json.dumps(sanitize_floats(data), indent=2))
        
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch DCF data for LLM agents")
    parser.add_argument("ticker", help="Stock ticker symbol (e.g., AAPL)")
    args = parser.parse_args()
    
    fetch_dcf_data(args.ticker)
