# Investment Analysis Automation

This is an investment assistance tool that combines **Python automation scripts** with **AI-powered analysis**. It is designed to automatically fetch data from the US and Taiwan stock markets (ETFs) and bond markets, calculate key technical indicators, generate K-line charts, and produce in-depth market insights and real-time news summaries with the help of an AI agent, ultimately delivering an easy-to-read comprehensive HTML analysis report. Of course, the frequency of execution and the data to be collected each time can be fully customized by the user.

# 投資分析自動化專案

這是一個結合 **Python 自動化腳本** 與 **AI 智慧分析** 的投資輔助工具。旨在自動抓取美股、台股 ETF 及債券市場數據，計算關鍵技術指標，繪製 K 線圖，並結合 AI 代理人生成深度市場觀點與即時新聞彙整，最終產出一份易於閱讀的 HTML 綜合分析報告。當然，一週要觸發多少次，以及每次要收集哪些資料，完全可以由使用者自行調整。

---

## 更新紀錄 (Changelog)

- **2026-08-16 (v2.9)**:
  - **指標速覽浮動面板 (Floating Overview Panel)**:
    - **需求**：使用者希望在報告開啟時能一眼掃過總經、技術面、情緒面的近期變化，不必逐區捲動；面板需可關閉、可再次叫出，且資料全部取自報告既有的收集結果。
    - **設計**：`templates/report_template.html` 新增浮動面板，分三區——**總經**（近 30 日有更新的指標，現值／前值／發布日，預設 6 項）、**技術**（核心 6 檔標的的 1／5／20 日漲跌與 KD、MACD、20MA、乖離、ADX 訊號）、**情緒**（VIX 及其 60 日區間百分位、HYG 風險偏好、外資／投信買賣超與連買連賣天數、融資餘額）。三區皆可展開為完整清單，頂部另有一行規則產生的重點摘要。桌機為右下浮動卡、手機為底部抽屜。
    - **休市標示**：面板頂端標示「資料截至　台股 YYYY-MM-DD｜美股 YYYY-MM-DD」，若與報告日期不同（週末、國定假日、08:00 retry）會以紅字註明該市場休市——避免把上一交易日的收盤誤讀為當日行情（報告本體各區塊原本就有休市標示，面板是第一個跳出來的畫面，不能漏）。
    - **顯示行為**：`DOMContentLoaded` 即渲染（JSON 資料標籤位於 `<head>`，不必等 4MB 的 K 線圖），每份新報告自動跳出一次（以報告日期為 localStorage 記憶鍵），關閉後可用右下「速覽」按鈕或再次點擊叫出，支援 Esc 關閉。localStorage 不可用時（file:// 或隱私模式）自動降級為每次跳出。
    - **無伺服器端注入**：面板置於 `.container` 之外、`</body>` 之前，完全避開 `update_report.py` 的四組 DOTALL 正則注入區；每一格數值皆由前端從 `<script type="application/json">` 標籤即時計算，因此對已注入報告重跑 `update_report.py` 不會影響面板（等冪）。
  - **RWD 補強 (矮視窗)**:
    - 以 8 種視窗實測 (320 / 390 / 430 / 844x390 橫向 / 768 / 1024 / 1366 / 1920)：面板皆不超出視窗、無頁面或表格橫向溢出、按鈕不重疊。
    - 橫向手機 (844x390) 原本內容區僅 222px、約兩列可見，新增 `max-height: 500px` 媒體查詢壓縮標題列/摘要/頁尾留白並放寬高度上限，內容區提升至 289px。
  - **面板調整 (依使用者回饋)**:
    - **手機版改為浮動視窗**：原本滿版貼齊螢幕，改為左右與下方各留 12px、四角圓角，視覺上明確是「浮在報告之上的視窗」而非頁面區塊。
    - **公債殖利率固定依 3M -> 10Y -> 30Y 排列**：原本與其他指標一起按「最近更新」排序會被打散，看不出曲線形狀。三檔固定連續排在總經區最前面，並在最短天期那列標示曲線狀態（正常／平坦／倒掛，含利差 bps），判讀標準對齊 CLAUDE.md 中 Atlas 的殖利率監控規則 (利差 < 25bps 為平坦、< 0 為倒掛)。預設顯示改為「殖利率三檔 + 最近更新 5 項」。
  - **面板精簡 (依使用者回饋：預設資訊量減半)**:
    - 預設列數由 27 降為 **15**（總經 6 / 技術 4 / 情緒 3 / 基本面 2），其餘 80 列全部收進「展開全部」（展開後共 95 列）。
    - 技術面預設標的由 6 檔縮為 4 檔（加權指數、台積電、標普 500、費城半導體）；情緒面預設只留 VIX、外資買賣超（台積電）、融資餘額，HYG 與投信買賣超移入展開區；基本面預設 2 檔。
    - 移除冗字：備註本身已含資料月份與發布日，當日更新時不再重複標「今日更新」，僅在隔一天以上才顯示「N 日前更新」。
    - 預設列數集中於 `CORE`、`MACRO_DEFAULT`、`FUND_DEFAULT` 三個常數，日後調整不必改邏輯。
  - **總經歷史紀錄 (`macro_history.json` / `macro_history.py`)**:
    - **問題**：`macro_cache.json` 只保存每個指標的最新值，面板無法顯示「前值 → 現值」。
    - **作法**：新增 `macro_history.py`，重用 `update_report.py` 既有的 `MacroParser` 掃描 `report/invest_analysis_*.html`（保留 30 份，約 6 週）一次性回填歷史，之後由 `update_report.py` 每日 upsert；僅在數值或備註實際變動時才追加版本。比對採正規化字串（解析器會移除 `-`、`▲`、`▼`，若不正規化，`3.50%-3.75%` 這類區間值會每天被誤判為新版本），但保留開頭負號以區分 `-2.3 萬` 與 `2.3 萬`。
  - **修正：內嵌 JSON 含 NaN 導致前端無法解析 (既有問題)**:
    - **問題**：`market-data` 等內嵌 JSON 由 Python `json.dumps` 產生，pandas 的缺值會輸出 `NaN`。Python 可讀，但那不是合法 JSON，瀏覽器 `JSON.parse` 會整包拋錯（線上報告實際含 45 個 `NaN`）。因先前無任何前端程式讀取這些標籤，問題一直未被發現。
    - **修正**：`investment_analysis.py` 新增 `json_safe()`，在寫入 `technical_data.json` 與渲染模板前將 `NaN`／`Inf` 轉為 `null`；面板的 `readJSON()` 另保留一層向下相容的容錯解析。
  - **基本面資料補齊 (零額外抓取成本)**:
    - **問題**：`CLAUDE.md` 要求 Sophia 依據「`fundamental-data` 標籤中的真實 ROE、毛利率、PEG」評估，但 `get_fundamental_data()` 只取了 `shortPercentOfFloat`、`shortRatio` 兩個欄位，那些基本面數字**從未存在**於資料中。
    - **作法**：該函式本來就已呼叫 `yf.Ticker().info`（為了空單資料），因此改為多取 ROE、毛利率、淨利率、本益比、預估本益比、PEG、股價淨值比、殖利率、營收年增、盈餘年增、負債權益比——**不增加任何一次網路請求**。取不到的欄位一律為 `None`，不做推估。實測 16 檔標的中 15 檔有資料：個股 (台積電) 欄位完整，ETF 多半僅有本益比與殖利率，指數與期貨則無。
    - **呈現**：速覽面板新增「基本面」區（名稱／本益比／殖利率，並以標籤顯示 ROE、毛利率、PEG、營收年增、股價淨值比），有 ROE 者優先排序。
  - **修正：三大法人買賣超單位標錯 1000 倍 (既有問題)**:
    - **問題**：`investment_analysis.py` 台股表格欄位標題為「外資(張)」「投信(張)」，但 FinMind 的 `TaiwanStockInstitutionalInvestorsBuySell` 回傳單位是**股**，程式直接原值輸出——台積電單日曾顯示 `3,972,231 張`，遠超過全市場成交量。
    - **修正**：新增 `to_lots()` 換算 (1 張 = 1000 股)，表格與速覽面板一致顯示張數 (台積電當日 -3,024 張)。K 線圖的法人流向子圖為累積趨勢線，不受單位影響。
  - **修正：`[hidden]` 被作者樣式覆蓋**:
    - `.ov-panel` 的 `display: flex` 會蓋過瀏覽器對 `[hidden]` 的預設隱藏，導致面板「關閉」後仍實際可見（僅屬性改變）。補上 `.ov-panel[hidden], .ov-backdrop[hidden] { display: none; }`。此問題由端到端瀏覽器測試（檢查實際可見性而非 `hidden` 屬性）攔截。

- **2026-08-05 (v2.8)**:
  - **每日報告提前 + 休市不出報告**:
    - **需求**：使用者要求每日投資分析報告提前產生，且「前一日美股與台股都休市」時不要產生報告。
    - **提前時間 (夏/冬令自動切換)**：cron 由固定 07:00 改為依美東時區判斷——夏令 (America/New_York = EDT) 06:00 起跑、冬令 (EST) 維持 07:00（保留已驗證的美股日 K 抓取緩衝），以美股收盤到台北的時差決定，每天僅一行實際執行。同時將 yt_analysis 第三班由 06:00 挪到 06:30，避開與投資分析共用重型鎖的同刻競用。08:00 retry 守門不變，作為夏令偶爾美股日 K 晚到或誤判 skip 的自動補救。
    - **休市守門 (`market_open_gate.py`)**：`invest_analysis.sh` 在取重型鎖、啟動 claude 之前先跑輕量 gate——比對 `^GSPC`／`^TWII` 最新交易日與既有 `technical_data.json` 中「標普 500」「加權指數」最後一根 K 棒日期；**兩市皆無新交易日 (等同前一日兩市皆休市) 才 skip**（回傳碼 10，直接結束、不動任何資料、不 commit），只要任一市有新交易日（例如僅美股開盤）即照常出報告。採保守原則：檔案缺失、抓取失敗或資料異常一律照常執行，把關交給既有資料完整性 gate。不維護節假日行事曆，天然涵蓋週末、連假與多日中斷。

- **2026-07-29 (v2.7)**:
  - **全報告事實鐵律 (Facts-Only & Event-Timing Integrity)**:
    - **問題**：2026-07-29 早上生成的報告把「市場預期 FOMC 按兵不動」寫成「FOMC 於今日宣布維持利率不變」的既成事實，並掛上捏造的 CNBC 來源——實際決策要到美東 7/29 下午（台灣時間 7/30 凌晨）才公布。現有驗證只比對數值、不檢查事件是否真的已發生，未能攔截。
    - **修正**：依使用者要求，`CLAUDE.md` 新聞規範與 AI 分析反幻覺協定全面禁止預期性內容：(1) 新聞只准報導「官方發布時間（含美東→台灣時區換算）早於報告生成時間」的已發生事件；(2) 排程性事件（央行決策、財報、經濟數據）只能以「何時公布」的行事曆事實呈現，不得附帶預期結果；(3) 市場預期、共識預估、機率定價、分析師預測等預測型內容全報告禁用，搜尋到的前瞻/展望型報導一律棄用不改寫；(4) Rain 的三情境（Bull/Base/Bear）策略框架廢除，改為僅基於已實現數據的市場現況總結，禁止情境機率、目標價與方向性預測。
  - **update_report.py 表格替換正則修正**:
    - **問題**：總經表格替換的正則 `<table.*?id="us-macro-table">` 在 DOTALL 下會從全文件第一個 `<table` 貪吃到總經表格；對「已注入過的報告」重跑本腳本時（2026-07-29 實際發生），中間的 26 張 K 線圖（約 3.2MB）被整段吞掉。每日正常流程因走 placeholder 分支而未曾觸發。
    - **修正**：開頭標籤內的 id 改用 `<table[^>]*id=...>` 匹配，替換範圍限定在表格自身，重跑注入成為安全的等冪操作。
  - **朗讀時保持螢幕亮 (Wake Lock) 與 iOS 切音修正**:
    - **問題**：報告的「朗讀新聞／朗讀分析」播放途中，手機待機時間一到螢幕自動熄滅，頁面轉為隱藏即觸發停止朗讀，長文無法聽完；另 iOS 每段語音開頭有被切掉一個音節的既有問題。
    - **修正**：`templates/report_template.html`（並同步補上線上 `index.html`）的 TTS 控制器加入兩項與多益單字卡 PWA 相同的已驗證機制：(1) 朗讀開始時以 Screen Wake Lock API 保持螢幕亮，停止或唸完時釋放；(2) 朗讀期間以 Web Audio 輸出 20Hz、約 -80dB 的無聲訊號保持音訊通道常開，避免 iOS 每段開頭被切音。不支援 Wake Lock 的環境自動降級為原行為。主動切換至其他 App 時仍會停止朗讀（原設計保留）。
  - **導覽列新增「動能選股」按鈕**:
    - `templates/report_template.html` 導覽列 (nav-bar) 於「財經節目」之後新增外連按鈕「動能選股」，連往 `https://gwanlinho.github.io/Stock_Selection/` (target="_blank")，方便讀者從總經擇時報告一鍵前往攻擊型個股選股週報。同步補進現有 `index.html` 使其即時上線。

- **2026-07-06 (v2.4)**:
  - **GitHub Pages 部署護欄 (sync.sh)**:
    - **問題**：GitHub Pages 偶發「Deployment failed, try again later」暫時性故障 (2026-07-05 本 repo 即發生一次，2026-07-03 stock_selection 連續三次)，部署失敗時網頁停留在舊版且無人察覺，直到下次 push 才有機會重試。
    - **修正**：`sync.sh` 推送成功後改為呼叫共用函式庫 `WorkDir/_lib/pages_guard.sh` 的 `verify_pages_or_retrigger`：以公開 Actions API (免 token) 輪詢該 commit 的部署結論 (最多 3 分鐘)；若為 failure 則推一個空 commit 自動重觸發一次；API 查不到狀態時僅警告、不中斷報告流程。三個公開 repo (investment_analysis / Stock_Selection / yt_podcast_analysis) 共用同一份護欄。

- **2026-06-15 (v2.3)**:
  - **休市顯示上一交易日 (移除停更天數門檻)**:
    - **問題**：v2.2 以「最新資料距執行日超過 5 天」作為缺失判定之一，但休市 (尤其過年等長假可達九天) 屬正常現象，以天數判定缺失並無道理 — 長假會讓原本有上一交易日資料的標的被誤顯示為 n/a。
    - **修正**：缺失 / n/a 收斂為唯一標準「完全沒有任何有效資料可顯示」(yfinance 與 FinMind 皆抓不到、或序列全為 NaN)。只要有任何歷史有效資料，休市時一律顯示「最後有效交易日 (上一交易日)」並逐列標註資料日，不再顯示 n/a。abort 門檻 (≥3) 僅在資料源真正掛掉 (連歷史資料都抓不到) 時觸發。

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
