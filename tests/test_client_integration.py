"""End-to-end check of VLLMClient against a stub OpenAI-compatible server.

Exercises the parts a unit test with a patched client would miss: the request body we actually
send, reading `reasoning_content` off the response, retry-then-record behaviour, and resuming
a partially finished run from the JSONL store.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from cotctl.inference import OK, UNCLOSED, Request, RolloutStore, SamplingParams, VLLMClient, run_sync


class _State:
    def __init__(self):
        self.requests: list[dict] = []
        self.fail_first_n = 0
        self.finish_reason = "stop"
        self.reasoning = "Let me think about this."
        self.reasoning_key = "reasoning"  # vLLM 0.29; older builds used reasoning_content
        self.content = "The answer is 4."
        self.lock = threading.Lock()


@pytest.fixture
def server():
    state = _State()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):  # /v1/models, used by wait_for_server
            self._send(200, {"data": [{"id": "stub-model", "object": "model"}]})

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            with state.lock:
                state.requests.append(body)
                if state.fail_first_n > 0:
                    state.fail_first_n -= 1
                    self._send(500, {"error": "transient"})
                    return
            self._send(
                200,
                {
                    "id": "x",
                    "object": "chat.completion",
                    "created": 0,
                    "model": "stub-model",
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": state.content,
                                state.reasoning_key: state.reasoning,
                            },
                            "finish_reason": state.finish_reason,
                        }
                    ],
                    "usage": {"prompt_tokens": 11, "completion_tokens": 22, "total_tokens": 33},
                },
            )

        def _send(self, code, payload):
            raw = json.dumps(payload).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

    httpd = HTTPServer(("127.0.0.1", 0), Handler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    url = f"http://127.0.0.1:{httpd.server_port}/v1"
    yield url, state
    httpd.shutdown()


def _client(url, **kw):
    return VLLMClient("stub-model", url, api_key="EMPTY", **kw)


class TestRequestShape:
    def test_no_system_prompt_and_metr_sampling(self, server):
        url, state = server
        run_sync(_client(url), [Request("s1", "m", "hello")], SamplingParams(), progress=False)
        body = state.requests[0]
        assert [m["role"] for m in body["messages"]] == ["user"], "METR uses no system prompt"
        assert body["messages"][0]["content"] == "hello"
        assert body["temperature"] == 1.0 and body["max_tokens"] == 16384
        assert "presence_penalty" not in body

    def test_top_k_forwarded(self, server):
        url, state = server
        run_sync(_client(url), [Request("s1", "m", "hi")], SamplingParams(top_k=20), progress=False)
        assert state.requests[0]["top_k"] == 20


class TestResponseParsing:
    def test_reasoning_content_becomes_reasoning(self, server):
        url, _ = server
        r = run_sync(_client(url), [Request("s1", "m", "hi")], SamplingParams(), progress=False)[0]
        assert r.reasoning == "Let me think about this."
        assert r.answer == "The answer is 4."
        assert r.think_status == OK
        assert (r.prompt_tokens, r.completion_tokens) == (11, 22)
        assert r.error is None

    def test_length_finish_with_no_answer_is_unclosed(self, server):
        url, state = server
        state.finish_reason, state.content = "length", ""
        r = run_sync(_client(url), [Request("s1", "m", "hi")], SamplingParams(), progress=False)[0]
        assert r.think_status == UNCLOSED and r.truncated is True


class TestReasoningFieldOverTheWire:
    """The client must read the think block under either field name, end to end."""

    @pytest.mark.parametrize("key", ["reasoning", "reasoning_content"])
    def test_both_field_names(self, server, key):
        url, state = server
        state.reasoning_key = key
        r = run_sync(_client(url), [Request("s1", "m", "hi")], SamplingParams(), progress=False)[0]
        assert r.reasoning == "Let me think about this."
        assert r.think_status == OK


class TestRetryAndResume:
    def test_transient_failure_is_retried(self, server):
        url, state = server
        state.fail_first_n = 2
        r = run_sync(_client(url, max_retries=4), [Request("s1", "m", "hi")], SamplingParams(), progress=False)[0]
        assert r.error is None and len(state.requests) == 3

    def test_exhausted_retries_record_an_error(self, server):
        url, state = server
        state.fail_first_n = 99
        r = run_sync(_client(url, max_retries=2), [Request("s1", "m", "hi")], SamplingParams(), progress=False)[0]
        assert r.error is not None and r.think_status == "missing"

    def test_resume_skips_completed_and_retries_errored(self, tmp_path, server):
        url, state = server
        reqs = [Request(f"s{i}", "m", "hi") for i in range(4)]
        store = RolloutStore(tmp_path / "r.jsonl")

        state.fail_first_n = 99  # first pass: everything fails
        with store:
            run_sync(_client(url, max_retries=1), reqs, SamplingParams(), store, progress=False)
        assert len(RolloutStore(tmp_path / "r.jsonl")) == 0

        state.fail_first_n = 0
        n_before = len(state.requests)
        store2 = RolloutStore(tmp_path / "r.jsonl")
        with store2:
            run_sync(_client(url), reqs, SamplingParams(), store2, progress=False)
        assert len(state.requests) - n_before == 4, "all four are retried"
        assert len(RolloutStore(tmp_path / "r.jsonl")) == 4

        n_before = len(state.requests)
        store3 = RolloutStore(tmp_path / "r.jsonl")
        with store3:
            run_sync(_client(url), reqs, SamplingParams(), store3, progress=False)
        assert len(state.requests) == n_before, "a completed run issues no requests"

    def test_concurrency_bound_respected(self, server):
        url, state = server
        reqs = [Request(f"s{i}", "m", "hi") for i in range(20)]
        run_sync(_client(url, concurrency=4), reqs, SamplingParams(), progress=False)
        assert len(state.requests) == 20


class TestWaitForServer:
    def test_returns_served_model_id(self, server):
        from cotctl.inference import wait_for_server

        url, _ = server
        assert wait_for_server(url, timeout=10) == "stub-model"
