# 程式碼審查報告：investment_analysis

**審查日期:** 2026-02-19

## 總體評價

此專案結構清晰，完成了從資料獲取、技術指標計算到 HTML 報告生成的完整流程。程式碼整體可讀性良好，並透過 `config.json` 實現了一定程度的客製化。

經過本次優化，已針對 **Magic Number**、**錯誤處理的穩健性** 與 **自動化測試** 進行了大幅改善。

---

## 主要問題與改善進度

### 1. Magic Number (硬式編碼) [已改善]

*   **改善內容:**
    *   `config.json`: 新增了 `parameters` 區塊，包含 `kd_window`、`bias_periods`、`color_thresholds`、`history_days` 等設定。
    *   `config.json`: 新增了 `inverse_symbols` 區塊，將 VIX 等反向指標的邏輯從程式碼抽離。
    *   `investment_analysis.py`: 全面改為從設定檔讀取參數，並提供合理的預設值。HTML 表頭與欄位亦改為動態生成，以適應不同參數。

### 2. 錯誤處理與穩健性 [已改善]

*   **改善內容:**
    *   `investment_analysis.py`: 強化了設定檔讀取失敗的處理，若 `config.json` 遺失或格式錯誤，程式將顯示明確錯誤並立即終止 (`sys.exit(1)`)。
    *   `investment_analysis.py`: 優化 `get_scalar` 函式，遇到 `NaN` 時改為回傳 `None`，並在 HTML 生成時透過 `fmt_num` 輔助函式正確顯示為 "N/A"，避免了錯誤的數值判斷。
    *   `investment_analysis.py`: 在檔案讀寫與圖表產生處增加了異常捕捉，提升系統穩定性。

### 3. 程式碼冗餘與邏輯 [處理中]

*   **問題點:**
    *   `investment_analysis.py`: `generate_html_report` 函式中仍在使用 f-string 手動拼接 HTML，長度過長且難以維護。
    *   `investment_analysis.py`: `main` 函式依然較為臃腫。
    *   `run_analysis.sh`: 仍包含硬式編碼的路徑。

*   **建議項目 (下一步):**
    *   **引入 Jinja2 模板引擎**: 彻底分離邏輯與 HTML 結構。
    *   **重構 `main` 函式**: 將資料獲取、指標計算、報告渲染拆分為獨立函式。

### 4. 潛在安全問題 [處理中]

*   **問題點:**
    *   透過 f-string 生成 HTML 仍存在 XSS 風險。

*   **建議項目 (下一步):**
    *   透過 Jinja2 的自動轉義機制來解決此問題。

---

## 5. 缺乏自動化測試 [已改善]

**進度**: 已成功引入 `pytest` 測試框架，並建立單元測試機制。

*   **已實作測試項目 (`tests/test_investment_analysis.py`):**
    1.  **`calculate_all_indicators(df)`**: 驗證技術指標 (KD, BIAS, ADX 等) 欄位是否存在，以及在正常資料下能否正確計算數值。
    2.  **`determine_trend(k, d, bias_signal_val)`**: 驗證四種關鍵趨勢 (多頭、反彈、空頭、回檔) 的判斷邏輯。
    3.  **`get_color_class(value, ...)`**: 驗證顏色 class 判斷邏輯，包含正向、反向指標以及對 `None/NaN` 的邊界處理。

---

## 結論

本專案已完成初步的架構強化，移除了大部分硬式編碼並建立了測試基礎。下一階段將專注於 **引入 Jinja2 模板引擎** 以及 **重構主程式邏輯**，以進一步提升程式碼的可維護性與安全性。
