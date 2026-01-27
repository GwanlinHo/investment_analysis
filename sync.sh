#!/bin/bash

# 1. 從遠端拉取並合併 (Pull from remote first)
echo "正在從遠端拉取最新狀態... (Pulling from remote...)"
git pull

# 檢查拉取是否成功 (例如是否有衝突)
if [ $? -ne 0 ]; then
    echo "拉取時發生衝突或錯誤，請先手動解決後再繼續。(Conflict detected. Please resolve manually.)"
    exit 1
fi

# 2. 將所有變更加入暫存區 (Add all changes)
git add .

# 3. 檢查是否有需要提交的變更並提交 (Commit local changes)
if ! git diff-index --quiet HEAD --; then
    echo "發現本地變更，正在提交... (Local changes detected. Committing...)"
    git commit -m "Auto-sync: $(date '+%Y-%m-%d %H:%M:%S')"
else
    echo "沒有本地變更需要提交。(No local changes to commit.)"
fi

# 4. 推送到遠端 (Push to remote)
echo "正在推送到遠端... (Pushing to remote...)"
git push
