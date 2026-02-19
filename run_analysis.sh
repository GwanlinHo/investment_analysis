#!/bin/bash
# 讓腳本在遇到錯誤時立即停止執行
set -e

# 取得腳本所在的目錄，並切換至該目錄，增加可攜性
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

echo "[Info] 開始執行投資分析工作流..."

# 檢查 gemini 指令是否存在
if ! command -v gemini &> /dev/null; then
    echo "[Error] 找不到 'gemini' 指令。請確保已安裝 Gemini CLI 並正確設定 PATH。"
    exit 1
fi

# 執行 Gemini CLI 進行完整的投資分析工作流 (包含 Python 資料生成、AI 搜尋與報告更新)
# 這裡使用 'investment analysis' 觸發 GEMINI.md 中定義的自動化流程
gemini -p 'investment analysis' -y

echo "[Success] 投資分析工作流執行完畢。"
