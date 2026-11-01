"""Verify the freeze or run it through an explicitly supplied trusted local adapter."""

import argparse
import asyncio
import importlib
from pathlib import Path
from typing import cast

from apps.decision_program.baseline import FrozenBaseline, LocalBackend
from apps.decision_program.versions import PROJECT_ROOT, verify_freeze
from apps.evaluation.dataset import load_dataset
from apps.evaluation.runner import evaluate


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--verify", action="store_true", help="Check implementation bytes; no inference"
    )
    parser.add_argument(
        "--backend", help="Trusted local Python module:factory returning LocalBackend"
    )
    parser.add_argument("--split", choices=("train", "dev"), default="train")
    parser.add_argument("--allow-draft", action="store_true")
    parser.add_argument("--dataset-root", type=Path, default=PROJECT_ROOT / "datasets")
    parser.add_argument("--manifest", default="manifests/incident-decisions-draft-v1.json")
    parser.add_argument("--expected-sha256")
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "artifacts/baseline")
    args = parser.parse_args()
    try:
        digest = verify_freeze()
        if args.verify:
            if args.backend:
                parser.error("--verify cannot be combined with --backend")
            print(f"Frozen implementation verified: {digest}")
            print("Core implementation verified; concrete model bindings are separate artifacts.")
            return
        if not args.backend or args.backend.count(":") != 1:
            parser.error("supply --verify or a trusted local --backend module:factory")
        module_name, factory_name = args.backend.split(":")
        backend = cast(LocalBackend, getattr(importlib.import_module(module_name), factory_name)())
        dataset = load_dataset(
            args.dataset_root,
            args.dataset_root / args.manifest,
            expected_digest=args.expected_sha256,
            allow_draft=args.allow_draft,
        )
        destination = asyncio.run(
            evaluate(
                dataset,
                args.split,
                FrozenBaseline(backend),
                args.output,
                allow_draft=args.allow_draft,
            )
        )
    except (ValueError, OSError, ImportError, AttributeError) as error:
        parser.error(str(error))
    print(f"Run artifacts: {destination}")


if __name__ == "__main__":
    main()
