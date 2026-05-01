# Methodology: Integrating yfinance Data into Agent Skills

This document outlines the systematic process used to upgrade investment skills from relying on inconsistent web searches to using deterministic, structured financial data via the `yfinance` Python API.

## 1. Evaluate Skill Data Requirements
The first step is to thoroughly read the target `SKILL.md` to map out exactly what metrics are required to complete the analysis. 
- **Examples**: The `dcf-valuation` skill requires TTM Free Cash Flow, Beta, and the 10-Year Treasury Yield for WACC. The `stock-eval` skill requires up to 4 years of historical data to compute Year-over-Year changes for the 9-point Piotroski F-Score.

## 2. Assess yfinance Capabilities & Limitations
Before writing any code, we cross-reference the required data points with the `yfinance` API capabilities.

> [!IMPORTANT]
> **Extensive API Research Required:** Before concluding that specific data is unavailable in `yfinance`, you MUST conduct a comprehensive review of the official documentation at [https://ranaroussi.github.io/yfinance/reference/index.html](https://ranaroussi.github.io/yfinance/reference/index.html). Do NOT limit your search to only the basic `Ticker` API. `yfinance` offers several other robust APIs (such as Options, Sector/Industry data, Screener, etc.) that might provide the exact data needed.

When evaluating capabilities, keep a close eye on data timeliness and structural limits:
- **`ticker.info`**: Used for extracting current metrics, TTM data, beta, and live valuation multiples (P/E, EV/EBITDA).
- **`ticker.income_stmt` / `balance_sheet` / `cashflow`**: Used for historical data. *Critical Limitation Identified*: `yfinance` generally only provides the most recent **4 years** of annual statements. We must assess if this satisfies the skill (it works perfectly for YoY comparisons like the Piotroski score or 3-year CAGRs, but limits 10-year historical charts).
- **Indices Data**: `yf.Ticker("^TNX").fast_info.last_price` is used for the Risk-Free Rate instead of `.info` to avoid slower, brittle API calls.

## 3. Build the Extraction Script
We then build a dedicated Python script (e.g., `.agents/scripts/fetch_dcf_data.py`) tailored specifically for the skill.
- **Fail-Safe Design**: The script is wrapped in a `try/except` block. If `yfinance` is missing, or the network drops, it outputs `{"error": "<reason>"}`. This prevents the agent from crashing and allows it to gracefully report the error.
- **Targeted Extraction**: Instead of dumping the entire `info` dictionary (which is massive and eats up LLM context windows), the script plucks only the exact keys required by the skill.
- **Data Sanitization**: `yfinance` returns pandas DataFrames containing `pd.Timestamp` and `NaN` values. The script sanitizes these into standard strings and `null` values to ensure clean JSON serialization.

## 4. Refactor the Skill Instructions
The final step is to securely couple the skill to the new script.
- **Forbid Web Search**: An `IMPORTANT DATA SOURCING INSTRUCTION` is injected into the `SKILL.md` explicitly forbidding the agent from using web search tools to gather baseline financial data.
- **Mandate Script Execution**: The skill is updated to provide the exact terminal command required to fetch the data:
  ```bash
  .venv/bin/python .agents/scripts/<script_name>.py <TICKER>
  ```
- **Establish Ground Truth**: The instructions explicitly state that the data returned by the script satisfies the timeliness requirements for the analysis, giving the agent the confidence to proceed solely with the local data.
