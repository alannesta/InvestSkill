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

def fetch_fundamental_data(ticker_symbol):
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        
        # Base dictionary
        data = {
            "ticker": ticker_symbol,
            "data_timeliness": "Latest available from Yahoo Finance (up to 4 years of annual statements)",
            "current_price": info.get("currentPrice", info.get("regularMarketPrice")),
            "multiples": {
                "trailingPE": info.get("trailingPE"),
                "forwardPE": info.get("forwardPE"),
                "priceToBook": info.get("priceToBook"),
                "priceToSales": info.get("priceToSalesTrailing12Months"),
                "enterpriseToEbitda": info.get("enterpriseToEbitda"),
                "pegRatio": info.get("pegRatio")
            },
            "profitability": {
                "grossMargins": info.get("grossMargins"),
                "operatingMargins": info.get("operatingMargins"),
                "profitMargins": info.get("profitMargins"),
                "returnOnEquity": info.get("returnOnEquity"),
                "returnOnAssets": info.get("returnOnAssets")
            },
            "growth": {
                "revenueGrowth": info.get("revenueGrowth"),
                "earningsGrowth": info.get("earningsGrowth")
            },
            "historical_financials": {}
        }
        
        # Helper to extract a row series to dict indexed by date string
        def extract_series(df, row_name):
            if df is not None and not df.empty and row_name in df.index:
                row = df.loc[row_name].dropna()
                return {str(d.date()) if hasattr(d, 'date') else str(d): float(v) for d, v in row.items()}
            return {}

        inc = ticker.income_stmt
        bal = ticker.balance_sheet
        cf = ticker.cashflow
        
        data["historical_financials"] = {
            "income_statement": {
                "Total Revenue": extract_series(inc, "Total Revenue"),
                "Net Income": extract_series(inc, "Net Income"),
                "Basic EPS": extract_series(inc, "Basic EPS")
            },
            "balance_sheet": {
                "Total Assets": extract_series(bal, "Total Assets"),
                "Total Liabilities Net Minority Interest": extract_series(bal, "Total Liabilities Net Minority Interest"),
                "Total Equity Gross Minority Interest": extract_series(bal, "Total Equity Gross Minority Interest"),
                "Total Debt": extract_series(bal, "Total Debt")
            },
            "cash_flow": {
                "Operating Cash Flow": extract_series(cf, "Operating Cash Flow"),
                "Capital Expenditure": extract_series(cf, "Capital Expenditure"),
                "Free Cash Flow": extract_series(cf, "Free Cash Flow"),
                "Cash Dividends Paid": extract_series(cf, "Cash Dividends Paid"),
                "Repurchase Of Capital Stock": extract_series(cf, "Repurchase Of Capital Stock"),
                "Repayment Of Debt": extract_series(cf, "Repayment Of Debt")
            }
        }
        
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
    parser = argparse.ArgumentParser(description="Fetch Fundamental Analysis data for LLM agents")
    parser.add_argument("ticker", help="Stock ticker symbol (e.g., AAPL)")
    args = parser.parse_args()
    
    fetch_fundamental_data(args.ticker)
