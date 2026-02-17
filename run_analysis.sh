#!/bin/bash
# 1. 進入專案目錄
cd /home/pi/WorkDir/investment_analysis/

# 2. 執行 Gemini CLI 進行 AI 分析 (這會根據 GEMINI.md 自動執行 Python 腳本)
export PATH=$PATH:/home/pi/.config/nvm/versions/node/v22.17.0/bin
gemini -p 'investment analysis' -y

# 3. 順利產生後，刪除暫時的 HTML 檔案
rm -f ai_analysis.html tw_macro_table.html us_macro_table.html weekly_news.html
