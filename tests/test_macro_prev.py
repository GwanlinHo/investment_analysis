"""總經表格「前值」欄（2026-11-12 使用者指示：第三欄改顯示上一期數值，上限 10 字）。"""

import re

import macro_history as mh
import update_report as ur


def _hist(*versions):
    return [{"value": v, "note": n, "trend": "neutral", "first_seen": d} for v, n, d in versions]


def _payload(cache, history):
    return mh.build_payload(cache, history)


# --- resolve_prev -----------------------------------------------------------

def test_explicit_prev_wins_over_history():
    item = {"name": "非農", "value": "16.5 萬", "note": "2026-10 (...)", "prev": "6 萬"}
    assert mh.resolve_prev(item, "2.9 萬", "2026-09 (...)") == "6 萬"


def test_history_prev_used_when_period_differs():
    item = {"name": "CPI", "value": "3.7%", "note": "2026-09 (...)"}
    assert mh.resolve_prev(item, "3.4%", "2026-08 (...)") == "3.4%"


def test_same_period_revision_is_not_previous_period():
    # 密大：同月初值 -> 終值，不可把初值當成上一期
    item = {"name": "密大", "value": "48.0", "note": "2026-10 (終值...)"}
    assert mh.resolve_prev(item, "46.3", "2026-10 (初值...)") == ""


def test_unchanged_value_from_earlier_period_is_valid():
    item = {"name": "利率", "value": "3.75%-4.00%", "note": "2026-10-28 (...)"}
    assert mh.resolve_prev(item, "3.75%-4.00%", "2026-09-16 (...)") == "3.75-4.00%"


def test_overlong_history_prev_is_blanked_not_truncated():
    item = {"name": "外匯存底", "value": "5,964.37 億美元", "note": "2026-10 (...)"}
    assert mh.resolve_prev(item, "6,007.45 億美元", "2026-09 (...)") == ""


def test_no_history_gives_blank():
    item = {"name": "x", "value": "1", "note": "2026-09 (...)"}
    assert mh.resolve_prev(item, "", "") == ""


def test_explicit_prev_errors_flags_only_overlong():
    cache = {"US_MACRO": [{"name": "a", "prev": "1234567890"}, {"name": "b", "prev": "12345678901"}],
             "TW_MACRO": [{"name": "c"}]}
    errs = mh.explicit_prev_errors(cache)
    assert len(errs) == 1 and "b" in errs[0]


# --- build_payload：表格與速覽面板共用同一個 prev --------------------------------

def test_payload_prev_is_resolved_value():
    cache = {"US_MACRO": [{"name": "密大", "value": "48.0", "note": "2026-10 (終值)"}], "TW_MACRO": []}
    history = {"US_MACRO": {"密大": _hist(("48.1", "2026-09 (終值)", "2026-10-01"),
                                         ("46.3", "2026-10 (初值)", "2026-10-11"),
                                         ("48.0", "2026-10 (終值)", "2026-10-25"))},
               "TW_MACRO": {}}
    row = _payload(cache, history)["US_MACRO"][0]
    assert row["prev"] == ""  # 前一版本是同月初值 -> 不採用
    cache["US_MACRO"][0]["prev"] = "48.1"
    assert _payload(cache, history)["US_MACRO"][0]["prev"] == "48.1"


# --- generate_macro_table ---------------------------------------------------

def _cells(html):
    return [re.sub(r"<[^>]+>", "", c).strip() for c in re.findall(r"<td[^>]*>(.*?)</td>", html, flags=re.S)]


def test_table_third_column_is_prev_not_note():
    rows = [{"name": "CPI", "value": "3.7%", "trend": "up", "note": "2026-09 (很長的查證備註" + "字" * 200 + ")",
             "prev": "3.4%"},
            {"name": "重貼現率", "value": "2%", "trend": "neutral", "note": "2026-09-17 (...)", "prev": ""}]
    html = ur.generate_macro_table(rows, "us-macro-table")
    assert "<th style=\"text-align:right;\">前值</th>" in html
    assert "日期/備註" not in html and "查證備註" not in html
    cells = _cells(html)
    assert cells[2] == "3.4%" and cells[5] == "-"
    assert all(len(c) <= mh.PREV_MAX_LEN for c in cells[2::3])


def test_table_escapes_prev():
    html = ur.generate_macro_table([{"name": "a", "value": "1", "prev": "<b>"}], "us-macro-table")
    assert "<b>" not in html and "&lt;b&gt;" in html


# --- MacroParser：新舊報告的第三欄 ------------------------------------------------

def test_parser_reads_new_table_third_column_as_prev():
    html = ur.generate_macro_table([{"name": "CPI", "value": "3.7%", "trend": "up", "prev": "3.4%"}],
                                   "us-macro-table")
    p = ur.MacroParser()
    p.feed(html)
    row = p.results["US_MACRO"][0]
    assert row["prev"] == "3.4%" and "note" not in row


def test_parser_reads_old_table_third_column_as_note():
    html = ('<table class="macro-table" id="tw-macro-table"><thead><tr><th>指標名稱</th><th>數值</th>'
            '<th>日期/備註</th></tr></thead><tbody><tr><td>CPI</td><td>2.33%</td>'
            '<td>2026-10 (主計總處)</td></tr></tbody></table>')
    p = ur.MacroParser()
    p.feed(html)
    assert p.results["TW_MACRO"][0]["note"] == "2026-10 (主計總處)"


def test_backfill_upsert_without_note_does_not_duplicate_version():
    history = {"US_MACRO": {"CPI": _hist(("3.7%", "2026-09 (BLS)", "2026-10-15"))}, "TW_MACRO": {}}
    added = mh.upsert(history, "US_MACRO", [{"name": "CPI", "value": "3.7%", "prev": "3.4%"}], "2026-11-12")
    assert added == 0
    assert history["US_MACRO"]["CPI"][-1]["note"] == "2026-09 (BLS)"
