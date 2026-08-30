"""發布資料淨化 (publish data minimization)。

用途
----
本專案的報告會推送到公開 repo。Yahoo Finance 的服務條款限「個人、非商業使用」，
禁止再散布其資料；而報告 HTML 原本在 <script id="market-data"> 內嵌了
33 檔標的 x 60 天的完整 OHLCV 原值 (約 1.1MB)，等同把 Yahoo 的價格資料集
原樣轉發給第三人。<script id="fundamental-data"> 內嵌的 PE/PB/殖利率/ROE 等
欄位同樣是 Yahoo `.info` 的原值。

本模組把「Yahoo 原值」這一層從『發布面』拿掉，保留：
  - 自行計算的衍生指標 (KD、RSI、MACD、乖離、MA、ADX/DI 等)
  - 前端速覽面板必需的 Date 與 Close (面板要算 1/5/20 日漲跌與 VIX 百分位)
  - FinMind 來源的三大法人買賣超 (`*_institutional`，非 Yahoo 資料)

『本機面』不受影響：`technical_data.json` 仍保存完整 OHLCV，供 AI 分析遵守
CLAUDE.md 的 Fact-Only Rule (只能引用檔案中確實存在的高低點) 與
`market_open_gate.py` 使用。該檔已從 `sync.sh` 白名單移除、不再發布。

淨化時機
--------
`investment_analysis.py` 在 render 模板時套用 (此時尚未進行 AI 分析，
故本機 JSON 仍為完整資料)；`update_report.py` 只改寫 <script id="macro-data">，
不會把原值寫回，淨化結果不會被後續注入還原。
"""

import json
import re
import sys

# Yahoo 原始價量欄位：發布版一律移除 (衍生指標如 5MA/20MA/BIAS 由本專案計算，保留)。
RAW_PRICE_FIELDS = ("Open", "High", "Low", "Volume")

# 是否發布基本面欄位。這些值是 Yahoo `.info` 的原值 (PE/PB/殖利率/ROE/毛利率...)，
# 官方開放資料 (TWSE BWIBBU_ALL) 僅涵蓋上市個股、不含本專案主要的 ETF 標的，
# 無法等值回補，故預設不發布；報告本文的 AI 分析文字仍會以敘述方式引用這些數值。
# 若日後取得可再散布的來源，把此旗標改為 True 即可恢復。
PUBLISH_FUNDAMENTAL = False

# 基本面缺席時，速覽面板顯示的說明文字 (取代舊的「資料源未提供」，該說法在
# 停止發布後已不正確)。
FUND_EMPTY_TEXT = "基本面數值不隨報告發布，相關解讀請見報告本文的 AI 分析段落。"


def sanitize_market(market):
    """回傳移除 Yahoo 原始價量欄位後的 market 資料 (不修改傳入物件)。

    `*_institutional` 序列來自 FinMind，欄位名稱完全不同，天然不受影響。
    """
    if not isinstance(market, dict):
        return market
    out = {}
    for name, rows in market.items():
        if not isinstance(rows, list):
            out[name] = rows
            continue
        out[name] = [
            {k: v for k, v in row.items() if k not in RAW_PRICE_FIELDS}
            if isinstance(row, dict) else row
            for row in rows
        ]
    return out


def sanitize_fundamental(fundamental):
    """回傳發布用的 fundamental 資料；預設為空清單 (見 PUBLISH_FUNDAMENTAL)。"""
    if PUBLISH_FUNDAMENTAL:
        return fundamental
    return []


def _replace_tag(html, tag_id, payload):
    """把 <script id="tag_id" type="application/json"> 的內容換成 payload。

    找不到標籤時原樣回傳 (舊版報告沒有這些標籤)。
    """
    pattern = r'(<script id="%s" type="application/json">).*?(</script>)' % re.escape(tag_id)
    if not re.search(pattern, html, flags=re.DOTALL):
        return html, False
    body = json.dumps(payload, ensure_ascii=False)
    # 避免 payload 內的 </script> 提前結束標籤 (JSON 內容理論上不會有，仍做防護)。
    body = body.replace("</", "<\\/")
    return re.sub(pattern, lambda m: m.group(1) + body + m.group(2),
                  html, count=1, flags=re.DOTALL), True


def sanitize_html(html):
    """淨化一份已產生的報告 HTML；回傳 (新內容, 是否有變更)。

    供既有報告回溯處理使用 (report/*.html、index.html)，與 render 時的淨化等效。
    """
    changed = False

    m = re.search(r'<script id="market-data" type="application/json">(.*?)</script>',
                  html, flags=re.DOTALL)
    if m:
        try:
            market = json.loads(m.group(1))
        except ValueError:
            # 舊報告可能含 pandas 的 NaN，JSON.parse 與 json.loads 皆不接受。
            market = json.loads(re.sub(r'\bNaN\b|\b-?Infinity\b', 'null', m.group(1)))
        clean = sanitize_market(market)
        if clean != market:
            html, ok = _replace_tag(html, "market-data", clean)
            changed = changed or ok

    if not PUBLISH_FUNDAMENTAL:
        m = re.search(r'<script id="fundamental-data" type="application/json">(.*?)</script>',
                      html, flags=re.DOTALL)
        if m and m.group(1).strip() not in ("[]", ""):
            html, ok = _replace_tag(html, "fundamental-data", [])
            changed = changed or ok

    # 舊報告的空狀態文字說「資料源未提供」，停止發布後改為正確說法。
    old_text = "本報告標的以指數與 ETF 為主，資料源未提供基本面欄位。"
    if not PUBLISH_FUNDAMENTAL and old_text in html:
        html = html.replace(old_text, FUND_EMPTY_TEXT)
        changed = True

    return html, changed


def _main(paths):
    total = 0
    for path in paths:
        with open(path, encoding="utf-8") as f:
            html = f.read()
        before = len(html)
        html, changed = sanitize_html(html)
        if not changed:
            print(f"[-] {path} 無需變更")
            continue
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        total += 1
        print(f"[O] {path} {before:,} -> {len(html):,} bytes "
              f"(-{(before - len(html)) / 1024:.0f} KB)")
    print(f"[*] 共處理 {total} 份檔案。")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: uv run publish_filter.py <report.html> [...]")
        sys.exit(1)
    _main(sys.argv[1:])
