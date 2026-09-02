# Investment Analysis Project Memories

## General Constraints
- **NO EMOJIS ALLOWED** in any output.
- **LANGUAGE**: All generated content must be in **Traditional Chinese**.
- **Python Execution**: ALWAYS use `uv run` to execute Python scripts to ensure dependency isolation.
- **Consistency Check**: Before final injection, verify that no market-active phrases (e.g., "observed today") are used if the market status is "Market Closed". Refer to the "Last Trading Day" instead.
- **Documentation**: A summary of changes and the date must be added to the "Changelog" section at the top of `README.md` ONLY when modifying the source code or `CLAUDE.md` itself.
- **Tool Usage Standard**: Prohibit guessing string positions in files (e.g., using offset). MUST use the Grep tool (or `grep` via the Bash tool) for precise positioning and content reading.

## Development Workflow
- **Branch-based Development (Systematic Changes Only)**: Modifications to source code, project configuration, formatting, or rules (including `CLAUDE.md` and system prompts) **MUST** be performed in a dedicated feature branch (e.g., `feature/xxx`).
- **Daily Reports (Direct to Main)**: Daily investment analysis reports (including `index.html`, `report/index.html`, and `macro_cache.json`) do **NOT** require a feature branch and can be committed directly to the `main` branch.
- **Verification & Debugging**: Systematic changes must be fully developed, verified, and debugged within the feature branch. Daily reports must pass the automated validation in `update_report.py`.

## Merge & Upload Policy
- **Systematic Changes**: Merging to `main` and pushing to GitHub is **STRICTLY PROHIBITED** until the user has reviewed the results and provided explicit consent. After consent, merge to `main`, push, and switch the local environment back to `main`.
- **Daily Reports**: Upon successful completion of the analysis cycle (`uv run investment_analysis.py` and `uv run update_report.py`), the results must be committed and pushed to the `main` branch **IMMEDIATELY** and **AUTOMATICALLY**, without requiring manual consent or a feature branch.
- **Data Integrity Abort (overrides auto-push)**: If `investment_analysis.py` aborts due to the data-completeness gate (3+ symbols missing, non-zero exit / `[ABORT]`), the auto-push rule above does NOT apply — produce nothing and push nothing for this cycle. As a final safeguard, `update_report.py` independently refuses to inject when `technical_data.json` is not updated today.

- **Publish Data Minimization**: `technical_data.json`, `news.html`, `ai.html` and `ai_context.json` are LOCAL ONLY — all four are gitignored and must never be committed or added to the `sync.sh` whitelist. `technical_data.json` holds Yahoo's raw OHLCV series; the other three are workflow intermediates whose content is already injected into `index.html`, and nothing on the published site links to them. Report HTML is sanitized by `publish_filter.py` at render time (raw `Open`/`High`/`Low`/`Volume` and Yahoo `.info` fundamentals are stripped from the embedded JSON). Do NOT reintroduce raw Yahoo values into any published artifact. The local file stays complete for AI analysis (Fact-Only Rule) and `market_open_gate.py`.

## Workflow: Investment Analysis

### 0. Technical Data Generation
- **Action**: ALWAYS execute `uv run investment_analysis.py` as the first step.
- **Purpose**: This generates the base HTML report with the latest technical indicators (KD, MACD, BIAS), price data, and K-line charts.
- **Verification**: Ensure the script finishes successfully before proceeding to macro data collection.
- **Data Integrity Gate (MANDATORY)**: `investment_analysis.py` enforces a data-completeness gate — a symbol counts as missing ONLY when it has NO valid data at all (entirely unavailable from BOTH yfinance AND FinMind, or an all-NaN series). Market closures (weekends / holidays / long breaks, even 9-day Lunar New Year) are NORMAL and are NOT missing: as long as any historical data exists, the symbol shows its last valid trading day (annotated with that date), never `n/a`. If 3 or more symbols are truly missing, the script prints `[ABORT]` and exits non-zero WITHOUT producing a report. If the script exits non-zero (or prints `[ABORT]`), you MUST **terminate the entire workflow immediately**: do NOT run macro collection / news / AI analysis / `update_report.py`, and **do NOT git commit or push**. Leave the previous report untouched and log the reason. Fewer than 3 truly-missing symbols is acceptable: those rows render as `n/a` and the workflow proceeds normally.
- **Gap Backfill (`gap_backfill.py`)**: Yahoo occasionally drops a trading day's daily bar **permanently** (2026-08-28 was missing for nine symbols and never returned). The script now backfills such **mid-series** holes automatically — first from the local `_ohlcv_cache.json`, then by aggregating Yahoo's 1-hour bars into a daily bar. Watch the `[backfill]` lines in stdout:
  - `以本機快取補回` / `以盤中線重建` — the hole was filled. Reconstructed Open/High/Low are near-exact; **Close is systematically 0.002%~0.09% low** (the settlement print lands after the last intraday bar) and **Volume is an underestimate** (no pre/post-market or closing auction). This is immaterial for the indicators, but do NOT quote a reconstructed bar as an official close — cite a Tier-1 source for that number instead.
  - `[!] 仍有補不到的破洞` — the hole remains. You MUST disclose it in the report exactly as before (state the affected symbols and dates, note that the tabulated single-day change actually spans more than one session, and take quoted closes from Tier-1 reporting).
  - Tail lag (a symbol not yet updated for today) is NOT a hole and is deliberately never backfilled; it stays handled by the table's reference date and the per-row `[!] 資料 MM/DD` annotation.

### 1. Macro Data Collection
- **Principle**: Use **OFFICIAL Historical Actuals ONLY**. Strictly prohibit forecasts, estimates, or outlooks.
- **Verification**: `Data Month < Current Month`. Cross-verify data across official sites (BEA, BLS, CBC, NDC, MOEA, DGBAS).
- **Accuracy**: Data must match official press releases exactly. If sources conflict, prioritize the primary government agency.
- **Lag Compliance**: GDP/Investment (Min 1 Quarter lag); Other indicators (Min 1 Month lag).
- **US Indicators**: GDP, CPI, PPI, Retail Sales, Non-farm Payrolls, Unemployment Rate, Jobless Claims, ISM Mfg Index, M2, Credit Card Delinquency, Real Private Invest, DXY.
- **TW Indicators**: TAIEX (Taiwan Capitalization Weighted Stock Index), Monitoring Indicator (Signal - Query NDC site for score/color), Export Orders YoY, Industrial Production, Consumer Confidence, M1B/M2, Credit Card Delinquency, Real Private Invest, Unemployment, Overtime Hours, Margin/Short Balance (Display Total & Daily Change).
- **Local Cache**: Use `macro_cache.json` to store and retrieve historical data when latest figures are not yet released. Update cache only when newer official data is found.
- **Cache Update Rule**: When updating `macro_cache.json`, you MUST follow the **Upsert logic**: Update the values for specific indicators while strictly preserving all other existing historical data. Direct overwriting of the entire JSON object is strictly prohibited.
- **Data Integrity**: Before saving the cache, verify that the total count of indicators has not decreased significantly.

- **News Focus (20 Items)**
- **Authority**: Tier-1 ONLY (Bloomberg, Reuters, WSJ, FT, CNBC, Barron's, BBC, CNN, Economic Daily, Commercial Times, CNA, Anue).
- **Freshness**: All news must be published within the **LAST 7 DAYS**. **MANDATORY**: Each news item must include its publication date in (YYYY-MM-DD) format.
- **Authenticity**: MANDATORY cross-verification of all major claims. If a story is only reported by a single non-wire source, it must be excluded. Compare at least two Tier-1 sources for critical news.
- **Facts-Only & Event-Timing Integrity (MANDATORY)**: News items may report ONLY events that have ALREADY OCCURRED. An event counts as occurred only if its official announcement time, converted to Taiwan time, is verifiably EARLIER than the report generation time. **Timezone conversion is mandatory**: e.g., FOMC statements are released at 14:00 ET, which is 02:00-03:00 the NEXT DAY in Taiwan — a report generated on a Taiwan morning can NEVER contain that week's FOMC outcome before that moment. Scheduled-but-unannounced events (FOMC decisions, earnings releases, economic data) may be mentioned ONLY as calendar facts — what will be released and when (Taiwan time) — with NO expected outcome attached. **Forecast-type content is PROHIBITED report-wide**: market expectations, consensus estimates, probability pricing, analyst forecasts/outlooks (e.g., "市場預期", "共識預估", "升息機率", "分析師預測") must not appear in news items or analysis, regardless of source. Preview/outlook-type articles found in search results must be discarded, not rewritten. Converting expectations into accomplished facts, or attaching a fabricated source/date, is a critical violation. (Incident: the 2026-07-29 report falsely stated FOMC had announced a rate hold before the meeting had even concluded.)
- **Language & Translation**: **MANDATORY**. All news titles and summaries MUST be translated into **Traditional Chinese**. Strictly prohibit direct copy-pasting of English text for international news.
- **Search Strategy**: Execute **4 distinct searches** (use the WebSearch tool):
    1. Global Macro/Fed
    2. TW Stock/Tech/TSMC
    3. Geopolitical Risks (Conflict regions, Middle East, Red Sea, etc.)
    4. Energy Supply & Global Shipping (Oil prices, Freight rates, Supply chain disruption)
- **Dynamic Injection**: Strictly prohibit hardcoding news content in scripts. News must be dynamically injected into the script or report by AI after each search.
- **Selection**: 20 items total. Maintain a **70% Global / 30% Taiwan** ratio.
- **Format**:
  - Line 1: **[Source] Title (YYYY-MM-DD)** (No links allowed).
  - Line 2: Concise summary focusing on impact and facts, not speculation.
- **Date & Language Check**: AI must verify the publication date (within 7 days) and the language (Traditional Chinese) of each news item before saving. Any item in English or from more than 7 days ago must be discarded or translated/re-sourced.
- **HTML Target**: `#weekly-news-focus` (Use `<ul><li>`, NO `<a>` tags or URLs in the final HTML).

### 3. AI Comprehensive Analysis (Persona-Driven Framework)
AI must dynamically generate analysis based on current real-world data. **Strict adherence to data integrity is mandatory.**

#### **Numerical Integrity & Anti-Hallucination Protocol**
- **Fact-Only Rule**: Strictly prohibit referencing any historical high/low points not present in `technical_data.json` or `macro_cache.json`. Do not invent descriptions like "plunged/surged from level X" for dramatic effect.
- **Facts-Only Rule (MANDATORY)**: The analysis must be built EXCLUSIVELY on realized, officially published data. Prohibit citing any forecast-type content: market expectations, consensus estimates, probability pricing, rate-path odds, analyst outlooks, or predicted outcomes of scheduled events. Before writing any "已宣布/已確認/決議" style claim, cross-check the event's official release schedule with timezone conversion to Taiwan time (see Facts-Only & Event-Timing Integrity in the News section). Scheduled-but-unannounced events may be mentioned only as calendar facts (what and when, Taiwan time). Prohibit scenario probabilities, price targets, and directional market predictions.
- **Dynamic Narrative Rule (Anti-Template)**: STRICTLY PROHIBIT using fixed sentence structures or "mad-lib" style templates. Analysis must be written as a professional, dynamic narrative that flows naturally based on the data.
- **Variable Description Mandate**: Every time a tag-based variable (e.g., `{{VIX}}`) is used, it MUST be accompanied by a clear description of what the number represents.
    - **WRONG**: "促使 {{VIX}} 回落至 18 以下"
    - **RIGHT**: "促使恐慌指數 (VIX: {{VIX}}) 回落至 18 以下"
    - **RIGHT**: "隨著加權指數 ({{TAIEX}}) 創下新高"
- **Tag-Based Substitution (Mandatory)**: To ensure 100% numerical accuracy, AI must prioritize using tags instead of manual numbering when writing `ai.html`. `update_report.py` will automatically perform physical replacement:
    - `{{TAIEX}}`: TAIEX Closing Price
    - `{{VIX}}`: VIX Index Closing Price
    - `{{DXY}}`: US Dollar Index (DXY)
    - `{{US10Y}}`: US 10-Year Treasury Yield
    - `{{MARGIN_BALANCE}}`: Margin Balance
    - `{{MARGIN_CHANGE}}`: Daily Change in Margin Balance
- **Field Consistency**: When quoting indices, you must explicitly correspond to the `Close` field. It is strictly forbidden to misinterpret technical indicator fields like `TR` (True Range), `Volume`, or `ADX` as price levels.
- **Numerical Validation**: Before the final report injection, the system will compare the numbers in the content with the fact repository. If an abnormal deviation occurs (e.g., the VIX data is 21 but the analysis writes 60), the update will be forcibly intercepted.

#### 1. Atlas - Macro Strategist
- **Responsibilities**:
  - **Yield Monitoring Logic**: Calculate the spreads between 3M, 10Y, and 30Y yields.
  - **Trigger Rule**: Mention the yield curve state (e.g., flattening or inverted) in the report ONLY when the spread between any two is **< 0.25% (25bps)** or an **inversion (spread < 0)** occurs.
  - **Silence Rule**: If the gaps between all three are > 0.25%, the curve is considered steep and normal. **STRICTLY PROHIBIT** mentioning the yield curve; focus should shift to other indicators like DXY, M2, or GDP.
  - **Geopolitical Warning Protocol**:
    - **Scanning Mechanism**: Atlas must scan the 20 news items for keywords such as "Middle East, Red Sea, Hormuz, Suez, Iran, Sanctions, Blockade, Conflict, Disruption".
    - **Forward-looking Projection**: If risks are detected, Atlas must perform a two-tier impact analysis:
      1. **Immediate Impact**: Assess the psychological shock to oil prices, gold prices, and safe-haven sentiment.
      2. **Chain Reaction**: Project potential interference with global freight rates, energy inflation paths, and central bank interest rate trajectories.
    - **Warning Output**: If risks are significant, Atlas must present them as a dedicated sub-item: "Geopolitical & Supply Chain Warning," rather than just summarizing historical data.
  - Audit all indicators to ensure they are official historical actuals.
  - **Check `ai_context.json`** before writing to verify all macro constants.

#### 2. Sophia - Fundamental Quality Analyst
- **Responsibilities**:
  - Evaluate performance based on real ROE, Gross Margin, and PEG from the `fundamental-data` script tags.
  - **Data availability (as of 2026-08-16)**: `get_fundamental_data()` now populates `roe`, `gross_margin`, `profit_margin`, `pe`, `forward_pe`, `peg`, `pb`, `dividend_yield`, `revenue_growth`, `earnings_growth`, `debt_to_equity` from the same `yf.Ticker().info` call already used for short interest — no extra network cost. Coverage is uneven by design: individual stocks (2330.TW) are complete, ETFs usually carry only PE and dividend yield, indices and futures carry none. Missing fields are `None`. **Never estimate or fill a missing field** — omit the claim instead.

#### 3. Kenji - Technical Chartist
- **Responsibilities**:
  - Detect real KD and MACD divergence situations and Moving Average Bias (BIAS).

#### 4. Crow - Flow & Sentiment Sentinel
- **Responsibilities**:
  - Quantify market sentiment based on current real **VIX Index** and margin/short balance data.

#### 5. Rain - Portfolio Manager
- **Responsibilities**:
  - Synthesize the four analysts' realized-data readings into a **current market-state summary**: valuation and risk posture, flow/sentiment conditions, and what has materially changed since the previous report.
  - **Strictly NO scenario forecasting** (Bull/Base/Bear frameworks are prohibited), no probability assignments, no price targets, no predicted market direction (per Facts-Only Rule). Risk-control observations tied to already-observed data (e.g., noting that margin balance remains elevated) are acceptable; asserting future outcomes is not.

### 3.5 Floating Overview Panel (指標速覽面板)
- **What it is**: A client-side floating panel in `templates/report_template.html` summarizing 總經 / 技術 / 情緒 recent changes. It auto-opens once per report date, can be closed, and re-opened via the 速覽 button.
- **Data flow**: The panel computes EVERY cell in the browser from the embedded `<script type="application/json">` tags (`market-data`, `macro-data`). It contains **NO server-injected HTML**. Do not "fix" the panel by writing values into it from Python.
- **`panel-data`**: precomputed scalars for the overview panel (per symbol: latest close, `d1`/`d5`/`d20`, `ma20` cross; plus `pctile` for 恐慌指數), built by `publish_filter.build_panel_data()` at render time. The panel reads these INSTEAD of a Close series — publishing 25 symbols x 60 days of Yahoo closes was redistribution under Yahoo's ToS. `Close` is therefore stripped from `market-data` alongside OHLV. The Python helpers in `publish_filter` are line-for-line equivalents of the template's `pctChange()`/`percentile()`/`signals()`; **change one side and you must change the other**, or the panel silently disagrees with the report tables. Quoting a few closes in the report prose is commentary and remains fine.
- **`macro-data`**: injected by `update_report.py: inject_macro_payload()` from `macro_cache.json` + `macro_history.json` (現值 / 前值 / 變動日). Replace ONLY the tag contents with the anchored pattern `(<script id="macro-data" type="application/json">).*?(</script>)`. NEVER use `<script.*?id=` (same class of bug as the 2026-07-29 table-regex incident).
- **`macro_history.json`**: maintained by `macro_history.py` (daily upsert; `--backfill` rebuilds from `report/*.html`; `--show` inspects). Only append a version when the value or note actually changes.
- **Placement rule**: the panel markup MUST stay outside `.container` (just before `</body>`) so it never falls inside any `update_report.py` injection zone. Re-running `update_report.py` on an injected report must remain a no-op for the panel.
- **Market-closed labeling**: the panel header MUST show 資料截至 (last bar `Date` of 加權指數 / 標普 500) and flag it when it differs from the report date. The panel is the first thing the reader sees; presenting a previous trading day's close under today's date is the same class of error the 休市中 badge exists to prevent.
- **JSON validity**: embedded JSON must not contain `NaN`/`Infinity` — `investment_analysis.py: json_safe()` converts them to `null` before saving/rendering. Python tolerates `NaN`; browsers do not.
- **Verification**: after touching the template or injection code, re-run the end-to-end browser test (headful chromium) and assert **actual visibility** (`getComputedStyle().display`), not the `hidden` attribute — author styles can override `[hidden]`.

### 4. Data Injection & Synchronization
- **Mandatory Preparations**:
  1. **Write AI News**: Format the 20 news items into an HTML `<ul><li>` structure and overwrite `news.html`.
  2. **Write AI Analysis**: Write the persona-driven analysis into `ai.html`.
- **Injection**: Execute `uv run update_report.py` ONLY AFTER updating the files above. The script now enforces a 5-minute recency check.
- **No Hardcoding**: Scripts must not contain static variables or hardcoded macroeconomic values for `AI_ANALYSIS_TEXT`.
- **Cleanup**: Ensure no placeholders remain.
- **Finalization**: Synchronize updates to `index.html` and `report/index.html`.
