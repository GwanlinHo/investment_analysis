# Investment Analysis Automation

This is an investment assistance tool that combines **Python automation scripts** with **AI-powered analysis**. It is designed to automatically fetch data from the US and Taiwan stock markets (ETFs) and bond markets, calculate key technical indicators, generate K-line charts, and produce in-depth market insights and real-time news summaries with the help of an AI agent, ultimately delivering an easy-to-read comprehensive HTML analysis report. Of course, the frequency of execution and the data to be collected each time can be fully customized by the user.

# 投資分析自動化專案

這是一個結合 **Python 自動化腳本** 與 **AI 智慧分析** 的投資輔助工具。旨在自動抓取美股、台股 ETF 及債券市場數據，計算關鍵技術指標，繪製 K 線圖，並結合 AI 代理人生成深度市場觀點與即時新聞彙整，最終產出一份易於閱讀的 HTML 綜合分析報告。當然，一週要觸發多少次，以及每次要收集哪些資料，完全可以由使用者自行調整。

---

## 更新紀錄 (Changelog)

- **2026-04-11**:
  - **報告標籤系統擴充與分析優化**:
    - **CPI 標籤支援**：優化 `update_report.py` 數據提取邏輯，新增 `{{CPI}}` 標籤支援，確保分析內容能精確引用最新消費者物價指數數據。
    - **地緣政治風險分析**：在 AI 分析中引入地緣政治預警機制，針對 3 月 CPI 跳升與中東局勢提供多維度情境分析。
    - **數據精準度提升**：修復 AI 報告中數值單位的顯示問題，確保百分比與金額單位的正確映射。

- **2026-04-10**:
  - **報告數據注入與台股同步修復**:
    - **JSON 注入修復**：修正 `investment_analysis.py` 在渲染模板時未傳遞市場數據 JSON 的問題，並同步更新 `report_template.html` 以支援 Jinja2 變數，解決報告中技術圖表數據為空的 Bug。
    - **總經表格注入邏輯優化**：修正 `update_report.py` 僅能替換現有表格而無法處理初始占位符的邏輯，確保宏觀經濟指標能正確填入報告。
    - **台股數據同步確認**：解決台股加權指數數據抓取延遲問題，目前報告已完整包含昨（4/9）與今（4/10）的最新盤後數據。


- **2026-04-09**:
  - **數值精確度修復與自動化防護系統 (Anti-Hallucination System)**:
    - **重大幻覺修復**：修正 AI 將 VIX 技術指標欄位 `TR` (真實波幅) 誤認為 `Close` (收盤價) 導致的數據錯誤。
    - **標籤化引用機制**：更新 `GEMINI.md` 並修改 `update_report.py`，支援於 `ai.html` 中使用 `{{VIX}}`、`{{TAIEX}}` 等變數標籤。系統現在會在報告生成時自動從事實庫提取真實數值進行物理替換，徹底杜絕人為手寫數字錯誤。
    - **自動校驗攔截器**：於 `update_report.py` 導入「數值一致性檢查器」。系統現在會自動比對 AI 生成內容中的數字與數據庫事實，若偵測到異常偏差（如 VIX 數據為 21 但內容寫 60），將強制攔截更新流程並報錯。
    - **AI 數據上下文簡化**：新增 `ai_context.json` 生成邏輯，僅向 AI 提供過濾後的核心關鍵指標清單，降低 AI 讀取複雜 JSON 結構時的解析壓力。
    - **規範升級**：於 `GEMINI.md` 正式寫入「標籤化引用」與「禁止編造歷史高低點」準則。

- **2026-04-03**:
  - **新聞內容語言與安全防護機制**:
    - **強制翻譯準則**：更新 `GEMINI.md`，明確定義所有非中文來源的新聞必須翻譯為繁體中文，禁止直接複製英文摘要，確保報告內容的一致性。
    - **注入攔截機制**：於 `update_report.py` 中新增 `is_mostly_chinese` 語言檢查邏輯。若偵測到 `news.html` 或 `ai.html` 內容之英文字元佔比過高，系統將自動中止注入流程並報錯，有效攔截不合規內容。
    - **流程強化**：完善 AI 執行新聞搜尋後的彙整規範，要求生成後必須進行語系與時效性（7天內）的雙重核對。

- **2026-04-02**:
  - **系統 Bug 修復與時區校準**:
    - **時區轉換邏輯修正**：將 `investment_analysis.py` 中 naive 的 `utcnow()` 替換為 `now(datetime.timezone.utc)`，解決在特定時段執行時因 naive 對象轉換時區導致報告檔名日期錯誤（誤判為前一日）的問題。
    - **自動化數據同步增強**：優化了 `update_report.py` 的注入流程，確保在生成跨日報告時，`index.html` 與 `report/` 目錄下的歷史存檔能精確同步。

- **2026-03-29**:
  - **重大功能更新：籌碼分析系統**:
    - **台股三大法人追蹤**：整合 FinMind API，於 K 線圖新增第三層籌碼流向 (Flow) 面板，即時繪製投信、外資、自營商累計買賣超曲線，精確識別法人鎖碼與出貨訊號。
    - **美股籌碼指標整合**：新增空單比率 (Short Float %) 與補空天數 (Short Ratio) 欄位，並於圖表導入 OBV 能量潮曲線，捕捉大戶資金動能與量價背離。
    - **專業繪圖佈局優化**：實施「座標軸分離」設計（成交量座標位於左側，價格與籌碼位於右側），徹底解決數值重疊問題；採用 5:1:1 黃金比例配置。
    - **動態報表邏輯**：系統自動根據標的屬性切換顯示欄位，針對指數標的自動簡化圖表與表格內容，減少冗餘雜訊。
    - **籌碼判讀教學**：於報告末尾新增「籌碼分析判讀教學」區塊，提供系統性的技術判讀指南。

- **2026-03-28**:
  - **系統架構優化**:
    - **標的群組更名**：將原本的「主要指數」更名為「美股指數」，使分類更具語義化。
    - **權重平衡調整**：將「加權指數 (^TWII)」從美股指數群組移至「台股 ETF」群組首位，優化台股分析的視覺流向。
    - **導覽功能擴充**：於報告導覽列新增「財經節目」按鈕，串接外部 YouTube 分析平台 `yt_podcast_analysis`。

- **2026-03-17**:
  - **GEMINI.md 規範強化**: 
    - 新增 TAIEX 指數強制引用規則：強制要求 AI 在進行台灣分析前，必須先從 `technical_data.json` 提取當前加權指數，確保分析數據的連貫性。
    - 建立動態新聞日期校驗機制：要求 AI 必須根據執行當下的系統日期自動過濾超過 7 天的舊聞，並強制要求新聞標題須包含 (YYYY-MM-DD)。
  - **AI 報告結構優化**: 重構 `ai.html` 模板，改用簡潔的 `.persona` 區段結構，提升動態注入內容時的穩定性與營運效果。
  - **新聞數據精確化**: 全面更新並過濾 `news.html` 中的內容，確保 20 則新聞焦點完全符合當前執行週之真實市場動態。

---

## Live Demo (操作示範)

[![專案操作影片](https://img.youtube.com/vi/lfzpw7sPqhI/maxresdefault.jpg)](https://www.youtube.com/watch?v=lfzpw7sPqhI)

---

## Key Features

1.  **Multi-Market Data Tracking**: Supports tracking of US stock indices, popular Taiwan ETFs, individual stocks, and bond ETFs.
2.  **Advanced Chip Analysis (New!)**:
    *   **Taiwan Market**: Tracks net buy/sell data for the Three Institutional Investors (Foreign, Investment Trust, Dealer).
    *   **US Market**: Monitors Short Float % and Short Ratio to identify potential short squeeze opportunities.
    *   **Volume-Price Dynamic**: Integrates OBV (On-Balance Volume) to track professional money flow.
3.  **Automated Technical Indicator Calculation**:
    *   KD, BIAS, DMI, ADX, and Moving Averages.
4.  **Visual Chart Generation**: Automatically generates professional K-line charts with a dual-axis design (Volume on Left, Price/Chips on Right) to prevent data overlapping.
5.  **AI-Powered In-Depth Comprehensive Analysis**:
    *   Crow - Flow Sentinel: Specialized persona for chip analysis and sentiment monitoring.
    *   Atlas - Macro Strategist: Geopolitical risk and macroeconomic cycle interpretation.
6.  **Professional-Grade Report Style**:
    *   Strict No-Emoji Policy: No emojis are used in code logs or report content.
    *   Taiwan Stock Market Convention: Adopts the red-for-up, green-for-down K-line color convention.
7.  **Macroeconomic Indicator Monitoring**: Automatically tracks key US and Taiwan economic data.

## 主要功能

1.  **多市場數據追蹤**：支援追蹤美股指數、台股熱門 ETF、個股及債券 ETF。
2.  **進階籌碼分析 (新功能!)**：
    *   **台股市場**：追蹤三大法人（外資、投信、自營商）累計買賣超，掌握法人鎖碼動態。
    *   **美股市場**：監控空單比率 (Short Float %) 與補空天數 (Short Ratio)，識別潛在軋空風險。
    *   **量價動能**：整合 OBV 能量潮，追蹤大戶資金流向。
3.  **自動化技術指標計算**：
    *   包含 KD, BIAS, DMI, ADX, 以及各期移動平均線。
4.  **視覺化圖表生成**：自動繪製專業 K 線圖，採用座標軸分離設計（左側成交量、右側價格/籌碼），防止數值重疊。
5.  **AI 深度綜合分析**：
    *   Crow (籌碼哨兵)：專精於籌碼面流向與市場情緒監控。
    *   Atlas (宏觀策略師)：地緣政治風險與總經週期解讀。
6.  **專業級報告風格**：
    *   嚴格禁絕表情符號 (No-Emoji Policy)：確保報告輸出專業且簡潔。
    *   台股配色慣例：採用紅漲綠跌 K 線配色。
7. **總體經濟指標監控**：自動追蹤美台核心經濟數據 (GDP, CPI, PPI, M2, 失業率等)。

---

## Report Reading Guide: Chip Analysis

### 1. Taiwan Flow (Three Institutional Investors)
*   **Red Line (Investment Trust)**: Swing traders. Rising line indicates "Locked-in" stocks with strong momentum.
*   **Blue Line (Foreign Investor)**: Long-term trend. Defines the valuation ceiling for weighted stocks.
*   **Green Line (Dealer)**: Short-term speculators and hedging activities.

### 2. US Sentiment Indicators
*   **Short Float %**: Percentage of shares shorted. Values over 15% signal high bearish sentiment and potential Short Squeeze.
*   **OBV (On-Balance Volume)**: Grey/Blue line in the 3rd panel. Rising OBV during price consolidation indicates accumulation by big money.

---

## ⚠️ Disclaimer
The reports generated by this project are for research and reference purposes only and do not constitute any investment advice. Financial markets are unpredictable; please conduct your own thorough risk assessment before investing.

## ⚠️ 免責聲明
本專案生成的報告僅供研究與參考，不構成任何投資建議。金融市場變化莫測，投資前請務必自行審慎評估風險。
