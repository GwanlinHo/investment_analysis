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

# Real Data fetched on 2026-02-22
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
    {"source": "Binance", "title": "全球市場迎接「數據風暴」週", "link": "https://www.binance.com", "summary": "投資人屏息以待聯準會會議紀錄與PCE數據，市場波動恐加劇。"},
    {"source": "TheStreet", "title": "聯準會紀錄：官員不排除升息可能", "link": "https://www.thestreet.com", "summary": "1月會議紀錄顯示，若通膨頑固，部分官員討論重啟升息，引發市場震盪。"},
    {"source": "Focus Taiwan", "title": "台積電2026資本支出估達560億美元", "link": "https://focustaiwan.tw", "summary": "為滿足AI與5G強勁需求，傳台積電將上調2026資本支出至歷史新高。"},
    {"source": "FT", "title": "輝達擬向OpenAI注資300億美元", "link": "https://www.ft.com", "summary": "輝達深化AI生態系佈局，傳將參與OpenAI新一輪融資，金額達300億美元。"},
    {"source": "Seeking Alpha", "title": "微軟擴大部署輝達GB300系統", "link": "https://seekingalpha.com", "summary": "超大規模雲端業者加速導入NVIDIA GB300 NVL72，AI基礎設施建設方興未艾。"},
    {"source": "Wealth", "title": "台灣1月外銷訂單暴增69.9%創高", "link": "https://www.wealth.com.tw", "summary": "受惠AI需求噴發，1月外銷訂單達657.7億美元，寫下歷年單月新高紀錄。"},
    {"source": "NDC", "title": "12月景氣亮紅燈 綜合分數38分", "link": "https://www.ndc.gov.tw", "summary": "國內景氣持續熱絡，對策信號轉為紅燈，顯示經濟活動強勁擴張。"},
    {"source": "Whalesbook", "title": "地緣政治與Fed政策壓抑美股", "link": "https://www.whalesbook.com", "summary": "美伊緊張局勢升溫加上貨幣政策不確定性，美股主要指數承壓下挫。"},
    {"source": "Nasdaq", "title": "市場聚焦2/25輝達財報", "link": "https://www.nasdaq.com", "summary": "投資人押注輝達財報將再創驚奇，新技術與中國市場回溫成關鍵。"},
    {"source": "Digitimes", "title": "魏哲家：AI需求真實且持續", "link": "https://www.digitimes.com", "summary": "台積電董座確認AI需求未來幾年不變，相關營收佔比將達高兩位數。"},
    {"source": "DGBAS", "title": "台灣1月CPI年增0.69% 通膨溫和", "link": "https://www.dgbas.gov.tw", "summary": "春節效應未引發物價大漲，1月CPI僅增0.69%，通膨壓力減輕。"},
    {"source": "Reuters", "title": "2026風險：地緣政治與Fed繼任", "link": "https://www.reuters.com", "summary": "市場展望指出，地緣衝突與聯準會領導層更迭將是今年最大變數。"},
    {"source": "CNBC", "title": "參議員關切輝達晶片銷中", "link": "https://www.cnbc.com", "summary": "美國參議員致函商務部，要求審查輝達H200晶片對中國出口狀況。"},
    {"source": "CentralBank", "title": "M1B/M2年增率持穩", "link": "https://www.cbc.gov.tw", "summary": "12月M1B及M2年增率分別為4.85%及5.00%，資金動能維持適度。"},
    {"source": "Market", "title": "美元指數攀升至97.8", "link": "https://tradingeconomics.com", "summary": "避險需求與鷹派預期推升美元指數DXY至97.80價位。"}
]

AI_ANALYSIS_TEXT = """
<h3>1. 總體經濟與循環架構 (Atlas)</h3>
<p>
    <strong>美國：成長降溫與政策分歧</strong><br>
    美國 Q4 GDP 放緩至 1.4%，顯示高利率滯後效應顯現，但 1 月零售銷售年增 5.72% 顯示消費韌性仍強。最令人憂心的是 Fed 內部的分歧：會議紀錄顯示部分官員不排除「重啟升息」以對抗黏性通膨 (CPI 2.4%)，這與市場預期的降息路徑劇烈衝突，導致 DXY 攀升至 97.8。政策不確定性將是 Q1 最大逆風。
</p>
<p>
    <strong>台灣：AI 驅動的紅燈榮景</strong><br>
    台灣總經數據呈現「脫鉤式」暴衝。12 月景氣燈號亮出 38 分紅燈，1 月外銷訂單更以 +69.9% 的驚人年增率創歷史新高，證實 AI 實體需求已進入主升段。CPI 0.69% 的溫和通膨為央行提供了穩定的貨幣環境，台灣正處於「高成長、低通膨」的甜蜜點。
</p>

<h3>2. 基本面質量透視 (Sophia)</h3>
<ul>
    <li><strong>台積電的資本支出護城河：</strong> 傳出 2026 年資本支出上調至 560 億美元，這不僅是產能擴張，更是對競爭對手的「資本門檻」封殺。配合輝達擬注資 OpenAI 300 億美元的消息，AI 基礎設施的長期獲利能見度極高。</li>
    <li><strong>供應鏈的雨露均霑：</strong> 外銷訂單的暴增並非單點突破，而是伺服器、散熱、封測的全面開花。重點關注 ROE 持續提升且 PEG < 1 的設備與耗材族群。</li>
</ul>

<h3>3. 技術與籌碼博弈 (Kenji & Crow)</h3>
<ul>
    <li><strong>美股的修正壓力：</strong> 地緣政治（伊朗）與 Fed 鷹派訊號使美股承壓，技術面需提防 M 頭成型。VIX 雖未失控但蠢蠢欲動，避險情緒推升美元。</li>
    <li><strong>台股的籌碼優勢：</strong> 儘管融資餘額 3680 億仍高，但近期小幅下降顯示籌碼沈澱。加權指數在紅燈基本面支撐下，下檔支撐強勁。操作上需觀察外資在期貨市場的空單是否回補，作為短線多空轉折訊號。</li>
</ul>

<h3>4. 投資策略建議 (Rain)</h3>
<div class="strategy-card" style="background: #e8f5e9; padding: 15px; border-radius: 8px; border-left: 5px solid #2e7d32;">
    <strong>核心策略：強弱分歧下的精準打擊</strong>
    <ul>
        <li><strong>做多台灣 AI 核心 (70%)：</strong> 數據（外銷訂單 +70%）不會說謊。堅定持有 <strong>台積電</strong> 及其高階製程供應鏈。任何受美股拖累的急殺都是絕佳買點。</li>
        <li><strong>避險配置 (30%)：</strong> 面對 Fed 政策不確定性與地緣風險，保留 3 成現金或配置短債/美元部位。避免在財報前追高美股科技股，等待 2/25 輝達財報落地後的方向確認。</li>
        <li><strong>關鍵事件：</strong> 2/25 輝達財報是全村的希望，若指引強勁，將帶動台股挑戰新高。</li>
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
    # Target the specifically generated file
    report_file = "report/invest_analysis_20260222.html"
    
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
