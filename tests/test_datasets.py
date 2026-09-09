from collections import Counter

from cotctl.datasets import load_cotcontrol, load_reasonif, proportional_sample


def test_reasonif_counts():
    s = load_reasonif()
    assert len(s) == 300
    assert Counter(x.metadata["instruction_type"] for x in s) == {
        "no_comma": 56, "number_words": 53, "reasoning_language": 52,
        "end_checker": 49, "json_format": 47, "english_capital": 43,
    }
    nw = next(x for x in s if x.metadata["instruction_type"] == "number_words")
    assert "num_words" in nw.metadata["constraint_args"]


def test_proportional_sample_is_deterministic_and_proportional():
    s = load_cotcontrol()
    a = proportional_sample(s, 300, seed=42)
    b = proportional_sample(s, 300, seed=42)
    assert [x.id for x in a] == [x.id for x in b]
    assert len(a) == 300
    assert all(x.metadata["valid_keywords"] for x in a)
    c = Counter(x.dataset for x in a)
    # 427/453/289 rows with keywords -> roughly 110/116/74
    assert 100 <= c["cotcontrol/gpqa"] <= 120 and 105 <= c["cotcontrol/hle"] <= 125 and 65 <= c["cotcontrol/mmlu_pro"] <= 85
    assert proportional_sample(s, 900, seed=42) != proportional_sample(s, 900, seed=43)
