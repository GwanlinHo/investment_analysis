# Investment Analysis Project Memories

## Workflow: Investment Analysis
- When the user types the phrase `investment analysis` (or similar trigger within this context), perform the following sequence:
  1. Execute `uv run investment_analysis.py` to generate the HTML report in the report directory.
  2. Read the generated HTML file from `report/`.
  3. **Collect Macroeconomic Data:**
     - **CRITICAL RULE:** Always use the latest **OFFICIAL released data** (e.g., from government bureaus like BEA, BLS, NDC). **Do NOT use forecast/estimated data** for the current or future months unless explicitly requested. If the current month's data is not yet out, use the previous month's official data.
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
         - **市場趨勢分析 (道氏理論應用) (Market Trend Analysis - Dow Theory Application)**:
           - **主要趨勢判斷 (Primary Trend Identification)**: AI 必須根據市場過去 60 個交易日的價格走勢，識別出主要的長期趨勢。
             - **上升趨勢 (Uptrend)**: 確認出現「一系列更高的高點 (Higher Highs)」和「更高的低點 (Higher Lows)」。
             - **下降趨勢 (Downtrend)**: 確認出現「一系列更低的高點 (Lower Highs)」和「更低的低點 (Lower Lows)」。
             - 報告中必須明確說明當前是處於「主要上升趨勢」、「主要下降趨勢」還是「橫盤整理」。
           - **次級折返走勢 (Secondary Reactions)**: 在主要趨勢中，AI 應識別任何逆勢的「次級折返」走勢。必須評估此折返是否伴隨成交量縮小，這通常是健康的修正訊號。
           - **成交量確認 (Volume Confirmation)**: 趨勢必須由成交量確認。在上升趨勢中，價格上漲時成交量應放大；在下降趨勢中，價格下跌時成交量應放大。如果量價背離，必須提出警示。
         - **關鍵 K 棒型態 (酒田戰法應用) (Key Candlestick Patterns - Sakata Method Application)**:
           - **K 棒組合掃描 (Pattern Scanning)**: AI 必須掃描最近 30 個交易日的 K 線圖，尋找酒田戰法中的關鍵反轉或持續型態。
           - **型態識別與標注 (Pattern Identification & Labeling)**: 當識別出顯著型態時（例如：「晨星」、「夜星」、「鎚子」、「吊人」、「三陽開泰」、「三鴉蔽日」等），**必須標注型態發生的確切日期**。
           - **報告範例 (Example)**: 「在 2026-02-20 觀察到晨星（Morning Star）型態，為潛在的底部反轉訊號。」
           - **結合趨勢分析 (Contextual Analysis)**: 型態的解讀必須結合道氏理論的趨勢分析。例如，在一個主要上升趨勢中的回檔出現「鎚子線」，其看漲訊號的可靠性會更高。
         - **指標與價量背離 (Indicators & Divergence)**:
           - **量價分析 (Volume Analysis)**: 分析成交量與價格變動的關聯，以識別「價漲量縮」或「低檔吸籌」等信號。
           - **指標背離 (Indicator Divergence)**: 將價格與 KD、MACD、RSI 進行交叉比對。若發現背離（例如，價格創新高但指標未跟上），**必須標注事件發生的日期**（例如：「KD 指標於 2026-02-15 出現看跌背離」）。
           - **關鍵價位 (Key Levels)**: 識別近期的支撐與壓力區，並評估突破或跌破的真實性。
         - **品質與安全邊際 (Quality & Margin of Safety)**:
           - **財務評估 (Financial Assessment)**: 讀取 `fundamental-data`。使用 ROE 與毛利率評估「護城河」；比較 PE/PB 與歷史區間，判斷當前價值。
           - **成長估值 (PEG) (Growth Valuation (PEG))**: 計算或引用 PEG Ratio (PEG < 1 通常代表低估)，以評估盈餘成長是否支撐當前股價。
           - **安全邊際 (Margin of Safety)**: 計算當前價格與 AI 評估價值之間的差距，提供明確的「風險緩衝」評估。
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
  7. **Finalization:** The analysis is now complete. The updated report is available in the `report/` directory as both a dated file and `index.html`.

