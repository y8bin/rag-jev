"""Pinned GEval LF-Eval with every provider call routed through the shared budget."""
from __future__ import annotations

from importlib.metadata import version
import json
import math
import os
from pathlib import Path

from .config import provider_identity
from .io import digest, file_hash, read_json, read_jsonl, write_json
from .providers import Transport


def budget_judge(cfg, *, client=None):
    # Do this before importing the evaluator; do not upload evaluation data to a tracing service.
    os.environ["DEEPEVAL_TELEMETRY_OPT_OUT"] = "YES"
    os.environ["DEEPEVAL_UPDATE_WARNING_OPT_OUT"] = "YES"
    if version("deepeval") != "4.3.3":
        raise ValueError("Use the pinned .venv-lf-eval environment (DeepEval 4.3.3)")
    from deepeval.models import DeepEvalBaseLLM
    from openai.types.chat.chat_completion import ChatCompletion
    if cfg.budget_ledger is None:
        raise ValueError("LF-Eval requires the shared experiment budget ledger")

    class Judge(DeepEvalBaseLLM):
        def __init__(self):
            self.identity = provider_identity("judge", cfg.judge_backend)
            self.transport = Transport(cfg, client)
            self.traces = []
            super().__init__(model=self.identity["model"])

        def load_model(self):
            return self

        def get_model_name(self):
            return self.identity["model"]

        def supports_log_probs(self):
            return True

        def generate(self, *args, **kwargs):
            raise RuntimeError("Only asynchronous budgeted evaluation is enabled")

        async def a_generate(self, *args, **kwargs):
            # Never let the framework silently replace probability-weighted scoring with another API.
            raise RuntimeError("LF-Eval requires raw responses with token log probabilities")

        async def a_generate_raw_response(self, prompt, top_logprobs=20, **kwargs):
            if not isinstance(prompt, str):
                raise ValueError("Only text-only LF-Eval is supported")
            body = {"model": self.identity["model"], "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": cfg.max_output_tokens, "temperature": 0,
                    "logprobs": True, "top_logprobs": min(top_logprobs, 20), "store": False}
            key = digest({"body": body, "deepeval": "4.3.3"})
            cache = Path(cfg.cache_dir) / "lf-eval" / (key + ".json")
            if cache.exists():
                saved = read_json(cache)
                if saved["request_digest"] != key:
                    raise ValueError("LF-Eval cache identity mismatch")
                data, trace = saved["response"], {**saved["trace"], "cached": True, "current_cost_usd": 0}
            else:
                r = await self.transport.request("judge", self.identity, "/chat/completions", body)
                data, trace = r.value, r.trace
                write_json(cache, {"request_digest": key, "response": data, "trace": trace})
            completion = ChatCompletion.model_validate(data)
            choice = completion.choices[0]
            if choice.finish_reason != "stop" or choice.logprobs is None or not choice.logprobs.content:
                raise ValueError("Incomplete LF-Eval response or missing token probabilities")
            self.traces.append({**trace, "request_digest": key, "response": data})
            return completion, trace.get("cost_usd") or 0.0

    return Judge()


async def evaluate(cfg, gold_file: str, predictions_file: str, output: str,
                   rubric_file: str = "research/prompts/koblex_lf_eval.json") -> dict:
    gold, predictions = read_jsonl(gold_file), read_jsonl(predictions_file)
    expected_ids = [r["query_id"] for r in gold]
    if not expected_ids or len(set(expected_ids)) != len(expected_ids) or [p["query_id"] for p in predictions] != expected_ids:
        raise ValueError("LF-Eval predictions must match all gold IDs in order")
    if any(not isinstance(p.get("answer"), str) for p in predictions):
        raise ValueError("LF-Eval predictions need an answer string")
    rubric = read_json(rubric_file)
    # Inputs contain only background+question; expected answers and contexts remain in the gold file.
    questions = {q["query_id"]: q["question"] for q in read_jsonl(cfg.queries)}
    if set(questions) != set(expected_ids):
        raise ValueError("LF-Eval query inputs must cover exactly the gold IDs")
    judge = budget_judge(cfg)
    try:
        from deepeval.metrics import GEval
        from deepeval.test_case import LLMTestCase, SingleTurnParams
        signature = {"prediction_sha256": file_hash(predictions_file), "gold_sha256": file_hash(gold_file),
            "questions_sha256": file_hash(cfg.queries), "rubric_sha256": file_hash(rubric_file),
            "model": judge.get_model_name(), "deepeval": version("deepeval"), "openai": version("openai"),
            "top_logprobs": 20, "max_output_tokens": cfg.max_output_tokens, "temperature": 0,
            "score_scale": "framework 0..1, paper table multiplies by 100", "answer_clip_chars": 800}
        destination = Path(output)
        manifest_path = destination / "manifest.json"
        if manifest_path.exists():
            if read_json(manifest_path)["signature"] != signature:
                raise ValueError("Existing LF-Eval output uses a different frozen signature")
        elif destination.exists():
            raise ValueError("LF-Eval destination exists without a manifest")
        else:
            write_json(manifest_path, {"signature": signature, "completed": False})
        record_path = destination / "metrics.jsonl"
        records = read_jsonl(record_path) if record_path.exists() else []
        if [r["query_id"] for r in records] != expected_ids[:len(records)]:
            raise ValueError("LF-Eval resume IDs are incomplete, duplicated or reordered")
        for i in range(len(records), len(gold)):
            g, p = gold[i], predictions[i]
            metric = GEval(name="legal-fidelity", criteria=rubric["criteria"],
                evaluation_steps=rubric["evaluation_steps"], model=judge, top_logprobs=20,
                evaluation_params=[SingleTurnParams.INPUT, SingleTurnParams.ACTUAL_OUTPUT,
                                   SingleTurnParams.EXPECTED_OUTPUT, SingleTurnParams.CONTEXT],
                async_mode=True)
            before = len(judge.traces)
            score = await metric.a_measure(LLMTestCase(input=questions[g["query_id"]],
                actual_output=p["answer"].split("<\think>")[0][:800], expected_output=g["answer"],
                context=g["provisions"]), _show_indicator=False)
            # DeepEval can exceed its normalized bound by one floating-point ULP.
            if 1.0 < score <= 1.0 + 1e-12:
                score = 1.0
            if not math.isfinite(score) or not 0 <= score <= 1:
                raise ValueError(f"LF-Eval framework score {score!r} is outside the frozen 0..1 range")
            record = {"query_id": g["query_id"], "score": score, "reason": metric.reason,
                      "trace": judge.traces[before:]}
            with record_path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n")
            records.append(record)
        summary = {"questions": len(records), "lf_eval": sum(r["score"] for r in records) / len(records),
                   "signature": signature, "budget": judge.transport.budget.summary(), "completed": True}
        write_json(destination / "summary.json", summary)
        write_json(manifest_path, {"signature": signature, "completed": True})
        return summary
    finally:
        await judge.transport.close()
