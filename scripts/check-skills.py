#!/usr/bin/env python3
"""Validate the skills in this repo.

Three checks, all of which catch failures that are otherwise silent:

1. Every skill directory holds a SKILL.md whose `name:` matches the
   directory name. A skill that fails this does not load, and nothing
   reports an error — it simply never appears. That bug went unnoticed in
   nucleus-docs for months.
2. No two skills declare the same `name:`.
3. Relative links inside skill and reference files resolve to a real file.

Exit codes: 0 clean, 1 findings, 2 the check could not run.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "plugins" / "nucleus" / "skills"

FRONTMATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.DOTALL)
FIELD = re.compile(r"^(name|description):\s*(.+?)\s*$", re.MULTILINE)
MD_LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")
FENCE = re.compile(r"^(?P<fence>```+|~~~+).*?^(?P=fence)", re.DOTALL | re.MULTILINE)
CODE_SPAN = re.compile(r"`+[^`\n]*`+")


def strip_code(text: str) -> str:
    """Blank out fenced blocks and inline code.

    Links inside them are examples and regexes, not references. Newlines are
    kept so nothing downstream cares about line offsets.
    """
    blank = lambda m: re.sub(r"[^\n]", " ", m.group(0))
    return CODE_SPAN.sub(blank, FENCE.sub(blank, text))


def frontmatter_fields(text: str) -> dict[str, str] | None:
    match = FRONTMATTER.match(text)
    if match is None:
        return None
    return {k: v for k, v in FIELD.findall(match.group(1))}


def check_skill(directory: Path, findings: list[str], seen: dict[str, Path]) -> None:
    skill_file = directory / "SKILL.md"
    if not skill_file.is_file():
        findings.append(f"{directory.relative_to(ROOT)}: no SKILL.md — this skill cannot load")
        return

    fields = frontmatter_fields(skill_file.read_text(encoding="utf-8"))
    rel = skill_file.relative_to(ROOT)
    if fields is None:
        findings.append(f"{rel}: no YAML frontmatter — this skill cannot load")
        return

    name = fields.get("name")
    if name is None:
        findings.append(f"{rel}: frontmatter has no `name:` field — this skill cannot load")
    elif name != directory.name:
        findings.append(f"{rel}: `name: {name}` does not match directory `{directory.name}`")
    else:
        first = seen.get(name)
        if first is not None:
            findings.append(f"{rel}: duplicate `name: {name}`, already declared by {first}")
        else:
            seen[name] = rel

    if not fields.get("description"):
        findings.append(f"{rel}: frontmatter has no `description:` — the model cannot decide to load it")


def check_links(path: Path, findings: list[str]) -> None:
    text = strip_code(path.read_text(encoding="utf-8"))
    for target in MD_LINK.findall(text):
        target = target.split("#", 1)[0].split(" ", 1)[0].strip()
        if not target or "://" in target or target.startswith(("#", "mailto:")):
            continue
        resolved = (ROOT if target.startswith("/") else path.parent) / target.lstrip("/")
        if not resolved.exists():
            findings.append(f"{path.relative_to(ROOT)}: link target does not exist — {target}")


def main() -> int:
    if not SKILLS.is_dir():
        print(f"error: {SKILLS.relative_to(ROOT)} does not exist", file=sys.stderr)
        return 2

    findings: list[str] = []
    seen: dict[str, Path] = {}
    directories = sorted(d for d in SKILLS.iterdir() if d.is_dir())
    if not directories:
        print(f"error: no skill directories under {SKILLS.relative_to(ROOT)}", file=sys.stderr)
        return 2

    for directory in directories:
        check_skill(directory, findings, seen)

    for markdown in sorted((ROOT / "plugins").rglob("*.md")):
        check_links(markdown, findings)

    if findings:
        print(f"⛔️ {len(findings)} finding(s):\n")
        for finding in findings:
            print(f"  {finding}")
        return 1

    print(f"✅ {len(directories)} skills, all loadable, no duplicate names, links resolve")
    return 0


if __name__ == "__main__":
    sys.exit(main())
