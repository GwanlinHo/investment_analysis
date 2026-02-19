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
     - **CRITICAL: News Verification Protocol (新聞查核協議)**
       - **Source Validation (來源驗證)**: Only accept news from Tier-1 authoritative media. 
         - **Global**: Bloomberg, Reuters, WSJ, Financial Times, CNBC, Barron's.
         - **Taiwan**: 經濟日報, 工商時報, 中央通訊社 (CNA), 鉅亨網 (Anue).
         - **STRICTLY PROHIBITED**: Social media (X/Facebook), personal blogs, content farms, or sites with sensationalist clickbait titles.
       - **Cross-Verification (交叉比對)**: Major market events (e.g., Fed decisions, CPI data) MUST be confirmed by at least **two** independent Tier-1 sources.
       - **Recency Check (時效性檢查)**: All news MUST be published within the last **7 days**.
       - **Data Consistency (數據一致性)**: If a news item contains economic figures (e.g., GDP growth), it MUST match the official data collected in Step 3. Discard the news if there's a conflict.
       - **No Hallucination (嚴禁虛構)**: Do NOT generate simulated or fake news. All news must be real, current, and verifiable.
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
       - **Market Status Awareness**: AI MUST check the `.market-status` tags in the HTML report. If a market is labeled as **"休市中 (Market Closed)"**, the AI MUST explicitly mention the holiday or market closure in its analysis and ensure all price-related statements refer to the **"最後交易日"** instead of the current date.
       - **1. 宏觀環境定調 (Macro Framework)**:
         - **總經解讀**: 結合 CPI, PPI, 零售銷售與利率週期，判斷目前處於經濟週期的哪個階段。
         - **債市訊號**: 計算 10Y-3M 價差，評估殖利率曲線對衰退風險或成長動能的指示。
       - **2. 市場動態與產業趨勢 (Market & Industry Dynamics)**:
         - **資金流向 (Capital Flow)**: 分析美元指數 (DXY) 與公債殖利率對全球資金流向的影響，特別是針對台股外資流出壓力與美股權值股動能進行關聯分析。
         - **產業估值 (Sector Valuation)**: 評估高成長科技股 (如 AI, 半導體) 在當前利率環境下的估值回調風險；結合 M2 貨幣供給判斷市場流動性是否支撐當前股價。
         - **籌碼面監控 (Positioning)**: 結合台股融資融券餘額與信用卡違約率數據，分析散戶情緒與潛在的信用風險背離。
       - **3. 技術面與個股健檢 (Technical & Fundamental Deep Dive)**:
         - **量價與指標**: 針對特定標的 (例如 S&P 500 或 TSMC) 分析量價背離、KD 交叉日期及 MACD 趨勢。
         - **品質與估值**: 運用 ROE 與毛利率評估企業競爭力，並對比 PE/PB 歷史區間尋找具備「安全邊際」的切入點。
       - **4. 綜合對策與情境預測 (Actionable Strategy)**:
         - **情境模擬**: 分別定義「樂觀 (Bull)」、「中立 (Base)」、「悲觀 (Bear)」三種情境及觸發條件。
         - **具體行動**: 提供分批布局、避險、或提高現金比重的具體操作建議。
       - **Constraint:** Do NOT write MBTI labels in the output. Structure the output with clear headings and a final "Actionable Strategy" section.
       - Target div: `#ai-analysis-report`.
  6. **Update HTML Report:**
     - **Inject Macro Data:** Format the collected economic indicators into **two separate** HTML tables (one for US, one for Taiwan).
       - **Target Placeholders:**
         - Inject US indicators table into `<div id="us-macro-placeholder"></div>`.
         - Inject Taiwan indicators table into `<div id="tw-macro-placeholder"></div>`.
       - **Formatting Rules:**
         - **Language:** The "Indicator Name" column MUST be written in Traditional Chinese (例如：國內生產總值 (GDP)、非農就業人數、失業率等).
         - **Columns:** "Indicator Name" (Left-aligned), "Value" (Right-aligned), "Date/Note" (Right-aligned). **Do NOT include a 'Region' column.**
         - **Trends:** Do not show plain numbers. Use trend arrows (**▲/▼**) and color coding (Red for positive/up, Green for negative/down).
         - **Mobile Layout:** Ensure tables use standard HTML `<table>` tags. The container divs already handle responsiveness.
         - **Margin Data (Taiwan):** Display "Margin Purchase Balance" and "Short Sale Balance" as two distinct rows. Show the total balance in the "Value" column with trend coloring. Show the daily change (e.g., "-8.95億") in the "Date/Note" column.
     - **Inject Analysis Content:**
       - Inject the **Weekly News Focus** content into the `<div id="weekly-news-focus"></div>`.
       - Inject the **AI Comprehensive Analysis** content into the `<div id="ai-analysis-report"></div>`.
       - **CRITICAL:** Ensure NO emojis are used in the injected content.
  7. Execute `git add report/ && git commit -m "Update analysis report" && git push` to upload the changes to GitHub.
