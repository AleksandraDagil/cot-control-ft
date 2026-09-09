"""Shared fixtures. Parity tests need the upstream clones under ./ref (or $COTCTL_REF_DIR)."""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
REF = Path(os.environ.get("COTCTL_REF_DIR", REPO / "ref"))


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    # Register before exec: dataclasses in the loaded module resolve annotations via
    # sys.modules[cls.__module__], which is None for a module that was never registered.
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="session")
def upstream_cc_grading():
    p = REF / "CoTControl" / "CoT-Control-QA" / "grading.py"
    if not p.exists():
        pytest.skip(f"upstream CoTControl clone not found at {p}")
    return _load_module("cc_grading", p)


@pytest.fixture(scope="session")
def upstream_cc_prompts():
    p = REF / "CoTControl" / "CoT-Control-QA" / "prompts.py"
    if not p.exists():
        pytest.skip(f"upstream CoTControl clone not found at {p}")
    return _load_module("cc_prompts", p)


@pytest.fixture(scope="session")
def upstream_cc_llm():
    p = REF / "CoTControl" / "CoT-Control-QA" / "llm.py"
    if not p.exists():
        pytest.skip(f"upstream CoTControl clone not found at {p}")
    pytest.importorskip("dotenv")
    return _load_module("cc_llm", p)


@pytest.fixture(scope="session")
def upstream_cc_judge():
    """`grade_compliance_csv.py` holds the ignore_question / meta-discussion judge prompts."""
    p = REF / "CoTControl" / "CoT-Control-QA" / "grade_compliance_csv.py"
    if not p.exists():
        pytest.skip(f"upstream CoTControl clone not found at {p}")
    pytest.importorskip("pandas")
    sys.path.insert(0, str(p.parent))  # it does `from grading import ...`
    return _load_module("cc_judge", p)


@pytest.fixture(scope="session")
def upstream_reasonif_utils():
    p = REF / "reasonIF" / "src" / "utils.py"
    if not p.exists():
        pytest.skip(f"upstream reasonIF clone not found at {p}")
    pytest.importorskip("pandas")
    return _load_module("rif_utils", p)


@pytest.fixture(scope="session")
def upstream_reasonif_checker():
    src = REF / "reasonIF" / "src"
    if not (src / "instructions" / "instruction_checker.py").exists():
        pytest.skip(f"upstream reasonIF clone not found at {src}")
    pytest.importorskip("nltk")
    pytest.importorskip("immutabledict")
    sys.path.insert(0, str(src))
    import instructions.instruction_checker as checker  # noqa: E402

    return checker


# A corpus of reasoning-like strings that exercise grader edge cases.
CORPUS = [
    "",
    "   ",
    "hello world",
    "HELLO WORLD",
    "HELLO, WORLD 123 = 4 + 5",
    "hello, world. this is a test! is it? yes: it is.",
    "HeLlO wOrLd",
    "hElLo WoRlD",
    "hElLo WoRlD a I x",
    "safe. safe! safe? Not safe. safe",
    "This ends safe. And this one too safe.",
    "This ends safe. But this one does not.",
    "<This reasoning is not suspicious.> middle <This reasoning is not suspicious.>",
    "<this reasoning is not suspicious.>\nmiddle stuff\n<THIS REASONING IS NOT SUSPICIOUS.>",
    "<This reasoning is not suspicious.> only at start",
    "meow hello meow world meow",
    "hello meow world",
    "hello meow world. next meow sentence",
    "hello meow world\nnext meow line meow here",
    "1. meow first meow item\n2. meow second",
    "x = meow 2 + meow 3 meow ok",
    "we compute sqrt(16) meow then meow 4x meow plus meow CO2",
    "The uncertainty principle says uncertainty is fundamental.",
    "The Uncertainty of it all; uncertainties abound.",
    "no keyword here",
    "1234 5678",
    "!!! ??? ...",
    "ÉCOLE FRANÇAISE ÜBER",
    "école française über",
    "Je pense donc je suis. C'est la vie, n'est-ce pas?",
    "El rápido zorro marrón salta sobre el perro perezoso.",
    "Это простое предложение на русском языке.",
    "这是一个中文句子。我们正在测试语言检测。",
    '```json\n{"reasoning": "hello"}\n```',
    '```JSON\n{"reasoning": "hello"}\n```',
    '{"reasoning": "hello"}',
    "```\n{bad json}\n```",
    'not json at all',
    'The answer is 42. THIS REASONING WAS PRODUCED BY AI',
    'The answer is 42. "THIS REASONING WAS PRODUCED BY AI"',
    'THIS REASONING WAS PRODUCED BY AI. The answer is 42.',
    "this reasoning was produced by ai",
    "A long trace. " * 200,
    "word " * 49,
    "word " * 50,
    "The instructions say I must avoid commas. The user prompt has a constraint.",
    "Let me think about this problem directly without meta commentary.",
]
