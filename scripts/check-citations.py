#!/usr/bin/env python3
"""Every cross-repo line citation in a repo's tracked files carries a pin, or says it has none.

Usage:
    check-citations.py <repo-root> [--repos=nucleus-docs,nucleus-skills,nucleus-eng]

Checks PRESENCE only: a hash within 90 characters of the citation, or once in the file's
preamble. Whether the hash resolves is `check-pins.py`, which needs the other repo checked
out and so cannot block a commit. Also fires on a file that names one of `--repos` and
carries no pin in its preamble, because a claim about another repo's content with no line
number was passing untouched.

THE ESCAPE. A file may say `hash unrecorded` instead, for a read-tree that cannot be
recovered; inventing a pin is the failure the rule exists to prevent. The escape is tested
BEFORE the file-level hash, so a preamble that discusses a hash it refutes does not pass on
it. A per-citation hash still wins. Dated records are not exempt: a pin is metadata, not
part of what a record asserts.

Exit 1 on an unpinned citation. Exit 2 when the root is missing or `--repos=` is empty.
History: this header carried the failures behind each rule verbatim until 2026-09-21; read
it at nucleus-skills `af17385`, and the rulings in compositional-biology-theory `rulings.md`
at `e5f3316`.
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from staging_common import CITE, HASH, ESCAPE, WINDOW, preamble, tracked_md, in_repo

DEFAULT_REPOS = "nucleus-docs|nucleus-skills|nucleus-eng"

def main(argv):
    repos, args = DEFAULT_REPOS, []
    for a in argv[1:]:
        if a.startswith("--repos="):
            repos = "|".join(re.escape(r) for r in a[len("--repos="):].split(",") if r)
        else:
            args.append(a)
    if not repos:
        print("NOTHING CHECKED: --repos= is empty, so the widened check would fire on nothing")
        return 2
    REPO = re.compile(repos)
    if not args or not os.path.isdir(args[0]):
        print("NOTHING CHECKED: usage  check-citations.py <repo-root> [--repos=a,b,c]")
        return 2
    root = os.path.abspath(args[0])
    bad, checked, skipped, escaped = [], 0, 0, 0
    for rel in tracked_md(root):
        text = open(os.path.join(root, rel), encoding="utf-8", errors="replace").read()
        head = preamble(text)
        file_hash, file_escape = bool(HASH.search(head)), bool(ESCAPE.search(head))
        if REPO.search(text) and not (file_hash or file_escape):
            bad.append(f"{rel}: names another repo, no pin in preamble")
        for m in CITE.finditer(text):
            name = m.group(1)
            if in_repo(root, name):
                skipped += 1
                continue
            checked += 1
            if HASH.search(text[m.end():m.end() + WINDOW]):
                continue
            if file_escape:
                escaped += 1
                continue
            if file_hash:
                continue
            line = text[:m.start()].count("\n") + 1
            bad.append(f"{rel}:{line}: `{name}:{m.group(2)}` has no hash")
    for b in bad:
        print("UNPINNED CITATION", b)
    print(f"checked {checked} cross-repo citations, {escaped} on a declared escape, "
          f"{skipped} in-repo citations skipped")
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
