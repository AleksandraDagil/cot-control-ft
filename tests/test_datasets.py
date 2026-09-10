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


class TestAnswerLetterResolution:
    """The three CoTControl CSVs disagree on the `answer` column format."""

    def test_bare_letter_passes_through(self):
        from cotctl.datasets import answer_letter

        assert answer_letter("C", ["a", "b", "c", "d"]) == "C"
        assert answer_letter("c", ["a", "b", "c", "d"]) == "C"

    def test_answer_text_resolves_to_its_option_letter(self):
        from cotctl.datasets import answer_letter

        assert answer_letter("R-loops", ["polyA tail", "lariat", "antisense", "R-loops"]) == "D"
        assert answer_letter("lariat", ["polyA tail", "lariat", "antisense", "R-loops"]) == "B"

    def test_whitespace_and_case_tolerated(self):
        from cotctl.datasets import answer_letter

        assert answer_letter("  R-LOOPS ", ["polyA tail", "lariat", "antisense", "R-loops"]) == "D"

    def test_unresolvable_returns_none_not_a_wrong_letter(self):
        from cotctl.datasets import answer_letter

        assert answer_letter("something absent", ["a", "b"]) is None
        assert answer_letter("", ["a", "b"]) is None
        assert answer_letter("long text", None) is None

    def test_every_upstream_row_resolves(self):
        from cotctl.datasets import load_cotcontrol

        for s in load_cotcontrol():
            assert s.metadata["answer_letter"] is not None, f"{s.id} did not resolve"


class TestCotcontrolScoring:
    def test_text_gold_scored_via_letter_not_first_character(self):
        from cotctl.eval import score_answer

        # Gold "The compounds..." must not be compared as "T".
        assert score_answer("cotcontrol", "ANSWER: C", "The compounds allow", gold_letter="C") is True
        assert score_answer("cotcontrol", "ANSWER: T", "The compounds allow", gold_letter="C") is False

    def test_unresolvable_gold_is_unscorable_not_wrong(self):
        from cotctl.eval import score_answer

        assert score_answer("cotcontrol", "ANSWER: C", "some long answer text") is None

    def test_bare_letter_gold_still_works_without_a_key(self):
        from cotctl.eval import score_answer

        assert score_answer("cotcontrol", "ANSWER: C", "C") is True
        assert score_answer("cotcontrol", "ANSWER: A", "C") is False

    def test_answer_key_regrades_stored_rollouts(self):
        from cotctl.eval import grade_rollout

        r = {"sample_id": "cotcontrol/gpqa_0", "mode": "word_suppression", "prompt": "p",
             "reasoning": "x", "answer": "ANSWER: D", "think_status": "ok",
             "meta": {"suite": "cotcontrol", "correct_answer": "R-loops"}}
        assert grade_rollout(r).correct is None                                   # no key: unscorable
        assert grade_rollout(r, None, {"cotcontrol/gpqa_0": "D"}).correct is True  # with key: right
