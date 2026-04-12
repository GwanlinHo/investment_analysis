import json
import os
import glob
from datetime import datetime

# 設定保留策略
MAX_REPORT_FILES = 30
MAX_TECH_DATA_DAYS = 120
REPORT_DIR = "report/"
TECH_DATA_PATH = "technical_data.json"

def prune_reports():
    """清理舊的 HTML 報告，僅保留最近 30 份"""
    print(f"[*] 正在清理 {REPORT_DIR} 中的舊報表...")
    report_pattern = os.path.join(REPORT_DIR, "invest_analysis_*.html")
    report_files = glob.glob(report_pattern)
    
    # 按檔案名稱日期排序 (invest_analysis_YYYYMMDD.html)
    report_files.sort(reverse=True)
    
    if len(report_files) > MAX_REPORT_FILES:
        files_to_delete = report_files[MAX_REPORT_FILES:]
        for f in files_to_delete:
            try:
                os.remove(f)
                # print(f"    - 已刪除: {f}")
            except Exception as e:
                print(f"    [!] 無法刪除 {f}: {e}")
        print(f"[*] 已成功清理 {len(files_to_delete)} 份舊報表。")
    else:
        print("[*] 報表數量未達清理門檻。")

def prune_technical_data():
    """清理 technical_data.json，每個標的僅保留最近 120 筆資料"""
    if not os.path.exists(TECH_DATA_PATH):
        print(f"[!] 找不到 {TECH_DATA_PATH}，跳過清理。")
        return

    print(f"[*] 正在清理 {TECH_DATA_PATH} 的歷史資料 (保留最近 {MAX_TECH_DATA_DAYS} 筆)...")
    try:
        with open(TECH_DATA_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 根據實際結構清理 'market'
        if "market" in data:
            for symbol in data["market"]:
                hist_list = data["market"][symbol]
                if isinstance(hist_list, list) and len(hist_list) > MAX_TECH_DATA_DAYS:
                    data["market"][symbol] = hist_list[-MAX_TECH_DATA_DAYS:]
            
            with open(TECH_DATA_PATH, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print("[*] technical_data.json 清理完成。")
        else:
            print("[!] technical_data.json 中找不到 'market' 欄位。")
    except Exception as e:
        print(f"[!] 清理 JSON 時發生錯誤: {e}")

if __name__ == "__main__":
    prune_reports()
    prune_technical_data()
