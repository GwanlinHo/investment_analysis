#!/bin/bash
# 讓腳本在遇到錯誤時立即停止執行
set -e

# 取得腳本所在的目錄，並切換至該目錄，增加可攜性
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

echo "[Info] 開始執行投資分析工作流..."

# 檢查 claude 指令是否存在
if ! command -v claude &> /dev/null; then
    echo "[Error] 找不到 'claude' 指令。請確保已安裝 Claude Code 並正確設定 PATH。"
    exit 1
fi

# 執行 Claude Code 進行完整的投資分析工作流 (包含 Python 資料生成、AI 搜尋與報告更新)
# 這裡使用 'investment analysis' 觸發 CLAUDE.md 中定義的自動化流程
claude -p '請依照本專案目錄的 CLAUDE.md 執行完整的 investment analysis 工作流程，從技術資料生成、總經數據蒐集、新聞、五人格AI分析到 update_report.py 報表注入與同步，全部完成。' --dangerously-skip-permissions

echo "[Success] 投資分析工作流執行完畢。"
