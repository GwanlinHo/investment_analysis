# Investment Analysis Project Memories

## Workflow: Investment Analysis
- When the user types the phrase `investment analysis` (or similar trigger within this context), perform the following sequence:
  1. Execute `uv run investment_analysis.py` to generate the HTML report in the report directory.
  2. Read the generated HTML file from `report/`.
  3. **Collect Macroeconomic Data:**
     - **CRITICAL RULE:** Always use the latest **OFFICIAL released data** (e.g., from government bureaus like BEA, BLS, NDC). **STRICTLY PROHIBITED:** Using any forecast, estimated, or outlook data (預測值/估計值/展望值). All data MUST be historical actuals that have been formally released.
     - **Verification Protocol:** 
       1. **Date Backtest:** `Data Month` MUST be < `Current Month`. If `Current Month` is Feb, any data labeled "Feb" or later is REJECTED.
       2. **Keyword Blacklist:** Any data source containing "Forecast", "Estimated", "Expected", "Outlook", "預測", "預估", "展望" MUST be discarded.
       3. **Lag Compliance:** 
          - GDP/Investment: Min 1 Quarter lag.
          - CPI/Jobs/Signals: Min 1 Month lag.
       4. **Fail-Safe:** If no valid historical data is found for the current cycle, use the "Latest Confirmed Historical Actual" and explicitly mark the "Data Month" in the table. NEVER fill a cell with future-dated data.
     - Search for the latest **US Economic Indicators**: GDP (國內生產總值), CPI (消費者物價指數), PPI (生產者物價指數), Retail Sales (零售銷售), Non-farm payrolls (非農就業人數), Unemployment rate (失業率), Initial Jobless Claims (初次請領失業救濟金人數), ISM Manufacturing Index (ISM 製造業指數), M2 Money Supply (M2 貨幣供給), Credit Card Delinquency Rate (信用卡違約率), Real Private Investment (實質民間投資), US Dollar Index (美元指數).
     - Search for the latest **Taiwan Economic Indicators**: Monitoring Indicator (景氣對策信號) [MUST query directly from NDC official site: https://index.ndc.gov.tw/n/zh_tw to confirm the latest color/score], Export Orders YoY (外銷訂單年增率), Industrial Production Index (工業生產指數), Consumer Confidence Index (消費者信心指數), M1B & M2 Money Supply (M1B & M2 貨幣供給), Credit Card Delinquency Rate (信用卡違約率), Real Private Investment (實質民間投資), Unemployment rate (失業率), Industrial/Service Overtime Hours (工業及服務業加班工時), Margin Purchase Balance (融資餘額) and Short Sale Balance (融券餘額) [Query specifically for the "Total Market Balance" and "Daily Change" (increase/decrease)].
  4. Collect **15** important news items impacting US/Taiwan economy, FX, and rates.
     - **CRITICAL: News Verification Protocol**
       - **Source Validation**: Only accept news from Tier-1 authoritative media. 
         - **Global**: Bloomberg, Reuters, WSJ, Financial Times, CNBC, Barron's.
         - **Taiwan**: Economic Daily News (經濟日報), Commercial Times (工商時報), Central News Agency (CNA/中央通訊社), Anue (鉅亨網).
         - **STRICTLY PROHIBITED**: Social media (X/Facebook), personal blogs, content farms, or sites with sensationalist clickbait titles.
       - **Cross-Verification**: Major market events (e.g., Fed decisions, CPI data) MUST be confirmed by at least **two** independent Tier-1 sources.
       - **Recency Check**: All news MUST be published within the last **7 days**.
       - **Data Consistency**: If a news item contains economic figures (e.g., GDP growth), it MUST match the official data collected in Step 3. Discard the news if there is a conflict.
       - **No Hallucination**: Do NOT generate simulated or fake news. All news must be real, current, and verifiable.
     - **Requirement:** Every news item **MUST** include a valid, **DIRECT** source link to the specific article (NOT the homepage URL).
     - **Format:** Compact style (Title + Source Link on Line 1, Summary on Line 2). Max 2 lines per item.
  5. Generate analysis content (**STRICTLY NO EMOJIS ALLOWED**):
     - **Part A: Weekly News Focus**
       - **Step 1: Multi-Angle Search (Expand the Pool):**
         - Do NOT rely on a single search query. Execute **3 distinct searches** to gather a broad pool of candidates:
           1.  **Global/US Macro:** `query="Top market moving financial news US economy Fed rate this week"`
           2.  **Taiwan/Tech:** `query="Taiwan stock market TSMC export orders major news this week"`
           3.  **Risks/Earnings:** `query="Major geopolitical risks corporate earnings surprises finance this week"`
       - **Step 2: Curation & Filtering (Select High Impact):**
         - From the combined search results, select the **15 most impactful** stories.
         - **Selection Criteria:** Focus on items that move markets (e.g., rate decisions, CPI/jobs data), affect major industries (e.g., AI, Semis), or signal trend changes. Discard minor corporate news or duplicates.
         - **Ratio:** Keep roughly 70% Global/US and 30% Taiwan.
       - **Step 3: Content Generation (Use Search Snippets):**
         - **Source of Truth:** Use the *Title* and *Snippet* text directly from the Google Search results. This ensures consistency.
         - **Translation:** Translate all news titles and summaries into Traditional Chinese.
       - **Formatting:**
         - Format as a clean HTML list (`<ul>` with `<li>`).
         - **No Hyperlinks:** Do NOT include `<a>` tags for news items.
         - **Bold Titles:** Wrap the source and title in `<strong>` tags.
         - **Compact Layout:** Ensure the title and summary are visually close (minimal margin).
         - **Example:**
           ```html
           <li class="news-item" style="margin-bottom: 15px;">
               <div class="news-content">
                   <div style="font-weight: bold; margin-bottom: 2px;">[Bloomberg] Fed Signals Rate Cut Delay</div>
                   <div style="font-size: 14px; color: #555;">Fed Chair Powell indicated that inflation data remains too hot to justify an immediate rate cut.</div>
               </div>
           </li>
           ```
       - Target div: `#weekly-news-focus`.
     - **Part B: AI Comprehensive Analysis**
       - **Data Requirement:** The Python script MUST embed the last 60 days of OHLCV market data into `<script id="market-data">` in the HTML. The AI MUST read this data along with `<script id="fundamental-data">` and `<script id="yield-data">`. 
       - **Market Status Awareness**: AI MUST check the `.market-status` tags in the HTML report. If a market is labeled as **"休市中 (Market Closed)"**, the AI MUST explicitly mention the holiday or market closure in its analysis and ensure all price-related statements refer to the **"最後交易日" (Last Trading Day)** instead of the current date.
       - **Logic and Chronological Consistency Check**: Before injecting the "AI Comprehensive Analysis" into the HTML, AI MUST perform a final consistency check to eliminate logic or chronological errors. Specifically, it MUST NOT report market-active phenomena (e.g., "observed a specific candlestick pattern today") during periods labeled as **"休市中 (Market Closed)"**. All such analysis during holidays must explicitly refer to the **"最後交易日" (Last Trading Day)** to maintain factual accuracy.
       - **1. Macro Framework**:
         - **Macro Interpretation**: Combine CPI, PPI, Retail Sales, and interest rate cycles to determine the current stage of the economic cycle.
         - **Yield Curve Signal (CRITICAL)**: AI **MUST** read the latest values from `<script id="yield-data">` and manually calculate the **10Y minus 3M** spread.
           - If (10Y - 3M) < 0: Describe as "Yield Curve Inversion" and warn of recession risks.
           - If (10Y - 3M) > 0: Describe as "Spread Normalized/Positive" and evaluate growth expectations.
           - **STRICTLY PROHIBITED (Duration Speculation)**: Do NOT use phrases like "X years long," "ending X years of inversion," or any specific numerical duration (e.g., "three years long") without explicit historical data support. AI must only describe the "Current Value State" and the "Direction of Change" compared to the previous period. If historical context is mentioned, it MUST cite specific data points (date and value); avoid baseless inferences.
       - **2. Market & Industry Dynamics**:
         - **Capital Flow**: Analyze the impact of the US Dollar Index (DXY) and Treasury yields on global capital flows, specifically regarding foreign capital outflow pressure in Taiwan and momentum in US mega-cap stocks.
         - **Sector Valuation**: Evaluate valuation correction risks for high-growth tech stocks (e.g., AI, Semiconductors) in the current interest rate environment; use M2 money supply to judge if market liquidity supports current prices.
         - **Positioning & Sentiment**: Combine Taiwan's margin/short balance with credit card delinquency rates to analyze retail sentiment and potential credit risk divergences.
       - **3. Technical & Fundamental Deep Dive**:
         - **Market Trend Analysis (Dow Theory Application)**:
           - **Primary Trend Identification**: AI must identify the primary long-term trend based on the market's price action over the past 60 trading days. **The analysis must explicitly name the specific asset and its symbol (e.g., S&P 500 (^GSPC)).**
             - **Uptrend**: Confirm a "series of Higher Highs and Higher Lows".
             - **Downtrend**: Confirm a "series of Lower Highs and Lower Lows".
             - The report must clearly state whether the specific asset is in a "Primary Uptrend", "Primary Downtrend", or "Sideways Consolidation".
           - **Secondary Reactions**: Identify any "Secondary Reactions" (counter-trend movements) within the primary trend. Evaluate if these reactions are accompanied by decreasing volume, which typically signals a healthy correction.
           - **Volume Confirmation**: Trends must be confirmed by volume. In an uptrend, volume should expand on price increases; in a downtrend, volume should expand on price decreases. AI must alert on any price-volume divergence.
         - **Key Candlestick Patterns (Sakata Method Application)**:
           - **Pattern Scanning**: AI must scan the candlestick charts of the last 30 trading days for key reversal or continuation patterns defined in the Sakata Method.
           - **Identification & Labeling**: When significant patterns are identified (e.g., "Morning Star", "Evening Star", "Hammer", "Hanging Man", "Three White Soldiers", "Three Black Crows", etc.), **AI must specify the asset name and symbol, and the exact date of occurrence.**
           - **Example**: "On 2026-02-20, **S&P 500 (^GSPC)** exhibited a Morning Star pattern, signaling a potential bottom reversal."
           - **Contextual Analysis**: Pattern interpretation must be integrated with Dow Theory trend analysis. For instance, a "Hammer" appearing during a pullback in a primary uptrend carries significantly higher reliability.
         - **Indicators & Divergence**:
           - **Volume Analysis**: Analyze the correlation between volume and price movement to identify signals such as "Price Up, Volume Down" or "Bottom Accumulation". **The target asset must be specified.**
           - **Indicator Divergence**: Cross-reference price action with KD, MACD, and RSI. If a divergence is found (e.g., price hits a new high but the indicator does not), **AI must specify the asset name and symbol, and the exact date of occurrence** (e.g., "KD indicator for **TSMC (2330.TW)** showed a bearish divergence on 2026-02-15").
           - **Key Levels**: Identify recent support and resistance zones and evaluate the authenticity of any breakouts or breakdowns.
         - **Quality & Margin of Safety**:
           - **Financial Assessment**: Read `fundamental-data`. Use ROE and Gross Margin to evaluate the "Moat"; compare PE/PB with historical ranges to judge current valuation.
           - **Growth Valuation (PEG)**: Calculate or cite the PEG Ratio (PEG < 1 usually suggests undervaluation) to assess if earnings growth supports the current stock price.
           - **Margin of Safety**: Calculate the gap between the current price and the AI-estimated intrinsic value, providing a clear "Risk Buffer" assessment.
       - **4. Actionable Strategy**:
         - **Scenario Simulation**: Define "Bull," "Base," and "Bear" scenarios with specific trigger conditions.
         - **Execution Plan**: Provide specific operational suggestions such as tiered entry, hedging, or increasing cash positions.
       - **Constraint:** Do NOT write MBTI labels in the output. Structure the output with clear headings and a final "Actionable Strategy" section.
       - Target div: `#ai-analysis-report`.
  6. **Update HTML Report:**
     - **Inject Macro Data:** Format the collected economic indicators into **two separate** HTML tables (one for US, one for Taiwan).
       - **Target Placeholders:**
         - Inject US indicators table into `<div id="us-macro-placeholder"></div>`.
         - Inject Taiwan indicators table into `<div id="tw-macro-placeholder"></div>`.
       - **Formatting Rules:**
         - **Language:** The "Indicator Name" column MUST be written in Traditional Chinese (e.g., 國內生產總值 (GDP), 非農就業人數, 失業率, etc.).
         - **Columns:** "Indicator Name" (Left-aligned), "Value" (Right-aligned), "Date/Note" (Right-aligned). **Do NOT include a 'Region' column.**
         - **Trends:** Do not show plain numbers. Use trend arrows (**▲/▼**) and color coding (Red for positive/up, Green for negative/down).
         - **Mobile Layout:** Ensure tables use standard HTML `<table>` tags. The container divs already handle responsiveness.
         - **Margin Data (Taiwan):** Display "Margin Purchase Balance" and "Short Sale Balance" as two distinct rows. Show the total balance in the "Value" column with trend coloring. Show the daily change (e.g., "-8.95億") in the "Date/Note" column.
     - **Inject Analysis Content:**
       - Inject the **Weekly News Focus** content into the `<div id="weekly-news-focus"></div>`.
       - Inject the **AI Comprehensive Analysis** content into the `<div id="ai-analysis-report"></div>`.
       - **CRITICAL:** Ensure NO emojis are used in the injected content.
  7. **Finalization:** The analysis is now complete. 
     - **Sync Updated Report:** Copy the final updated dated HTML file to `index.html` and `report/index.html` to ensure the root index and directory index are always up-to-date with the latest AI analysis and macro data.
     - The updated report is available in the `report/` directory as both a dated file and `index.html`.

