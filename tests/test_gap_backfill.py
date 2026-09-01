"""gap_backfill 的離線測試：不打網路，只驗規則。

這些規則都是實測踩出來的，改壞了不會有人發現 (報告照樣產出，只是數字悄悄錯)，
所以每一條都對應模組說明裡的一個具體理由。
"""

import pandas as pd
import pytest

import gap_backfill as gb


def _df(rows):
    """rows: [(date, o, h, l, c, v)] -> 標準 OHLCV DataFrame"""
    idx = pd.to_datetime([r[0] for r in rows])
    return pd.DataFrame(
        {"Open": [r[1] for r in rows], "High": [r[2] for r in rows],
         "Low": [r[3] for r in rows], "Close": [r[4] for r in rows],
         "Volume": [r[5] for r in rows]}, index=idx)


# --- market_of ---

@pytest.mark.parametrize("sym,expect", [
    ("^GSPC", "US"), ("HYG", "US"), ("^VIX", "US"),
    ("^N225", "JP"),
    ("^TWII", "TW"), ("0050.TW", "TW"), ("00937B.TWO", "TW"),
    ("GC=F", None),  # 期貨日曆與股市不同(有週日盤)，套股市日曆會製造假破洞
])
def test_market_of(sym, expect):
    assert gb.market_of(sym) == expect


# --- 第 1 層：快取 union 合併 ---

def test_cache_fills_only_missing_never_overwrites():
    """只補缺漏，絕不覆蓋新抓到的值。

    上游會合理修正數值(Yahoo 曾把 08/28 黃金由 4529.90 改為 4478.10)，偏好舊值等於
    凍結錯誤資料。
    """
    df = _df([("2026-08-27", 1, 1, 1, 100.0, 10), ("2026-08-31", 1, 1, 1, 102.0, 10)])
    cache = {"X": {
        "2026-08-27": {"Open": 9, "High": 9, "Low": 9, "Close": 999.0, "Volume": 9},  # 新抓有 → 不可覆蓋
        "2026-08-28": {"Open": 1, "High": 1, "Low": 1, "Close": 101.0, "Volume": 5},  # 新抓缺 → 應補
    }}
    out, filled = gb.merge_from_cache("X", df, cache)
    assert filled == ["2026-08-28"]
    assert out.loc[pd.Timestamp("2026-08-27"), "Close"] == 100.0
    assert out.loc[pd.Timestamp("2026-08-28"), "Close"] == 101.0
    assert list(out.index) == sorted(out.index)


def test_cache_does_not_fill_tail_lag():
    """尾端落後不是破洞。

    標的當日尚未更新是正常現象，該由逐列 `[!] 資料 MM/DD` 標註呈現，不能用舊值假裝
    已更新。
    """
    df = _df([("2026-08-27", 1, 1, 1, 100.0, 10)])
    cache = {"X": {"2026-08-31": {"Open": 1, "High": 1, "Low": 1, "Close": 103.0, "Volume": 5}}}
    out, filled = gb.merge_from_cache("X", df, cache)
    assert filled == []
    assert pd.Timestamp("2026-08-31") not in out.index


def test_cache_fills_nan_close_row():
    """日期在但 Close 為 NaN，也算缺漏(Yahoo 曾回傳只有 Volume、OHLC 全 NaN 的空殼 K 棒)。"""
    df = _df([("2026-08-27", 1, 1, 1, 100.0, 10), ("2026-08-28", None, None, None, None, 7),
              ("2026-08-31", 1, 1, 1, 102.0, 10)])
    cache = {"X": {"2026-08-28": {"Open": 1, "High": 1, "Low": 1, "Close": 101.0, "Volume": 5}}}
    out, filled = gb.merge_from_cache("X", df, cache)
    assert filled == ["2026-08-28"]
    assert out.loc[pd.Timestamp("2026-08-28"), "Close"] == 101.0


def test_missing_cache_is_not_fatal():
    df = _df([("2026-08-27", 1, 1, 1, 100.0, 10)])
    out, filled = gb.merge_from_cache("X", df, {})
    assert filled == [] and len(out) == 1


# --- 破洞偵測 ---

def test_detect_gaps_only_inside_range():
    """只找 [首, 末] 之內：早於上市日與尾端未更新都不算破洞。"""
    df = _df([("2026-08-26", 1, 1, 1, 1.0, 1), ("2026-08-27", 1, 1, 1, 1.0, 1),
              ("2026-08-31", 1, 1, 1, 1.0, 1)])
    cal = {"US": set(pd.to_datetime(
        ["2026-08-24", "2026-08-25", "2026-08-26", "2026-08-27", "2026-08-28", "2026-08-31", "2026-09-01"]))}
    assert [d.strftime("%Y-%m-%d") for d in gb.detect_gaps("^GSPC", df, cal)] == ["2026-08-28"]


def test_detect_gaps_skips_futures():
    """期貨不做偵測(週日盤等日曆差異會被誤判成破洞)。"""
    df = _df([("2026-08-27", 1, 1, 1, 1.0, 1), ("2026-08-31", 1, 1, 1, 1.0, 1)])
    cal = {"US": set(pd.to_datetime(["2026-08-27", "2026-08-28", "2026-08-31"]))}
    assert gb.detect_gaps("GC=F", df, cal) == []


def test_detect_gaps_without_calendar_returns_nothing():
    """沒有日曆就不猜。寧可不補，不可誤補。"""
    df = _df([("2026-08-27", 1, 1, 1, 1.0, 1), ("2026-08-31", 1, 1, 1, 1.0, 1)])
    assert gb.detect_gaps("^GSPC", df, {}) == []


# --- 除息校正 ---

def test_adjust_ratio_corrects_dividend_basis():
    """盤中線沒有除息調整、日線有。

    實測 HYG 在 2026-08-03 除息(0.384)之前，盤中收盤系統性高於日線調整收盤 +0.48%；
    不校正就會在補值處注入一個等於配息率的價格斷階。
    """
    daily = _df([("2026-07-29", 1, 1, 1, 79.0, 1), ("2026-07-31", 1, 1, 1, 79.0, 1)])
    sess = pd.DataFrame({"Close": [79.38, 79.38]},
                        index=pd.to_datetime(["2026-07-29", "2026-07-31"]))
    r = gb._adjust_ratio("HYG", pd.Timestamp("2026-07-30"), daily, sess)
    assert r == pytest.approx(79.0 / 79.38, rel=1e-6)


def test_adjust_ratio_ignores_close_print_noise():
    """收盤結算價造成的 0.0x% 微小偏差不是除息，不該被當成調整係數套用。"""
    daily = _df([("2026-08-27", 1, 1, 1, 100.00, 1), ("2026-08-31", 1, 1, 1, 100.00, 1)])
    sess = pd.DataFrame({"Close": [100.02, 100.02]},
                        index=pd.to_datetime(["2026-08-27", "2026-08-31"]))
    assert gb._adjust_ratio("^GSPC", pd.Timestamp("2026-08-28"), daily, sess) == 1.0


def test_adjust_ratio_prefers_previous_day_when_sides_disagree():
    """前後兩側比值不一致代表中間有除息；破洞日與前一日必屬同一調整區間，故取前一日。"""
    daily = _df([("2026-07-31", 1, 1, 1, 79.0, 1), ("2026-08-04", 1, 1, 1, 79.5, 1)])
    sess = pd.DataFrame({"Close": [79.38, 79.50]},
                        index=pd.to_datetime(["2026-07-31", "2026-08-04"]))
    r = gb._adjust_ratio("HYG", pd.Timestamp("2026-08-03"), daily, sess)
    assert r == pytest.approx(79.0 / 79.38, rel=1e-6)


def test_twii_defines_tw_calendar_not_peer_union(monkeypatch):
    """台股日曆只認 ^TWII，不用台股標的聯集。

    實測 Yahoo 會給台股 ETF 生出不存在的交易日 (2026-07-10 在 Yahoo 的 0050/2330 有 K 棒，
    但 FinMind 的 TAIEX/0050/2330 全無 — 那天沒開市)。用聯集當日曆會把幻影日當成 ^TWII
    的破洞，每天發一次補不到的請求並印出假警訊。
    """
    gb._CALENDAR_CACHE.clear()
    monkeypatch.setattr(gb, "US_CANARIES", [])
    twii = _df([("2026-07-09", 1, 1, 1, 1.0, 1), ("2026-07-13", 1, 1, 1, 1.0, 1)])
    etf = _df([("2026-07-09", 1, 1, 1, 1.0, 1), ("2026-07-10", 1, 1, 1, 1.0, 1),
               ("2026-07-13", 1, 1, 1, 1.0, 1)])  # 幻影日 07-10
    cal = gb.build_calendars({"^TWII": twii, "0050.TW": etf},
                             pd.Timestamp("2026-07-01"), pd.Timestamp("2026-07-20"))
    assert pd.Timestamp("2026-07-10") not in cal["TW"]
    assert gb.detect_gaps("^TWII", twii, cal) == []
    gb._CALENDAR_CACHE.clear()
