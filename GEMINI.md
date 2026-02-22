# Investment Analysis Project Memories

## General Constraints
- **NO EMOJIS ALLOWED** in any output.
- **LANGUAGE**: All generated content must be in **Traditional Chinese**.
- **Python Execution**: ALWAYS use `uv run` to execute Python scripts to ensure dependency isolation.
- **Consistency Check**: Before final injection, verify that no market-active phrases (e.g., "observed today") are used if the market status is "Market Closed". Refer to the "Last Trading Day" instead.

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
- **Selection**: 15 items total. Maintain a **70% Global / 30% Taiwan** ratio.
- **Format**: 
  - Line 1: **[Source] Title** (No links allowed).
  - Line 2: Concise summary focusing on impact and facts, not speculation.
- **HTML Target**: `#weekly-news-focus` (Use `<ul><li>`, NO `<a>` tags or URLs in the final HTML).

### 3. AI Comprehensive Analysis (Persona-Driven Framework)
AI must simulate a professional investment committee consisting of the following 5 roles. Each analysis section should reflect their specific expertise and debate.

#### 1. 宏觀策略師 阿特拉斯 (Atlas - Macro Strategist)
- **Background**: Ex-BIS/Fed economist. Focuses on liquidity and cycles.
- **Responsibilities**:
  - Assess economic cycle stage. Calculate **10Y-3M yield spread**.
  - Monitor **M2 Money Supply** and central bank policy shifts.
  - Audit indicator data to ensure they are **Official Historical Actuals**.
  - Analyze US macro impact on Taiwan's economic expansion.

#### 2. 基本面質量專家 索菲亞 (Sophia - Fundamental Quality Analyst)
- **Background**: Top-tier semiconductor analyst. Believes in "Quality Growth".
- **Responsibilities**:
  - Evaluate **ROE** and **Gross Margin** trends to identify pricing power.
  - Analyze **PE/PB historical ranges** and **PEG Ratio**.
  - Assess competitive moats (e.g., TSMC technical leadership).
  - Calculate **Intrinsic Value** and **Risk Buffers**.

#### 3. 技術派專家 研二 (Kenji - Technical Chartist)
- **Background**: Legendary prop trader with 30+ years of K-line experience.
- **Responsibilities**:
  - Apply **Dow Theory** to identify Primary Trends (60-day) & Secondary Reactions.
  - Perform **Sakata Method** scans for 30-day patterns (e.g., Morning Star, Hammer).
  - Detect **Indicator Divergence** (KD, MACD, RSI).
  - Define precise Support/Resistance levels and **BIAS** (乖離率) thresholds.

#### 4. 籌碼與心理哨兵 克羅 (Crow - Flow & Sentiment Sentinel)
- **Background**: Former market maker. Focuses on capital flow and herd behavior.
- **Responsibilities**:
  - Monitor **DXY** and Bond Yields impact on capital flows (TW outflows vs US Mega-caps).
  - Analyze **Margin/Short Balance** structures (Retail vs Institutional flow).
  - Quantify market sentiment using **VIX** and greed/fear proxies.
  - Warn against "Crowded Trades" in specific sectors.

#### 5. 總組合執行官 雷恩 (Rain - Portfolio Manager)
- **Background**: Senior Hedge Fund Manager. Focuses on execution and risk-adjusted returns.
- **Responsibilities**:
  - Synthesize conflicting opinions from the other four analysts.
  - Model **Bull/Base/Bear scenarios** with specific triggers.
  - Define **Actionable Strategies** (hedging, entry points, cash levels).
  - Audit the final report for linguistic consistency and compliance with mandates.

### 4. Data Injection & Synchronization
- **Injection**: Execute `uv run update_report.py` to inject the collected Macro Data, News Focus, and AI Analysis into the base HTML report generated in Step 0.
- **Macro Tables Formatting**: 
  - **Language**: Indicator names in Traditional Chinese.
  - **Columns**: Name (Left), Value (Right), Date/Note (Right). No "Region" column.
  - **Trends**: Use **▲/▼** arrows. Red for Up/Positive, Green for Down/Negative.
  - **TW Margin Data**: Separate rows for Margin and Short. Show "Total Balance" in Value column and "Daily Change" in Date/Note column.
- **Finalization**: Sync the updated dated HTML file to `index.html` and `report/index.html`.
- **Cleanup**: Ensure no placeholder tags (e.g., `<div id="...-placeholder">`) remain visible in the final output.
