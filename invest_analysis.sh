#!/bin/bash
# 1. 進入專案目錄
cd /home/pi/WorkDir/investment_analysis/

# 2. 執行 Claude Code 進行 AI 分析 (依工作目錄 CLAUDE.md 的 investment analysis 工作流自動執行 Python 腳本)
# 確保 cron 環境能找到 claude 與 uv (皆位於 ~/.local/bin)
export PATH=/home/pi/.local/bin:$PATH:/home/pi/.node-current/bin

# 0. 休市前置守門:前一日美股與台股「都休市(兩市皆無新交易日)」則不出報告。
#    在取重型鎖、啟動 claude 之前先判斷,skip 時不動任何資料、不 commit。
#    保守原則:gate 只有回傳 10 才 skip,其餘(含例外)一律照常執行。
uv run market_open_gate.py
gate_rc=$?
if [ "$gate_rc" -eq 10 ]; then
  echo "$(date -Is) [invest] 休市守門判定 skip,本次不出報告。"
  exit 0
fi

# 全域重型鎖(避免與其他 claude/ASR 併發 OOM);wait 模式:要出報告,寧可等前一個結束也要跑。
source /home/pi/WorkDir/_lib/heavy_lock.sh
acquire_heavy_lock /home/pi/WorkDir/_logs/invest_analysis_cron.log "invest_analysis" "wait" || exit 0

timeout 45m claude -p '請依照本專案目錄的 CLAUDE.md 執行完整的 investment analysis 工作流程，從技術資料生成、總經數據蒐集、新聞、五人格AI分析到 update_report.py 報表注入與同步，全部完成。注意：報告或日誌中若需提及今天是星期幾，務必先執行 `date` 取得系統當前的星期，不可自行用日期推算，以免算錯。' --model claude-opus-5 --dangerously-skip-permissions

# 3. 順利產生後，刪除暫時的 HTML 檔案
rm -f ai_analysis.html tw_macro_table.html us_macro_table.html weekly_news.html
