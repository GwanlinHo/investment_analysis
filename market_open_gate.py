#!/usr/bin/env python3
"""market_open_gate.py -- 「前一日美股、台股是否都休市」的輕量前置守門。

用途：在 invest_analysis.sh 啟動昂貴的 claude 分析流程「之前」判斷，
若美股與台股「都沒有新的交易日」(等同前一日兩市都休市)，就回報 skip，
讓外層腳本直接結束、不出報告、不覆寫任何資料、不 commit。

判斷方式(不需維護節假日行事曆)：
  - 從既有已發佈的 technical_data.json 取「標普 500」(美股)與「加權指數」(台股)
    各自最後一根 K 棒日期，代表上一份報告已涵蓋到的交易日。
  - 用 yfinance 抓 ^GSPC / ^TWII 最新一根日期。
  - 兩邊都「沒有往前」 -> 前一日兩市都休 -> skip。
    只要任一邊往前(例如僅美股開盤) -> 有新資料 -> 照常出報告。

保守原則：任何無法明確判定「兩市都沒新資料」的情況(檔案缺失、抓取失敗、
資料異常)一律「照常執行」，把關交給後續既有的資料完整性 gate，避免誤 skip。

回傳碼：
  10 -> skip(兩市都休，外層應結束不出報告)
  0  -> proceed(照常執行)
其餘非 10 值(例外)外層一律視為 proceed。
"""
import json
import sys

US_KEY = "標普 500"      # ^GSPC
TW_KEY = "加權指數"      # ^TWII
DATA_FILE = "technical_data.json"


def _log(msg: str) -> None:
    # 統一輸出到 stdout，由 cron 重導至 invest_analysis_cron.log
    print(f"[market-gate] {msg}", flush=True)


def _prev_last_date(market: dict, key: str):
    """從既有 technical_data.json 取某市場最後一根 K 棒日期(YYYY-MM-DD)。"""
    bars = market.get(key)
    if not isinstance(bars, list) or not bars:
        return None
    last = bars[-1]
    d = last.get("Date") if isinstance(last, dict) else None
    return d if isinstance(d, str) and d else None


def _fresh_last_date(symbol: str):
    """用 yfinance 抓最新一根日 K 的日期(市場當地日期，YYYY-MM-DD)；失敗回 None。"""
    import yfinance as yf

    df = yf.download(symbol, period="10d", progress=False, auto_adjust=True)
    if df is None or df.empty:
        return None
    return df.index[-1].strftime("%Y-%m-%d")


def main() -> int:
    # 1) 讀既有報告涵蓋到的最後交易日
    try:
        with open(DATA_FILE, encoding="utf-8") as f:
            data = json.load(f)
        market = data.get("market", {})
        prev_us = _prev_last_date(market, US_KEY)
        prev_tw = _prev_last_date(market, TW_KEY)
    except Exception as e:  # 檔案缺失/毀損 -> 保守照常執行
        _log(f"[proceed] 無法讀取 {DATA_FILE} 既有日期({e})，保守照常執行")
        return 0

    if not prev_us or not prev_tw:
        _log(f"[proceed] 既有報告缺少基準日期(US={prev_us}, TW={prev_tw})，保守照常執行")
        return 0

    # 2) 抓最新交易日
    try:
        cur_us = _fresh_last_date("^GSPC")
        cur_tw = _fresh_last_date("^TWII")
    except Exception as e:  # 抓取例外 -> 保守照常執行
        _log(f"[proceed] 最新交易日抓取失敗({e})，保守照常執行")
        return 0

    if not cur_us or not cur_tw:
        _log(f"[proceed] 最新交易日抓取不完整(US={cur_us}, TW={cur_tw})，保守照常執行")
        return 0

    us_advanced = cur_us != prev_us
    tw_advanced = cur_tw != prev_tw

    _log(f"US: 既有={prev_us} 最新={cur_us} ({'前進' if us_advanced else '未動'})")
    _log(f"TW: 既有={prev_tw} 最新={cur_tw} ({'前進' if tw_advanced else '未動'})")

    if not us_advanced and not tw_advanced:
        _log("[skip] 美股與台股皆無新交易日(前一日兩市皆休市)，本次不出報告")
        return 10

    _log("[proceed] 至少一市有新交易日，照常出報告")
    return 0


if __name__ == "__main__":
    sys.exit(main())
