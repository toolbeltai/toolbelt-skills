#!/usr/bin/env python3
"""
Validate every */SKILL.md file:
  - YAML frontmatter is present and well-formed
  - Required fields: name, description, license
  - name matches the parent directory name
  - description is non-empty
"""
import sys
from pathlib import Path

import yaml


def parse_frontmatter(text: str) -> dict | None:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    try:
        end = next(i for i, l in enumerate(lines[1:], 1) if l.strip() == "---")
    except StopIteration:
        return None
    return yaml.safe_load("\n".join(lines[1:end]))


def validate(path: Path) -> list[str]:
    errors = []
    fm = parse_frontmatter(path.read_text())

    if fm is None:
        return ["missing or malformed YAML frontmatter"]

    for field in ("name", "description", "license"):
        if field not in fm:
            errors.append(f"missing required field: {field}")
        elif not str(fm[field]).strip():
            errors.append(f"field '{field}' is empty")

    dir_name = path.parent.name
    if "name" in fm and fm["name"] != dir_name:
        errors.append(f"name '{fm['name']}' does not match directory '{dir_name}'")

    return errors


def main() -> None:
    skills = sorted(Path(".").glob("*/SKILL.md"))
    if not skills:
        print("ERROR: no SKILL.md files found")
        sys.exit(1)

    failed = False
    for path in skills:
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
    print(f"All {len(skills)} SKILL.md files valid.")


if __name__ == "__main__":
    main()
