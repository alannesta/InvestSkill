import json
import os
import sys

def fetch_data():
    data = {
        "market_data": {},
        "macro_data": {},
        "yield_curve": {}
    }

    # 1. Fetch from yfinance
    try:
        import yfinance as yf
        vix = yf.Ticker("^VIX").fast_info.last_price
        dxy = yf.Ticker("DX-Y.NYB").fast_info.last_price
        
        # ^TNX, ^FVX, ^TYX could also be pulled, but FRED is cleaner for historical spreads
        data["market_data"] = {
            "VIX_Volatility_Index": round(vix, 2) if vix else None,
            "US_Dollar_Index_DXY": round(dxy, 2) if dxy else None
        }
    except Exception as e:
        data["market_data"]["error"] = f"yfinance error: {str(e)}"

    # 2. Fetch from FRED
    api_key = os.getenv('FRED_API_KEY', '46c5ae5f3bd362e85a74d3ffa8a3fb0b') # Fallback to user provided key
        
    try:
        from fredapi import Fred
        import warnings
        # Suppress warnings from fredapi/pandas
        warnings.filterwarnings("ignore")
        
        fred = Fred(api_key=api_key)
        
        # Helper to safely get the last value
        def get_latest(series_id, units='lin'):
            try:
                s = fred.get_series(series_id, units=units)
                # Filter out NaNs and get the last valid value
                s = s.dropna()
                if not s.empty:
                    return round(float(s.iloc[-1]), 2)
                return None
            except Exception:
                return None

        # Fetch major economic indicators
        data["macro_data"] = {
            "Real_GDP_Growth_Rate_Annualized": get_latest('A191RL1Q225SBEA'),
            "Unemployment_Rate": get_latest('UNRATE'),
            "NonFarm_Payrolls_Thousands": get_latest('PAYEMS'),
            "CPI_YoY_Percent_Change": get_latest('CPIAUCSL', units='pc1'),
            "PCE_YoY_Percent_Change": get_latest('PCEPI', units='pc1'),
            "Core_PCE_YoY_Percent_Change": get_latest('PCEPILFE', units='pc1'),
            "Fed_Funds_Rate_Effective": get_latest('FEDFUNDS'),
            "High_Yield_OAS_Spread": get_latest('BAMLH0A0HYM2'),
            "Investment_Grade_OAS_Spread": get_latest('BAMLC0A0CMEY'),
            "TED_Spread": get_latest('TEDRATE'),
            "Sahm_Rule_Recession_Indicator": get_latest('SAHMREALTIME')
        }
        
        # Fetch Yield Curve metrics
        data["yield_curve"] = {
            "10Y_Treasury_Yield": get_latest('DGS10'),
            "5Y_Treasury_Yield": get_latest('DGS5'),
            "2Y_Treasury_Yield": get_latest('DGS2'),
            "3M_Treasury_Yield": get_latest('DGS3MO'),
            "Spread_10Y_minus_2Y": get_latest('T10Y2Y'),
            "Spread_10Y_minus_3M": get_latest('T10Y3M')
        }
        
    except Exception as e:
        data["macro_data"]["error"] = f"FRED API error: {str(e)}"
        data["yield_curve"]["error"] = f"FRED API error: {str(e)}"

    print(json.dumps(data, indent=4))

if __name__ == "__main__":
    fetch_data()
