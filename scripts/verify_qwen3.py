"""Opt-in local smoke check: one train case x five seeds, then one tokenizer probe."""

from __future__ import annotations

import argparse
import asyncio
import json
import platform
import time
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Any

import httpx

from apps.decision_program.baseline import FrozenBaseline, Message, render_request
from apps.decision_program.ollama_backend import BASE_URL, PINNED_MANIFEST, create_backend
from apps.decision_program.qwen3_tokenizer import TEMPLATE_ID, metadata_bytes
from apps.decision_program.signature import sha256
from apps.decision_program.versions import PROJECT_ROOT, SEEDS
from apps.evaluation.dataset import load_dataset
from apps.evaluation.metrics.correctness import score_attempt
from apps.evaluation.runner import summarize


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"
    )


async def verify(output_root: Path) -> Path:
    print("Verifying existing model blobs and building the local tokenizer...", flush=True)
    backend = create_backend()
    program = FrozenBaseline(backend)
    dataset = load_dataset(
        PROJECT_ROOT / "datasets",
        PROJECT_ROOT / "datasets/manifests/incident-decisions-draft-v1.json",
        allow_draft=True,
    )
    counts = {c.case_id: backend.tokenizer.count(render_request(c.input)) for c in dataset.cases}
    if max(counts.values()) > 8192:
        raise ValueError("at least one case exceeds the frozen input ceiling")
    # Selected before inference; failures do not trigger case substitution or retries.
    case = next(c for c in dataset.split("train") if "diagnostic" in c.tags and "initial" in c.tags)
    run_id = "qwen3-verification-" + uuid.uuid4().hex
    destination = output_root / run_id
    destination.mkdir(parents=True, exist_ok=False)
    binding = {
        "schema_version": "local-execution-binding/v1",
        "execution_id": program.execution_id,
        "implementation_sha256": program.implementation_digest,
        "model": backend.identity.model_dump(),
        "ollama_manifest_sha256": PINNED_MANIFEST,
        "tokenizer_metadata_sha256": backend.tokenizer.metadata_sha256,
        "chat_template_id": TEMPLATE_ID,
    }
    write_json(destination / "execution-binding.json", binding)
    metadata = {
        "run_id": run_id,
        "purpose": "local_verification_not_benchmark",
        "dataset_sha256": dataset.manifest_sha256,
        "dataset_draft": True,
        "case_id": case.case_id,
        "split": "train",
        "seeds": list(SEEDS),
        "scheduled_baseline_attempts": 5,
        "separate_conformance_probes": 1,
        "max_model_calls": 6,
        "max_call_deadline_ms": 30000,
        "warm_up": "none; short conformance probe runs AFTER baseline attempts",
        "response_cache": "none",
        "kv_cache": "Ollama may reuse prompt prefixes",
        "hardware": {"platform": platform.platform(), "processor": platform.processor()},
        "all_100_input_token_counts": counts,
        "binding_file_sha256": sha256((destination / "execution-binding.json").read_bytes()),
        "verification_script_sha256": sha256(Path(__file__).read_bytes()),
    }
    write_json(destination / "run.json", metadata)
    observations = []
    print(
        f"Token preflight: {min(counts.values())}..{max(counts.values())}/8192; "
        f"case={case.case_id}",
        flush=True,
    )
    try:
        with (destination / "observations.jsonl").open("x") as stream:
            for replicate, seed in enumerate(SEEDS):
                attempt = await program.run(case.input, seed)
                score = score_attempt(case, attempt)
                row: dict[str, Any] = {
                    "run_id": run_id,
                    "case_id": case.case_id,
                    "replicate": replicate,
                    "attempt": asdict(attempt),
                    "score": asdict(score),
                }
                row["attempt"]["decision"] = (
                    attempt.decision.model_dump() if attempt.decision else None
                )
                row["score"]["decision"] = score.decision.model_dump() if score.decision else None
                stream.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")
                stream.flush()
                observations.append(row)
                print(
                    f"seed={seed} status={score.status} correct={score.correct_next_action} "
                    f"unsafe={score.unsafe_action} "
                    f"tokens={attempt.input_tokens}/{attempt.output_tokens} "
                    f"latency_ms={attempt.latency_ms:.0f}",
                    flush=True,
                )
                if "tokenizer_usage_mismatch" in attempt.failure_flags:
                    raise ValueError("tokenizer conformance failed; no more calls are allowed")
    finally:
        result = summarize(observations, len(SEEDS))
        result["scope"] = "single_train_case_smoke_check_not_benchmark_accuracy"
        write_json(destination / "summary.json", result)
    probe_messages = (
        Message("system", "Reply briefly."),
        Message("user", "Reply only OK. Tokenization fixture: café 中文 नमस्ते 🧪 12345\nline two."),
    )
    expected = backend.tokenizer.count(probe_messages)
    probe: dict[str, Any] = {
        "purpose": "tokenizer_transport_conformance_not_baseline",
        "expected_input_tokens": expected,
        "max_output_tokens": 8,
        "deadline_ms": 30000,
        "seed": 101,
        "status": "incomplete",
    }
    start = time.monotonic()
    try:
        async with asyncio.timeout(30):
            completion = await backend.generate(
                probe_messages,
                seed=101,
                temperature=0.0,
                top_p=1.0,
                max_output_tokens=8,
                timeout_ms=30000,
            )
        probe.update(asdict(completion))
        probe["status"] = "passed" if completion.input_tokens == expected else "tokenizer_mismatch"
    except TimeoutError:
        probe.update(status="timeout", input_tokens=None, output_tokens=None)
    except Exception as error:
        probe.update(
            status="model_error",
            error_type=type(error).__name__,
            input_tokens=None,
            output_tokens=None,
        )
    probe["latency_ms"] = (time.monotonic() - start) * 1000
    write_json(destination / "tokenizer-probe.json", probe)
    async with httpx.AsyncClient(base_url=BASE_URL, trust_env=False, timeout=5) as client:
        response = await client.get("/api/ps")
        response.raise_for_status()
        write_json(destination / "loaded-models.json", response.json())
    # Seal artifacts for inspection; later invocations always get a new directory.
    hashes = {p.name: sha256(p.read_bytes()) for p in sorted(destination.iterdir()) if p.is_file()}
    (destination / "checksums.json").write_bytes(metadata_bytes(hashes) + b"\n")
    print(f"Tokenizer conformance probe: {probe['status']}; artifacts: {destination}", flush=True)
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=PROJECT_ROOT / "artifacts/local-verification"
    )
    args = parser.parse_args()
    asyncio.run(verify(args.output))


if __name__ == "__main__":
    main()
