import os
import datetime
import json
import re
import shutil
from html.parser import HTMLParser

# --- Constants ---
CACHE_FILE = "macro_cache.json"
TECHNICAL_DATA_FILE = "technical_data.json"
AI_CONTEXT_FILE = "ai_context.json"

class MacroParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.results = {"US_MACRO": [], "TW_MACRO": []}
        self.current_region = None
        self.current_row = None
        self.td_index = 0
        self.capture = False
        self.text_buffer = ""

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        if tag == "table":
            if attr_dict.get("id") == "us-macro-table": self.current_region = "US_MACRO"
            elif attr_dict.get("id") == "tw-macro-table": self.current_region = "TW_MACRO"
        elif tag == "tr" and self.current_region:
            self.current_row = {}
            self.td_index = 0
        elif tag == "td" and self.current_region:
            self.capture = True
            self.text_buffer = ""

    def handle_data(self, data):
        if self.capture: self.text_buffer += data

    def handle_endtag(self, tag):
        if tag == "td" and self.current_region:
            self.capture = False
            self.td_index += 1
            val = self.text_buffer.strip()
            if self.td_index == 1: self.current_row["name"] = val
            elif self.td_index == 2:
                self.current_row["value"] = val.replace("▲", "").replace("▼", "").replace("-", "").strip()
                self.current_row["trend"] = "up" if "▲" in self.text_buffer else "down" if "▼" in self.text_buffer else "neutral"
            elif self.td_index == 3: self.current_row["note"] = val
        elif tag == "tr" and self.current_region:
            if self.current_row and "name" in self.current_row and self.current_row["name"] != "指標名稱":
                self.results[self.current_region].append(self.current_row)
            self.current_row = None
        elif tag == "table":
            self.current_region = None

def load_cache():
    cache = {"US_MACRO": [], "TW_MACRO": []}
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)
        except: pass
    return cache

def get_latest_report_file():
    reports = [f for f in os.listdir("report") if f.startswith("invest_analysis_") and f.endswith(".html")]
    if not reports: return None
    return os.path.join("report", sorted(reports)[-1])

def load_from_json(filename):
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[Warning] 讀取 {filename} 失敗: {e}")
    return None

def get_data_context(tech_data, macro_data):
    ctx = {}
    if tech_data and "market" in tech_data:
        m = tech_data["market"]
        if "恐慌指數" in m and m["恐慌指數"]:
            ctx["VIX"] = round(float(m["恐慌指數"][-1].get("Close", 0)), 2)
        taiex_keys = ["台股加權指數", "^TWII", "加權指數"]
        for k in taiex_keys:
            if k in m and m[k]:
                ctx["TAIEX"] = round(float(m[k][-1].get("Close", 0)), 2)
                break
        if "標普 500" in m and m["標普 500"]:
            ctx["SP500"] = round(float(m["標普 500"][-1].get("Close", 0)), 2)

    def find_val(region, name_part):
        for item in macro_data.get(region, []):
            if name_part in item["name"]:
                num_str = re.sub(r'[^\d.]', '', item["value"])
                try: return float(num_str)
                except: return item["value"]
        return None

    ctx["DXY"] = find_val("US_MACRO", "美元指數")
    ctx["US10Y"] = find_val("US_MACRO", "10 年期公債")
    ctx["US3M"] = find_val("US_MACRO", "3 個月期公債")
    ctx["CPI"] = find_val("US_MACRO", "消費者物價指數")
    
    margin_str = find_val("TW_MACRO", "融資餘額")
    if margin_str: ctx["MARGIN_BALANCE"] = margin_str

    with open(AI_CONTEXT_FILE, "w", encoding="utf-8") as f:
        json.dump(ctx, f, ensure_ascii=False, indent=4)
    return ctx

def apply_tags(content, context):
    def replacer(match):
        tag = match.group(1)
        return str(context.get(tag, match.group(0)))
    return re.sub(r'\{\{(.*?)\}\}', replacer, content)

def validate_numerical_integrity(content, context):
    """
    強化版校驗邏輯：將數字分類並嚴格對比事實庫
    """
    # 提取內容中所有的浮點數 (忽略 {{ }} 中的內容，因為那會被替換)
    # 先暫時移除標籤以檢查原始文字中的硬編碼數字
    clean_content = re.sub(r'\{\{.*?\}\}', '', content)
    found_numbers = [float(n) for n in re.findall(r'\d+\.\d+', clean_content)]
    
    # 事實庫數值
    facts = [v for v in context.values() if isinstance(v, (int, float))]
    
    # 針對宏觀指標 (通常 < 1000)
    macro_facts = [v for v in facts if v < 1000]
    max_macro = max(macro_facts) if macro_facts else 150 # 預設 DXY 左右
    
    for n in found_numbers:
        # 如果數字在宏觀範圍 (例如 10-1000 之間)
        if 10 < n < 1000:
            # 檢查它是否與事實庫中的任何宏觀數字接近 (10% 容差)
            matched = False
            for f in macro_facts:
                if abs(n - f) / f < 0.1:
                    matched = True
                    break
            
            if not matched:
                print(f"[Critical Error] 分析內容中發現可疑數字: {n}。")
                print(f"該數字不在事實庫宏觀範圍內 {macro_facts}。")
                print("[Action] 懷疑發生數字幻覺 (Hallucination)，更新已被攔截。")
                return False
    return True

def generate_macro_table(data, region_id):
    html = f'<table class="macro-table" id="{region_id}"><thead><tr><th style="text-align:left;">指標名稱</th><th style="text-align:right;">數值</th><th style="text-align:right;">日期/備註</th></tr></thead><tbody>'
    for item in data:
        trend_icon = "▲" if item.get('trend') == "up" else "▼" if item.get('trend') == "down" else "-"
        trend_class = "text-up" if item.get('trend') == "up" else "text-down" if item.get('trend') == "down" else "text-secondary"
        val_cell = f'<span class="{trend_class}"><strong>{item["value"]}</strong> <span style="font-size:10px;">{trend_icon}</span></span>'
        html += f'<tr><td style="text-align:left;">{item["name"]}</td><td style="text-align:right;">{val_cell}</td><td style="text-align:right; font-size: 12px; color: #666;">{item["note"]}</td></tr>'
    html += '</tbody></table>'
    return html

def is_mostly_chinese(text):
    clean_text = re.sub(r'<[^>]+>', '', text)
    clean_text = re.sub(r'[\s\d]', '', clean_text)
    if not clean_text: return True
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', clean_text))
    return (chinese_chars / len(clean_text)) > 0.3

def main():
    report_file = get_latest_report_file()
    if not report_file: return
    
    tech_data = load_from_json(TECHNICAL_DATA_FILE)
    macro_cache = load_cache()
    context = get_data_context(tech_data, macro_cache)
    
    if not os.path.exists("ai.html"): return
    with open("ai.html", "r", encoding="utf-8") as f: ai_content = f.read().strip()
    
    if not is_mostly_chinese(ai_content): return
    
    # 執行強化版校驗
    if not validate_numerical_integrity(ai_content, context):
        print("[Abort] 由於內容校驗失敗，停止報告更新。")
        return

    ai_content = apply_tags(ai_content, context)

    with open(report_file, "r", encoding="utf-8") as f: content = f.read()
    us_table = generate_macro_table(macro_cache.get("US_MACRO", []), "us-macro-table")
    tw_table = generate_macro_table(macro_cache.get("TW_MACRO", []), "tw-macro-table")
    
    # 支援占位符與現有表格的替換
    content = re.sub(r'<div id="us-macro-placeholder"></div>|<table.*?id="us-macro-table">.*?</table>', us_table, content, flags=re.DOTALL)
    content = re.sub(r'<div id="tw-macro-placeholder"></div>|<table.*?id="tw-macro-table">.*?</table>', tw_table, content, flags=re.DOTALL)

    if os.path.exists("news.html"):
        with open("news.html", "r", encoding="utf-8") as f: news_html = f.read().strip()
        pattern_news = r'(<div id="weekly-news-focus">).*?(?=<!-- news-anchor -->)'
        content = re.sub(pattern_news, f'\\1\n{news_html}\n</div>', content, flags=re.DOTALL)

    # 修正 AI 分析區塊的匹配邏輯 (使用非貪婪模式 .*? 並確保 anchor 正確)
    pattern_ai = r'(<div id="ai-analysis-report">).*?(<!-- ai-anchor -->)'
    
    # 清理 ai_content 中的包裝標籤，避免重複嵌套
    ai_content_clean = re.sub(r'^<div id="ai-analysis-report">', '', ai_content)
    ai_content_clean = re.sub(r'</div>$', '', ai_content_clean).strip()
    
    # 執行替換
    content = re.sub(pattern_ai, f'\\1\n{ai_content_clean}\n\\2', content, flags=re.DOTALL)

    with open(report_file, "w", encoding="utf-8") as f: f.write(content)
    shutil.copy2(report_file, "index.html")
    print(f"[Success] Done.")
    
    # 執行資料清理
    try:
        import prune_manager
        prune_manager.prune_reports()
        prune_manager.prune_technical_data()
    except Exception as e:
        print(f"[Warning] 清理過程中發生錯誤: {e}")

if __name__ == "__main__":
    main()
