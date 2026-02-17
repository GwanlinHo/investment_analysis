#!/bin/bash
# 1. 進入專案目錄
cd /home/pi/WorkDir/investment_analysis/

# 2. 使用虛擬環境的 Python 執行腳本
./.venv/bin/python3 investment_analysis.py

# 3. 執行 Gemini CLI 進行 AI 分析
export PATH=$PATH:/home/pi/.config/nvm/versions/node/v22.17.0/bin
gemini -p 'investment analysis' -y
