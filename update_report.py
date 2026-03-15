import os
import datetime
import json
import re

# --- Cache Management ---
CACHE_FILE = "macro_cache.json"

class MacroHTMLParser(json.JSONEncoder): # 使用繼承來避開類別定義衝突
    pass

from html.parser import HTMLParser
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
    
    # 穩健性檢查：如果快取指標太少，嘗試從最新報告中還原
    if len(cache.get("US_MACRO", [])) < 5 or len(cache.get("TW_MACRO", [])) < 5:
        print("[Info] 快取數據不完整，嘗試從現有報告還原...")
        reports = [f for f in os.listdir("report") if f.startswith("invest_analysis_") and f.endswith(".html")]
        if reports:
            latest_report = os.path.join("report", sorted(reports)[-1])
            try:
                with open(latest_report, "r", encoding="utf-8") as f:
                    parser = MacroParser()
                    parser.feed(f.read())
                    # 合併數據
                    for region in ["US_MACRO", "TW_MACRO"]:
                        existing_names = {item["name"] for item in cache[region]}
                        for item in parser.results[region]:
                            if item["name"] not in existing_names:
                                item["last_updated"] = "Restored"
                                cache[region].append(item)
                print(f"[Success] 已從 {latest_report} 還原缺失的指標。")
            except Exception as e:
                print(f"[Warning] 還原失敗: {e}")
    return cache

def save_cache(cache_data):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=4)

def get_latest_report_file():
    reports = [f for f in os.listdir("report") if f.startswith("invest_analysis_") and f.endswith(".html")]
    if not reports: return None
    return os.path.join("report", sorted(reports)[-1])

def extract_data_from_html(html_content):
    data = {}
    patterns = {
        "fundamental": r'<script id="fundamental-data" type="application/json">(.*?)</script>',
        "yield": r'<script id="yield-data" type="application/json">(.*?)</script>',
        "market": r'<script id="market-data" type="application/json">(.*?)</script>'
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, html_content, re.DOTALL)
        if match:
            try: data[key] = json.loads(match.group(1))
            except: data[key] = {}
    return data

def load_from_json(filename="technical_data.json"):
    """從 JSON 檔案載入分析所需數據"""
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[Warning] 讀取 {filename} 失敗: {e}")
    return None

def generate_dynamic_ai_analysis(market_info, macro_data):
    yields = market_info.get("yield", {})
    y3m, y10y, y30y = yields.get("3M"), yields.get("10Y"), yields.get("30Y")
    
    atlas_text = "目前全球市場關注聯準會對通膨數據的反應。"
    if y3m and y10y and y30y:
        spreads = {"10Y-3M": y10y - y3m, "30Y-10Y": y30y - y10y, "30Y-3M": y30y - y3m}
        yield_comments = []
        trigger = False
        for pair, val in spreads.items():
            if val < 0 or abs(val) < 0.25:
                trigger = True
                status = "倒掛" if val < 0 else "趨平"
                yield_comments.append(f"{pair} 利差僅 {val:.2f}% ({status})")
        if trigger:
            atlas_text += f" 值得注意的是，殖利率曲線出現警訊：{', '.join(yield_comments)}，顯示市場對長線成長與流動性有所顧慮。"
        else:
            dxy = next((x for x in macro_data.get("US_MACRO", []) if "DXY" in x['name']), None)
            if dxy: atlas_text += f" 目前美元指數 (DXY) 報 {dxy['value']}，整體流動性環境仍是宏觀調控的核心。"

    vix_val = 20
    vix_data = market_info.get("market", {}).get("恐慌指數", [])
    if vix_data: vix_val = vix_data[-1].get("Close", 20)
    sentiment_status = "市場情緒偏向謹慎" if vix_val > 20 else "市場情緒相對穩定"
    
    return f"""
<h3>1. 宏觀策略師 阿特拉斯 (Atlas - Macro Strategist)</h3>
<p><strong>經濟循環與流動性分析：</strong><br>{atlas_text}</p>
<h3>2. 基本面分析師 索菲亞 (Sophia - Fundamental Quality Analyst)</h3>
<p><strong>核心競爭力與估值評估：</strong><br>AI 基礎設施需求依然是全球資本市場的增長引擎. 台積電在先進製程的技術護城河確保了極高的毛利率與 ROE. 從 PEG 估值角度來看, 具備實質獲利能力且處於供應鏈核心的台灣半導體企業, 仍具備高度的內在價值.</p>
<h3>3. 技術面分析師 研二 (Kenji - Technical Chartist)</h3>
<p><strong>趨勢判斷與型態分析：</strong><br>從道氏理論觀察, 美股受到通膨數據與地緣干擾. 投資人應留意 KD、MACD 指標是否出現背離. 台股則在基本面支撐下, 需防範短期乖離率 (BIAS) 過大的修正風險.</p>
<h3>4. 籌碼與散戶心理觀察家 克羅 (Crow - Flow & Sentiment Sentinel)</h3>
<p><strong>資金流向與市場情緒：</strong><br>{sentiment_status}。目前 VIX 指數報 {vix_val:.1f}，資金在避險資產與高成長標的間快速輪動。</p>
<h3>5. 綜合策略分析師 雷恩 (Rain - Portfolio Manager)</h3>
<div class="strategy-card" style="background: #e8f5e9; padding: 15px; border-radius: 8px; border-left: 5px solid #2e7d32;">
    <strong>行動策略與情境推演：</strong>
    <ul>
        <li><strong>基本情境：</strong> 通膨黏性拉長觀望期，AI 長期趨勢不變。建議維持中性偏多，現金比重保留 20% 以應對波動。</li>
        <li><strong>風險控管：</strong> 嚴格設定停損點，若數據引發聯準會實質升息動作，應迅速降低股票部位。</li>
    </ul>
</div>
"""

def generate_macro_table(data, region_id):
    html = f'<table class="macro-table" id="{region_id}"><thead><tr><th style="text-align:left;">指標名稱</th><th style="text-align:right;">數值</th><th style="text-align:right;">日期/備註</th></tr></thead><tbody>'
    for item in data:
        trend_icon = "▲" if item.get('trend') == "up" else "▼" if item.get('trend') == "down" else "-"
        trend_class = "text-up" if item.get('trend') == "up" else "text-down" if item.get('trend') == "down" else "text-secondary"
        val_cell = f'<span class="{trend_class}"><strong>{item["value"]}</strong> <span style="font-size:10px;">{trend_icon}</span></span>'
        html += f'<tr><td style="text-align:left;">{item["name"]}</td><td style="text-align:right;">{val_cell}</td><td style="text-align:right; font-size: 12px; color: #666;">{item["note"]}</td></tr>'
    html += '</tbody></table>'
    return html

def main():
    report_file = get_latest_report_file()
    if not report_file: 
        print("[Error] No report file found in report/ directory.")
        return
    
    # --- Robustness Checks for Intermediate Files ---
    now = datetime.datetime.now().timestamp()
    for filename in ["news.html", "ai.html"]:
        if not os.path.exists(filename):
            print(f"[Error] Required file '{filename}' is missing.")
            return
        
        # Check if file is empty
        if os.path.getsize(filename) < 10:
            print(f"[Error] File '{filename}' is empty or too small.")
            return
            
        # Check file recency (must be updated within the last 5 minutes)
        mtime = os.path.getmtime(filename)
        if (now - mtime) > 300: # 300 seconds = 5 minutes
            print(f"[Error] File '{filename}' is stale (last updated {(now - mtime)/60:.1f} minutes ago).")
            print("[Action] Please update 'news.html' and 'ai.html' with fresh AI content before running this script.")
            return

    # 優先從 JSON 讀取
    market_info = load_from_json()
    if not market_info:
        # 如果 JSON 不存在, 才從 HTML 抓 (保持向下相容)
        with open(report_file, "r", encoding="utf-8") as f: content = f.read()
        market_info = extract_data_from_html(content)
    
    with open(report_file, "r", encoding="utf-8") as f: content = f.read()
    macro_cache = load_cache()
    
    # --- Inject Macro Tables (Robust Replacement) ---
    us_table_html = generate_macro_table(macro_cache.get("US_MACRO", []), "us-macro-table")
    tw_table_html = generate_macro_table(macro_cache.get("TW_MACRO", []), "tw-macro-table")
    
    # 邏輯：先嘗試匹配 placeholder, 若無則匹配已存在的 table
    patterns = {
        "US": (r'<div id="us-macro-placeholder"></div>', r'<table class="macro-table" id="us-macro-table">.*?</table>'),
        "TW": (r'<div id="tw-macro-placeholder"></div>', r'<table class="macro-table" id="tw-macro-table">.*?</table>')
    }
    
    for region, (placeholder_p, table_p) in patterns.items():
        replacement = us_table_html if region == "US" else tw_table_html
        if re.search(placeholder_p, content):
            content = re.sub(placeholder_p, replacement, content)
        else:
            # 使用 re.DOTALL 確保跨行匹配
            content = re.sub(table_p, replacement, content, flags=re.DOTALL)

    # --- Inject AI News ---
    with open("news.html", "r", encoding="utf-8") as f: news_content = f.read().strip()
    news_id = 'weekly-news-focus'
    
    # 移除 news_content 中重複的 id 屬性，避免多層卡片樣式疊加
    news_content = news_content.replace(f'id="{news_id}"', '')
    
    # 僅當內容被外層容器包裹時才移除 (向下相容)
    if f'<div >' in news_content: # 如果 id 已經被移除了，這裡會變成 <div >
        news_content = re.sub(r'^<div >', '', news_content)
        news_content = re.sub(r'</div>$', '', news_content).strip()
    
    # 使用更穩健的替換邏輯：匹配 div 並利用 anchor 標籤定位
    if f'id="{news_id}"' in content:
        # 使用錨點 <!-- news-anchor --> 作為精準匹配終點
        pattern_news = rf'(<div id="{news_id}">).*?(?=<!-- news-anchor -->)'
        if re.search(pattern_news, content, re.DOTALL):
            content = re.sub(pattern_news, f'\\1\n{news_content}\n</div>', content, flags=re.DOTALL)
        else:
            # 如果是初次生成的空標籤
            content = content.replace(f'<div id="{news_id}"></div>', f'<div id="{news_id}">\n{news_content}\n</div>')

    # --- Inject AI Analysis ---
    with open("ai.html", "r", encoding="utf-8") as f: ai_content = f.read().strip()
    ai_id = 'ai-analysis-report'
    
    # 僅當內容被外層容器包裹時才移除
    if f'<div id="{ai_id}"' in ai_content:
        ai_content = re.sub(rf'^<div id="{ai_id}">', '', ai_content)
        ai_content = re.sub(r'</div>$', '', ai_content).strip()
    
    if f'id="{ai_id}"' in content:
        # 使用錨點 <!-- ai-anchor --> 作為精準匹配終點
        pattern_ai = rf'(<div id="{ai_id}">).*?(?=<!-- ai-anchor -->)'
        if re.search(pattern_ai, content, re.DOTALL):
            content = re.sub(pattern_ai, f'\\1\n{ai_content}\n</div>', content, flags=re.DOTALL)
        else:
            content = content.replace(f'<div id="{ai_id}"></div>', f'<div id="{ai_id}">\n{ai_content}\n</div>')

    with open(report_file, "w", encoding="utf-8") as f: f.write(content)
    import shutil
    shutil.copy2(report_file, "index.html")
    print(f"[Success] Done.")

if __name__ == "__main__":
    main()
