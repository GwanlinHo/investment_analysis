"""ai.html 結構與篇幅檢查：只准五位分析師、依序、每段漢字上限。"""

import update_report as ur


def _sec(name, n=10):
    return f"<h3>{name}｜標題</h3>\n<p>{'字' * n}</p>\n"


def _ok_doc(n=10):
    return '<div class="ai-analysis">\n' + "".join(_sec(p, n) for p in ur.AI_PERSONAS) + "</div>"


def test_valid_passes():
    assert ur.validate_ai_structure(_ok_doc()) == []


def test_extra_section_rejected():
    doc = _ok_doc().replace('<div class="ai-analysis">\n', '<div class="ai-analysis">\n<h3>本期資料品質揭露</h3><p>說明</p>\n')
    errs = ur.validate_ai_structure(doc)
    assert any("不允許的標題" in e for e in errs)


def test_sub_heading_rejected():
    doc = _ok_doc().replace("<h3>Kenji", "<h4>補充</h4><h3>Kenji")
    assert any("補充" in e for e in ur.validate_ai_structure(doc))


def test_missing_or_out_of_order():
    doc = '<div>' + _sec("Sophia") + _sec("Atlas") + _sec("Kenji") + _sec("Crow") + _sec("Rain") + '</div>'
    assert any("依序" in e for e in ur.validate_ai_structure(doc))
    doc = '<div>' + "".join(_sec(p) for p in ur.AI_PERSONAS[:4]) + '</div>'
    assert any("依序" in e for e in ur.validate_ai_structure(doc))


def test_text_before_first_persona_rejected():
    doc = _ok_doc().replace('<div class="ai-analysis">\n', '<div class="ai-analysis"><p>前言</p>')
    assert any("之前不得有內容" in e for e in ur.validate_ai_structure(doc))


def test_length_limit():
    assert ur.validate_ai_structure(_ok_doc(ur.AI_SECTION_MAX_ZH)) == []
    errs = ur.validate_ai_structure(_ok_doc(ur.AI_SECTION_MAX_ZH + 1))
    assert len(errs) == 5 and all("超過上限" in e for e in errs)


def test_tags_and_markup_not_counted():
    body = "字" * ur.AI_SECTION_MAX_ZH + " {{TAIEX}} <strong>ABC</strong> 123"
    doc = '<div>' + "".join(f"<h3>{p}</h3><p>{body}</p>" for p in ur.AI_PERSONAS) + '</div>'
    assert ur.validate_ai_structure(doc) == []
