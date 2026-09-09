"""METR reference numbers and the baseline sanity check."""

from __future__ import annotations

import pytest

from cotctl.analysis.metr import (
    EXPECTED_BASELINE_RANGE,
    METR_RESULTS,
    comparison_table,
    sanity_check,
)


class TestReferenceNumbers:
    def test_plan_numbers_present(self):
        by_model = {r.model: r for r in METR_RESULTS}
        assert by_model["Qwen3-8B"].cotcontrol_base == 1.1
        assert by_model["Qwen3-8B"].cotcontrol_ft240 == 5.6
        assert by_model["GPT-OSS-120B"].reasonif_ft240 == 49.0

    def test_qwen35_rows_are_baseline_only(self):
        for r in METR_RESULTS:
            if r.model.startswith("Qwen3.5"):
                assert not r.has_ft, f"{r.model} has no published FT number"

    def test_finetuning_improved_every_measured_model(self):
        # The whole premise of the replication: FT@240 beats base everywhere METR measured it.
        for r in METR_RESULTS:
            if r.has_ft:
                assert r.cotcontrol_ft240 > r.cotcontrol_base
                assert r.reasonif_ft240 > r.reasonif_base

    def test_expected_range_brackets_our_model(self):
        lo, hi = EXPECTED_BASELINE_RANGE["cotcontrol"]
        assert lo == 0.0 and hi == 1.3  # Qwen3.5-4B .. Qwen3.5-27B


class TestComparisonTable:
    def test_includes_our_row(self):
        t = comparison_table(0.8, 9.6)
        assert "Qwen3.5-9B (this replication)" in t
        assert "0.8" in t and "9.6" in t

    def test_handles_missing_values(self):
        assert "—" in comparison_table(None, None)

    def test_all_models_listed(self):
        t = comparison_table(1.0, 10.0)
        for r in METR_RESULTS:
            assert r.model in t


class TestSanityCheck:
    def test_in_range_passes(self):
        notes = sanity_check(0.8, 9.6)
        assert all("as expected" in n for n in notes)

    def test_far_out_of_range_flagged(self):
        notes = sanity_check(45.0, 9.6)
        assert any("OUTSIDE" in n for n in notes)

    def test_slack_is_applied(self):
        # 3.0 is above the 1.3 ceiling but inside the default +-3 pp slack.
        assert all("as expected" in n for n in sanity_check(3.0, 9.6))
        assert any("OUTSIDE" in n for n in sanity_check(3.0, 9.6, slack=0.5))

    def test_none_handled(self):
        assert any("no value" in n for n in sanity_check(None, None))
