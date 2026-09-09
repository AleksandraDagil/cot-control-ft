import pytest

from cotctl import prompts
from cotctl.datasets import load_cotcontrol, load_reasonif


def test_reasonif_prompt_reconstructs_dataset_prompts():
    """Rendering instruction + question must reproduce every stored ReasonIF prompt byte-for-byte."""
    mismatches = []
    for s in load_reasonif():
        instr = prompts.reasonif_instruction(s.metadata["instruction_type"], s.metadata["constraint_args"])
        if prompts.reasonif_prompt(s.question, instr) != s.metadata["prompt"]:
            mismatches.append(s.id)
    assert not mismatches, f"{len(mismatches)} mismatches, e.g. {mismatches[:5]}"


@pytest.mark.parametrize("mode", prompts.COTCONTROL_MODES)
@pytest.mark.parametrize("with_options", [True, False])
def test_cotcontrol_prompt_parity(upstream_cc_prompts, mode, with_options):
    up = upstream_cc_prompts
    question = "What is the capital of France?"
    options = ["Paris", "Lyon", "Nice", "Lille"] if with_options else None
    keywords = ["capital", "France"]
    control_value = prompts.cotcontrol_control_value(mode, keywords)
    sys_up, user_up = up.create_controlled_prompt(
        question=question, control_type=mode, control_value=control_value,
        adversarial_pressure="none", model_name="qwen/qwen3.5-9b", choices=options,
    )
    assert sys_up == ""
    assert prompts.cotcontrol_prompt(question, mode, control_value, options) == user_up


def test_cotcontrol_baseline_prompt():
    p = prompts.cotcontrol_prompt("Q?", None, options=["a", "b"])
    assert p.startswith("Question: Q?\n\nA) a\nB) b\n")
    assert "Requirement:" not in p
    assert prompts.cotcontrol_prompt("Q?", "baseline") == "Question: Q?"


def test_control_values():
    assert prompts.cotcontrol_control_value("word_suppression", ["x", "y"]) == "x"
    assert prompts.cotcontrol_control_value("multiple_word_suppression", ["x", "y"]) == "x, y"
    assert prompts.cotcontrol_control_value("meow_between_words") == "meow"
    assert prompts.cotcontrol_control_value("uppercase_thinking") == ""


def test_cotcontrol_dataset_loads_with_options():
    samples = load_cotcontrol()
    by = {}
    for s in samples:
        by.setdefault(s.dataset, []).append(s)
    assert {k: len(v) for k, v in by.items()} == {"cotcontrol/gpqa": 445, "cotcontrol/hle": 469, "cotcontrol/mmlu_pro": 300}
    assert all(s.options for s in by["cotcontrol/mmlu_pro"]), "MMLU-Pro choices live in the `options` column"
