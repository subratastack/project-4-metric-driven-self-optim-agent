"""Validate the full dataset artifact; draft admission requires an explicit flag."""

import argparse
from pathlib import Path

from apps.decision_program.versions import PROJECT_ROOT
from apps.evaluation.dataset import load_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT / "datasets")
    parser.add_argument("--manifest", default="manifests/incident-decisions-draft-v1.json")
    parser.add_argument("--expected-sha256")
    parser.add_argument("--allow-draft", action="store_true")
    args = parser.parse_args()
    try:
        dataset = load_dataset(
            args.root,
            args.root / args.manifest,
            expected_digest=args.expected_sha256,
            allow_draft=args.allow_draft,
        )
    except (ValueError, OSError) as error:
        parser.error(str(error))
    lifecycle = "draft" if dataset.draft else "reviewed release"
    print(f"Validated {len(dataset.cases)} cases ({lifecycle}).")
    print(f"Manifest SHA-256: {dataset.manifest_sha256}")
    if dataset.draft:
        print("Independent label review and model-specific token admission remain pending.")


if __name__ == "__main__":
    main()
