
import os
import datetime

# --- Data ---
US_MACRO = [
    {"name": "國內生產毛額 (GDP) Q4", "value": "1.4%", "note": "2025 Q4 (年化)", "trend": "down"},
    {"name": "消費者物價指數 (CPI)", "value": "2.4%", "note": "2026-01 (YoY)", "trend": "down"},
    {"name": "生產者物價指數 (PPI)", "value": "3.0%", "note": "2025-12 (YoY)", "trend": "up"},
    {"name": "零售銷售 (Retail Sales)", "value": "0.0%", "note": "2025-12 (MoM)", "trend": "neutral"},
    {"name": "非農就業人口", "value": "+13.0萬", "note": "2026-01", "trend": "neutral"},
    {"name": "失業率", "value": "4.3%", "note": "2026-01", "trend": "up"},
    {"name": "初領失業金人數", "value": "22.7萬", "note": "截至 2026-02-07", "trend": "neutral"},
    {"name": "ISM 製造業指數", "value": "52.6", "note": "2026-01", "trend": "up"},
    {"name": "M2 貨幣供給", "value": "4.60%", "note": "2025-12 (YoY)", "trend": "up"},
    {"name": "實質私人投資", "value": "3.8%", "note": "2025 Q4 (成長率)", "trend": "up"},
]

TW_MACRO = [
    {"name": "景氣對策信號", "value": "38分 (紅燈)", "note": "2025-12", "trend": "up"},
    {"name": "外銷訂單", "value": "+43.8%", "note": "2025-12 (YoY)", "trend": "up"},
    {"name": "工業生產指數", "value": "+21.57%", "note": "2025-12 (YoY)", "trend": "up"},
    {"name": "消費者信心指數 (CCI)", "value": "67.16", "note": "2026-01", "trend": "up"},
    {"name": "失業率", "value": "3.30%", "note": "2025-12", "trend": "down"},
    {"name": "製造業加班工時", "value": "17.6小時", "note": "2025-12", "trend": "up"},
    {"name": "融資餘額", "value": "3680.47億", "note": "-45.40億 (2/11)", "trend": "down"},
    {"name": "融券餘額", "value": "24.8萬張", "note": "-1771張 (2/11)", "trend": "down"},
]

NEWS_ITEMS = [
    {"source": "TradingKey", "title": "聯準會新主席沃許上任：貨幣政策大轉向？", "link": "https://www.tradingkey.com", "summary": "川普提名凱文·沃許為下一任主席，主張縮表加降息，市場關注2026貨幣政策轉向。"},
    {"source": "財經新報", "title": "Fed 會議紀錄偏鷹，決策者看法分歧", "link": "https://technews.tw", "summary": "1月會議紀錄顯示官員對降息路徑有歧見，若通膨持續不排除維持高利率。"},
    {"source": "CNYES", "title": "川普全球關稅被推翻 美股歡漲", "link": "https://news.cnyes.com", "summary": "最高法院裁定川普依IEEPA實施的全球關稅違憲，市場解讀為貿易戰風險解除，股市大漲。"},
    {"source": "經濟日報", "title": "美第四季GDP僅增1.4% 受政府停擺拖累", "link": "https://money.udn.com", "summary": "受2025年底政府停擺影響，Q4 GDP成長放緩至1.4%，但私人投資仍強勁。"},
    {"source": "FX168", "title": "資金湧入歐洲股市 對沖美國風險", "link": "https://www.fx168.com", "summary": "投資人擔憂美國政治不確定性，資金創紀錄規模流入歐股，防務與銀行股受惠。"},
    {"source": "Reuters", "title": "輝達財報成焦點 AI資本支出受檢視", "link": "https://www.reuters.com", "summary": "輝達將於2/26公布財報，市場高度關注AI變現能力與巨頭資本支出持續性。"},
    {"source": "自由時報", "title": "日本通膨降至1.5% 跌破央行目標", "link": "https://ec.ltn.com.tw", "summary": "日本1月通膨率降至1.5%，為2022年來新低，日銀升息壓力減輕。"},
    {"source": "經濟日報", "title": "美初領失業金22.7萬人 就業市場降溫", "link": "https://money.udn.com", "summary": "最新一週初領失業金人數略高於預期，顯示勞動市場逐漸放緩但未崩潰。"},
    {"source": "Nasdaq", "title": "Cadence 財報優於預期 積壓訂單創高", "link": "https://www.nasdaq.com", "summary": "受惠AI晶片設計需求，Cadence Q4業績與展望皆強勁，顯示半導體上游景氣熱絡。"},
    {"source": "TradingKey", "title": "地緣政治緊張 油價波動加劇", "link": "https://www.tradingkey.com", "summary": "美國對委內瑞拉制裁及中東局勢，推升原油價格波動，成為通膨潛在變數。"},
    {"source": "工商時報", "title": "台積電1月營收4012億 創歷史新高", "link": "https://ctee.com.tw", "summary": "受惠AI強勁需求，台積電1月營收年增36.8%，首度突破4000億大關。"},
    {"source": "國發會", "title": "12月景氣燈號亮紅燈 分數38分", "link": "https://www.ndc.gov.tw", "summary": "台灣景氣對策信號轉為紅燈，顯示經濟處於熱絡狀態，出口與生產皆強勁。"},
    {"source": "Focus Taiwan", "title": "12月外銷訂單年增43.8% 創歷年同期新高", "link": "https://focustaiwan.tw", "summary": "受惠AI及高效能運算需求，台灣12月外銷訂單表現亮眼，年增率達雙位數。"},
    {"source": "鉅亨網", "title": "台積電ADR春節大漲 台股開紅盤看俏", "link": "https://news.cnyes.com", "summary": "休市期間台積電ADR上漲，法人看好台股金馬年開紅盤挑戰歷史新高。"},
    {"source": "明日智庫", "title": "兩岸衝突強度降溫 地緣風險趨緩", "link": "https://www.tomorrow.org.tw", "summary": "2026年2月兩岸軍事與政治摩擦顯著減少，地緣政治風險指數下降。"}
]

# --- Analysis Text ---
AI_ANALYSIS_TEXT = """
<h3>1. 總體經濟與循環架構</h3>
<p>
    <strong>美國經濟：軟著陸中的政策轉折</strong><br>
    美國 2025 Q4 GDP 雖受政府停擺影響降至 1.4%，但私人投資仍維持 3.8% 的穩健增長，顯示實體經濟韌性猶存。通膨方面，1 月 CPI 降至 2.4%，雖高於 2% 目標但趨勢向下；惟 PPI 反彈至 3.0% 暗示上游價格壓力未除。最關鍵的轉折在於最高法院推翻川普全球關稅，大幅降低了貿易戰引發的通膨與衰退風險，市場解讀為重大利多。此外，聯準會主席提名人選沃許主張「縮表+降息」，預示 2026 年貨幣政策將進入新的結構性調整期。殖利率曲線（10Y-3M）目前呈現正斜率（+0.49%），顯示市場對未來經濟擴張重拾信心，衰退警報解除。
</p>
<p>
    <strong>台灣經濟：AI 驅動的繁榮擴張</strong><br>
    台灣經濟正處於典型的「繁榮期」。12 月景氣燈號亮出代表熱絡的「紅燈」（38分），外銷訂單年增率高達 43.8%，創下 16 年來次高紀錄，完全由 AI 與高效能運算需求驅動。台積電 1 月營收突破 4000 億元大關創新高，證實硬體基本面極度強勁。與美國的「軟著陸」相比，台灣呈現「強勁擴張」態勢。
</p>

<h3>2. 市場資金動能與評價</h3>
<ul>
    <li><strong>資金流向：</strong> 美國關稅風險解除後，全球資金風險偏好提升。雖然部分資金分散至歐洲以對沖美國政治風險，但 AI 核心資產（美股七巨頭、台積電）仍是吸金主力。美元指數在關稅利空下可能轉弱，有利於新興市場與亞幣資產。</li>
    <li><strong>評價面：</strong> 台股與美股科技股評價雖處高檔，但獲利成長性（Earnings Growth）足以支撐。台積電 Forward PE 僅約 17.5 倍，相較於其 30%+ 的營收成長率，PEG 遠小於 1，評價甚至被低估。</li>
    <li><strong>籌碼面：</strong> 台灣融資餘額近期小幅減少（-45億），顯示散戶在農曆年前後操作謹慎，籌碼相對安定，有利於年後法人回補發動攻勢。</li>
</ul>

<h3>3. 深度焦點分析：台積電 (2330.TW)</h3>
<ul>
    <li><strong>基本面護城河：</strong> 1 月營收月增 19.8%、年增 36.8%，毛利率維持在 60% 高檔，ROE 高達 35%。在 AI 晶片壟斷地位穩固下，幾乎沒有競爭對手能威脅其定價權。</li>
    <li><strong>技術面結構：</strong>
        <ul>
            <li><strong>道氏理論：</strong> 主要趨勢（Primary Trend）呈現明確多頭排列，休市期間 ADR 創高預示現貨將跳空開高，確認新一輪漲勢。</li>
            <li><strong>指標分析：</strong> KD 與 MACD 均處於多方強勢區。需留意若跳空過大造成的短線乖離過大（BIAS），但長線趨勢完好。</li>
        </ul>
    </li>
    <li><strong>操作策略：</strong> 由於基本面與消息面共振，建議採取「拉回即買點」策略。支撐區上移至 1050-1080 元整數關卡，若有回測均為長線布局良機。</li>
</ul>

<h3>4. 投資策略建議</h3>
<div class="strategy-card" style="background: #e8f5e9; padding: 15px; border-radius: 8px; border-left: 5px solid #2e7d32;">
    <strong>核心觀點：多頭續行，聚焦 AI 硬體與政策受惠股</strong>
    <ul>
        <li><strong>積極型配置 (70%)：</strong> 重倉 <strong>AI 半導體 / 伺服器供應鏈</strong> (台積電、廣達、鴻海)。關稅風險解除後，亦可關注先前受壓抑的<strong>非電族群</strong>或<strong>航運股</strong> (貿易量回升)。</li>
        <li><strong>防禦型配置 (30%)：</strong> 雖然衰退風險降低，但地緣政治仍存變數。保留部分<strong>美國短債 (SHV)</strong> 或 <strong>投資級債 (LQD)</strong> 以獲取穩定收益，並對沖股市高檔波動。</li>
        <li><strong>風險監控：</strong> 密切觀察 2/26 輝達財報指引，以及 3 月聯準會會議紀錄對通膨的態度。若 CPI 意外反彈至 3% 以上，需降低槓桿。</li>
    </ul>
</div>
"""

# --- Helper Functions ---
def generate_macro_table(data, region_id):
    html = f'<table class="macro-table" id="{region_id}"><thead><tr><th style="text-align:left;">指標名稱</th><th style="text-align:right;">數值</th><th style="text-align:right;">日期/備註</th></tr></thead><tbody>'
    for item in data:
        trend_icon = "▲" if item['trend'] == "up" else "▼" if item['trend'] == "down" else "-"
        trend_class = "text-up" if item['trend'] == "up" else "text-down" if item['trend'] == "down" else "text-secondary"
        # Invert colors for Unemployment (Down is Good/Red? No, usually Red is Up/Hot in TW stock context, but for econ indicators:
        # GEMINI.md says: "Red for Up/Positive, Green for Down/Negative".
        # For Unemployment, Up is Negative (Green?), Down is Positive (Red?).
        # Let's stick to strict direction: Red = Up, Green = Down.
        # User interpretation of good/bad is separate.
        
        # Special handling for "Red Light" in text? No, just stick to arrow color.
        
        val_cell = f'<span class="{trend_class}"><strong>{item["value"]}</strong> <span style="font-size:10px;">{trend_icon}</span></span>'
        
        html += f'<tr><td style="text-align:left;">{item["name"]}</td><td style="text-align:right;">{val_cell}</td><td style="text-align:right; font-size: 12px; color: #666;">{item["note"]}</td></tr>'
    html += '</tbody></table>'
    return html

def generate_news_list(news_items):
    html = '<div id="weekly-news-focus"><h2>財經焦點 (Weekly Focus)</h2><ul class="news-list" style="list-style: none; padding: 0;">'
    for item in news_items:
        html += f'<li style="margin-bottom: 15px; border-bottom: 1px solid #eee; padding-bottom: 10px;">'
        html += f'<div style="font-weight: bold; font-size: 16px; color: #1a237e; margin-bottom: 4px;">[{item["source"]}] {item["title"]}</div>'
        html += f'<div style="font-size: 14px; color: #444; line-height: 1.5;">{item["summary"]} <a href="{item["link"]}" target="_blank" style="color: #999; text-decoration: none; font-size: 12px;">(來源)</a></div>'
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
report_file = "report/invest_analysis_20260222.html"
if not os.path.exists(report_file):
    print(f"Error: {report_file} not found.")
    exit(1)

with open(report_file, "r", encoding="utf-8") as f:
    content = f.read()

# Inject US Macro
us_table = generate_macro_table(US_MACRO, "us-macro-table")
content = content.replace('<div id="us-macro-placeholder"></div>', us_table)

# Inject TW Macro
tw_table = generate_macro_table(TW_MACRO, "tw-macro-table")
content = content.replace('<div id="tw-macro-placeholder"></div>', tw_table)

# Inject News
news_html = generate_news_list(NEWS_ITEMS)
content = content.replace('<div id="weekly-news-focus"></div>', news_html)

# Inject AI Analysis
ai_html = generate_ai_analysis(AI_ANALYSIS_TEXT)
content = content.replace('<div id="ai-analysis-report"></div>', ai_html)

# Save
with open(report_file, "w", encoding="utf-8") as f:
    f.write(content)

print(f"Successfully updated {report_file}")
