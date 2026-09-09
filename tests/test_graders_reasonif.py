import pytest

from cotctl.graders import reasonif as ours
from cotctl.prompts import END_PHRASES

from conftest import CORPUS


def _upstream(checker_cls, **kwargs):
    c = checker_cls()
    c.build_description(**kwargs)
    return c


@pytest.mark.parametrize("text", CORPUS)
def test_rule_based_parity(upstream_reasonif_checker, text):
    up = upstream_reasonif_checker
    assert ours.check_no_comma(text) == bool(_upstream(up.CommaChecker).check_following(text))
    assert ours.check_json_format(text) == bool(_upstream(up.JsonFormat).check_following(text))
    for n in (1, 50, 100):
        assert ours.check_number_words(text, n) == bool(_upstream(up.NumberOfWords, num_words=n).check_following(text))
    for phrase in END_PHRASES[:2]:
        assert ours.check_end_phrase(text, phrase) == bool(_upstream(up.EndChecker, end_phrase=phrase).check_following(text))


@pytest.mark.parametrize("text", [t for t in CORPUS if t.strip()])
def test_language_parity(upstream_reasonif_checker, text):
    pytest.importorskip("fast_langdetect")
    up = upstream_reasonif_checker
    # Upstream calls detect(value, low_memory=False); newer fast_langdetect versions changed the API.
    # Apply the same normalisation METR used so we compare like with like.
    import fast_langdetect as fld

    orig = fld.detect

    def compat(value, **kw):
        kw.pop("low_memory", None)
        r = orig(value, **kw)
        if isinstance(r, list):
            return r[0] if r else {"lang": "unknown", "score": 0.0}
        return r

    fld.detect = compat
    up.detect = compat
    try:
        for lang in ("en", "fr", "es", "ru", "zh"):
            assert ours.check_reasoning_language(text, lang) == bool(
                _upstream(up.ReasoningLanguageChecker, language=lang).check_following(text)
            )
        assert ours.check_english_capital(text) == bool(_upstream(up.CapitalLettersEnglishChecker).check_following(text))
    finally:
        fld.detect = orig
        up.detect = orig


def test_empty_reasoning_is_noncompliant():
    assert ours.grade_reasonif("no_comma", "") is False
    assert ours.grade_reasonif("no_comma", "   ") is False
    assert ours.grade_reasonif("no_comma", "fine") is True
    assert ours.grade_reasonif("number_words", "a b c", {"num_words": 4}) is True
    assert ours.grade_reasonif("number_words", "a b c d", {"num_words": 4}) is False
