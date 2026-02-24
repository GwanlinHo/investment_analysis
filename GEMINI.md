# Investment Analysis Project Memories

## General Constraints
- **NO EMOJIS ALLOWED** in any output.
- **LANGUAGE**: All generated content must be in **Traditional Chinese**.
- **Python Execution**: ALWAYS use `uv run` to execute Python scripts to ensure dependency isolation.
- **Consistency Check**: Before final injection, verify that no market-active phrases (e.g., "observed today") are used if the market status is "Market Closed". Refer to the "Last Trading Day" instead.
- **Tool Usage Standard**: 禁止猜測檔案內字串的位置（如使用 offset）。必須使用 `grep_search` 或 `run_shell_command` 的 `grep` 工具進行精確定位與內容讀取。

## Workflow: Investment Analysis

### 0. Technical Data Generation
- **Action**: ALWAYS execute `uv run investment_analysis.py` as the first step.
- **Purpose**: This generates the base HTML report with the latest technical indicators (KD, MACD, BIAS), price data, and K-line charts.
- **Verification**: Ensure the script finishes successfully before proceeding to macro data collection.

### 1. Macro Data Collection
- **Principle**: Use **OFFICIAL Historical Actuals ONLY**. Strictly prohibit forecasts, estimates, or outlooks.
- **Verification**: `Data Month < Current Month`. Cross-verify data across official sites (BEA, BLS, CBC, NDC, MOEA, DGBAS).
- **Accuracy**: Data must match official press releases exactly. If sources conflict, prioritize the primary government agency.
- **Lag Compliance**: GDP/Investment (Min 1 Quarter lag); Other indicators (Min 1 Month lag).
- **US Indicators**: GDP, CPI, PPI, Retail Sales, Non-farm Payrolls, Unemployment Rate, Jobless Claims, ISM Mfg Index, M2, Credit Card Delinquency, Real Private Invest, DXY.
- **TW Indicators**: Monitoring Indicator (Query NDC site for score/color), Export Orders YoY, Industrial Production, Consumer Confidence, M1B/M2, Credit Card Delinquency, Real Private Invest, Unemployment, Overtime Hours, Margin/Short Balance (Display Total & Daily Change).
- **Local Cache**: Use `macro_cache.json` to store and retrieve historical data when latest figures are not yet released. Update cache only when newer official data is found.

### 2. News Focus (15 Items)
- **Authority**: Tier-1 ONLY (Bloomberg, Reuters, WSJ, FT, CNBC, Barron's, Economic Daily, Commercial Times, CNA, Anue).
- **Freshness**: All news must be published within the **LAST 7 DAYS**.
- **Authenticity**: MANDATORY cross-verification of all major claims. If a story is only reported by a single non-wire source, it must be excluded. Compare at least two Tier-1 sources for critical news.
- **Search Strategy**: Execute **3 distinct searches**: (1) Global Macro/Fed, (2) TW Stock/Tech/TSMC, (3) Geopolitical Risks/Earnings surprises.
- **Dynamic Injection**: 嚴禁在腳本中硬編碼新聞內容。必須每次由 AI 搜尋後動態注入腳本或報告。
- **Selection**: 15 items total. Maintain a **70% Global / 30% Taiwan** ratio.
- **Format**: 
  - Line 1: **[Source] Title** (No links allowed).
  - Line 2: Concise summary focusing on impact and facts, not speculation.
- **HTML Target**: `#weekly-news-focus` (Use `<ul><li>`, NO `<a>` tags or URLs in the final HTML).

### 3. AI Comprehensive Analysis (Persona-Driven Framework)
AI 必須根據當前真實數據動態生成分析，嚴禁使用包含硬編碼數據（如固定的 VIX 數值、通膨率、利差描述）的靜態模板。

#### 1. 宏觀策略師 阿特拉斯 (Atlas - Macro Strategist)
- **Responsibilities**:
  - **殖利率監測邏輯**：計算 3M, 10Y, 30Y 三者間的利差。
  - **觸發規則**：僅當任意兩者利差 **< 0.25% (25bps)** 或出現 **倒掛 (利差 < 0)** 時，才在報告中提及殖利率曲線狀態（如趨平或倒掛）。
  - **靜默規則**：若三者差距均 > 0.25%，則視為曲線陡峭且正常，**嚴禁提及**殖利率曲線，應將焦點轉向 DXY、M2 或 GDP 等指標。
  - 審核所有指標必須為官方歷史實績。

#### 2. 基本面分析師 索菲亞 (Sophia - Fundamental Quality Analyst)
- **Responsibilities**:
  - 根據 `fundamental-data` 腳本標籤中的真實 ROE、毛利率與 PEG 進行評價。

#### 3. 技術面分析師 研二 (Kenji - Technical Chartist)
- **Responsibilities**:
  - 檢測真實的 KD、MACD 背離情形與均線乖離率 (BIAS)。

#### 4. 籌碼與散戶心理觀察家 克羅 (Crow - Flow & Sentiment Sentinel)
- **Responsibilities**:
  - 根據當前真實 **VIX 指數** 與融資券餘額數據量化市場情緒。

#### 5. 綜合策略分析師 雷恩 (Rain - Portfolio Manager)
- **Responsibilities**:
  - 根據上述動態分析合成 Bull/Base/Bear 情境與行動策略。

### 4. Data Injection & Synchronization
- **Injection**: Execute `uv run update_report.py`。該腳本必須從基礎 HTML 報告的 JSON 標籤中提取數據，進行動態文本合成後再注入。
- **No Hardcoding**: 腳本內不得含有 `AI_ANALYSIS_TEXT` 的靜態變數或硬編碼的巨觀經濟數值。
- **Cleanup**: 確保無佔位符殘留。
- **Finalization**: 同步更新至 `index.html` 與 `report/index.html`。
