"""Stage-2 transforms: parity with METR, and the property that actually matters --
every transform must produce text its own canonical grader accepts.
"""

from __future__ import annotations

import asyncio
import json

import pytest

from cotctl.graders.reasonif import grade_reasonif
from cotctl.prompts import END_PHRASES
from cotctl.sft import transforms as tr

SAMPLES = [
    "Let me think about this. First, I note that 2 + 2 = 4, which is clear.",
    "Step 1: read the question.\nStep 2: answer it.\nDone.",
    "A trace with, several, commas, in it.",
    "Short.",
    "word " * 300,
]


class TestRuleBasedMatchMetr:
    def test_english_capital_is_upper(self):
        assert tr.transform_english_capital("Hello, World") == "HELLO, WORLD"

    def test_no_comma_removes_commas_only(self):
        assert tr.transform_no_comma("a, b, c") == "a b c"

    def test_json_format_shape(self):
        out = tr.transform_json_format("hello")
        assert out.startswith("```json\n{\"reasoning\": ") and out.endswith("\n```")
        assert json.loads(out.removeprefix("```json\n").removesuffix("\n```"))["reasoning"] == "hello"

    def test_end_checker_appends_phrase(self):
        out = tr.transform_end_checker("some reasoning", {"end_phrase": END_PHRASES[0]})
        assert out.endswith(END_PHRASES[0])

    def test_end_checker_idempotent_when_already_ending(self):
        p = END_PHRASES[1]
        once = tr.transform_end_checker("text", {"end_phrase": p})
        assert tr.transform_end_checker(once, {"end_phrase": p}) == once

    def test_end_checker_without_phrase_is_a_noop(self):
        assert tr.transform_end_checker("text", {}) == "text"


class TestTransformsSatisfyTheirGrader:
    """The dataset is only as good as this: an edit that does not pass its own checker
    would teach the model the wrong target."""

    @pytest.mark.parametrize("text", SAMPLES)
    def test_english_capital(self, text):
        assert grade_reasonif("english_capital", tr.transform_english_capital(text)) is True

    @pytest.mark.parametrize("text", SAMPLES)
    def test_no_comma(self, text):
        assert grade_reasonif("no_comma", tr.transform_no_comma(text)) is True

    @pytest.mark.parametrize("text", SAMPLES)
    def test_json_format(self, text):
        assert grade_reasonif("json_format", tr.transform_json_format(text)) is True

    @pytest.mark.parametrize("text", SAMPLES)
    @pytest.mark.parametrize("phrase", END_PHRASES[:3])
    def test_end_checker(self, text, phrase):
        out = tr.transform_end_checker(text, {"end_phrase": phrase})
        assert grade_reasonif("end_checker", out, {"end_phrase": phrase}) is True


class TestNumberWords:
    def _run(self, text, args=None, ctx=None):
        return asyncio.run(tr.transform_number_words(text, args if args is not None else {}, ctx or tr.TransformContext()))

    def test_target_is_70_percent_with_a_floor_of_50(self):
        args = {}
        self._run("word " * 300, args)
        assert args["num_words"] == 210
        args2 = {}
        self._run("word " * 10, args2)
        assert args2["num_words"] == 50, "floor applies to short traces"

    def test_already_short_traces_pass_through_unchanged(self):
        text = "word " * 10
        assert self._run(text, {}) == text

    def test_without_an_editor_it_hard_truncates_below_target(self):
        args = {}
        out = self._run("word " * 300, args)
        assert tr.count_words(out) < args["num_words"]
        assert grade_reasonif("number_words", out, {"num_words": args["num_words"]}) is True

    def test_result_passes_the_grader_at_the_recorded_target(self):
        for n in (60, 120, 500, 1200):
            args = {}
            out = self._run("word " * n, args)
            assert grade_reasonif("number_words", out, {"num_words": args["num_words"]}) is True, n

    def test_editor_overshoot_is_truncated(self):
        class FakeEditor:
            async def call(self, system, user, temperature=0.3):
                return "<edited>" + "word " * 999 + "</edited>"   # ignores the budget

        args = {}
        out = self._run("word " * 300, args, tr.TransformContext(editor=FakeEditor()))
        assert tr.count_words(out) < args["num_words"]

    def test_editor_failure_falls_back_to_truncation(self):
        class BrokenEditor:
            async def call(self, system, user, temperature=0.3):
                raise RuntimeError("boom")

        args = {}
        out = self._run("word " * 300, args, tr.TransformContext(editor=BrokenEditor()))
        assert tr.count_words(out) <= args["num_words"]


class TestReasoningLanguage:
    def test_english_is_already_compliant_and_untouched(self):
        text = "some reasoning"
        out = asyncio.run(tr.transform_reasoning_language(text, {"language": "en"}, tr.TransformContext()))
        assert out == text

    def test_non_english_requires_an_editor(self):
        with pytest.raises(ValueError):
            asyncio.run(tr.transform_reasoning_language("x", {"language": "fr"}, tr.TransformContext()))

    def test_uses_the_last_edited_block(self):
        class FakeEditor:
            async def call(self, system, user, temperature=0.3):
                return "thinking...<edited>first</edited> more <edited>final</edited>"

        out = asyncio.run(
            tr.transform_reasoning_language("x", {"language": "fr"}, tr.TransformContext(editor=FakeEditor()))
        )
        assert out == "final"

    def test_missing_tags_raise(self):
        class FakeEditor:
            async def call(self, system, user, temperature=0.3):
                return "no tags here"

        with pytest.raises(tr.EditorTagError):
            asyncio.run(
                tr.transform_reasoning_language("x", {"language": "fr"}, tr.TransformContext(editor=FakeEditor()))
            )


class TestHelpers:
    def test_count_words_matches_the_grader_tokenizer(self):
        from cotctl.graders.reasonif import count_words as grader_count

        for t in SAMPLES:
            assert tr.count_words(t) == grader_count(t)

    def test_truncate_respects_the_token_count(self):
        assert tr.count_words(tr.truncate_to_word_limit("word " * 100, 25)) <= 25

    def test_extract_edited_returns_last_block(self):
        assert tr.extract_edited("<edited>a</edited><edited>b</edited>") == "b"
        assert tr.extract_edited("none") is None


class TestDispatch:
    def test_all_six_reasonif_modes_are_registered(self):
        from cotctl.prompts import REASONIF_INSTRUCTION_TYPES

        assert set(tr.REASONIF_MODES) == set(REASONIF_INSTRUCTION_TYPES)

    def test_unknown_mode_raises(self):
        with pytest.raises(ValueError):
            asyncio.run(tr.apply_transform("nope", "text"))

    @pytest.mark.parametrize("mode", ["english_capital", "no_comma", "json_format"])
    def test_dispatch_matches_direct_call(self, mode):
        text = "Some, reasoning."
        assert asyncio.run(tr.apply_transform(mode, text, {})) == tr.RULE_BASED[mode](text, {})
