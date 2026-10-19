"""補 Yahoo 日線序列「中間破洞」。

Yahoo 偶爾會永久性地少掉某個交易日的日 K 棒，且不會回補。實測 2026-08-28 當天
`^GSPC`/`^IXIC`/`^DJI`/`^VIX`/`^SOX`/`^RUT`/`^NYFANG`/`^N225`/`HYG` 全缺，但同一天
SPY/QQQ/SOXX/AAPL/GLD 卻有 — 破洞隨機散落在個別標的，任何標的任何一天都可能中。

後果不只是「少一天」：表列單日漲跌會變成跨兩個交易日的變動，而且 MA/KD/RSI/MACD/ADX
全部建立在少一根 K 棒的序列上，會一路錯到該筆滾出視窗為止。

本模組兩層防護：

1. **本機快取 union 合併** (`_ohlcv_cache.json`，不進 repo)
   每次抓取後把原始 OHLCV 存檔；下次只補「新抓結果沒有的日期」，**絕不覆蓋新抓有的
   日期** — 上游合理修正過的數值 (例如 Yahoo 曾把 08/28 黃金由 4,529.90 改為 4,478.10)
   必須跟著更新，偏好舊值會凍結錯誤資料。

2. **盤中線重建**
   Yahoo 的 1 小時線沒有這些破洞，且可回溯約 730 天。以各標的自己的交易所時區分組
   後聚合成日 K。實測重建已知日與真實日線的偏差：Open/High/Low 多數 0.000% (最差
   -0.066%)，Close 系統性略低 0.002%~0.087% (收盤結算價在最後一根盤中 K 棒之後才
   產生)，對技術指標無實質影響。Volume 則會低估 (指數 -46%~-100%、ETF -4%~-11%)，
   因為缺少盤前盤後與收盤集合競價，屬估計值。

兩個實測踩過的坑，改動時務必保留：

* **時區**：必須用標的自己的交易所時區切日。用 America/New_York 去切 `^N225`，東京盤
  會被切成兩半 (只剩 3 根、OHLC 全錯)；改 Asia/Tokyo 後才正確。
* **配息**：盤中線**沒有**除息調整，日線 `auto_adjust=True` **有**。實測 HYG 在
  2026-08-03 除息 (0.384) 之前，盤中收盤系統性高於日線調整收盤 +0.48% (= 0.384/79.3)。
  故重建後一律以相鄰交易日的「日線調整收盤 / 盤中收盤」比值做等比校正。
"""

import json
import os
import time

import pandas as pd
import yfinance as yf

CACHE_FILE = "_ohlcv_cache.json"
OHLCV = ["Open", "High", "Low", "Close", "Volume"]

# 各市場的交易所時區。切日一定要用標的自己的時區，見模組說明。
MARKET_TZ = {"US": "America/New_York", "JP": "Asia/Tokyo", "TW": "Asia/Taipei"}

# 美股交易日曆的哨兵標的。破洞會同時打中我們清單裡的所有指數 (2026-08-28 即如此)，
# 所以日曆不能只由自家標的的聯集推出，必須另外抓流動性最高、最不可能同時缺漏的標的。
US_CANARIES = ["SPY", "AAPL"]

# 單次執行最多對幾個標的做盤中重建，避免對 Yahoo 連續發太多請求。
MAX_INTRADAY_SYMBOLS = 12

# 校正比值偏離 1 超過這個幅度才視為真正的除息調整而套用；以下視為收盤價微小雜訊，不動。
RATIO_EPS = 0.001

# 本次執行的補值紀錄：{symbol: [(date, source), ...]}，供上層列印與報告揭露。
backfill_log = {}

# 交易日曆在單次執行內 memoize。主流程分三個群組各呼叫一次 apply()，哨兵與 JP 盤中線
# 是與群組無關的固定成本，不快取就會對 Yahoo 重複發三倍請求。
_CALENDAR_CACHE = {}


def market_of(symbol):
    """判斷標的所屬市場；期貨與無法判斷者回傳 None (不做破洞偵測)。

    期貨 (`=F`) 的交易日曆與股市根本不同 (有週日盤、假日不同)，套用股市日曆只會製造
    假破洞，故一律排除。
    """
    if symbol.endswith("=F"):
        return None
    if symbol == "^N225":
        return "JP"
    if symbol == "^TWII" or symbol.endswith(".TW") or symbol.endswith(".TWO"):
        return "TW"
    return "US"


# --- 第 1 層：本機快取 union 合併 ---

def load_cache(path=CACHE_FILE):
    """讀本機原始 OHLCV 快取；不存在或毀損一律回空 dict (視同沒有快取，不中斷主流程)。"""
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"    [backfill] 快取讀取失敗，本次略過 union 合併: {e}")
        return {}


def save_cache(cache, path=CACHE_FILE):
    """寫回快取。失敗不影響本次報告，只是下次少一層防護。"""
    try:
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, separators=(",", ":"))
        os.replace(tmp, path)
    except Exception as e:
        print(f"    [backfill] 快取寫入失敗: {e}")


def update_cache(cache, symbol, df):
    """把本次抓到的有效列寫進快取 (以新抓結果為準，覆蓋同日舊值)。"""
    entry = cache.setdefault(symbol, {})
    for dt, row in df.iterrows():
        if pd.isna(row.get("Close")):
            continue
        entry[dt.strftime("%Y-%m-%d")] = {
            c: (None if pd.isna(row.get(c)) else float(row.get(c))) for c in OHLCV if c in df.columns
        }


def merge_from_cache(symbol, df, cache):
    """用快取補新抓結果缺漏的日期。只補「不存在或 Close 為 NaN」的日期，不覆蓋既有有效值。

    只補落在本次資料區間 [首, 末] 之內的日期：尾端落後 (標的當日尚未更新) 是正常現象，
    由既有的逐列 `[!] 資料 MM/DD` 標註處理，不該用舊值假裝已更新。
    """
    entry = cache.get(symbol)
    if not entry or df.empty:
        return df, []
    first, last = df.index[0], df.index[-1]
    filled = []
    for ds, row in sorted(entry.items()):
        dt = pd.Timestamp(ds)
        if not (first <= dt <= last):
            continue
        if dt in df.index and not pd.isna(df.loc[dt].get("Close")):
            continue
        for c, v in row.items():
            if v is not None:
                df.loc[dt, c] = v
        filled.append(ds)
    if filled:
        df = df.sort_index()
    return df, filled


# --- 第 2 層：盤中線重建 ---

def _session_frame(symbol, start, end, tz):
    """抓 1 小時線並依交易所時區聚合成日 K。取不到回 None。"""
    h = yf.download(symbol, start=start, end=end, interval="1h", progress=False, auto_adjust=True)
    if h is None or h.empty:
        return None
    if isinstance(h.columns, pd.MultiIndex):
        h.columns = h.columns.droplevel(1)
    idx = h.index
    idx = idx.tz_localize("UTC") if idx.tz is None else idx
    h = h.set_index(idx.tz_convert(tz))
    agg = h.groupby(h.index.strftime("%Y-%m-%d")).agg(
        Open=("Open", "first"), High=("High", "max"), Low=("Low", "min"),
        Close=("Close", "last"), Volume=("Volume", "sum"),
    )
    agg.index = pd.to_datetime(agg.index)
    return agg.sort_index()


def build_calendars(stock_data, start_date, end_date):
    """建立各市場的交易日曆。

    US 用哨兵標的 (見 US_CANARIES 說明)；JP 只有 ^N225 一檔，以它自己的盤中線推出實際
    開盤日；TW 標的數多且有 FinMind 補值，用自家標的日期聯集即可。任何一步失敗就不對該
    市場做破洞偵測 (寧可不補，不可誤補)。
    """
    cal = {}
    key = (start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"))
    shared = _CALENDAR_CACHE.get(key)
    if shared is not None:
        cal.update(shared)

    us_dates = set() if "US" not in cal else set(cal["US"])
    for c in ([] if "US" in cal else US_CANARIES):
        try:
            d = yf.download(c, start=start_date, end=end_date, progress=False, auto_adjust=True)
            if d is not None and not d.empty:
                if isinstance(d.columns, pd.MultiIndex):
                    d.columns = d.columns.droplevel(1)
                us_dates |= set(d.dropna(subset=["Close"]).index)
            time.sleep(1)
        except Exception as e:
            print(f"    [backfill] 日曆哨兵 {c} 取得失敗: {e}")
    if us_dates:
        cal["US"] = us_dates

    if "^N225" in stock_data and "JP" not in cal:
        try:
            s = _session_frame("^N225", start_date, end_date, MARKET_TZ["JP"])
            if s is not None and not s.empty:
                cal["JP"] = set(s.index)
            time.sleep(1)
        except Exception as e:
            print(f"    [backfill] 日曆 JP 取得失敗: {e}")

    # TW 日曆只認 ^TWII 的日期，不能用台股標的日期聯集。
    # 實測 Yahoo 會給台股 ETF 生出不存在的交易日：2026-07-10 在 Yahoo 的 0050／2330／
    # 00631L 等都有 K 棒，但 FinMind 的 TAIEX／0050／2330 全都沒有該日 — 那天根本沒開市。
    # 用聯集當日曆會把這種幻影日當成 ^TWII 的破洞，每天發一次補不到的請求並印出假警訊。
    # ^TWII 已先經 fill_latest_from_finmind 以本土源補過，是最可信的台股交易日曆。
    if "TW" not in cal and "^TWII" in stock_data:
        twii = stock_data["^TWII"]
        if not twii.empty:
            cal["TW"] = set(twii.dropna(subset=["Close"]).index)

    _CALENDAR_CACHE[key] = {k: v for k, v in cal.items() if k in ("US", "JP", "TW")}
    return cal


def detect_gaps(symbol, df, calendars):
    """找出序列「中間」缺漏的交易日。

    只看 [首筆, 末筆] 之內：早於上市日與尾端尚未更新都不算破洞。
    """
    mkt = market_of(symbol)
    if mkt is None or mkt not in calendars or df.empty:
        return []
    valid = df.dropna(subset=["Close"]) if "Close" in df.columns else df
    if valid.empty:
        return []
    first, last = valid.index[0], valid.index[-1]
    have = set(valid.index)
    return sorted(d for d in calendars[mkt] if first < d < last and d not in have)


def _adjust_ratio(symbol, gap, daily, sess):
    """求除息調整比值 = 日線調整收盤 / 盤中原始收盤。

    盤中線沒有除息調整、日線有，故補一個比最近一次除息更早的洞時，必須把重建值等比
    還原到日線的口徑，否則會注入一個等於配息率的價格斷階 (實測 HYG 為 +0.48%)。

    取相鄰交易日計算：優先用前一日 — auto_adjust 是把「除息日之前」的所有 K 棒乘上係數，
    故破洞日與前一日必屬同一調整區間，除非破洞日本身就是除息日。前後兩日比值一致時取
    平均以降低單日收盤雜訊的影響。
    """
    common = [d for d in sess.index if d in daily.index and not pd.isna(daily.loc[d].get("Close"))]
    prev = [d for d in common if d < gap]
    nxt = [d for d in common if d > gap]
    def ratio(d):
        hc = float(sess.loc[d, "Close"])
        return float(daily.loc[d, "Close"]) / hc if hc else None
    rp = ratio(prev[-1]) if prev else None
    rn = ratio(nxt[0]) if nxt else None
    if rp is not None and rn is not None and abs(rp - rn) <= 0.0005:
        r = (rp + rn) / 2
    else:
        r = rp if rp is not None else rn
    if r is None or abs(r - 1) <= RATIO_EPS:
        return 1.0
    return r


def reconstruct(symbol, df, gaps, start_date, end_date):
    """以盤中線重建破洞日的日 K，回傳 (df, 已補日期清單)。"""
    mkt = market_of(symbol)
    tz = MARKET_TZ.get(mkt)
    if tz is None or not gaps:
        return df, []
    try:
        sess = _session_frame(symbol, start_date, end_date, tz)
    except Exception as e:
        print(f"    [backfill] {symbol} 盤中線取得失敗: {e}")
        return df, []
    if sess is None or sess.empty:
        print(f"    [backfill] {symbol} 無盤中線可用，破洞保留: {[g.strftime('%Y-%m-%d') for g in gaps]}")
        return df, []
    filled = []
    for gap in gaps:
        if gap not in sess.index:
            continue
        r = _adjust_ratio(symbol, gap, df, sess)
        row = sess.loc[gap]
        for c in ["Open", "High", "Low", "Close"]:
            v = row.get(c)
            if not pd.isna(v):
                df.loc[gap, c] = float(v) * r
        v = row.get("Volume")
        # Volume 為盤中加總的估計值 (缺盤前盤後與收盤集合競價)；指數群組不顯示量比，
        # ETF 實測低估 4%~11%，落在單筆對 20 日均量影響 <1% 的範圍。
        if not pd.isna(v):
            df.loc[gap, "Volume"] = float(v)
        filled.append(gap.strftime("%Y-%m-%d"))
    if filled:
        df = df.sort_index()
    return df, filled


def apply(stock_data, start_date, end_date, cache_path=CACHE_FILE):
    """對一組標的套用兩層補值，回傳修補後的 {symbol: df}。

    任何一層出錯都只是少補，不會中斷主流程 — 補不到的破洞由既有的逐列標註與報告內文
    揭露機制處理，靜默補錯比留著標記的洞更糟。
    """
    cache = load_cache(cache_path)

    # 第 1 層：先用快取補，補完的日期不會再被當成破洞
    for sym, df in stock_data.items():
        try:
            stock_data[sym], filled = merge_from_cache(sym, df, cache)
            if filled:
                print(f"    [backfill] {sym} 由本機快取補回 {len(filled)} 日: {', '.join(filled)}")
                backfill_log.setdefault(sym, []).extend((d, "cache") for d in filled)
        except Exception as e:
            print(f"    [backfill] {sym} 快取合併略過: {e}")

    # 第 2 層：偵測仍然存在的破洞，以盤中線重建
    try:
        calendars = build_calendars(stock_data, start_date, end_date)
    except Exception as e:
        print(f"    [backfill] 交易日曆建立失敗，略過盤中重建: {e}")
        calendars = {}

    if calendars:
        pending = {}
        for sym, df in stock_data.items():
            try:
                gaps = detect_gaps(sym, df, calendars)
            except Exception as e:
                print(f"    [backfill] {sym} 破洞偵測略過: {e}")
                gaps = []
            if gaps:
                pending[sym] = gaps
        if len(pending) > MAX_INTRADAY_SYMBOLS:
            keep = dict(list(pending.items())[:MAX_INTRADAY_SYMBOLS])
            print(f"    [backfill] [!] 有破洞的標的 {len(pending)} 個，超過單次上限 "
                  f"{MAX_INTRADAY_SYMBOLS}，本次只處理前 {len(keep)} 個，其餘下次執行再補")
            pending = keep
        for sym, gaps in pending.items():
            print(f"    [backfill] {sym} 偵測到 {len(gaps)} 個破洞: "
                  f"{', '.join(g.strftime('%Y-%m-%d') for g in gaps)}")
            try:
                stock_data[sym], filled = reconstruct(sym, stock_data[sym], gaps, start_date, end_date)
            except Exception as e:
                print(f"    [backfill] {sym} 盤中重建略過: {e}")
                filled = []
            if filled:
                print(f"    [backfill] {sym} 以盤中線重建 {len(filled)} 日: {', '.join(filled)}")
                backfill_log.setdefault(sym, []).extend((d, "intraday") for d in filled)
            missed = [g.strftime("%Y-%m-%d") for g in gaps if g.strftime("%Y-%m-%d") not in filled]
            if missed:
                print(f"    [backfill] [!] {sym} 仍有補不到的破洞: {', '.join(missed)}")
            time.sleep(1)

    # 補完再存快取，讓重建結果下次不必重算
    for sym, df in stock_data.items():
        try:
            update_cache(cache, sym, df)
        except Exception as e:
            print(f"    [backfill] {sym} 快取更新略過: {e}")
    save_cache(cache, cache_path)
    return stock_data
