#!/usr/bin/env python3
import sys
import json
import argparse
import pandas as pd
import numpy as np

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
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    return obj

def calculate_cagr(start_val, end_val, periods):
    if periods <= 0 or start_val <= 0:
        return None
    return (end_val / start_val) ** (1 / periods) - 1

def fetch_dividend_data(ticker_symbol):
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        
        data = {
            "ticker": ticker_symbol,
            "data_timeliness": "Latest available from Yahoo Finance",
            "price_and_yield": {
                "current_price": info.get("currentPrice", info.get("regularMarketPrice")),
                "dividendYield": info.get("dividendYield"),
                "trailingAnnualDividendYield": info.get("trailingAnnualDividendYield"),
                "trailingAnnualDividendRate": info.get("trailingAnnualDividendRate"),
                "fiveYearAvgDividendYield": info.get("fiveYearAvgDividendYield"),
                "payoutRatio": info.get("payoutRatio"),
                "trailingEps": info.get("trailingEps"),
            },
            "dividend_history": {
                "consecutive_years_paid": 0,
                "consecutive_years_increased": 0,
                "cagr_1yr": None,
                "cagr_3yr": None,
                "cagr_5yr": None,
                "cagr_10yr": None,
                "last_5_years_annual_totals": {}
            },
            "financial_health": {
                "freeCashFlow": info.get("freeCashflow"),
                "totalDebt": info.get("totalDebt"),
                "totalCash": info.get("totalCash"),
                "ebitda": info.get("ebitda"),
                "totalRevenue": info.get("totalRevenue")
            }
        }
        
        # Calculate DGR metrics
        try:
            divs = ticker.dividends
            if not divs.empty:
                # Group by year
                yearly_divs = divs.groupby(divs.index.year).sum()
                current_year = pd.Timestamp.now().year
                
                # Filter out current year if it's incomplete to avoid skewing DGR
                if current_year in yearly_divs:
                    yearly_divs = yearly_divs[yearly_divs.index < current_year]
                
                if not yearly_divs.empty:
                    years = yearly_divs.index.tolist()
                    amounts = yearly_divs.values.tolist()
                    
                    data["dividend_history"]["last_5_years_annual_totals"] = {
                        str(year): amt for year, amt in zip(years[-5:], amounts[-5:])
                    }
                    
                    # Calculate consecutive paid
                    cons_paid = 0
                    for i in range(len(years) - 1, 0, -1):
                        if years[i] - years[i-1] == 1:
                            cons_paid += 1
                        else:
                            break
                    data["dividend_history"]["consecutive_years_paid"] = cons_paid + 1 if len(years) > 0 else 0
                    
                    # Calculate consecutive increased
                    cons_inc = 0
                    for i in range(len(amounts) - 1, 0, -1):
                        if amounts[i] > amounts[i-1]:
                            cons_inc += 1
                        else:
                            break
                    data["dividend_history"]["consecutive_years_increased"] = cons_inc
                    
                    # Calculate CAGRs
                    latest_amt = amounts[-1]
                    if len(amounts) >= 2:
                        data["dividend_history"]["cagr_1yr"] = calculate_cagr(amounts[-2], latest_amt, 1)
                    if len(amounts) >= 4:
                        data["dividend_history"]["cagr_3yr"] = calculate_cagr(amounts[-4], latest_amt, 3)
                    if len(amounts) >= 6:
                        data["dividend_history"]["cagr_5yr"] = calculate_cagr(amounts[-6], latest_amt, 5)
                    if len(amounts) >= 11:
                        data["dividend_history"]["cagr_10yr"] = calculate_cagr(amounts[-11], latest_amt, 10)
        except Exception as e:
            data["dividend_history"]["error"] = f"Could not calculate dividend history: {str(e)}"

        # Enhance financial health with cashflow statement data
        try:
            cf = ticker.cashflow
            if not cf.empty:
                latest_date = cf.columns[0]
                if "Cash Dividends Paid" in cf.index:
                    data["financial_health"]["dividendsPaid"] = abs(cf.loc["Cash Dividends Paid", latest_date])
                elif "Dividends Paid" in cf.index:
                    data["financial_health"]["dividendsPaid"] = abs(cf.loc["Dividends Paid", latest_date])
        except Exception:
            pass

        try:
            inc = ticker.income_stmt
            if not inc.empty:
                latest_date = inc.columns[0]
                if "Interest Expense" in inc.index:
                    data["financial_health"]["interestExpense"] = abs(inc.loc["Interest Expense", latest_date])
                if "EBIT" in inc.index:
                    data["financial_health"]["ebit"] = inc.loc["EBIT", latest_date]
        except Exception:
            pass

        print(json.dumps(convert_timestamps(data), indent=2))
        
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch Dividend data for LLM agents")
    parser.add_argument("ticker", help="Stock ticker symbol (e.g., JNJ)")
    args = parser.parse_args()
    
    fetch_dividend_data(args.ticker)
