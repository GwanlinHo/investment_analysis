@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo Git 同步工具
echo ========================================
echo.

REM 取得當前目錄
cd /d "%~dp0"
echo 當前目錄: %CD%
echo.

REM 檢查是否為 Git repository
if not exist ".git" (
    echo [錯誤] 此目錄不是 Git repository
    pause
    exit /b 1
)

REM 步驟 1: Pull - 從遠端拉取更新
echo [步驟 1/4] 從遠端拉取更新...
git pull --no-rebase
if errorlevel 1 (
    echo [警告] Pull 過程中發生問題，嘗試繼續...
)
echo.

REM 步驟 2: Add - 將所有變更加入暫存區
echo [步驟 2/4] 將變更加入暫存區...
git add .
if errorlevel 1 (
    echo [錯誤] 無法加入變更到暫存區
    pause
    exit /b 1
)
echo.

REM 檢查是否有需要提交的變更
git diff-index --quiet HEAD --
if %errorlevel% equ 0 (
    echo [資訊] 沒有需要提交的變更
    echo.
    echo 同步完成！
    pause
    exit /b 0
)

REM 步驟 3: Commit - 建立提交
echo [步驟 3/4] 建立提交...

REM 取得當前時間 (格式: YYYY-MM-DD HH:MM:SS)
for /f "tokens=1-4 delims=/-. " %%a in ('date /t') do (
    set year=%%a
    set month=%%b
    set day=%%c
)
for /f "tokens=1-2 delims=: " %%a in ('time /t') do (
    set hour=%%a
    set minute=%%b
)

REM 格式化時間
set timestamp=%year%-%month%-%day% %hour%:%minute%:00

REM 建立 commit 訊息
set commit_msg=Auto sync - %timestamp% from %COMPUTERNAME%

echo 提交訊息: %commit_msg%
git commit -m "%commit_msg%"
if errorlevel 1 (
    echo [錯誤] 提交失敗
    pause
    exit /b 1
)
echo.

REM 步驟 4: Push - 推送到遠端
echo [步驟 4/4] 推送到遠端...
git push
if errorlevel 1 (
    echo [錯誤] 推送失敗
    echo 請檢查網路連線或遠端 repository 設定
    pause
    exit /b 1
)
echo.

echo ========================================
echo 同步完成！
echo ========================================

