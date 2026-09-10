"""Think-block extraction and the resumable rollout store."""

from __future__ import annotations

import json

import pytest

from cotctl.inference import (
    EMPTY,
    MISSING,
    OK,
    UNCLOSED,
    Request,
    Rollout,
    RolloutStore,
    SamplingParams,
    split_think,
)


class TestSplitThink:
    def test_reasoning_parser_path(self):
        r, a, s = split_think("The answer is 4.", "Let me add 2 and 2.", "stop")
        assert (r, a.strip(), s) == ("Let me add 2 and 2.", "The answer is 4.", OK)

    def test_truncated_inside_think_is_unclosed(self):
        r, a, s = split_think("", "I am still thinking and ran out of", "length")
        assert s == UNCLOSED and a == ""

    def test_closed_think_but_empty_answer_is_gradeable(self):
        # finish_reason "stop" with no answer text: the block *was* closed, so the
        # reasoning is still gradeable for compliance.
        _, _, s = split_think("", "some reasoning", "stop")
        assert s == OK

    def test_raw_tags_in_content(self):
        r, a, s = split_think("<think>reasoning here</think>\n\nanswer here", None, "stop")
        assert (r, a.strip(), s) == ("reasoning here", "answer here", OK)

    def test_raw_unclosed_tag(self):
        r, a, s = split_think("<think>never closed", None, "length")
        assert s == UNCLOSED and r == "never closed"

    def test_no_think_block(self):
        r, a, s = split_think("just an answer", None, "stop")
        assert (r, a, s) == ("", "just an answer", MISSING)

    def test_whitespace_only_think_is_empty(self):
        _, _, s = split_think("<think>   </think>answer", None, "stop")
        assert s == EMPTY

    def test_whitespace_only_reasoning_content_is_empty(self):
        _, _, s = split_think("answer", "   ", "stop")
        assert s == EMPTY

    def test_multiline_reasoning_preserved(self):
        r, _, _ = split_think("<think>line one\nline two</think>ans", None, "stop")
        assert r == "line one\nline two"

    def test_none_content(self):
        assert split_think(None, None, "stop") == ("", "", MISSING)


class TestRolloutStore:
    def _rollout(self, sid, mode="m", error=None):
        return Rollout(
            sample_id=sid, mode=mode, prompt="p", reasoning="r", answer="a",
            think_status=OK, error=error,
        )

    def test_roundtrip_and_membership(self, tmp_path):
        p = tmp_path / "r.jsonl"
        with RolloutStore(p) as s:
            s.append(self._rollout("a"))
            s.append(self._rollout("b"))
        assert len(RolloutStore(p)) == 2
        assert ("a", "m") in RolloutStore(p)
        assert ("zzz", "m") not in RolloutStore(p)

    def test_errored_rollouts_are_retried(self, tmp_path):
        p = tmp_path / "r.jsonl"
        with RolloutStore(p) as s:
            s.append(self._rollout("a", error="boom"))
        assert ("a", "m") not in RolloutStore(p)

    def test_retry_supersedes_error_in_read_all(self, tmp_path):
        p = tmp_path / "r.jsonl"
        with RolloutStore(p) as s:
            s.append(self._rollout("a", error="boom"))
            s.append(self._rollout("a"))
        rows = RolloutStore(p).read_all()
        assert len(rows) == 1 and rows[0]["error"] is None

    def test_truncated_last_line_is_tolerated(self, tmp_path):
        p = tmp_path / "r.jsonl"
        with RolloutStore(p) as s:
            s.append(self._rollout("a"))
        with open(p, "a") as f:
            f.write('{"sample_id": "b", "mo')  # interrupted mid-write
        assert len(RolloutStore(p)) == 1

    def test_same_id_different_modes_are_distinct(self, tmp_path):
        p = tmp_path / "r.jsonl"
        with RolloutStore(p) as s:
            s.append(self._rollout("a", "m1"))
        st = RolloutStore(p)
        assert ("a", "m1") in st and ("a", "m2") not in st


class TestSamplingParams:
    def test_metr_defaults(self):
        sp = SamplingParams()
        assert sp.temperature == 1.0 and sp.max_tokens == 16384

    def test_no_presence_penalty(self):
        # A presence penalty would bias the meow/repeat_sentences modes.
        assert "presence_penalty" not in json.dumps(SamplingParams().to_request())

    def test_top_k_goes_in_extra_body(self):
        assert SamplingParams(top_k=20).to_request()["extra_body"]["top_k"] == 20


class TestReasoningField:
    """vLLM 0.29 renamed the parser's output field from reasoning_content to reasoning."""

    def test_reads_vllm_029_reasoning(self):
        from cotctl.inference import reasoning_field

        assert reasoning_field({"reasoning": "thought", "content": "ans"}) == "thought"

    def test_reads_legacy_reasoning_content(self):
        from cotctl.inference import reasoning_field

        assert reasoning_field({"reasoning_content": "thought"}) == "thought"

    def test_prefers_populated_field(self):
        from cotctl.inference import reasoning_field

        assert reasoning_field({"reasoning_content": "", "reasoning": "thought"}) == "thought"

    def test_none_when_absent_or_empty(self):
        from cotctl.inference import reasoning_field

        assert reasoning_field({"content": "ans"}) is None
        assert reasoning_field({"reasoning": ""}) is None

    def test_works_on_objects_not_just_dicts(self):
        from cotctl.inference import reasoning_field

        class Msg:
            content = "ans"
            reasoning = "thought"

        assert reasoning_field(Msg()) == "thought"
