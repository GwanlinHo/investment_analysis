# Investment Analysis Project Memories

## Workflow: Investment Analysis
- When the user types the phrase `investment analysis` (or similar trigger within this context), perform the following sequence:
  1. Execute `python3 investment_analysis.py` to generate the HTML report in the report directory.
  2. Read the generated HTML file from `report/`.
  3. Collect **15** important news items impacting US/Taiwan economy, FX, and rates.
     - **CRITICAL:** Do NOT generate simulated or fake news. All news must be real, current, and verifiable.
     - **Requirement:** Every news item **MUST** include a valid, **DIRECT** source link to the specific article (NOT the homepage URL).
     - **Format:** Compact style (Title + Source Link on Line 1, Summary on Line 2). Max 2 lines per item.
  4. Generate analysis using three distinct AI personas (**Strictly NO emojis allowed in the output**):
     - **Technical Analysis Master (ISTP):** Analyze volume/price, support/resistance, divergence, and "Sakata Goho" (酒田戰法) candlestick patterns. Warn of reversals. Be direct.
     - **Value Investing Master (ISTJ):** Evaluate financial history, intrinsic value, safety margin, and profit quality.
     - **Macro & Industry Master (INTJ):** Analyze interest rates, industry cycles, and geopolitical risks.
  5. Append the analysis and news to the HTML file (replace the `#text-analysis-report` div).
  6. Execute `git add report/ && git commit -m "Update analysis report" && git push` to upload the changes to GitHub.

# Gemini CLI Command Rule: video summary

## Description
當輸入 `video summary` 指令時，自動抓取最新的 YouTube 影片清單，並整理出影片中的財經議題與詳細內容。

## Trigger
- command: video summary

## Workflow Steps

1. **更新影片清單 (Update Video List)**
   - 執行 `python fetch_yt_list.py` 以更新 `videolist.md`。

2. **讀取與解析 (Read & Parse)**
   - 讀取 `videolist.md` 檔案。
   - 根據清單中的網址解析每則影片。

3. **內容整理 (Summarize)**
   - 列出每一部影片中提及的每一項財經議題。
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
