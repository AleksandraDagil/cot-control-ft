"""Loss masking. The run is invalid if this is wrong, and wrong in a way that still trains."""

from __future__ import annotations

import pytest

from cotctl.train.data import ASSISTANT_HEADER, IGNORE_INDEX, Example, collate, encode, render


class FakeTok:
    """Minimal stand-in: character-level ids, and a chat template with the Qwen3.5 shape."""

    pad_token_id = 0

    def apply_chat_template(self, messages, tokenize=False):
        out = ""
        for m in messages:
            out += f"<|im_start|>{m['role']}\n{m['content']}<|im_end|>\n"
        return out

    def __call__(self, text, add_special_tokens=False):
        return {"input_ids": [ord(c) % 1000 for c in text]}


MSGS = [{"role": "user", "content": "QUESTION"}, {"role": "assistant", "content": "<think>\nR\n</think>\n\nA"}]


class TestRender:
    def test_prompt_ends_at_the_assistant_header(self):
        full, prompt = render(FakeTok(), MSGS)
        assert prompt.endswith(ASSISTANT_HEADER)
        assert full.startswith(prompt)

    def test_missing_assistant_header_raises(self):
        class NoHeader(FakeTok):
            def apply_chat_template(self, messages, tokenize=False):
                return "no header here"

        with pytest.raises(ValueError):
            render(NoHeader(), MSGS)


class TestEncode:
    def test_prompt_tokens_are_masked_and_assistant_tokens_are_not(self):
        ids, labels = encode(FakeTok(), MSGS, 10_000)
        assert len(ids) == len(labels)
        n_masked = sum(1 for l in labels if l == IGNORE_INDEX)
        assert 0 < n_masked < len(labels), "mask must cover some but not all tokens"
        # everything after the boundary is supervised, and equals the input
        assert labels[n_masked:] == ids[n_masked:]
        assert all(l == IGNORE_INDEX for l in labels[:n_masked])

    def test_the_question_is_never_supervised(self):
        tok = FakeTok()
        full, prompt = render(tok, MSGS)
        ids, labels = encode(tok, MSGS, 10_000)
        n_prompt = len(tok(prompt)["input_ids"])
        assert all(l == IGNORE_INDEX for l in labels[:n_prompt])

    def test_rows_over_max_len_are_dropped_not_truncated(self):
        assert encode(FakeTok(), MSGS, max_len=5) is None

    def test_long_row_kept_when_under_limit(self):
        assert encode(FakeTok(), MSGS, max_len=10_000) is not None


class TestExampleStats:
    def test_supervised_count_and_masked_fraction(self):
        e = Example(input_ids=[1, 2, 3, 4], labels=[IGNORE_INDEX, IGNORE_INDEX, 3, 4], mode="m", row_idx=0)
        assert e.n_supervised == 2
        assert e.masked_fraction == 0.5


class TestCollate:
    def test_padding_is_never_supervised(self):
        a = Example([1, 2, 3], [IGNORE_INDEX, 2, 3], "m", 0)
        b = Example([1], [IGNORE_INDEX], "m", 1)
        batch = collate([a, b], pad_token_id=0)
        assert batch["input_ids"].shape == (2, 3)
        # every padded position must be ignored in the labels and zero in the attention mask
        assert batch["labels"][1].tolist() == [IGNORE_INDEX, IGNORE_INDEX, IGNORE_INDEX]
        assert batch["attention_mask"][1].tolist() == [1, 0, 0]

    def test_attention_mask_matches_real_tokens(self):
        a = Example([1, 2, 3, 4], [IGNORE_INDEX] * 2 + [3, 4], "m", 0)
        batch = collate([a], pad_token_id=0)
        assert batch["attention_mask"].sum().item() == 4


class TestLoraTargets:
    def test_vision_and_mtp_and_lm_head_are_excluded(self):
        import torch

        from cotctl.train.sft_lora import target_module_names

        class M(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.model = torch.nn.Module()
                self.model.layers = torch.nn.ModuleDict({
                    "0": torch.nn.ModuleDict({"self_attn": torch.nn.ModuleDict({"q_proj": torch.nn.Linear(2, 2)})}),
                })
                self.model.visual = torch.nn.ModuleDict({"blocks": torch.nn.ModuleDict({"qkv": torch.nn.Linear(2, 2)})})
                self.mtp = torch.nn.ModuleDict({"q_proj": torch.nn.Linear(2, 2)})
                self.lm_head = torch.nn.Linear(2, 2)

        names = target_module_names(M())
        assert any("q_proj" in n and "layers" in n for n in names)
        assert not any("visual" in n for n in names)
        assert not any(n.startswith("mtp") for n in names)
        assert not any(n.endswith("lm_head") for n in names)


class TestReasoningSurvivesTheChatTemplate:
    """A chat template that silently drops <think>...</think> from the assistant turn would
    train on answers only, with every diagnostic looking healthy: loss falls, the masking stats
    are sane, the adapter is non-zero. It surfaces at eval as "fine-tuning did nothing".

    This is not hypothetical. DeepSeek-R1-Distill's template does exactly that, while its
    *generation* prompt still prefills <think> -- so inference looks correct and training is
    empty. Assert the reasoning survives before spending GPU time on any new model.
    """

    REASONING = "UNIQUE_REASONING_SENTINEL"
    ANSWER = "UNIQUE_ANSWER_SENTINEL"

    def _messages(self):
        return [
            {"role": "user", "content": "question"},
            {"role": "assistant", "content": f"<think>\n{self.REASONING}\n</think>\n\n{self.ANSWER}"},
        ]

    def test_fake_template_round_trip(self):
        rendered = FakeTok().apply_chat_template(self._messages(), tokenize=False)
        assert self.REASONING in rendered, "reasoning was dropped by the template"
        assert self.ANSWER in rendered

    def test_qwen35_template_keeps_the_reasoning(self):
        # The real tokenizer, if the model is cached locally; skipped otherwise so CI stays offline.
        transformers = pytest.importorskip("transformers")
        try:
            tok = transformers.AutoTokenizer.from_pretrained(
                "Qwen/Qwen3.5-9B", local_files_only=True
            )
        except Exception:
            pytest.skip("Qwen3.5-9B tokenizer not cached locally")
        rendered = tok.apply_chat_template(self._messages(), tokenize=False)
        assert self.REASONING in rendered, (
            "the chat template dropped the think block: training would see answers only"
        )
        assert self.ANSWER in rendered
        assert rendered.count("<think>") == 1, "think tag duplicated by the template"

    def test_encode_supervises_the_reasoning_tokens(self):
        tok = FakeTok()
        ids, labels = encode(tok, self._messages(), 10_000)
        supervised = "".join(chr(i) for i, l in zip(ids, labels) if l != IGNORE_INDEX)
        # Character-level fake tokenizer, so the sentinel appears verbatim in supervised text.
        assert self.REASONING in supervised, "reasoning present but not supervised"
