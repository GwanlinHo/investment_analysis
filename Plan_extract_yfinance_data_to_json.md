# Investment Analysis Data Refactor Plan

## 專案目標
將 `investment_analysis.py` 產出的原始數據從 HTML 檔案中分離，儲存至獨立的 JSON 檔案中，以優化 HTML 讀取速度並實現數據與展示層的分離。

## 執行步驟

### Step 1: 建立新分支
- 執行 `git checkout -b data-refactor`

### Step 2: 修改 `investment_analysis.py`
- **數據儲存**:
    - 實作 `save_to_json(data, filename)` 函數。
    - 在腳本執行結束前，將完整資料結構儲存至 `technical_data.json`。
- **HTML 內容精簡**:
    - 修改 HTML 模板或生成邏輯。
    - 移除原本嵌入在 `<script id="fundamental-data" type="application/json">` 中的原始數據。
    - 僅保留報告前端渲染（如 Plotly 圖表）所需的最小數據集。

### Step 3: 修改 `update_report.py`
- **數據讀取**:
    - 實作 `load_from_json(filename)` 函數。
    - 調整數據來源優先級：優先從 `technical_data.json` 讀取，而非解析 `index.html`。
- **注入邏輯**:
    - 確保 AI 分析區塊（Atlas, Sophia 等角色）的數據注入不受影響。

### Step 4: 新增測試 `tests/test_data_handling.py`
- 撰寫測試案例驗證 JSON 讀寫。
- 驗證 `investment_analysis.py` 產出的 HTML 大小與內容。
- 確保 `update_report.py` 在讀取 JSON 後能正確生成報告內容。

### Step 5: 執行與驗證
1. 執行 `uv run investment_analysis.py`。
2. 執行 `uv run update_report.py`。
3. 運行所有測試：`pytest tests/`。
4. 手動檢查 `index.html` 與 `report/index.html`。

### Step 6: 合併與推送
- `git checkout main`
- `git merge data-refactor`
- `git push origin main`

## 預期結果
- `index.html` 檔案大小顯著縮減。
- `technical_data.json` 成為數據交換的中間層，提高系統解耦度。
- 報表顯示與分析結果維持 100% 準確度。
