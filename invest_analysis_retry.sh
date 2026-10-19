#!/bin/bash
# invest_analysis_retry.sh -- 投資分析「延1小時」重試守門(cron 夏令 07:00 / 冬令 08:00,主跑+1 小時)。
# 檢查 GitHub(origin/main) 主頁 index.html 標題日期是否為當日:
#   - 是  -> 07:00 主跑已成功發布,記一行 log 後結束(正常日零成本,不重跑)。
#   - 否  -> 07:00 主跑掛掉(Execution error)或 push 假成功,重跑一次 invest_analysis.sh。
# 用 origin/main(而非本機)判斷,才能同時抓到「跑掛」與「push 失敗」兩種失敗。
# 輸出走 stdout,由 cron 重導至 invest_analysis_cron.log(與 07:00 主跑同 log)。
set -o pipefail
export PATH=/home/pi/.local/bin:$PATH:/home/pi/.node-current/bin
REPO=/home/pi/WorkDir/investment_analysis
cd "$REPO" || exit 1

today="$(date +%Y-%m-%d)"

# 休市日不需要報告。主跑的休市守門 skip 時會把日期寫進 .last_gate_skip,此處據以直接放行。
# 沒有這一段的話,本腳本只會拿「已發布報告日期」比對「今天」,於是每個非交易日(週末、
# 週一早上、國定假日)都必然對不上,印出 [!] 並多重跑一次 —— 真正的失敗會被這些假警訊淹沒。
# 不在此直接重跑 market_open_gate.py:守門是拿 Yahoo 最新日比對 technical_data.json,
# 若主跑寫完 technical_data.json 後才掛掉,守門會回「未動」而讓真正該補的報告被跳過。
if [ "$(cat "$REPO/.last_gate_skip" 2>/dev/null)" = "$today" ]; then
  echo "$(date -Is) [retry-guard][O] 今日(${today})主跑已判定休市,無需報告,免重試"
  exit 0
fi

git fetch origin main >/dev/null 2>&1
published="$(git show origin/main:index.html 2>/dev/null \
  | grep -oE '<title>[^<]*</title>' \
  | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}' | head -1)"

if [ "$published" = "$today" ]; then
  echo "$(date -Is) [retry-guard][O] 今日(${today})報告已在 GitHub,免重試"
  exit 0
fi

echo "$(date -Is) [retry-guard][!] GitHub 最新報告為 ${published:-未知},非今日(${today}),觸發重跑一次"
/home/pi/WorkDir/investment_analysis/invest_analysis.sh
echo "$(date -Is) [retry-guard] 重跑結束 rc=$?"
exit 0
