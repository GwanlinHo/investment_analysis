# Investment Analysis Project Memories

## General Constraints
- **NO EMOJIS ALLOWED** in any output.
- **LANGUAGE**: All generated content must be in **Traditional Chinese**.
- **NO MBTI**: Do NOT include any MBTI-related labels or personality archetypes.
- **Consistency Check**: Before final injection, verify that no market-active phrases (e.g., "observed today") are used if the market status is "Market Closed". Refer to the "Last Trading Day" instead.

## Workflow: Investment Analysis

### 1. Macro Data Collection
- **Principle**: Use **OFFICIAL Historical Actuals ONLY**. Strictly prohibit forecasts, estimates, or outlooks.
- **Verification**: `Data Month < Current Month`. Ensure data matches official sources (BEA, BLS, NDC).
- **Lag Compliance**: GDP/Investment (Min 1 Quarter lag); Other indicators (Min 1 Month lag).
- **US Indicators**: GDP, CPI, PPI, Retail Sales, Non-farm Payrolls, Unemployment Rate, Jobless Claims, ISM Mfg Index, M2, Credit Card Delinquency, Real Private Invest, DXY.
- **TW Indicators**: Monitoring Indicator (Query NDC site for score/color), Export Orders YoY, Industrial Production, Consumer Confidence, M1B/M2, Credit Card Delinquency, Real Private Invest, Unemployment, Overtime Hours, Margin/Short Balance (Display Total & Daily Change).

### 2. News Focus (15 Items)
- **Search Strategy**: Execute **3 distinct searches**: (1) Global Macro/Fed, (2) TW Stock/Tech/TSMC, (3) Geopolitical Risks/Earnings surprises.
- **Selection**: 15 items total. Maintain a **70% Global / 30% Taiwan** ratio.
- **Sources**: Tier-1 ONLY (Bloomberg, Reuters, WSJ, FT, CNBC, Barron's, Economic Daily, Commercial Times, CNA, Anue).
- **Format**: 
  - Line 1: **[Source] Title** (Include direct source link).
  - Line 2: Concise summary.
- **HTML Target**: `#weekly-news-focus` (Use `<ul><li>`, no `<a>` tags for titles).

### 3. AI Comprehensive Analysis
- **1. Macro Framework**: Assess economic cycle stage. Calculate **10Y-3M yield spread**. 
  - *Strict Rule*: Do NOT speculate on duration (e.g., "X years long") without citing specific historical dates and values.
- **2. Market Dynamics**: Analyze DXY/Yields impact on capital flows (TW outflows/US Mega-caps). Evaluate Tech valuations (AI/Semis) vs M2 liquidity.
- **3. Deep Dive (MANDATORY: Specify Asset/Symbol & Exact Date)**:
  - **Dow Theory**: Identify Primary Trend (60-day) & Secondary Reactions. Confirm with volume.
  - **Sakata Method**: Scan 30-day patterns (e.g., Morning Star, Hammer).
  - **Indicators**: Price-Volume correlation, Divergence (KD, MACD, RSI), Support/Resistance levels.
  - **Quality/Safety**: ROE, Gross Margin, PE/PB range, PEG Ratio, Intrinsic Value/Risk Buffer.
- **4. Actionable Strategy**: Define Bull/Base/Bear scenarios with specific triggers and execution plans (hedging/entry/cash levels).
- **HTML Target**: `#ai-analysis-report`.

### 4. HTML Formatting & Synchronization
- **Macro Tables**: 
  - **Language**: Indicator names in Traditional Chinese.
  - **Columns**: Name (Left), Value (Right), Date/Note (Right). No "Region" column.
  - **Trends**: Use **▲/▼** arrows. Red for Up/Positive, Green for Down/Negative.
  - **TW Margin Data**: Separate rows for Margin and Short. Show "Total Balance" in Value column and "Daily Change" in Date/Note column.
- **Finalization**: Sync dated HTML file to `index.html` and `report/index.html`.
