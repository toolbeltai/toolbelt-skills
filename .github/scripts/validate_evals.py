#!/usr/bin/env python3
"""
Validate every */evals/evals.json file:
  - Valid JSON
  - Top-level 'evals' array is present
  - Each eval has: id, prompt, assertions (non-empty array)
"""
import json
import sys
from pathlib import Path


def validate(path: Path) -> list[str]:
    errors = []

    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        return [f"invalid JSON: {exc}"]

    evals = data.get("evals")
    if evals is None:
        return ["missing top-level 'evals' key"]
    if not isinstance(evals, list):
        return ["'evals' is not an array"]

    for i, case in enumerate(evals):
        tag = f"evals[{i}]"
        if "id" not in case:
            errors.append(f"{tag}: missing 'id'")
        if "prompt" not in case:
            errors.append(f"{tag}: missing 'prompt'")
        elif not str(case["prompt"]).strip():
            errors.append(f"{tag}: 'prompt' is empty")
        if "assertions" not in case:
            errors.append(f"{tag}: missing 'assertions'")
        elif not isinstance(case["assertions"], list):
            errors.append(f"{tag}: 'assertions' is not an array")
        elif len(case["assertions"]) == 0:
            errors.append(f"{tag}: 'assertions' array is empty")

    return errors


def main() -> None:
    paths = sorted(Path(".").glob("*/evals/evals.json"))
    if not paths:
        print("No evals.json files found — skipping.")
        sys.exit(0)

    failed = False
    for path in paths:
        errors = validate(path)
        if errors:
            for msg in errors:
                print(f"FAIL  {path}: {msg}")
            failed = True
        else:
            print(f"OK    {path}")

    print()
    if failed:
        sys.exit(1)
    print(f"All {len(paths)} evals.json files valid.")


if __name__ == "__main__":
    main()
