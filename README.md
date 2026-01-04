# 投資分析自動化專案 (Investment Analysis Automation)

這是一個結合 **Python 自動化腳本** 與 **AI 智慧分析** 的投資輔助工具。旨在每週自動抓取美股、台股 ETF 及債券市場數據，計算關鍵技術指標，繪製 K 線圖，並結合 AI 代理人生成深度市場觀點與即時新聞彙整，最終產出一份易於閱讀的 HTML 綜合分析報告。

## 主要功能

1.  **多市場數據追蹤**：支援追蹤美股指數（如 S&P 500, 費半）、台股熱門 ETF（如 0050, 0056）、個股及債券 ETF。
2.  **自動化技術指標計算**：
    *   **KD 指標**：判斷超買/超賣區間與趨勢強弱。
    *   **乖離率 (BIAS)**：計算 5日、20日、60日 乖離，判斷股價是否過熱或超跌。
    *   **DMI & ADX**：判斷趨勢方向與強度。
    *   **移動平均線 (MA)**：計算 5MA, 20MA, 60MA。
3.  **視覺化圖表生成**：自動繪製包含均線與成交量的 K 線圖，以及美國長短期公債殖利率曲線圖。
4.  **AI 大師觀點 (由 AI Agent 執行)**：
    *   **技術分析大師 (ISTP)**：分析量價結構、背離與 K 線型態。
    *   **價值投資大師 (ISTJ)**：評估估值風險與安全邊際。
    *   **總經與產業大師 (INTJ)**：分析利率環境、地緣政治與產業循環。
5.  **財經新聞彙整**：自動收集與美台經濟、匯率、利率相關的真實重要新聞。

---

## 專案結構

*   `investment_analysis.py`: 核心 Python 腳本。負責抓取 `yfinance` 數據、計算指標、繪圖並生成 HTML 報告框架。
*   `config.json`: 設定檔。管理追蹤清單、群組分類與中文名稱對照。
*   `report/`: 存放生成的 HTML 日報 (檔名格式：`invest_analysis_YYYYMMDD.html`)。
*   `README.md`: 專案說明文件。

---

## 運作方式與流程

本專案建議搭配 AI Agent (如 Gemini CLI) 使用以獲得完整體驗，流程如下：

1.  **執行腳本**：執行 `investment_analysis.py`。
    *   程式讀取 `config.json`。
    *   抓取歷史股價數據。
    *   計算指標並判斷趨勢訊號（如：多頭排列、空頭修正）。
    *   繪製圖表並轉換為 Base64 嵌入 HTML。
    *   生成包含數據表格與圖表的 HTML 檔案。
2.  **AI 分析與注入** (由 AI Agent 完成)：
    *   讀取生成的 HTML 報告。
    *   搜尋當日最新的財經新聞。
    *   根據數據與新聞撰寫「三位大師」的評論。
    *   將評論與新聞注入 HTML 中的 `#text-analysis-report` 區塊。
3.  **版本控制**：將報告推送到 GitHub 儲存庫。

---

## 🤖 AI Agent 協作指南 (AI Agent Collaboration Guide)

本專案的核心價值在於**「自動化程式碼」與「AI 認知能力」的結合**。雖然 Python 腳本可以精準計算數據，但無法解讀市場情緒或蒐集最新新聞。因此，我們設計了一套讓 AI Agent 接手後續工作的流程。

### 1. Gemini CLI 協作模式 (預設)

本專案已內建 Gemini CLI 的整合設定。

*   **觸發機制**：
    您只需要在 Gemini CLI 中輸入關鍵字：**`investment analysis`** (或 `run etf analysis`)。
*   **背後原理**：
    專案中的 `GEMINI.md` (或 `.gemini/GEMINI.md`) 扮演了「系統提示詞 (System Prompt)」的角色。當 AI 讀取到此檔案時，它會知道當使用者輸入特定關鍵字時，必須依序執行以下動作：
    1.  **執行 Shell 指令**：`python3 investment_analysis.py`。
    2.  **讀取檔案**：讀取生成的 HTML 內容。
    3.  **聯網搜尋**：使用 Google Search 尋找當日美股、台股與匯市的真實新聞（且被要求必須附上來源連結）。
    4.  **角色扮演分析**：切換成 ISTP (技術)、ISTJ (價值)、INTJ (宏觀) 三種人格進行分析。
    5.  **寫入檔案**：將新聞與分析寫回 HTML 檔案中。
    6.  **Git 操作**：自動 Commit 並 Push 到遠端。

### 2. 適配其他 AI Agent (如 Claude Code, Codex, Cursor)

這套「以檔案為基礎的上下文注入 (File-based Context Injection)」概念可以輕易移植到其他 AI 程式設計工具。

如果您使用的是 **Claude Code (Anthropic)**、**GitHub Copilot CLI** 或 **Cursor**，請參考以下修改方式：

#### 核心概念
所有 AI Agent 工具都遵循 **`Input (指令) -> Context (上下文規則) -> Action (工具調用)`** 的邏輯。您需要將 `GEMINI.md` 中的邏輯「翻譯」給您的工具聽。

#### 實作範例

*   **Claude Code**:
    *   在專案根目錄建立 `CLAUDE.md`。
    *   將 `GEMINI.md` 中的 Workflow 內容複製進去。
    *   Claude Code 會在啟動時讀取此檔案，並理解當您要求「分析投資」時該做什麼。
    *   *提示*：Claude Code 同樣具備 `run_command` (執行腳本) 與 `bash` 能力，邏輯完全通用。

*   **Cursor / VS Code Copilot**:
    *   建立 `.cursorrules` 檔案 (針對 Cursor)。
    *   將規則寫入：「當使用者要求『產生投資報告』時，請執行 `python3 investment_analysis.py`，然後搜尋網路新聞...」。
    *   *注意*：這些 IDE 內建的 Agent 可能需要您手動按確認才能執行 Terminal 指令或寫入檔案，自動化程度可能不如 CLI 工具高。

*   **自定義 LLM CLI**:
    *   將 `GEMINI.md` 的內容作為 System Prompt 的一部分傳送給模型。
    *   確保您的 CLI 環境有掛載 `Web Search` (搜尋新聞用) 與 `File I/O` (讀寫檔案用) 的工具權限。

### 總結
不論使用何種工具，關鍵在於**「定義工作流 (Workflow)」**：
> **執行計算腳本 (Python) -> 獲取外部資訊 (Web Search) -> 綜合分析 (LLM Inference) -> 產出結果 (File Write)**

---

## 安裝與設定

### 1. 環境需求
*   Python 3.8 或以上版本。
*   必要的 Python 套件：
    ```bash
    pip install yfinance pandas matplotlib mplfinance pytz
    ```

### 2. 設定追蹤清單 (`config.json`)
您可以透過修改 `config.json` 來自定義想追蹤的標的。檔案結構如下：

*   **`stock_groups`**: 定義報告中的分類群組。
    ```json
    {
      "title": "群組名稱 (如：美股)",
      "symbols": ["代碼1", "代碼2", ...],
      "description": "群組描述"
    }
    ```
*   **`key_indicators`**: 定義哪些標的會出現在報告最上方的「市場速覽」區塊。
*   **`symbol_name_map`**: 定義股票代碼對應的中文名稱 (若未設定則顯示代碼)。

**修改範例**：若要新增追蹤「特斯拉 (TSLA)」，請在 `stock_groups` 的對應陣列中加入 `"TSLA"`，並在 `symbol_name_map` 加入 `"TSLA": "特斯拉"`。

### 3. 執行指令
在終端機輸入以下指令即可產生基礎報告：
```bash
python3 investment_analysis.py
```
*注意：手動執行此指令僅會產生包含數據與圖表的報告，不包含 AI 文字分析與新聞摘要。*

---

## 📖 報告閱讀指南

生成的 HTML 報告包含以下關鍵資訊：

### 1. 技術訊號徽章 (Badges)
| 訊號 | 顏色 | 意義 | 判斷邏輯 |
| :--- | :--- | :--- | :--- |
| **多頭排列** | <span style="color:red">紅色</span> | 強勢上漲 | K > D 且 月線乖離 > 0 |
| **反彈** | <span style="color:lightcoral">淡紅</span> | 弱勢反彈 | K > D 但 月線乖離 < 0 |
| **回檔整理** | <span style="color:lightgreen">淡綠</span> | 多頭回調 | K < D 但 月線乖離 > 0 |
| **空頭修正** | <span style="color:green">綠色</span> | 趨勢向下 | K < D 且 月線乖離 < 0 |

### 2. 關鍵指標解讀
*   **K9 / D9**: KD 隨機指標。
    *   **> 80**: 超買區 (可能回檔，但也可能鈍化強漲)。
    *   **< 20**: 超賣區 (可能反彈)。
    *   **K > D**: 黃金交叉 (偏多)。
    *   **K < D**: 死亡交叉 (偏空)。
*   **乖離率 (BIAS)**: 股價與均線的距離百分比。
    *   **正值**: 股價在均線上。**負值**: 股價在均線下。
    *   數值過大代表短線過熱或超跌。
*   **ADX**: 趨勢強度指標。數值越高代表目前趨勢（無論多空）越強。通常 > 25 代表有明顯趨勢。
*   **+DI / -DI**: 方向指標。+DI 在上代表多方佔優，-DI 在上代表空方佔優。

### 3. 三位 AI 大師觀點
*   **技術大師**：告訴你現在「怎麼操作」（進出場點、型態風險）。
*   **價值大師**：告訴你現在「值不值得買」（便宜還是貴）。
*   **總經大師**：告訴你「大環境安不安全」（利率、戰爭、政策風險）。

---

## ⚠️ 免責聲明
本專案生成的報告僅供研究與參考，不構成任何投資建議。金融市場變化莫測，投資前請務必自行審慎評估風險。
