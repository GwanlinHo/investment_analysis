"""news.html 格式檢查：每則恰一個原文連結、摘要漢字上限、總則數上限。"""

import update_report as ur

URL = "https://news.cnyes.com/news/id/1234567"


def _item(summary="外資連八日賣超台股，單日賣超四百六十一億元。", href=URL, title="外資賣超"):
    link = f'<a href="{href}" target="_blank" rel="noopener">{title}</a>' if href is not None else title
    return f"<li><strong>[鉅亨網] {link} (2026-10-16)</strong><br>{summary}</li>"


def _doc(*items):
    return "<ul>\n" + "\n".join(items) + "\n</ul>"


def test_valid_passes():
    assert ur.validate_news_structure(_doc(*[_item()] * ur.NEWS_MAX_ITEMS)) == []


def test_missing_link_rejected():
    assert any("原文連結" in e for e in ur.validate_news_structure(_doc(_item(href=None))))


def test_two_links_rejected():
    item = _item(summary=f'摘要<a href="{URL}">另一連結</a>')
    assert any("原文連結" in e for e in ur.validate_news_structure(_doc(item)))


def test_non_http_link_rejected():
    assert any("有效網址" in e for e in ur.validate_news_structure(_doc(_item(href="#"))))


def test_summary_limit():
    ok = _item(summary="字" * ur.NEWS_SUMMARY_MAX_ZH)
    assert ur.validate_news_structure(_doc(ok)) == []
    long = _item(summary="字" * (ur.NEWS_SUMMARY_MAX_ZH + 1))
    assert any("超過上限" in e for e in ur.validate_news_structure(_doc(long)))


def test_title_not_counted():
    item = _item(title="長" * 100, summary="短摘要。")
    assert ur.validate_news_structure(_doc(item)) == []


def test_missing_summary_rejected():
    item = f'<li><strong>[鉅亨網] <a href="{URL}">標題</a> (2026-10-16)</strong></li>'
    assert any("缺少" in e for e in ur.validate_news_structure(_doc(item)))


def test_too_many_items_rejected():
    errs = ur.validate_news_structure(_doc(*[_item()] * (ur.NEWS_MAX_ITEMS + 1)))
    assert any("超過上限" in e and "則" in e for e in errs)


def test_empty_rejected():
    assert ur.validate_news_structure("<ul></ul>") != []


def test_current_style_news_rejected():
    """舊格式（無連結、長篇改寫）必須被擋下。"""
    old = "<li><strong>[鉅亨網] 加權指數上漲 141.39 點 (2026-10-16)</strong><br>" + "長" * 300 + "</li>"
    assert len(ur.validate_news_structure(_doc(old))) >= 2
