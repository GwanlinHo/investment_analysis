# 增強價值投資分析能力計畫 (Enhanced Value Investing Analysis Plan)

## 1. 目標 (Objective)
解決目前「價值投資大師」因缺乏個股基本面數據，導致分析流於總體經濟層面的問題。目標是透過程式化手段獲取個股的關鍵財務指標（如 PE, ROE, 現金流等），讓 AI 能依據巴菲特/蒙格的價值投資邏輯進行具體的個股分析。

## 2. 執行策略 (Execution Strategy)
採用「Python 腳本擴充」搭配「AI 指令優化」的雙軌策略。利用 `yfinance` 庫直接獲取結構化財務數據，而非依賴不穩定的自然語言搜尋。

## 3. 詳細步驟 (Step-by-Step Plan)

### 階段一：資料獲取與處理 (Data Acquisition & Processing)
- [x] **Step 1.1: 擴充 `investment_analysis.py`**
    - 新增 `get_fundamental_data(ticker)` 函式。
    - 使用 `yf.Ticker(symbol).info` 獲取以下關鍵欄位：
        - **估值**: `trailingPE`, `forwardPE`, `priceToBook`, `enterpriseValue`
        - **獲利**: `returnOnEquity` (ROE), `grossMargins`, `operatingMargins`
        - **股利**: `dividendYield`, `payoutRatio`
        - **現金流**: `freeCashflow`
        - **基本資料**: `sector`, `industry`
    - 處理 ETF 與個股的差異（ETF 可能缺乏部分財報數據，需側重殖利率與持股類別）。
- [x] **Step 1.2: 整合數據至報告結構**
    - 修改 `main` 函式，將抓取到的基本面數據彙整到 `summary_data_list` 或新的 `fundamental_data` 結構中。
    - 確保這些數據能以文字或 JSON 格式傳遞給最後生成分析報告的 Prompt。

### 階段二：AI 指令與記憶優化 (AI Prompt Engineering)
- [x] **Step 2.1: 更新 `GEMINI.md`**
    - 修改「價值投資大師 (ISTJ)」的角色指令：
        - 強制要求引用具體的財務數據（如 "ROE 為 25%"）。
        - 加入巴菲特/蒙格的分析框架關鍵詞：護城河 (Moat)、安全邊際 (Margin of Safety)、能力圈 (Circle of Competence)。
    - 在 Prompt 中明確區分「個股」與「ETF」的分析邏輯。

### 階段三：報告呈現優化 (Report Presentation)
- [x] **Step 3.1: 調整 HTML 模板**
    - (選用) 在 HTML 報告中新增一個「基本面數據摘要」的小表格，或直接將數據融入 AI 的文字分析中（目前傾向後者，保持版面簡潔）。
    - 確保 Prompt 收到數據後，是「解讀」數據而非「列出」數據。

## 4. 驗證標準 (Verification Criteria)
1.  **數據準確性**：執行腳本後，能成功印出台積電 (2330.TW) 或美股 (如 AAPL) 的 PE、ROE 等數據，且無程式錯誤。
2.  **報告內容**：生成的 HTML 報告中，價值投資大師的區塊必須包含：
    - 具體的數字佐證（例如：「本益比 15 倍，低於歷史平均」）。
    - 基於財務數據的質性判斷（例如：「高 ROE 顯示具備護城河」）。
    - 不再充斥重複的總經廢話。

## 5. 工作管理機制 (State Management)
為了確保跨天或中斷後能順利接續，將使用此文件 `PLAN_value_investing.md` 作為狀態追蹤。
- 每個步驟完成後，會在 Checkbox 打勾 `[x]`。
- 每次對話開始時，先讀取此計畫檔，確認目前進度。

---
**Current Status:** All steps completed. Ready for verification run.
