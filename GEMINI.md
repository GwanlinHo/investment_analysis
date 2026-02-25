# Investment Analysis Project Memories

## General Constraints
- **NO EMOJIS ALLOWED** in any output.
- **LANGUAGE**: All generated content must be in **Traditional Chinese**.
- **Python Execution**: ALWAYS use `uv run` to execute Python scripts to ensure dependency isolation.
- **Consistency Check**: Before final injection, verify that no market-active phrases (e.g., "observed today") are used if the market status is "Market Closed". Refer to the "Last Trading Day" instead.
- **Documentation**: Every time the source code or `GEMINI.md` is modified, a summary of changes with the date must be added to the "Changelog" section at the top of `README.md`.
- **Tool Usage Standard**: Prohibit guessing string positions in files (e.g., using offset). MUST use `grep_search` or the `grep` tool via `run_shell_command` for precise positioning and content reading.

## Workflow: Investment Analysis

### 0. Technical Data Generation
- **Action**: ALWAYS execute `uv run investment_analysis.py` as the first step.
- **Purpose**: This generates the base HTML report with the latest technical indicators (KD, MACD, BIAS), price data, and K-line charts.
- **Verification**: Ensure the script finishes successfully before proceeding to macro data collection.

### 1. Macro Data Collection
- **Principle**: Use **OFFICIAL Historical Actuals ONLY**. Strictly prohibit forecasts, estimates, or outlooks.
- **Verification**: `Data Month < Current Month`. Cross-verify data across official sites (BEA, BLS, CBC, NDC, MOEA, DGBAS).
- **Accuracy**: Data must match official press releases exactly. If sources conflict, prioritize the primary government agency.
- **Lag Compliance**: GDP/Investment (Min 1 Quarter lag); Other indicators (Min 1 Month lag).
- **US Indicators**: GDP, CPI, PPI, Retail Sales, Non-farm Payrolls, Unemployment Rate, Jobless Claims, ISM Mfg Index, M2, Credit Card Delinquency, Real Private Invest, DXY.
- **TW Indicators**: Monitoring Indicator (Query NDC site for score/color), Export Orders YoY, Industrial Production, Consumer Confidence, M1B/M2, Credit Card Delinquency, Real Private Invest, Unemployment, Overtime Hours, Margin/Short Balance (Display Total & Daily Change).
- **Local Cache**: Use `macro_cache.json` to store and retrieve historical data when latest figures are not yet released. Update cache only when newer official data is found.

### 2. News Focus (15 Items)
- **Authority**: Tier-1 ONLY (Bloomberg, Reuters, WSJ, FT, CNBC, Barron's, Economic Daily, Commercial Times, CNA, Anue).
- **Freshness**: All news must be published within the **LAST 7 DAYS**.
- **Authenticity**: MANDATORY cross-verification of all major claims. If a story is only reported by a single non-wire source, it must be excluded. Compare at least two Tier-1 sources for critical news.
- **Search Strategy**: Execute **3 distinct searches**: (1) Global Macro/Fed, (2) TW Stock/Tech/TSMC, (3) Geopolitical Risks/Earnings surprises.
- **Dynamic Injection**: Strictly prohibit hardcoding news content in scripts. News must be dynamically injected into the script or report by AI after each search.
- **Selection**: 15 items total. Maintain a **70% Global / 30% Taiwan** ratio.
- **Format**: 
  - Line 1: **[Source] Title** (No links allowed).
  - Line 2: Concise summary focusing on impact and facts, not speculation.
- **HTML Target**: `#weekly-news-focus` (Use `<ul><li>`, NO `<a>` tags or URLs in the final HTML).

### 3. AI Comprehensive Analysis (Persona-Driven Framework)
AI must dynamically generate analysis based on current real-world data. The use of static templates containing hardcoded data (e.g., fixed VIX values, inflation rates, interest rate spread descriptions) is strictly prohibited.

#### 1. Atlas - Macro Strategist
- **Responsibilities**:
  - **Yield Monitoring Logic**: Calculate the spreads between 3M, 10Y, and 30Y yields.
  - **Trigger Rule**: Mention the yield curve state (e.g., flattening or inverted) in the report ONLY when the spread between any two is **< 0.25% (25bps)** or an **inversion (spread < 0)** occurs.
  - **Silence Rule**: If the gaps between all three are > 0.25%, the curve is considered steep and normal. **STRICTLY PROHIBIT** mentioning the yield curve; focus should shift to other indicators like DXY, M2, or GDP.
  - Audit all indicators to ensure they are official historical actuals.

#### 2. Sophia - Fundamental Quality Analyst
- **Responsibilities**:
  - Evaluate performance based on real ROE, Gross Margin, and PEG from the `fundamental-data` script tags.

#### 3. Kenji - Technical Chartist
- **Responsibilities**:
  - Detect real KD and MACD divergence situations and Moving Average Bias (BIAS).

#### 4. Crow - Flow & Sentiment Sentinel
- **Responsibilities**:
  - Quantify market sentiment based on current real **VIX Index** and margin/short balance data.

#### 5. Rain - Portfolio Manager
- **Responsibilities**:
  - Synthesize Bull/Base/Bear scenarios and action strategies based on the above dynamic analysis.

### 4. Data Injection & Synchronization
- **Injection**: Execute `uv run update_report.py`. This script must extract data from JSON tags in the base HTML report, perform dynamic text synthesis, and then inject it.
- **No Hardcoding**: Scripts must not contain static variables or hardcoded macroeconomic values for `AI_ANALYSIS_TEXT`.
- **Cleanup**: Ensure no placeholders remain.
- **Finalization**: Synchronize updates to `index.html` and `report/index.html`.
