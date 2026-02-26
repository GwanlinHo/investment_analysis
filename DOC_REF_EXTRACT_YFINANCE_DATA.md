# 重構技術文檔：YFinance 數據與展示層分離

## 1. 修改目的
目前的分析報告將所有原始市場數據、基本面數據與殖利率數據直接透過 Jinja2 嵌入 HTML 檔案中。這導致：
- HTML 檔案體積過大，讀取緩慢。
- 數據與展示邏輯耦合，不利於後續 AI 分析工具的獨立開發。
- 難以在不讀取整個 HTML 的情況下提取結構化數據。

本次重構旨在將這些數據提取至獨立的 `technical_data.json` 檔案中。

## 2. 修改內容
### 2.1 `investment_analysis.py`
- **新增函數 `save_to_json()`**: 將 `fundamental_data`, `yield_data`, `market_data`, `summary_items` 打包存入 `technical_data.json`。
- **優化 `generate_html_report()`**: 停止向 HTML 模板傳遞大型 JSON 變數，顯著減輕渲染負擔。

### 2.2 `update_report.py`
- **新增函數 `load_from_json()`**: 提供從 JSON 檔案載入結構化數據的能力。
- **修改 `main()` 邏輯**: 優先從 `technical_data.json` 獲取數據。若檔案不存在，則嘗試從 HTML 標籤中提取（向下相容）。

### 2.3 `templates/report_template.html`
- **精簡標籤**: 將原本用於傳輸數據的 `<script id="...-data">` 標籤內容固定為 `{}`。

### 2.4 `tests/test_data_handling.py` (新增)
- 驗證 JSON 讀寫的完整性。
- 驗證 `load_from_json` 的異常處理（如檔案不存在）。

## 3. 驗證方法
- **自動化測試**: 執行 `pytest tests/test_data_handling.py`。
- **流程驗證**: 依序執行 `uv run investment_analysis.py` 與 `uv run update_report.py`，確認 `index.html` 內容是否正常更新。
- **文件驗證**: 檢查 `technical_data.json` 是否包含所有預期的鍵值對 (fundamental, yield, market, summary)。

## 4. 預期結果
- `index.html` 的 HTML 代碼部分顯著縮減。
- `technical_data.json` 成為數據交換的中間層，提高系統靈活性。
- 分析報告中的技術圖表與數據表格維持不變。

## 5. 風險評估
- **數據同步風險**: 若 JSON 檔案與 HTML 報告生成的頻次不一致，可能導致 AI 分析與報告圖表不匹配。
    - *緩解措施*: 確保 `investment_analysis.py` 每次執行都會同步更新 JSON。
- **文件路徑風險**: 在不同環境執行時，需確保 JSON 檔案具備寫入權限。
