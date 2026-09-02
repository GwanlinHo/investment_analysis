"""publish_filter 的發布面淨化與面板預算值測試。

重點在兩件事：發布面不得再帶出 Yahoo 原值(含 Close)，以及 build_panel_data 必須與
模板 JS 的 pctChange()/percentile()/signals() 逐項等價 —— 兩邊算法一旦不同步，面板數字
就會與報告表格對不起來，而且不會有任何錯誤訊息。
"""

import json

import pytest

import publish_filter as pf


def _series(closes, ma20=None):
    rows = []
    for i, c in enumerate(closes):
        r = {"Date": "2026-06-%02d" % (i + 1), "Close": c,
             "Open": 1.0, "High": 2.0, "Low": 0.5, "Volume": 100, "RSI": 50.0}
        if ma20 is not None:
            r["20MA"] = ma20[i]
        rows.append(r)
    return rows


# --- 淨化 ---

def test_sanitize_removes_all_yahoo_raw_fields_including_close():
    """Close 自 v3.2 起也不發布：25 檔 x 60 天的機器可讀價格序列等同再散布。"""
    market = {"標普 500": _series([1.0, 2.0, 3.0])}
    out = pf.sanitize_market(market)
    for row in out["標普 500"]:
        for f in ("Open", "High", "Low", "Volume", "Close"):
            assert f not in row
        assert row["Date"] and row["RSI"] == 50.0   # 衍生指標與日期保留


def test_sanitize_keeps_finmind_institutional_untouched():
    """*_institutional 來自 FinMind，不是 Yahoo 資料，不受淨化影響。"""
    market = {"台積電_institutional": [{"date": "2026-06-01", "Foreign_Investor": 123}]}
    assert pf.sanitize_market(market) == market


def test_sanitize_does_not_mutate_input():
    """本機面要保有完整 OHLCV 供 AI 分析與休市守門使用，淨化不得就地改壞。"""
    market = {"X": _series([1.0, 2.0])}
    pf.sanitize_market(market)
    assert market["X"][0]["Close"] == 1.0


# --- 面板預算值 ---

def test_panel_pct_change_matches_js_semantics():
    """pctChange(rows, back)：最後一列相對往前第 back 列(不是相對第一列)。"""
    closes = [100.0] * 6 + [110.0] * 14 + [50.0, 121.0]   # 共 22 筆
    p = pf.build_panel_data({"X": _series(closes)})["X"]
    assert p["close"] == 121.0
    assert p["d1"] == pytest.approx((121.0 / 50.0 - 1) * 100)     # 往前 1 筆 = 50
    assert p["d5"] == pytest.approx((121.0 / 110.0 - 1) * 100)    # 往前 5 筆 = 110
    assert p["d20"] == pytest.approx((121.0 / 100.0 - 1) * 100)   # 往前 20 筆 = 100


def test_panel_pct_change_none_when_series_too_short():
    p = pf.build_panel_data({"X": _series([100.0, 110.0])})["X"]
    assert p["d5"] is None and p["d20"] is None
    assert p["d1"] == pytest.approx(10.0)


def test_panel_pct_change_none_on_zero_base():
    """除以零在 JS 會得到 Infinity，前端 isNum 會擋掉；Python 端也必須回 None。"""
    assert pf.build_panel_data({"X": _series([0.0, 5.0])})["X"]["d1"] is None


def test_panel_percentile_only_for_vix():
    """百分位只有恐慌指數需要，其餘標的不算(面板也不顯示)。"""
    vals = [float(i) for i in range(1, 11)]
    panel = pf.build_panel_data({pf.PANEL_PCTILE_SYMBOL: _series(vals), "X": _series(vals)})
    assert panel[pf.PANEL_PCTILE_SYMBOL]["pctile"] == 100   # 最後一筆是最大值
    assert "pctile" not in panel["X"]


def test_panel_percentile_needs_five_points():
    """與 JS 的 vals.length < 5 門檻一致。"""
    panel = pf.build_panel_data({pf.PANEL_PCTILE_SYMBOL: _series([1.0, 2.0, 3.0])})
    assert panel[pf.PANEL_PCTILE_SYMBOL]["pctile"] is None


@pytest.mark.parametrize("closes,ma20,expect", [
    ([9.0, 11.0], [10.0, 10.0], "up"),     # 由下穿上
    ([11.0, 9.0], [10.0, 10.0], "down"),   # 由上穿下
    ([11.0, 12.0], [10.0, 10.0], None),    # 一直在上方，不算穿越
    ([9.0, 8.0], [10.0, 10.0], None),
])
def test_panel_ma20_cross(closes, ma20, expect):
    assert pf.build_panel_data({"X": _series(closes, ma20)})["X"]["ma20"] == expect


def test_panel_skips_institutional_series():
    panel = pf.build_panel_data({"台積電_institutional": [{"date": "2026-06-01", "Foreign_Investor": 1}]})
    assert panel == {}


def test_panel_is_json_safe():
    """內嵌 JSON 不得含 NaN/Infinity — 瀏覽器的 JSON.parse 不接受。"""
    rows = _series([float("nan"), 2.0])
    body = json.dumps(pf.build_panel_data({"X": rows}))
    assert "NaN" not in body and "Infinity" not in body


# --- 回溯處理 ---

def _html_with(market, panel_aware):
    js = ("<script>var PANEL = readJSON('panel-data') || {};</script>" if panel_aware else
          "<script>var c = rows[rows.length-1].Close;</script>")
    return ('<html><body>'
            '<script id="market-data" type="application/json">' + json.dumps(market) + '</script>'
            + js + '</body></html>')


def _market_of(html):
    return json.loads(html.split('<script id="market-data" type="application/json">')[1].split('</script>')[0])


def test_sanitize_html_keeps_close_for_pre_v32_reports():
    """舊報告的 JS 直接讀 Close，不認得 panel-data。

    對它移除 Close，速覽面板的收盤/漲跌/百分位會全部變成 '-'(已實測)，補上 panel-data
    也救不了 —— 那份 JS 根本不會去讀。所以舊檔必須沿用 v3.0 規則保留 Close。
    """
    market = {"恐慌指數": _series([10.0, 11.0, 12.0, 13.0, 14.0, 15.0])}
    out, _ = pf.sanitize_html(_html_with(market, panel_aware=False))
    rows = _market_of(out)["恐慌指數"]
    assert all("Close" in r for r in rows)            # 保留
    assert all("Open" not in r and "Volume" not in r for r in rows)   # OHLV 仍移除


def test_sanitize_html_strips_close_for_panel_aware_reports():
    """JS 已改讀 panel-data 的報告才移除 Close，並補上 panel-data(需在移除之前算)。"""
    market = {"恐慌指數": _series([10.0, 11.0, 12.0, 13.0, 14.0, 15.0])}
    out, changed = pf.sanitize_html(_html_with(market, panel_aware=True))
    assert changed and '<script id="panel-data"' in out
    panel = json.loads(out.split('<script id="panel-data" type="application/json">')[1].split('</script>')[0])
    assert panel["恐慌指數"]["close"] == 15.0
    assert panel["恐慌指數"]["pctile"] == 100
    assert all("Close" not in r for r in _market_of(out)["恐慌指數"])
