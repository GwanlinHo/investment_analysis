# Investment Analysis Automation

This is an investment assistance tool that combines **Python automation scripts** with **AI-powered analysis**. It is designed to automatically fetch data from the US and Taiwan stock markets (ETFs) and bond markets, calculate key technical indicators, generate K-line charts, and produce in-depth market insights and real-time news summaries with the help of an AI agent, ultimately delivering an easy-to-read comprehensive HTML analysis report. Of course, the frequency of execution and the data to be collected each time can be fully customized by the user.

# 投資分析自動化專案

這是一個結合 **Python 自動化腳本** 與 **AI 智慧分析** 的投資輔助工具。旨在自動抓取美股、台股 ETF 及債券市場數據，計算關鍵技術指標，繪製 K 線圖，並結合 AI 代理人生成深度市場觀點與即時新聞彙整，最終產出一份易於閱讀的 HTML 綜合分析報告。當然，一週要觸發多少次，以及每次要收集哪些資料，完全可以由使用者自行調整。

---

## 更新紀錄 (Changelog)

- **2026-03-29**:
  - **重大功能更新：籌碼分析系統 1.0**:
    - **台股三大法人追蹤**：整合 FinMind API，於 K 線圖新增第三層籌碼流向 (Flow) 面板，即時繪製 **🔴投信、🔵外資、🟢自營商** 累計買賣超曲線，精確識別法人鎖碼與出貨訊號。
    - **美股籌碼指標整合**：新增 **空單比率 (Short Float %)** 與 **補空天數 (Short Ratio)** 欄位，並於圖表導入 **OBV 能量潮** 曲線，捕捉大戶資金動能與量價背離。
    - **專業繪圖佈局優化**：實施「座標軸分離」設計（成交量座標位於左側，價格與籌碼位於右側），徹底解決數值重疊問題；採用 5:1:1 黃金比例配置。
    - **動態報表邏輯**：系統自動根據標的屬性切換顯示欄位，針對指數標的自動簡化圖表與表格內容，減少冗餘雜訊。
    - **籌碼判讀教學**：於報告末尾新增「籌碼分析判讀教學」區塊，提供系統性的技術判讀指南。
  - **系統修復與規範合規**:
    - 恢復被誤刪的 **ADX, +DI, -DI** 技術指標。
    - 全面移除所有表情圖示 (Emoji)，確保輸出符合專案專業風格。
    - 強化 `macro_cache.json` 的 **Upsert 邏輯**，防止歷史總經數據遭覆蓋遺失。

- **2026-03-28**:
  - **系統架構優化**:
    - **標的群組更名**：將原本的「主要指數」更名為「美股指數」，使分類更具語義化。
    - **權重平衡調整**：將「加權指數 (^TWII)」從美股指數群組移至「台股 ETF」群組首位，優化台股分析的視覺流向。
    - **導覽功能擴充**：於報告導覽列新增「財經節目」按鈕，串接外部 YouTube 分析平台 `yt_podcast_analysis`。

- **2026-03-21**:
  - **數據更新與分析生成**: 
    - 納入最新台灣與美國數據：2 月外銷訂單年增 23.8%、融資餘額攀升至 3,997.7 億、2 月失業率維持 3.29% 低點。
    - 針對紅海局勢再度緊張與中東供應鏈風險，由 Atlas 啟動風險預警，分析對全球運費與二次通膨的潛在影響。
    - Kenji 偵測到加權指數（33,543點）出現 KD 高位回落與 MACD 負柱狀體擴大，發出技術性回檔與乖離修正訊號。
    - Crow 警告融資餘額過高可能引發之多殺多風險，建議嚴格控管槓桿。
  - **系統同步與報告注入**: 完成 20 則權威新聞 (70% 全球 / 30% 台灣) 與 AI 綜合分析之注入，並同步更新 `index.html`。

- **2026-03-20**:
  - **數據更新與分析生成**: 
    - 納入最新美國總體經濟數據：2 月 PPI 年增率 3.4%、Q4 GDP 修正值 0.7%、及截至 3/14 之初領失業金人數 20.5 萬。
    - 針對中東伊朗衝突情境，啟動 Atlas 之「地緣政治與供應鏈警告協議」，分析對能源價格 ($166/bbl) 及全球通膨之連鎖反應。
    - 更新 20 則即時新聞焦點，涵蓋全球宏觀、台股科技、地緣政治與能源供應，並修正加權指數與台積電之實質市場數據。
  - **系統同步與報告注入**: 完成 `news.html` 與 `ai.html` 之動態注入，並同步更新根目錄之 `index.html`。

- **2026-03-17**:
  - **GEMINI.md 規範強化**: 
    - 新增 **TAIEX 指數強制引用規則**：強制要求 AI 在進行台灣分析前，必須先從 `technical_data.json` 提取當前加權指數，確保分析數據的連貫性。
    - 建立 **動態新聞日期校驗機制**：捨棄寫死日期，要求 AI 必須根據執行當下的 **系統日期** 自動過濾超過 7 天的舊聞，並強制要求新聞標題須包含 `(YYYY-MM-DD)`。
  - **AI 報告結構優化**: 重構 `ai.html` 模板，改用簡潔的 `.persona` 區段結構，提升動態注入內容時的穩定性與營運效果。
  - **新聞數據精確化**: 全面更新並過濾 `news.html` 中的內容，確保 20 則新聞焦點完全符合**當前執行週**之真實市場動態，並落實自動過濾過時資訊之邏輯。

- **2026-03-15**:
  - **總經數據遺失修復**: 修正 `macro_cache.json` 在更新過程中遭覆蓋而非合併的問題。
  - **數據還原機制**: 從 `invest_analysis_20260312.html` 成功還原了 23 項美國與台灣的關鍵總經指標。
  - **自動自我修復 (Self-Healing)**: 在 `update_report.py` 中新增 `MacroParser` 與自動還原邏輯。若偵測到快取指標數量異常（少於 5 個），程式將自動從現有報告中提取歷史數據進行填補，防止未來因抓取失敗導致資料斷層。
  - **強健性注入邏輯**: 升級 HTML 注入方式，支援使用 Regex 精確匹配並覆蓋已存在的總經表格 (`id="us-macro-table"` 等)，解決報告生成後無法再次更新的問題。

- **2026-03-14**:
  - **部分分析執行**: 由於無法檢索即時新聞，本次分析未能產生「新聞焦點」和完整的「AI綜合分析」。報告是基於已有的宏觀經濟數據和技術指標生成的精簡版。
  - **數據更新**: 更新了部分美國和台灣的宏觀經濟數據。

- **2026-03-10**:
  - **新增語音朗讀功能**: 為「週報焦點」與「AI 深度分析」區塊加入 Web Speech API 語音朗讀功能，並針對 iOS 與 Android 平台優化台灣腔調 (zh-TW) 及預設英文字音選取。
  - **模板結構優化**: 更新 `templates/report_template.html` 並強化 `update_report.py` 的注入邏輯，使用 HTML 註釋錨點 (`anchor`) 確保動態注入內容時不會破壞 TTS 控制按鈕與佈局。

- **2026-03-07**:
  - **新聞卡片巢狀顯示修復**: 修改 `update_report.py` 注入新聞的邏輯。藉由自動移除 `news.html` 中可能重複的 `id="weekly-news-focus"` 屬性，解決報告中因重複套用 CSS 而導致「卡片包著卡片」的多層錯覺問題。

- **2026-03-06**:
  - **黃金價格改為追蹤GC=F**: 原本追蹤 `^XAU` ，後來發現這是礦業股價，所以改為追蹤黃金期貨價格 `GC=F`，這樣比較能夠觀察到風險趨避。 
- **2026-03-03**:
  - **CSS 樣式修正**: 修復 `update_report.py` 在注入內容時會誤刪外層 `div` ID 容器的問題，確保 `#weekly-news-focus` 與 `#ai-analysis-report` 的背景樣式能正確顯示。
  - **邏輯優化**: 使用 `re.sub` 配合 lambda 函數進行安全注入，保留 HTML 結構完整性。
  - **流程驗證**: 建立 `fix/ai-report-styling-injection` 分支進行端到端測試，確認從數據抓取到 AI 注入的完整流程運作正常。

- **2026-03-01**:
  - **規範更新 (GEMINI.md)**: 全面將 `GEMINI.md` 翻譯為英文以確保指令精確性。
  - **功能增強**: 擴充新聞收集至 20 則，並納入 BBC 與 CNN 作為權威來源。
  - **預警邏輯**: 強化 Atlas (宏觀策略師) 角色，新增「地緣政治預警協定 (Geopolitical Warning Protocol)」，針對中東局勢、能源供應與全球航運進行前瞻性二階影響推演。
  - **注入流程優化**: 升級 `update_report.py` 的強健性檢查機制。新增 `news.html` 與 `ai.html` 的**時效性 (5分鐘內) 與內容檢查**，防止將過期或空白數據注入正式報告中。
- **2026-02-27**:
  - **規範更新**: 於 `GEMINI.md` 中明確化 `README.md` 的更新觸發條件，僅限修改 Source Code 或 `GEMINI.md` 本身時才執行變更紀錄。
- **2026-02-26**:
  - 使用 `technical_data.json` 存放技術分析數據，不再直接寫入報告中，減輕AI再次分析報告時的負擔。
- **2026-02-25**: 
  - 修正市場狀態判定邏輯：改善 `yf.download` 呼叫參數並改以週末判定休市，解決台股與美股誤報「休市中」的問題。
  - 調整專案文件：將 `GEMINI.md` 全面翻譯為英文，並將 `README.md` 的更新紀錄搬移至檔頭以提升可讀性。

---

## Live Demo (操作示範)

[![專案操作影片](https://img.youtube.com/vi/lfzpw7sPqhI/maxresdefault.jpg)](https://www.youtube.com/watch?v=lfzpw7sPqhI)

---

## Key Features

1.  **Multi-Market Data Tracking**: Supports tracking of US stock indices (e.g., S&P 500, Philadelphia Semiconductor Index), popular Taiwan ETFs (e.g., 0050, 0056), individual stocks, and bond ETFs.
2.  **Advanced Chip Analysis (New!)**:
    *   **Taiwan Market**: Tracks net buy/sell data for the **Three Institutional Investors** (Foreign, Investment Trust, Dealer).
    *   **US Market**: Monitors **Short Float %** and **Short Ratio** to identify potential short squeeze opportunities.
    *   **Volume-Price Dynamic**: Integrates **OBV (On-Balance Volume)** to track professional money flow.
3.  **Automated Technical Indicator Calculation**:
    *   **KD (Stochastic Oscillator)**: To identify overbought/oversold zones and trend strength.
    *   **Bias Ratio (BIAS)**: Calculates 5-day, 20-day, and 60-day BIAS to determine if the stock price is overheated or oversold.
    *   **DMI & ADX**: To determine the direction and strength of bullish/bearish trends.
    *   **Moving Averages (MA)**: Calculates 5MA, 20MA, and 60MA.
4.  **Visual Chart Generation**: Automatically generates professional K-line charts with a **dual-axis design** (Volume on Left, Price/Chips on Right) to prevent data overlapping. Includes aUS Treasury yield curve chart.
5.  **AI-Powered In-Depth Comprehensive Analysis**:
    *   **Crow - Flow Sentinel**: Specialized persona for chip analysis and sentiment monitoring.
    *   **Atlas - Macro Strategist**: Geopolitical risk and macroeconomic cycle interpretation.
6.  **Professional-Grade Report Style**:
    *   **Strict No-Emoji Policy**: No emojis are used in code logs or report content.
    *   **Taiwan Stock Market Convention**: Adopts the red-for-up, green-for-down K-line color convention.
7.  **Macroeconomic Indicator Monitoring**: Automatically tracks key US and Taiwan economic data (GDP, CPI, PPI, M2, Unemployment, etc.).

## 主要功能

1.  **多市場數據追蹤**：支援追蹤美股指數（如 S&P 500, 費半）、台股熱門 ETF（如 0050, 0056）、個股及債券 ETF。
2.  **進階籌碼分析 (新功能!)**：
    *   **台股市場**：追蹤**三大法人**（外資、投信、自營商）累計買賣超，掌握法人鎖碼動態。
    *   **美股市場**：監控**空單比率 (Short Float %)** 與 **補空天數 (Short Ratio)**，識別潛在軋空風險。
    *   **量價動能**：整合 **OBV 能量潮**，追蹤大戶資金流向。
3.  **自動化技術指標計算**：
    *   **KD 指標**：判斷超買/超賣區間與趨勢強弱。
    *   **乖離率 (BIAS)**：計算 5日、20日、60日 乖離，判斷股價是否過熱或超跌。
    *   **DMI & ADX**：判斷多/空趨勢方向與強度。
    *   **移動平均線 (MA)**：計算 5MA, 20MA, 60MA。
4.  **視覺化圖表生成**：自動繪製專業 K 線圖，採用**座標軸分離設計**（左側成交量、右側價格/籌碼），防止數值重疊。包含美國公債殖利率曲線圖。
5.  **AI 深度綜合分析**：
    *   **Crow (籌碼哨兵)**：專精於籌碼面流向與市場情緒監控。
    *   **Atlas (宏觀策略師)**：地緣政治風險與總經週期解讀。
6.  **專業級報告風格**：
    *   **嚴格禁絕表情符號 (No-Emoji Policy)**：確保報告輸出專業且簡潔。
    *   **台股配色慣例**：採用紅漲綠跌 K 線配色。
7. **總體經濟指標監控**：自動追蹤美台核心經濟數據 (GDP, CPI, PPI, M2, 失業率等)。

---

## Authoritative Data Sources

### 1. Macroeconomic Data
*   **United States (US)**: BEA, BLS, U.S. Census Bureau, Federal Reserve, Yahoo Finance.
*   **Taiwan**: NDC (景氣對策信號), MOEA (外銷訂單), Central Bank (M1B/M2), FSC, DGBAS (失業率/投資), TWSE (融資融券).

### 2. Market and Institutional Data
*   **Market Data**: Yahoo Finance (yfinance) API.
*   **TW Institutional Flow**: **FinMind API** (Taiwan Stock Institutional Investors Buy/Sell).

---

## Report Reading Guide: Chip Analysis

### 1. Taiwan Flow (Three Institutional Investors)
*   <strong style="color: #e53935;">Red Line (Investment Trust)</strong>: Swing traders. Rising line indicates "Locked-in" stocks with strong momentum.
*   <strong style="color: #1976d2;">Blue Line (Foreign Investor)</strong>: Long-term trend. Defines the valuation ceiling for weighted stocks.
*   <strong style="color: #43a047;">Green Line (Dealer)</strong>: Short-term speculators and hedging activities.

### 2. US Sentiment Indicators
*   **Short Float %**: Percentage of shares shorted. > 15% signals high bearish sentiment and potential **Short Squeeze**.
*   **OBV (On-Balance Volume)**: Grey/Blue line in the 3rd panel. Rising OBV during price consolidation indicates accumulation by big money.

---

## ⚠️ Disclaimer
The reports generated by this project are for research and reference purposes only and do not constitute any investment advice. Financial markets are unpredictable; please conduct your own thorough risk assessment before investing.

## ⚠️ 免責聲明
本專案生成的報告僅供研究與參考，不構成任何投資建議。金融市場變化莫測，投資前請務必自行審慎評估風險。
