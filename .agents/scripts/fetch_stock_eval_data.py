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

def fetch_stock_eval_data(ticker_symbol):
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        
        # Risk-Free Rate for WACC
        try:
            tnx = yf.Ticker("^TNX")
            risk_free_rate = tnx.fast_info.last_price / 100.0
        except Exception:
            risk_free_rate = 0.04  # Fallback
            
        data = {
            "ticker": ticker_symbol,
            "data_timeliness": "Latest available from Yahoo Finance",
            "current_price": info.get("currentPrice", info.get("regularMarketPrice")),
            "risk_free_rate": risk_free_rate,
            "beta": info.get("beta", 1.0),
            
            # Valuation Metrics
            "valuation_metrics": {
                "trailingPE": info.get("trailingPE"),
                "forwardPE": info.get("forwardPE"),
                "pegRatio": info.get("pegRatio"),
                "priceToBook": info.get("priceToBook"),
                "priceToSales": info.get("priceToSalesTrailing12Months"),
                "enterpriseToEbitda": info.get("enterpriseToEbitda"),
                "enterpriseValue": info.get("enterpriseValue"),
                "dividendYield": info.get("dividendYield"),
                "payoutRatio": info.get("payoutRatio")
            },
            
            # Key Ratios
            "key_ratios": {
                "returnOnEquity": info.get("returnOnEquity"),
                "returnOnAssets": info.get("returnOnAssets"),
                "grossMargins": info.get("grossMargins"),
                "operatingMargins": info.get("operatingMargins"),
                "profitMargins": info.get("profitMargins"),
                "currentRatio": info.get("currentRatio"),
                "quickRatio": info.get("quickRatio"),
                "debtToEquity": info.get("debtToEquity")
            },
            
            # Base info for FCF and ROIC
            "financial_health": {
                "freeCashflow": info.get("freeCashflow"),
                "operatingCashflow": info.get("operatingCashflow"),
                "totalCash": info.get("totalCash"),
                "totalDebt": info.get("totalDebt"),
                "sharesOutstanding": info.get("sharesOutstanding")
            },
            "historical_financials": {}
        }

        def extract_series(df, row_name):
            if df is not None and not df.empty and row_name in df.index:
                row = df.loc[row_name].dropna()
                return {str(d.date()) if hasattr(d, 'date') else str(d): float(v) for d, v in row.items()}
            return {}

        # Fetch up to 4 years for Piotroski F-Score calculations
        inc = ticker.income_stmt
        bal = ticker.balance_sheet
        cf = ticker.cashflow
        
        data["historical_financials"] = {
            "income_statement": {
                "Total Revenue": extract_series(inc, "Total Revenue"),
                "Gross Profit": extract_series(inc, "Gross Profit"),
                "EBIT": extract_series(inc, "EBIT"),
                "Net Income": extract_series(inc, "Net Income"),
                "Pretax Income": extract_series(inc, "Pretax Income"),
                "Tax Provision": extract_series(inc, "Tax Provision"),
                "Interest Expense": extract_series(inc, "Interest Expense")
            },
            "balance_sheet": {
                "Total Assets": extract_series(bal, "Total Assets"),
                "Current Assets": extract_series(bal, "Current Assets"),
                "Current Liabilities": extract_series(bal, "Current Liabilities"),
                "Total Liabilities Net Minority Interest": extract_series(bal, "Total Liabilities Net Minority Interest"),
                "Total Equity Gross Minority Interest": extract_series(bal, "Total Equity Gross Minority Interest"),
                "Total Debt": extract_series(bal, "Total Debt"),
                "Long Term Debt": extract_series(bal, "Long Term Debt")
            },
            "cash_flow": {
                "Operating Cash Flow": extract_series(cf, "Operating Cash Flow"),
                "Capital Expenditure": extract_series(cf, "Capital Expenditure"),
                "Free Cash Flow": extract_series(cf, "Free Cash Flow")
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
    parser = argparse.ArgumentParser(description="Fetch Stock Evaluation data for LLM agents")
    parser.add_argument("ticker", help="Stock ticker symbol (e.g., AAPL)")
    args = parser.parse_args()
    
    fetch_stock_eval_data(args.ticker)
