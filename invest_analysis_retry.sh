#!/bin/bash
# invest_analysis_retry.sh -- 投資分析「延1小時」重試守門(cron 每日 08:00)。
# 檢查 GitHub(origin/main) 主頁 index.html 標題日期是否為當日:
#   - 是  -> 07:00 主跑已成功發布,記一行 log 後結束(正常日零成本,不重跑)。
#   - 否  -> 07:00 主跑掛掉(Execution error)或 push 假成功,重跑一次 invest_analysis.sh。
# 用 origin/main(而非本機)判斷,才能同時抓到「跑掛」與「push 失敗」兩種失敗。
# 輸出走 stdout,由 cron 重導至 invest_analysis_cron.log(與 07:00 主跑同 log)。
set -o pipefail
export PATH=/home/pi/.local/bin:$PATH:/home/pi/.config/nvm/versions/node/v22.17.0/bin
REPO=/home/pi/WorkDir/investment_analysis
cd "$REPO" || exit 1

today="$(date +%Y-%m-%d)"
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
