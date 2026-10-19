"""總經指標歷史紀錄。

macro_cache.json 只保存每個指標的「最新值」，因此速覽面板無法顯示「前值 → 現值」。
本模組維護 macro_history.json：每個指標一串按時間排列的版本，只有在數值或備註
真的變動時才追加一筆，因此檔案成長極慢（多數指標為月頻或季頻）。

用法：
    python3 macro_history.py --backfill    # 從 report/*.html 回填歷史（一次性）
    python3 macro_history.py --show        # 檢視目前累積狀況

update_report.py 每日會呼叫 upsert_from_cache() 與 build_payload()。
"""

import glob
import json
import os
import re
import sys

HISTORY_FILE = "macro_history.json"
REPORT_DIR = "report"
REGIONS = ("US_MACRO", "TW_MACRO")


def load_history(path=HISTORY_FILE):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                for r in REGIONS:
                    data.setdefault(r, {})
                return data
        except Exception as e:
            print(f"[Warning] 讀取 {path} 失敗，改用空歷史: {e}")
    return {r: {} for r in REGIONS}


def save_history(history, path=HISTORY_FILE):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def upsert(history, region, items, seen_date):
    """把某一天觀察到的指標值併入歷史。值與備註都相同時不重複追加。

    回傳這次實際新增的筆數。
    """
    added = 0
    bucket = history.setdefault(region, {})
    for item in items or []:
        name = (item.get("name") or "").strip()
        if not name or name == "指標名稱":
            continue
        value = (item.get("value") or "").strip()
        note = (item.get("note") or "").strip()
        if not value:
            continue
        entries = bucket.setdefault(name, [])
        if entries and _norm(entries[-1].get("value")) == _norm(value) \
                and _norm(entries[-1].get("note")) == _norm(note):
            # 只是裝飾差異（解析器移除了 '-'、'▲'）：以較精確的來源字串就地更新，
            # 保留原本的 first_seen，不產生新版本。
            entries[-1]["value"] = value
            entries[-1]["note"] = note
            entries[-1]["trend"] = item.get("trend", entries[-1].get("trend", "neutral"))
            continue
        # 回填時可能以較舊的日期出現在較新的紀錄之後，維持時間排序
        entries.append({
            "value": value,
            "trend": item.get("trend", "neutral"),
            "note": note,
            "first_seen": seen_date,
        })
        entries.sort(key=lambda e: e.get("first_seen", ""))
        added += 1
    return added


def _report_date(path):
    m = re.search(r"invest_analysis_(\d{4})(\d{2})(\d{2})\.html$", os.path.basename(path))
    if not m:
        return None
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"


def parse_report(path):
    """從已注入的日報 HTML 取出美台總經表格內容。"""
    from update_report import MacroParser  # 重用既有解析器，避免兩份實作

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"[Warning] 讀取 {path} 失敗: {e}")
        return {r: [] for r in REGIONS}
    parser = MacroParser()
    try:
        parser.feed(content)
    except Exception as e:
        print(f"[Warning] 解析 {path} 失敗: {e}")
    return parser.results


def backfill_from_reports(history=None, report_dir=REPORT_DIR):
    """依日期由舊到新掃過歷史報告，重建指標版本序列。"""
    if history is None:
        history = load_history()
    files = sorted(glob.glob(os.path.join(report_dir, "invest_analysis_*.html")))
    total = 0
    for path in files:
        seen = _report_date(path)
        if not seen:
            continue
        results = parse_report(path)
        n = 0
        for region in REGIONS:
            n += upsert(history, region, results.get(region, []), seen)
        if n:
            print(f"  {seen}: 新增 {n} 筆")
        total += n
    print(f"[*] 回填完成，共掃描 {len(files)} 份報告、新增 {total} 筆版本紀錄。")
    return history


def upsert_from_cache(macro_cache, seen_date, history=None, path=HISTORY_FILE):
    """每日流程呼叫：把 macro_cache.json 的最新值併入歷史並存檔。"""
    if history is None:
        history = load_history(path)
    added = 0
    for region in REGIONS:
        added += upsert(history, region, macro_cache.get(region, []), seen_date)
    save_history(history, path)
    return history, added


def _norm(value):
    """比對用的正規化字串。

    歷史回填來源是 update_report.MacroParser，它為了判斷漲跌方向會把 '-'、'▲'、'▼'
    去掉（例如 '3.50%-3.75%' 變成 '3.50%3.75%'），與 macro_cache.json 的原始字串不同。
    若不正規化，這類指標每天都會被誤判為「有新版本」而不斷追加。

    保留開頭的負號：'-2.3 萬' 與 '2.3 萬' 是真正的不同值，不可視為相同。
    """
    s = (value or "").replace("▲", "").replace("▼", "").replace(" ", "").strip()
    neg = s.startswith("-")
    s = s.replace("-", "")
    return ("-" + s) if neg else s


def build_payload(macro_cache, history):
    """組出前端速覽面板要用的總經資料：現值 + 前值 + 變動日期。"""
    payload = {}
    for region in REGIONS:
        rows = []
        bucket = history.get(region, {})
        for item in macro_cache.get(region, []):
            name = (item.get("name") or "").strip()
            value = (item.get("value") or "").strip()
            entries = bucket.get(name, [])
            changed_on, prev_value, prev_note = "", "", ""
            # 找出目前這個值對應的版本，前一個版本即為前值
            idx = None
            for i in range(len(entries) - 1, -1, -1):
                if _norm(entries[i].get("value")) == _norm(value):
                    idx = i
                    break
            if idx is not None:
                changed_on = entries[idx].get("first_seen", "")
                if idx > 0:
                    prev_value = entries[idx - 1].get("value", "")
                    prev_note = entries[idx - 1].get("note", "")
            rows.append({
                "name": name,
                "value": value,
                "trend": item.get("trend", "neutral"),
                "note": (item.get("note") or "").strip(),
                "prev": prev_value,
                "prev_note": prev_note,
                "changed_on": changed_on,
            })
        payload[region] = rows
    return payload


def main(argv):
    if "--backfill" in argv:
        history = backfill_from_reports()
        save_history(history)
        print(f"[Success] 已寫入 {HISTORY_FILE}")
    elif "--show" in argv:
        history = load_history()
        for region in REGIONS:
            bucket = history.get(region, {})
            multi = sum(1 for v in bucket.values() if len(v) > 1)
            print(f"{region}: {len(bucket)} 項指標，其中 {multi} 項已有前值")
            for name, entries in bucket.items():
                tail = " <- ".join(f'{e["value"]}({e["first_seen"]})' for e in entries[-3:][::-1])
                print(f"  {name}: {tail}")
    else:
        print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
