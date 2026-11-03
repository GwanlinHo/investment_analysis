"""news.html 格式檢查：每則恰一個原文連結、摘要漢字上限、總則數上限、來源分散。"""

import update_report as ur

URL = "https://news.cnyes.com/news/id/1234567"


def _item(summary="外資連八日賣超台股，單日賣超四百六十一億元。", href=URL, title="外資賣超"):
    link = f'<a href="{href}" target="_blank" rel="noopener">{title}</a>' if href is not None else title
    return f"<li><strong>[鉅亨網] {link} (2026-10-16)</strong><br>{summary}</li>"


def _doc(*items):
    return "<ul>\n" + "\n".join(items) + "\n</ul>"


DOMAINS = ["https://news.cnyes.com/news/id/{}", "https://www.reuters.com/markets/{}",
           "https://www.cnbc.com/2026/11/03/{}.html", "https://www.cna.com.tw/news/afe/{}.aspx",
           "https://www.bloomberg.com/news/articles/{}"]


def _diverse(n):
    """n 則、輪流分配到 5 個網域（每網域至多 4 則，符合上限）。"""
    return [_item(href=DOMAINS[i % len(DOMAINS)].format(i)) for i in range(n)]


def test_valid_passes():
    assert ur.validate_news_structure(_doc(*_diverse(ur.NEWS_MAX_ITEMS))) == []


def test_source_key_normalizes_subdomains():
    assert ur.news_source_key("https://news.cnyes.com/news/id/1") == "cnyes.com"
    assert ur.news_source_key("https://m.cnyes.com/news/id/1") == "cnyes.com"
    assert ur.news_source_key("https://www.cna.com.tw/news/1.aspx") == "cna.com.tw"
    assert ur.news_source_key("https://www.bbc.co.uk/news/1") == "bbc.co.uk"
    assert ur.news_source_key("https://money.udn.com/money/story/1") == "udn.com"


def test_single_source_cap():
    items = _diverse(15) + [_item(href=f"https://m.cnyes.com/news/id/x{i}") for i in range(3)]
    errs = ur.validate_news_structure(_doc(*items))  # cnyes 3 + 3 = 6 則
    assert any("cnyes.com" in e and "上限" in e for e in errs)


def test_all_one_source_rejected():
    """2026-10-28 起的實況：20 則全來自鉅亨網，必須被擋下。"""
    errs = ur.validate_news_structure(_doc(*[_item()] * ur.NEWS_MAX_ITEMS))
    assert any("上限" in e and "cnyes.com" in e for e in errs)
    assert any("不同來源" in e for e in errs)


def test_min_sources():
    items = [_item(href=DOMAINS[i % 3].format(i)) for i in range(12)]  # 3 來源各 4 則
    assert any("不同來源" in e for e in ur.validate_news_structure(_doc(*items)))


def test_few_items_need_distinct_sources():
    assert ur.validate_news_structure(_doc(*_diverse(3))) == []
    assert any("不同來源" in e for e in ur.validate_news_structure(_doc(_item(), _item())))


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
