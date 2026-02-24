import os
import datetime
import json
import re

# --- Cache Management ---
CACHE_FILE = "macro_cache.json"

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"US_MACRO": [], "TW_MACRO": []}

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
    if not report_file: return
    with open(report_file, "r", encoding="utf-8") as f: content = f.read()
    market_info = extract_data_from_html(content)
    macro_cache = load_cache()
    
    content = content.replace('<div id="us-macro-placeholder"></div>', generate_macro_table(macro_cache.get("US_MACRO", []), "us-macro-table"))
    content = content.replace('<div id="tw-macro-placeholder"></div>', generate_macro_table(macro_cache.get("TW_MACRO", []), "tw-macro-table"))
    
    with open("ai.html", "r", encoding="utf-8") as f: ai_report_container = f.read()
    if '<div id="ai-analysis-report">' in content:
        content = re.sub(r'<div id="ai-analysis-report">.*?</div>', ai_report_container, content, flags=re.DOTALL)
    else: content = content.replace('<div id="ai-analysis-report"></div>', ai_report_container)

    with open("news.html", "r", encoding="utf-8") as f: news_container = f.read()
    if '<div id="weekly-news-focus">' in content:
        content = re.sub(r'<div id="weekly-news-focus">.*?</div>', news_container, content, flags=re.DOTALL)
    else: content = content.replace('<div id="weekly-news-focus"></div>', news_container)

    with open(report_file, "w", encoding="utf-8") as f: f.write(content)
    import shutil
    shutil.copy2(report_file, "index.html")
    print(f"[Success] Done.")

if __name__ == "__main__":
    main()
