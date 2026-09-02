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
  - Date
  - FinMind 來源的三大法人買賣超 (`*_institutional`，非 Yahoo 資料)

`Close` 自 v3.2 起也不發布。先前保留它是因為速覽面板要算 1/5/20 日漲跌、
VIX 60 日百分位與 20MA 穿越，但那等於在公開站台放上 25 檔 x 60 天、
共 1,500 點的機器可讀 Yahoo 價格序列 —— 仍是再散布。改由 `build_panel_data()`
在產出時先算好面板實際顯示的那幾十個純量，發布面只帶結果、不帶序列。
面板顯示完全不變。(報告本文以文字引用幾個收盤點屬評論引用，性質不同，不受影響。)

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
RAW_PRICE_FIELDS = ("Open", "High", "Low", "Volume", "Close")

# 舊報告 (v3.2 之前產生) 的內嵌 JS 直接讀 Close 序列，不認得 panel-data。對這種檔案
# 移除 Close 會讓速覽面板的收盤/漲跌/百分位全部變成 '-'，實測確認過。故回溯處理時
# 只對「JS 已改讀 panel-data」的檔案移除 Close，其餘沿用舊規則保留 Close。
LEGACY_RAW_FIELDS = ("Open", "High", "Low", "Volume")
PANEL_READER_MARK = "readJSON('panel-data')"

# 速覽面板需要、且必須在產出時先算好的量 (見模組說明)。
PANEL_LOOKBACKS = (1, 5, 20)
PANEL_PCTILE_SYMBOL = "恐慌指數"

# 是否發布基本面欄位。這些值是 Yahoo `.info` 的原值 (PE/PB/殖利率/ROE/毛利率...)，
# 官方開放資料 (TWSE BWIBBU_ALL) 僅涵蓋上市個股、不含本專案主要的 ETF 標的，
# 無法等值回補，故預設不發布；報告本文的 AI 分析文字仍會以敘述方式引用這些數值。
# 若日後取得可再散布的來源，把此旗標改為 True 即可恢復。
PUBLISH_FUNDAMENTAL = False

# 基本面缺席時，速覽面板顯示的說明文字 (取代舊的「資料源未提供」，該說法在
# 停止發布後已不正確)。
FUND_EMPTY_TEXT = "基本面數值不隨報告發布，相關解讀請見報告本文的 AI 分析段落。"


def sanitize_market(market, fields=RAW_PRICE_FIELDS):
    """回傳移除 Yahoo 原始價量欄位後的 market 資料 (不修改傳入物件)。

    `*_institutional` 序列來自 FinMind，欄位名稱完全不同，天然不受影響。
    `fields` 可指定要移除的欄位；回溯處理舊報告時會用 LEGACY_RAW_FIELDS(保留 Close)，
    原因見 sanitize_html。
    """
    if not isinstance(market, dict):
        return market
    out = {}
    for name, rows in market.items():
        if not isinstance(rows, list):
            out[name] = rows
            continue
        out[name] = [
            {k: v for k, v in row.items() if k not in fields}
            if isinstance(row, dict) else row
            for row in rows
        ]
    return out


def _is_num(v):
    """與前端 isNum() 等價：只接受有限的數值 (排除 None/NaN/Infinity/字串)。"""
    return isinstance(v, (int, float)) and not isinstance(v, bool) and v == v and v not in (
        float("inf"), float("-inf"))


def _pct_change(rows, back):
    """與前端 pctChange() 等價：最後一列相對往前第 back 列的變動百分比。"""
    if not rows or len(rows) <= back:
        return None
    now, then = rows[-1].get("Close"), rows[-1 - back].get("Close")
    if not _is_num(now) or not _is_num(then) or then == 0:
        return None
    return (now / then - 1) * 100


def _percentile(rows, key="Close"):
    """與前端 percentile() 等價：最後一筆在整個序列中的百分位 (小於等於者的占比)。"""
    if not rows:
        return None
    last = rows[-1].get(key)
    if not _is_num(last):
        return None
    vals = [r.get(key) for r in rows if _is_num(r.get(key))]
    if len(vals) < 5:
        return None
    return round(sum(1 for v in vals if v <= last) / len(vals) * 100)


def _ma20_cross(rows):
    """與前端 signals() 的 20MA 判斷等價；回傳 'up'/'down'/None。"""
    if not rows or len(rows) < 2:
        return None
    a, b = rows[-1], rows[-2]
    if not all(_is_num(x) for x in (a.get("Close"), a.get("20MA"), b.get("Close"), b.get("20MA"))):
        return None
    if b["Close"] < b["20MA"] and a["Close"] >= a["20MA"]:
        return "up"
    if b["Close"] > b["20MA"] and a["Close"] < a["20MA"]:
        return "down"
    return None


def build_panel_data(market):
    """算出速覽面板需要的純量，供發布面取代整條 Close 序列。

    必須在 `sanitize_market()` **之前**、以還帶有 Close 的原始 market 呼叫。
    每個標的回傳 {close, d1, d5, d20, ma20}；`恐慌指數` 另帶 pctile (60 日百分位)。

    這裡的四個函式與模板 JS 的 pctChange()/percentile()/signals() 逐行等價 —— 改動任一
    邊都必須同步，否則面板數字會與報告表格對不起來。
    """
    panel = {}
    if not isinstance(market, dict):
        return panel
    for name, rows in market.items():
        if not isinstance(rows, list) or not rows or name.endswith("_institutional"):
            continue
        last = rows[-1]
        if not isinstance(last, dict):
            continue
        entry = {"close": last.get("Close") if _is_num(last.get("Close")) else None,
                 "ma20": _ma20_cross(rows)}
        for back in PANEL_LOOKBACKS:
            entry["d%d" % back] = _pct_change(rows, back)
        if name == PANEL_PCTILE_SYMBOL:
            entry["pctile"] = _percentile(rows)
        panel[name] = entry
    return panel


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

    注意：自 v3.2 起 `Close` 也被移除，而速覽面板改讀 `panel-data`。舊報告沒有
    `panel-data` 標籤，若對其套用本函式，面板的收盤/漲跌/百分位會全部變成 '-'。
    因此對缺少該標籤的舊檔，這裡會就地補上由其自身 Close 序列算出的 panel-data，
    順序上必須在移除 Close 之前完成 —— 否則就是把舊報告的面板打壞。
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
        panel_aware = PANEL_READER_MARK in html
        fields = RAW_PRICE_FIELDS if panel_aware else LEGACY_RAW_FIELDS
        if not panel_aware:
            print("[!] 此檔的 JS 仍直接讀 Close 序列(v3.2 之前產生)，保留 Close 以免打壞速覽面板；"
                  "要徹底移除請重新產生報告。")
        elif '<script id="panel-data"' not in html:
            panel_body = json.dumps(build_panel_data(market), ensure_ascii=False).replace("</", "<\\/")
            end_i = html.find("</script>", html.find('<script id="market-data" type="application/json">'))
            if end_i >= 0:
                cut = end_i + len("</script>")
                html = (html[:cut] +
                        '\n    <script id="panel-data" type="application/json">' + panel_body + "</script>" +
                        html[cut:])
                changed = True

        clean = sanitize_market(market, fields)
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
