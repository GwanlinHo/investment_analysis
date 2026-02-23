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

CURRENT_US_DATA = [
    {"name": "國內生產毛額 (GDP) Q4", "value": "1.4%", "note": "2025 Q4 (年化初值)", "trend": "down"},
    {"name": "消費者物價指數 (CPI)", "value": "2.4%", "note": "2026-01 (YoY)", "trend": "down"},
    {"name": "生產者物價指數 (PPI)", "value": "3.0%", "note": "2025-12 (YoY)", "trend": "up"},
    {"name": "零售銷售 (Retail Sales)", "value": "+5.72%", "note": "2026-01 (YoY)", "trend": "up"},
    {"name": "非農就業人口", "value": "+13.0萬", "note": "2026-01", "trend": "neutral"},
    {"name": "失業率", "value": "4.3%", "note": "2026-01", "trend": "up"},
    {"name": "初領失業金人數", "value": "20.6萬", "note": "截至 2/14", "trend": "down"},
    {"name": "ISM 製造業指數", "value": "52.6", "note": "2026-01 (擴張)", "trend": "up"},
    {"name": "M2 貨幣供給", "value": "22.41兆", "note": "2025-12", "trend": "up"},
    {"name": "美元指數 (DXY)", "value": "97.80", "note": "2026-02-21", "trend": "up"},
]

CURRENT_TW_DATA = [
    {"name": "景氣對策信號", "value": "38分 (紅燈)", "note": "2025-12", "trend": "up"},
    {"name": "外銷訂單", "value": "657.7億美元", "note": "2026-01 (+69.9%)", "trend": "up"},
    {"name": "消費者物價指數 (CPI)", "value": "0.69%", "note": "2026-01 (YoY)", "trend": "down"},
    {"name": "工業生產指數", "value": "+21.57%", "note": "2025-12 (YoY)", "trend": "up"},
    {"name": "消費者信心指數 (CCI)", "value": "67.16", "note": "2026-01", "trend": "up"},
    {"name": "M1B 年增率", "value": "4.85%", "note": "2025-12", "trend": "down"},
    {"name": "M2 年增率", "value": "5.00%", "note": "2025-12", "trend": "down"},
    {"name": "失業率", "value": "3.35%", "note": "2026-01", "trend": "up"},
    {"name": "融資餘額", "value": "3680.47億", "note": "截至 2/11", "trend": "down"},
    {"name": "信用卡逾期率", "value": "0.25%", "note": "2025-10", "trend": "neutral"},
]

NEWS_ITEMS = [
    {"source": "U.S. Bank", "title": "評估通膨影響", "summary": "核心PCE在12月達到3.0%，高於預期，聯準會的目標是2%。"},
    {"source": "Federal Reserve Board", "title": "聯準會貨幣政策", "summary": "12月PCE物價指數月增0.4%，高於預期，核心PCE年增3.0%，為2024年4月以來最高。"},
    {"source": "U.S. Bank", "title": "聯準會降息預期", "summary": "聯準會預計2026年再降息一次，但市場預期可能會有兩到三次。"},
    {"source": "NerdWallet", "title": "聯準會首選通膨指標", "summary": "核心PCE是聯準會首選的通膨衡量指標，目前仍高於2%的目標。"},
    {"source": "Nasdaq", "title": "聯準會官員對利率路徑的看法", "summary": "聯準會官員暗示，如果通膨持續高於目標，可能需要升息。"},
    {"source": "Nasdaq", "title": "地緣政治風險推高油價和金價", "summary": "伊朗局勢導致地緣政治風險升高，推動油價和金價上漲。"},
    {"source": "Nasdaq", "title": "VIX指數上升", "summary": "VIX指數升至20.8，顯示市場不確定性增加。"},
    {"source": "Financial Post", "title": "避險需求推動公債上漲", "summary": "地緣政治緊張局勢和對通膨前景的擔憂，促使公債因避險需求而上漲。"},
    {"source": "Morningstar", "title": "美伊地緣政治風險推動油價上漲", "summary": "美國與伊朗之間的緊張關係使地緣政治風險溢價居高不下，推動油價上漲。"},
    {"source": "Trading Economics", "title": "美國10年期公債殖利率因地緣政治風險下滑", "summary": "美國與伊朗之間不斷升級的緊張局勢引發避險需求，導致美國10年期公債殖利率下滑。"},
    {"source": "Nasdaq", "title": "人工智慧投資的擔憂", "summary": "市場擔憂人工智慧可能顛覆整個經濟領域，且巨額投資可能無法獲得回報。"},
    {"source": "The Motley Fool", "title": "台積電受惠於AI基礎設施建設", "summary": "台積電是人工智慧基礎設施建設的主要受益者，預計到2029年營收複合年增長率為25%。"},
    {"source": "The Motley Fool", "title": "台積電股價表現強勁", "summary": "台積電股價在過去五年上漲了170%。"},
    {"source": "Investing.com Canada", "title": "台灣上調2026年經濟增長預測", "summary": "受人工智慧需求推動，台灣將2026年經濟增長預測上調至7.7%。"},
    {"source": "Investing.com Canada", "title": "科技股因AI支出擔憂而下跌", "summary": "由於對人工智慧支出的擔憂，大型科技股損失了數十億美元的市值。"}
]

AI_ANALYSIS_TEXT = """
<h3>1. 宏觀策略師 阿特拉斯 (Atlas - Macro Strategist)</h3>
<p>
    <strong>經濟循環與流動性分析：</strong><br>
    近期數據顯示美國核心 PCE 意外彈升至 3.0%，高於聯準會的 2% 目標。這使得市場對降息的預期必須重新錨定。聯準會官員甚至暗示，若通膨居高不下可能需要考慮升息，這直接反映在美元指數 (DXY) 走強與流動性緊縮的擔憂上。10Y-3M 殖利率曲線倒掛現象仍需密切關注。相對而言，台灣受惠於 AI 出口帶動，外銷訂單年增高達 69.9%，景氣信號亮出 38 分紅燈，展現出極強的抗壓性。宏觀環境正處於「美放緩、台擴張」的分歧階段。
</p>

<h3>2. 基本面質量專家 索菲亞 (Sophia - Fundamental Quality Analyst)</h3>
<p>
    <strong>核心競爭力與估值評估：</strong><br>
    AI 基礎設施需求依然是全球資本市場的增長引擎。台積電受惠於此，未來幾年營收複合年增長率上看 25%，其在先進製程的技術護城河確保了極高的毛利率與 ROE。儘管近期市場對 AI 巨額投資的回報產生疑慮，導致部分大型科技股市值受挫，但從 PEG 估值角度來看，具備實質獲利能力且處於供應鏈核心的台灣半導體企業，仍具備高度的內在價值與長線投資的安全邊際。
</p>

<h3>3. 技術派專家 研二 (Kenji - Technical Chartist)</h3>
<p>
    <strong>趨勢判斷與型態分析：</strong><br>
    從道氏理論觀察，美股受到地緣政治干擾與通膨數據影響，次級折返走勢變得劇烈。投資人需留意納斯達克指數是否出現頭部型態以及 KD、MACD 指標的潛在背離。台股加權指數則在基本面強勁支撐下，沿著短中期均線向上，但仍須防範乖離率 (BIAS) 過大的修正風險。前一個交易日K線若出現高檔十字線或長上影線，將是短線獲利了結的技術性警訊。
</p>

<h3>4. 籌碼與心理哨兵 克羅 (Crow - Flow & Sentiment Sentinel)</h3>
<p>
    <strong>資金流向與市場情緒：</strong><br>
    避險情緒正主導資金流向，VIX 指數攀升至 20.8 顯示市場恐慌與不確定性增加。美伊緊張局勢推升了金價與油價，同時促使資金湧入美國公債避險，壓低了 10 年期公債殖利率。在台灣市場方面，外資動向受國際避險情緒影響可能出現波動，但台灣內部資金充沛，M1B 與 M2 年增率維持穩定，需持續追蹤融資與融券餘額的變化，防範 AI 概念股過度擁擠的交易風險。
</p>

<h3>5. 總組合執行官 雷恩 (Rain - Portfolio Manager)</h3>
<div class="strategy-card" style="background: #e8f5e9; padding: 15px; border-radius: 8px; border-left: 5px solid #2e7d32;">
    <strong>行動策略與情境推演：</strong>
    <ul>
        <li><strong>基本情境 (Base Case)：</strong> 通膨黏性拉長聯準會觀望期，地緣風險帶來短期震盪，但 AI 長期趨勢不變。建議維持中性偏多，現金比重保留 20-30% 以應對波動。</li>
        <li><strong>戰術配置：</strong> 聚焦台灣具備高 ROE 的半導體與 AI 供應鏈核心標的，逢技術面回檔且籌碼安定時分批佈局。同時可配置部分美國公債作為避險緩衝。</li>
        <li><strong>風險控管：</strong> 嚴格設定停損點，若油價因中東衝突失控飆升，或通膨數據引發聯準會實質升息動作，應迅速降低股票部位，並增持避險資產。</li>
    </ul>
</div>
"""

# --- HTML Generator ---
def generate_macro_table(data, region_id):
    html = f'<table class="macro-table" id="{region_id}"><thead><tr><th style="text-align:left;">指標名稱</th><th style="text-align:right;">數值</th><th style="text-align:right;">日期/備註</th></tr></thead><tbody>'
    for item in data:
        trend_icon = "▲" if item['trend'] == "up" else "▼" if item['trend'] == "down" else "-"
        trend_class = "text-up" if item['trend'] == "up" else "text-down" if item['trend'] == "down" else "text-secondary"
        
        val_cell = f'<span class="{trend_class}"><strong>{item["value"]}</strong> <span style="font-size:10px;">{trend_icon}</span></span>'
        
        html += f'<tr><td style="text-align:left;">{item["name"]}</td><td style="text-align:right;">{val_cell}</td><td style="text-align:right; font-size: 12px; color: #666;">{item["note"]}</td></tr>'
    html += '</tbody></table>'
    return html

def generate_news_list(news_items):
    html = '<div id="weekly-news-focus"><h2>財經焦點 (Weekly Focus)</h2><ul class="news-list" style="list-style: none; padding: 0;">'
    for item in news_items:
        html += f'<li style="margin-bottom: 15px; border-bottom: 1px solid #eee; padding-bottom: 10px;">'
        html += f'<div style="font-weight: bold; font-size: 16px; color: #1a237e; margin-bottom: 4px;">[{item["source"]}] {item["title"]}</div>'
        html += f'<div style="font-size: 14px; color: #444; line-height: 1.5;">{item["summary"]}</div>'
        html += '</li>'
    html += '</ul></div>'
    return html

def generate_ai_analysis(text):
    html = '<div id="ai-analysis-report"><h2>AI 綜合分析報告 (Comprehensive Analysis)</h2>'
    html += '<div class="analysis-content" style="font-size: 16px; line-height: 1.8; color: #333;">'
    html += text
    html += '</div></div>'
    return html

# --- Main Execution ---
def main():
    report_file = "report/invest_analysis_20260223.html"
    
    if not os.path.exists(report_file):
        print(f"Error: {report_file} not found.")
        return

    # 1. Load Cache
    cache = load_cache()

    # 2. Merge current search results with cache
    def merge_data(current, cached):
        merged = []
        updated = False
        current_map = {item['name']: item for item in current}
        cached_map = {item['name']: item for item in cached}
        
        all_names = list(current_map.keys())
        for name in cached_map.keys():
            if name not in all_names:
                all_names.append(name)
                
        for name in all_names:
            if name in current_map:
                new_item = current_map[name].copy()
                new_item['last_updated'] = datetime.datetime.now().strftime("%Y-%m-%d")
                merged.append(new_item)
                updated = True
            elif name in cached_map:
                merged.append(cached_map[name])
                
        return merged, updated

    us_merged, us_updated = merge_data(CURRENT_US_DATA, cache.get("US_MACRO", []))
    tw_merged, tw_updated = merge_data(CURRENT_TW_DATA, cache.get("TW_MACRO", []))

    # 3. Update Cache File if needed
    if us_updated or tw_updated:
        cache["US_MACRO"] = us_merged
        cache["TW_MACRO"] = tw_merged
        save_cache(cache)
        print("[Info] Macro Cache Updated.")

    with open(report_file, "r", encoding="utf-8") as f:
        content = f.read()

    # 4. Inject Tables
    us_table = generate_macro_table(us_merged, "us-macro-table")
    content = content.replace('<div id="us-macro-placeholder"></div>', us_table)

    tw_table = generate_macro_table(tw_merged, "tw-macro-table")
    content = content.replace('<div id="tw-macro-placeholder"></div>', tw_table)

    # 5. Inject News
    news_html = generate_news_list(NEWS_ITEMS)
    if '<div id="weekly-news-focus">' in content:
        content = re.sub(r'<div id="weekly-news-focus">.*?</div>', news_html, content, flags=re.DOTALL)
    else:
        content = content.replace('<div id="weekly-news-focus"></div>', news_html)

    # 6. Inject AI Analysis
    ai_html = generate_ai_analysis(AI_ANALYSIS_TEXT)
    if '<div id="ai-analysis-report">' in content:
        content = re.sub(r'<div id="ai-analysis-report">.*?</div>', ai_html, content, flags=re.DOTALL)
    else:
        content = content.replace('<div id="ai-analysis-report"></div>', ai_html)

    # 7. Save Final
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(content)
        
    print(f"[Success] Updated {report_file} with Real Data.")
    
    # Sync to root index.html
    import shutil
    shutil.copy2(report_file, "index.html")
    print(f"[Info] Synced to index.html")

if __name__ == "__main__":
    main()