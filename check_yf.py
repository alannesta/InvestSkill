import sys
try:
    import yfinance as yf
except ImportError:
    print("yfinance not installed. Please install it first using: pip install yfinance")
    sys.exit(1)

def check_yf_capabilities(ticker_symbol):
    print(f"Checking yfinance capabilities for {ticker_symbol}...\n")
    ticker = yf.Ticker(ticker_symbol)
    
    info = ticker.info
    print("--- INFO KEYS (Sample of what's available) ---")
    keys_of_interest = [
        'shortRatio', 'shortPercentOfFloat', 'sharesShort', 
        'sharesOutstanding', 'impliedSharesOutstanding', 'floatShares',
        'beta', 'trailingPE', 'forwardPE', 'priceToBook', 'enterpriseToEbitda', 'pegRatio',
        'returnOnEquity', 'returnOnAssets', 'grossMargins', 'operatingMargins', 'profitMargins',
        'totalDebt', 'totalCash', 'freeCashflow', 'operatingCashflow'
    ]
    
    found = {}
    missing = []
    for k in keys_of_interest:
        if k in info:
            found[k] = info[k]
        else:
            missing.append(k)
            
    for k, v in found.items():
        print(f"{k}: {v}")
        
    print("\nMissing keys in info:", missing)
    
    print("\n--- FINANCIAL STATEMENTS ---")
    try:
        inc = ticker.income_stmt
        bs = ticker.balance_sheet
        cf = ticker.cashflow
        print(f"Income Statement columns (Years): {list(inc.columns) if inc is not None and not inc.empty else 'Empty'}")
        print(f"Balance Sheet columns (Years): {list(bs.columns) if bs is not None and not bs.empty else 'Empty'}")
        print(f"Cash Flow columns (Years): {list(cf.columns) if cf is not None and not cf.empty else 'Empty'}")
        
        # Check for SBC
        if cf is not None and not cf.empty:
            sbc_keys = [k for k in cf.index if 'Stock' in k or 'Compensation' in k]
            print(f"Found SBC related rows in Cash Flow: {sbc_keys}")
            
    except Exception as e:
        print("Error fetching statements:", e)
        
    print("\n--- OPTIONS DATA ---")
    try:
        opts = ticker.options
        if opts:
            print(f"Found {len(opts)} option expiration dates.")
            chain = ticker.option_chain(opts[0])
            print(f"Calls shape: {chain.calls.shape}, Puts shape: {chain.puts.shape}")
            print(f"Option data columns: {list(chain.calls.columns)}")
        else:
            print("No options data found.")
    except Exception as e:
        print("Error fetching options:", e)

if __name__ == '__main__':
    check_yf_capabilities("AAPL")
