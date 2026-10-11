#!/usr/bin/env python3
"""Flag markdown tables whose rows do not match their header's column count.

Shared by the Nucleus repos, like check-citations.py and check-pins.py beside
it. Takes the roots to check as arguments and defaults to the whole tree, which
is the only default true in every repo:

    python3 scripts/check-table-shape.py                 # everything tracked
    python3 scripts/check-table-shape.py docs/ guides/   # named roots

WHY IT LIVES HERE AND NOT IN ONE REPO. compositional-biology-theory asked for it
on 2026-09-29, after a seven-column row went into a five-column table there and
all six of that repo's guards passed. It was built in nucleus-docs, because that
corpus has the same gap. Two repos needed it before one had it, which is the
test for whether a checker is shared.

WHAT IT CATCHES. A row with the wrong column count renders with a dropped or
shifted cell, so a value reads under the wrong heading or vanishes. The table
still parses and still looks like a table. In a corpus where a table row IS a
record -- a register entry, a composition line, a bill of materials -- that is a
claim quietly changing meaning.

WHAT IT DOES NOT DO. It does not check that a cell holds the right kind of
thing. A repo's own checkers do that for the table kinds that have a contract.
This checks shape only.

ONLY `\\|` IS EXEMPT, AND THAT IS A GFM RULE RATHER THAN A CHOICE. GitHub
Flavored Markdown splits a row into cells BEFORE it parses inline spans, so a
pipe inside backticks is still a cell separator. An earlier version masked
inline code as well, which hid real breakage. Removing that mask changes the
verdict on zero rows in either corpus today -- measured over both trees,
byte-identical output -- so it is a correction with no sweep behind it.
"""
from __future__ import annotations
import re, subprocess, sys
from pathlib import Path

DEFAULT_ROOTS = ["."]
SEP = re.compile(r"^\s*\|?[\s:\-|]+\|[\s:\-|]*$")


def cells(line: str) -> int:
    """Column count of one table row, ignoring pipes that do not separate."""
    # Only an escaped pipe is exempt. GFM splits cells before parsing inline
    # spans, so a pipe inside backticks still separates.
    masked = line.replace(r"\|", "\x00\x00")
    row = masked.strip()
    if row.startswith("|"):
        row = row[1:]
    if row.endswith("|"):
        row = row[:-1]
    return len(row.split("|"))


def check_file(path: Path) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    lines = path.read_text(encoding="utf-8").splitlines()
    header_n = None
    header_line = 0
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if "|" not in stripped:
            header_n = None
            continue
        if SEP.match(stripped) and header_n is None and i >= 2 and "|" in lines[i - 2]:
            header_n = cells(lines[i - 2])
            header_line = i - 1
            continue
        if header_n is None:
            continue
        if SEP.match(stripped):
            continue
        n = cells(line)
        if n != header_n:
            out.append((i, f"row has {n} column(s), header at line {header_line} has {header_n}"))
    return out


def find_files(roots: list[str]) -> list[Path]:
    r = subprocess.run(["git", "ls-files"] + roots, capture_output=True, text=True)
    return sorted(
        Path(p) for p in r.stdout.splitlines()
        if p.endswith(".md") and "generated" not in Path(p).parts
    )


def main() -> int:
    roots = [a for a in sys.argv[1:] if not a.startswith("-")] or DEFAULT_ROOTS
    files = find_files(roots)
    errors = 0
    for f in files:
        if not f.exists():
            continue
        for lineno, msg in check_file(f):
            print(f"{f}:{lineno}  {msg}")
            errors += 1
    if errors:
        print(f"\n❌ {errors} malformed table row(s). A wrong column count drops or shifts a cell.")
        return 1
    print(f"✅ Every table row matches its header. {len(files)} file(s) checked.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
