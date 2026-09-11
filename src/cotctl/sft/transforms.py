"""Stage-2 edits that turn an unconstrained reasoning trace into a compliant one.

Semantics and editor prompts follow METR's
`cot_controllability/src/controllability/training/transforms.py` at the pinned SHA, so the
training data we build is the same shape as theirs. Four of the six ReasonIF modes are pure
string edits; `reasoning_language` and `number_words` need an editor LLM.

Every edited trace is verified with the canonical grader in `cotctl.graders.reasonif` before it
can enter the dataset — a transform that silently fails to satisfy its own constraint would
teach the model the wrong thing, so the grader, not the transform, is the arbiter.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field

from ..prompts import LANGUAGE_NAMES

log = logging.getLogger(__name__)

_EDITED_TAG_RE = re.compile(r"<edited>(.*?)</edited>", re.DOTALL)

# METR's editor protocol, verbatim: the editor may think aloud, and only the LAST tagged block
# is read. Keeping this identical matters -- the prompts were tuned against it.
TAG_PROTOCOL_INSTRUCTION = (
    "You may think briefly about the edit, then output your final edited "
    "reasoning between `<edited>` and `</edited>` tags. Only the contents of "
    "the LAST `<edited>...</edited>` block are read by the downstream pipeline."
)

TRANSLATE_SYSTEM = (
    "You are translating an AI's internal reasoning trace into {language}. "
    "Translate the content faithfully — the wording will obviously change, "
    "but preserve the original style, structure, sentence boundaries, "
    "paragraphing, list formatting, and tone. Do not add, remove, or "
    "reorganize content. Where the AI uses fragments rather than full "
    "sentences, your translation should also use fragments.\n\n"
    "Translate EVERYTHING into {language}, including any quoted user "
    "questions, quoted text, dialog, examples, or other passages the AI "
    "has copied from English. Preserve only mathematical notation, code, "
    "and numbers verbatim — everything else should be in {language}.\n\n"
    + TAG_PROTOCOL_INSTRUCTION
)

CONDENSE_PROMPT = (
    "You are shortening an AI's internal reasoning trace to fewer than "
    "{llm_target} words while keeping the same writing style and reasoning "
    "content.\n\n"
    "Guidance:\n"
    "- Hitting the word limit will likely require edits in several places — "
    "trimming filler, combining adjacent sentences, dropping redundant "
    "restatements, or rewording verbose phrasings into compact ones.\n"
    "- Where you DO have to edit, keep the same writing style, tone, and "
    "vocabulary as the original. The result should read like the same AI's "
    "natural shorter reasoning, not a different writer's summary.\n"
    "- Keep the original wording verbatim wherever possible. Don't rephrase "
    "sentences that are already concise.\n"
    "- Preserve all key logical steps and the final conclusion. Preserve "
    "math notation, code, and technical terms verbatim.\n"
    "- Where the AI uses fragments rather than full sentences, your edit "
    "should also use fragments.\n\n"
    + TAG_PROTOCOL_INSTRUCTION
)


class EditorTagError(RuntimeError):
    """The editor did not return an `<edited>...</edited>` block."""


@dataclass
class TransformContext:
    """What a transform needs beyond the reasoning itself."""

    question: str = ""
    full_prompt: str = ""
    editor: object | None = None  # cotctl.sft.editor.Editor; None = rule-based fallbacks only
    extras: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# helpers (same semantics as METR's private ones)
# ---------------------------------------------------------------------------


def count_words(text: str) -> int:
    """Same tokenizer as the ReasonIF checkers."""
    return len(re.findall(r"\w+", text))


def truncate_to_word_limit(text: str, max_words: int) -> str:
    """Hard-truncate at a word boundary, counting `\\w+` tokens like the grader does."""
    out, n = [], 0
    for word in text.split():
        k = len(re.findall(r"\w+", word))
        if n + k > max_words:
            break
        out.append(word)
        n += k
    return " ".join(out)


def extract_edited(text: str) -> str | None:
    """Last `<edited>` payload, or None."""
    if not text:
        return None
    m = _EDITED_TAG_RE.findall(text)
    return m[-1].strip("\n") if m else None


def format_prompt_block(full_prompt: str) -> str:
    return f"## Original prompt the AI received\n{full_prompt}".strip()


# ---------------------------------------------------------------------------
# rule-based transforms
# ---------------------------------------------------------------------------


def transform_english_capital(reasoning: str, args: dict | None = None) -> str:
    return reasoning.upper()


def transform_no_comma(reasoning: str, args: dict | None = None) -> str:
    return reasoning.replace(",", "")


def transform_end_checker(reasoning: str, args: dict | None = None) -> str:
    phrase = ((args or {}).get("end_phrase") or "").strip()
    if not phrase:
        return reasoning
    text = reasoning.rstrip()
    if not text.lower().endswith(phrase.lower()):
        text = text + "\n" + phrase
    return text


def transform_json_format(reasoning: str, args: dict | None = None) -> str:
    return f'```json\n{{"reasoning": {json.dumps(reasoning)}}}\n```'


# ---------------------------------------------------------------------------
# LLM-based transforms
# ---------------------------------------------------------------------------


async def transform_reasoning_language(reasoning: str, args: dict | None, ctx: TransformContext) -> str:
    """Translate the trace. English is already compliant and is returned untouched."""
    language = (args or {}).get("language", "en")
    if language == "en":
        return reasoning
    if ctx.editor is None:
        raise ValueError("reasoning_language needs an editor LLM")
    lang_name = LANGUAGE_NAMES.get(language, language)
    user = f"{format_prompt_block(ctx.full_prompt or ctx.question)}\n\n## Reasoning trace to translate\n{reasoning}"
    out = await ctx.editor.call(TRANSLATE_SYSTEM.format(language=lang_name), user, temperature=0.3)
    edited = extract_edited(out)
    if edited is None:
        raise EditorTagError("translator returned no <edited> block")
    return edited


async def transform_number_words(reasoning: str, args: dict | None, ctx: TransformContext) -> str:
    """Condense to a per-sample budget, then hard-truncate if the editor overshot.

    The budget is dynamic, not the eval's calibrated limit: 70 % of this trace's own length
    (floor 50), with the editor aimed at 85 % of that so it has headroom. `args["num_words"]`
    is updated in place to the target actually used, because the training prompt must state
    the same number the grader will check.
    """
    if args is None:
        args = {}
    raw = count_words(reasoning)
    target = max(int(raw * 0.7), 50)
    llm_target = max(int(target * 0.85), 30)
    args["num_words"] = target

    if raw < target:  # already short enough
        return reasoning
    if ctx.editor is None:
        return truncate_to_word_limit(reasoning, target - 1)

    user = f"{format_prompt_block(ctx.full_prompt or ctx.question)}\n\n## Reasoning trace to shorten\n{reasoning}"
    try:
        out = await ctx.editor.call(CONDENSE_PROMPT.format(llm_target=llm_target), user, temperature=0.3)
        condensed = extract_edited(out)
        if condensed is None:
            raise EditorTagError("condenser returned no <edited> block")
    except (EditorTagError, Exception) as e:  # noqa: BLE001 - fall back rather than lose the row
        log.warning("condense failed (%s); hard-truncating instead", e)
        return truncate_to_word_limit(reasoning, target)

    if count_words(condensed) >= target:
        condensed = truncate_to_word_limit(condensed, target - 1)
    return condensed


# ---------------------------------------------------------------------------
# dispatch
# ---------------------------------------------------------------------------

RULE_BASED = {
    "english_capital": transform_english_capital,
    "no_comma": transform_no_comma,
    "end_checker": transform_end_checker,
    "json_format": transform_json_format,
}
LLM_BASED = {
    "reasoning_language": transform_reasoning_language,
    "number_words": transform_number_words,
}
REASONIF_MODES = tuple(RULE_BASED) + tuple(LLM_BASED)


async def apply_transform(
    mode: str, reasoning: str, args: dict | None = None, ctx: TransformContext | None = None
) -> str:
    """Apply one Stage-2 edit. `args` may be mutated (number_words writes its target back)."""
    if mode in RULE_BASED:
        return RULE_BASED[mode](reasoning, args)
    if mode in LLM_BASED:
        return await LLM_BASED[mode](reasoning, args, ctx or TransformContext())
    raise ValueError(f"unknown ReasonIF mode: {mode}")
