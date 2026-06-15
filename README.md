# Investment Analysis Automation

This is an investment assistance tool that combines **Python automation scripts** with **AI-powered analysis**. It is designed to automatically fetch data from the US and Taiwan stock markets (ETFs) and bond markets, calculate key technical indicators, generate K-line charts, and produce in-depth market insights and real-time news summaries with the help of an AI agent, ultimately delivering an easy-to-read comprehensive HTML analysis report. Of course, the frequency of execution and the data to be collected each time can be fully customized by the user.

# 投資分析自動化專案

這是一個結合 **Python 自動化腳本** 與 **AI 智慧分析** 的投資輔助工具。旨在自動抓取美股、台股 ETF 及債券市場數據，計算關鍵技術指標，繪製 K 線圖，並結合 AI 代理人生成深度市場觀點與即時新聞彙整，最終產出一份易於閱讀的 HTML 綜合分析報告。當然，一週要觸發多少次，以及每次要收集哪些資料，完全可以由使用者自行調整。

---

## 更新紀錄 (Changelog)

- **2026-06-15 (v2.2)**:
  - **修正缺失判定誤觸發中止 (False Abort Fix)**:
    - **問題**：v2.1 缺失判定以「群組內有效日的最大值」為基準，週末與週一早晨，群組內持續交易的黃金期貨 (`GC=F`) 與時區領先的日經 (`^N225`) 已有比美股股指更新的日期，把群組基準拉高，導致正常休市的美股股票指數 (`^GSPC`/`^SOX`/`^DJI`/`^IXIC` 等，最新仍為上週五) 被誤判為「最新交易日缺失」，累積超過 3 個而**誤觸發中止 — 每週一的報告都會被誤擋**。
    - **修正**：缺失判定改採絕對標準 — 僅當「完全無有效收盤」或「最新資料距執行日超過 5 個日曆日 (長期停更，涵蓋一般週末與短連假)」才計為缺失；移除「落後群組基準即缺失」。僅落後群組基準但仍在期限內者不計缺失，續由逐列日期標註誠實呈現其實際資料日。

- **2026-06-14 (v2.1)**:
  - **資料完整性把關 (Data Integrity Gate)**:
    - **策略**：yfinance 取不到資料時改由 FinMind 補救；兩者皆失敗時依缺失標的數分流處理，避免殘缺或誤導性報告被上傳。
    - **缺失計數 (以標的為單位)**：某標的取不到「最近交易日」收盤 (台股 yfinance 失敗且 FinMind 亦失敗 / 美股 yfinance 失敗且無備援) 即計 1 個缺失。
    - **缺 0~2 個**：缺失標的整列數值以 `n/a` 呈現 (新增 `format_na_row`)，並標示「[!] API 無資料」，照常產生報告；使用者可一眼辨識數據異常源於 API 取不到。
    - **缺 3 個(含)以上**：`investment_analysis.py` 印出 `[ABORT]` 並以非零碼結束、**不產生報告、不更新 technical_data.json**，從源頭杜絕殘缺上傳，保留前一份報告。
    - **三道防線**：(1) py 中止不產出；(2) CLAUDE.md 規範工作流在 py 非零退出時終止、不 push；(3) `update_report.py` 於 technical_data.json 非當日更新時拒絕注入。
    - **備援強化**：`get_stock_data` 在 yfinance 完全失敗時，對台股標的改用 FinMind 全量抓取 (先前僅補當日缺漏，yfinance 全失敗會直接跳過)。

- **2026-06-13 (v2.0)**:
  - **台股資料源 FinMind 補洞 (TW Data Source Fallback)**:
    - **問題**：Yahoo Finance 對台股 ETF/指數的當日收盤回補常延遲跨日 (Close 為 NaN)，而 cron 每日 07:00 執行，結構性拿不到最新台股資料，導致報表台股區塊長期可能呈現前一交易日的過期數據、漏失當日行情 (例：國泰費半 ETF 6/12 實漲 6.6% 卻被漏掉)。
    - **修正**：`investment_analysis.py` 新增 `fill_latest_from_finmind`，於 `get_stock_data` 抓取 Yahoo 後，對台股標的 (`^TWII`／`.TW`／`.TWO`) 以 FinMind (本土源) 補上 Yahoo 缺漏的最新交易日 OHLC。僅補 Yahoo 缺漏列、不覆蓋既有有效值；近期還原價≈原始價，補在尾端口徑一致。FinMind 失敗時由 v1.9 的表頭基準日與逐列標註機制防呆。
    - **驗證**：FinMind 對一般 ETF、上櫃債券 ETF (`.TWO`)、槓桿 ETF (`00631L`)、指數 (`TAIEX`) 涵蓋完整，且指數值與 Yahoo 一致。

- **2026-06-13 (v1.9)**:
  - **交易日錯位修正 (Last Trading Date Bug Fix)**:
    - **問題**：表頭「最後交易日」原以群組內所有標的（含尾端 NaN 行）的 `df.index[-1]` 取最大值，當僅少數標的（如台積電）已回補最新交易日、而多數標的（加權指數、ETF）尚未回補時，表頭日期會被拉高，與各列實際呈現的前一交易日數據錯位（例：表頭標 6/12，但加權指數實為 6/11 的數據）。
    - **修正**：`investment_analysis.py` 改以各標的「最後有效數據日」（排除尾端 NaN）的**最大值**（即報告涵蓋到的最新交易日）作為群組基準交易日，取代原本含 NaN 的 `df.index[-1]`；並於 `format_data_row` 比對每列實際資料日，對尚未回補最新日的標的於該列標註「[!] 資料 MM/DD」，杜絕靜默呈現過期數據。

- **2026-06-03 (v1.8)**:
  - **系統優化 (System Optimization)**:
    - **強化數據注入標籤**：修改 `update_report.py` 以支援 `TSMC`、`ISM_PMI` 與 `OIL_PRICE` 等新標籤，提升 AI 分析的數值精確度與可讀性。
  - **每日分析報告 (Daily Analysis Update)**:
    - **數據更新**：更新 `macro_cache.json` 至 2026 年 5 月份實績，包括 ISM 製造業指數升至 54.0。
    - **Computex 專題分析**：AI 分析深度整合 Computex 2026 與黃仁勳加碼投資台灣之利多，並評估地緣政治引發的能源供應危機。

- **2026-05-15 (v1.7)**:
  - **總經數據自動化校正 (Macro Data Bug Fix)**:
    - **修復查找區域錯誤**：修正 `update_report.py` 中 `US10Y` 與 `US3M` 指標的查找邏輯，將區域來源由不存在的 `US10Y`/`US3M` 改回 `US_MACRO`，確保事實庫中的殖利率標籤能被正確載入。
  - **投資報告更新 (Daily Analysis Update)**:
    - **同步最新數據**：更新 `macro_cache.json` 包含 5 月份最新失業救濟、美元指數、美債殖利率與台股融資餘額。
    - **AI 分析深度強化**：針對 Kevin Warsh 接任聯準會主席與台積電 2026 技術論壇釋出的埃米世代製程規劃進行深度多維度評析。

- **2026-04-25 (v1.6)**:
  - **宏觀指標標籤映射擴充 (Macro Indicator Tag Update)**:
    - **新增多項標籤映射**：在 `update_report.py` 中新增 `{{RETAIL_SALES}}`、`{{GDP}}`、`{{PPI}}`、`{{UNEMPLOYMENT_RATE}}` 及 `{{NONFARM_PAYROLLS}}` 等宏觀指標的自動映射，解決 AI 分析中變數名稱未被正確替換的問題。
    - **自動化測試驗證**：已驗證 `index.html` 中的「零售銷售」等變數能正確替換為事實庫數值。

- **2026-04-18 (v1.5)**:
  - **AI 分析標籤擴充 (AI Tag Update)**:
    - **新增融資單日變動標籤**：修改 `update_report.py` 中的 `get_data_context` 函式，使其能從事實庫中提取「融資單日變動」數據並對應至 `{{MARGIN_CHANGE}}` 標籤。
    - **更新強制標籤列表**：於 `GEMINI.md` 中將 `{{MARGIN_CHANGE}}` 加入 Tag-Based Substitution 強制使用列表中，以解決 AI 分析報告中數字顯示不正確或出現幻覺的問題。

- **2026-04-17 (v1.4)**:
  - **資料顯示強健性優化 (Data Robustness Update)**:
    - **修正區塊日期邏輯**：重構 `investment_analysis.py` 中的 `process_stock_group` 函式，將區塊日期選取邏輯由「首個標的日期」改為「群組內所有標的之最大日期」，解決因單一指標（如加權指數）更新延遲導致整個市場區塊顯示日期落後的問題。
  - **AI 分析敘事規範升級**:
    - **禁止固定模板**：於 `GEMINI.md` 加入 `Dynamic Narrative Rule`，嚴禁 AI 使用固定句式，確保分析內容具備自然流動的專業敘事感。
    - **強制變數描述**：實施 `Variable Description Mandate`，要求所有標籤變數（如 {{VIX}}）必須附帶明確指標名稱描述，消除僅有數字而無主詞的表達缺陷。
    - **即時內容修正**：手動重構 `ai.html`，以身作則展示新版敘事風格，提升報告閱讀體驗。

- **2026-04-13 (v1.3)**:
  - **開發流程規範強化 (Workflow Standard Update)**:
    - **合併與同步要求**：於 `GEMINI.md` 中新增明確規範，要求在 feature branch 完成修改、驗證並獲得使用者同意後，必須執行合併至 `main`、推送至遠端倉庫，並將本地環境切換回 `main` 分支，確保開發環境的一致性與穩定性。

- **2026-04-13 (v1.2)**:
  - **事實校驗系統升級**:
    - **動態事實庫擴展**：修改了 `update_report.py`，使校驗系統能夠自動載入 `macro_cache.json` 中所有的數值指標作為分析事實庫，大幅提升校驗靈活性。
    - **數值完整性優化**：解決了 AI 在引用台積電營收、毛利率與油價目標等具體數據時被攔截的問題，確保專業分析與數據一致性能並存。
    - **地緣政治深度追蹤**：針對「霍爾木茲海峽封鎖」引發的能源、金價與全球供應鏈風險，由 Atlas 與 Crow 角色發布了針對性的預警報告。

- **2026-04-12 (v1.1)**:
  - **AI 分析敘事引擎優化**:
    - **消除模板感**：重新設計了 `ai.html` 的生成邏輯，徹底解決數據標籤（如 {{TAIEX}}）在分析內容中出現語句不通順的問題，改以更自然、更具洞察力的專業分析師口吻。
    - **全循環分析驗證**：在 `feature/full-analysis-cycle-fix` 分支中完成了技術數據、總經數據、新聞抓取與 AI 分析的完整生成測試，確保報告的高品質與邏輯一致性。
    - **地緣政治風險更新**：特別針對荷姆茲海峽的通行費狀況、船隻滯留排隊與通膨影響進行了跨領域深度分析。

- **2026-04-12 (v1.0)**:
  - **開發流程規範化與 GEMINI.md 翻譯**:
    - **新增開發流程規定**：在 `GEMINI.md` 中加入強制性開發流程，要求所有功能、格式或規則的修改必須在獨立分支進行，並在通過完整測試且取得使用者同意後方可合併至 `main`。
    - **內容完整翻譯**：將 `GEMINI.md` 中的「數字引用與幻覺防禦機制」等中文區塊翻譯為英文，以確保專案規則的一致性。
  - **資料清理系統與 Regex 穩定性修正**:
    - **新增 prune_manager.py**：實作自動清理功能，報表目錄 `report/` 僅保留最近 30 份 HTML 報表；`technical_data.json` 中的市場歷史序列限制為最近 120 個交易日，有效釋放硬碟空間並防止資料檔案無序膨脹。
    - **修正 update_report.py**：修復正則表達式匹配邏輯，改用非貪婪模式（Non-greedy）匹配 AI 分析區塊，避免在注入 AI 觀點時意外刪除或毀壞前端技術指標與 K 線圖區塊。
    - **自動化流程整合**：將清理流程整合至報表更新階段，實現「分析完畢即刻修剪」的維護機制。

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
