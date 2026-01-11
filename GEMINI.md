# Investment Analysis Project Memories

## Workflow: Investment Analysis
- When the user types the phrase `investment analysis` (or similar trigger within this context), perform the following sequence:
  1. Execute `python3 investment_analysis.py` to generate the HTML report in the report directory.
  2. Read the generated HTML file from `report/`.
  3. **Collect Macroeconomic Data:**
     - **CRITICAL RULE:** Always use the latest **OFFICIAL released data** (e.g., from government bureaus like BEA, BLS, NDC). **Do NOT use forecast/estimated data** for the current or future months unless explicitly requested. If the current month's data is not yet out, use the previous month's official data.
     - Search for the latest **US Economic Indicators**: GDP, Non-farm payrolls, Unemployment rate, Manufacturing PMI, US Dollar Index.
     - Search for the latest **Taiwan Economic Indicators**: Monitoring Indicator (景氣對策信號), Export Orders (外銷訂單), Unemployment rate, Industrial/Service Overtime Hours (工業及服務業加班工時), Margin Purchase Balance (融資餘額) and Short Sale Balance (融券餘額) [Query specifically for the "Total Market Balance" and "Daily Change" (increase/decrease)].
  4. Collect **15** important news items impacting US/Taiwan economy, FX, and rates.
     - **CRITICAL:** Do NOT generate simulated or fake news. All news must be real, current, and verifiable.
     - **Requirement:** Every news item **MUST** include a valid, **DIRECT** source link to the specific article (NOT the homepage URL).
     - **Format:** Compact style (Title + Source Link on Line 1, Summary on Line 2). Max 2 lines per item.
  5. Generate analysis using three distinct AI personas (**Strictly NO emojis allowed in the output**):
     - **Data Extraction:** EXTRACT the fundamental data JSON from the `<script id="fundamental-data">` block in the HTML file. USE this data for the Value Investing analysis.
     - **Note:** Adopt the *tone and thinking style* of the specified MBTI types, but **DO NOT** write the MBTI label (e.g., "ISTP") in the report headers or text.
     - **Technical Analysis Master (Style: ISTP):** Pragmatic, analytical, crisis-ready. Analyze volume/price, support/resistance, divergence, and "Sakata Goho" (酒田戰法) candlestick patterns. Warn of reversals. Be direct.
     - **Value Investing Master (Style: ISTJ):** Responsible, organized, fact-based.
       - **Core Logic:** Use the extracted JSON data to evaluate specific stocks. Focus on **Moat** (Gross Margin, ROE), **Margin of Safety** (PE vs Historical/Forward), and **Cash Flow**.
       - **Individual Stocks:** Cite specific numbers (e.g., "TSMC's ROE is 25%...").
       - **ETFs:** Focus on yield, expense ratio (if known), and underlying sector valuation. Avoid applying single-stock metrics to ETFs unless relevant.
     - **Macro & Industry Master (Style: INTJ):** Strategic, visionary, systems-thinker. Analyze interest rates, industry cycles, and geopolitical risks. **MUST** incorporate the collected US/Taiwan macroeconomic data into the analysis.
  6. **Update HTML Report:**
     - **Inject Macro Data:** Format the collected economic indicators into **two separate** HTML tables (one for US, one for Taiwan).
       - **Target Placeholders:**
         - Inject US indicators table into `<div id="us-macro-placeholder"></div>`.
         - Inject Taiwan indicators table into `<div id="tw-macro-placeholder"></div>`.
       - **Formatting Rules:**
         - **Columns:** "Indicator Name" (Left-aligned), "Value" (Right-aligned), "Date/Note" (Right-aligned). **Do NOT include a 'Region' column.**
         - **Trends:** Do not show plain numbers. Use trend arrows (**▲/▼**) and color coding (Red for positive/up, Green for negative/down).
         - **Mobile Layout:** Ensure tables use standard HTML `<table>` tags. The container divs already handle responsiveness.
         - **Margin Data (Taiwan):** Display "Margin Purchase Balance" and "Short Sale Balance" as two distinct rows. Show the total balance in the "Value" column with trend coloring. Show the daily change (e.g., "-8.95億") in the "Date/Note" column.
     - **Inject Analysis:** Append the textual analysis and news to the HTML file (replace the `#text-analysis-report` div).
  7. Execute `git add report/ && git commit -m "Update analysis report" && git push` to upload the changes to GitHub.

# Gemini CLI Command Rule: video summary

## Description
當輸入 `video summary` 指令時，自動抓取最新的 YouTube 影片清單，並整理出影片中的財經議題與詳細內容。

## Trigger
- command: video summary

## Workflow Steps

1. **更新影片清單 (Update Video List)**
   - 執行 `python fetch_yt_list.py` 以更新 `videolist.md`。

2. **多維度內容提取 (Multi-source Extraction)**
   - **程式化提取**: 優先使用 `yt-dlp` (可透過 Python 腳本 `get_video_details.py`) 抓取影片的 `description` 與 `chapters` 以建立議題骨架。
   - **語意補完**: 若影片描述欄資訊不足 (例如僅有廣告或連結)，自動針對影片標題執行 `google_web_search`，搜尋第三方筆記、社群討論或專業報導以獲取詳細論述內容。

3. **內容整理 (Summarize)**
   - 整合中繼資料與搜尋結果，列出每一部影片中提及的每一項財經議題。
   - 詳細說明該議題的重要內容。
   - 需註明創作者與影片名稱。

4. **輸出檔案 (Output)**
   - 輸出檔案命名規則: `report/video_YYYYMMDD.md`
   - **輸出格式**:
     ```markdown
     # 創作者: [創作者名稱]
     ## 影片名稱: [影片標題]
     ## 議題一: [議題標題]
     [詳細內容]
     ## 議題二: [議題標題]
     [詳細內容]
     ```
