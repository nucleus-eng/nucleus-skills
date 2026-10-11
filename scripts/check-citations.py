#!/usr/bin/env python3
"""Every cross-repo line citation in a repo's tracked files carries a pin, or says it has none.

Usage:
    check-citations.py <repo-root> [--repos=nucleus-docs,nucleus-skills,nucleus-eng]

Checks PRESENCE only: a hash within 90 characters of the citation, or once in the file's
preamble. Whether the hash resolves is `check-pins.py`, which needs the other repo checked
out and so cannot block a commit. Also fires on a file that names one of `--repos` and
carries no pin in its preamble, because a claim about another repo's content with no line
number was passing untouched.

THE REF HALF IS REPORT-ONLY, added 2026-10-06. compositional-biology-theory CLAUDE.md
Provenance says a cross-repo claim carries REPO, BRANCH AND HASH; this checker enforced the
hash alone, so three bare hashes landed there on 2026-10-06 and passed. It now also looks for
a labelled ref -- `branch X`, `tag X` or `ref X` -- in the same window, and REPORTS what is
missing without failing. Guard 7's shape: report-only until the count reaches zero.

WHY A REF AND NOT A BRANCH. 9d0f603 was cited three times as being on
docs/devcells-integration-pages and had been amended off that branch the day it was written:
correct in form, false in fact, and unreachable from any ref for 41 days against a 30-day
gc.reflogExpireUnreachable default. What rescued it was a TAG. So the field is whichever ref
contains the commit, and a branch is one kind.

ITS ESCAPE IS `on main`, NOT A BLANKET. `hash unrecorded` earns its blankness because an
unrecoverable read-tree is a real state. A missing ref name never is, so a blanket escape
would become the spelling everyone uses. `on main` is a claim check-pins.py can verify.

PRESENCE, NEVER CONTAINMENT. Whether the named ref actually contains the hash is one
`git merge-base --is-ancestor` and belongs to check-pins.py, which has the other repo. On the
evidence of 2026-10-06 that is the half that finds the real failures: a ref requirement would
have caught three cosmetic cases and sailed past the two where something was nearly lost.

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

# A LABELLED ref, never a bare slashed token: `docs/processes/encapsulate/main.md` is a path
# and would match any shape loose enough to catch `roll/refinement-rulings`. The label is what
# the corpus already writes -- "branch `X` at `hash`" -- so this reads practice, not a new form.
REF  = re.compile(r"\b(?:branch|tag|ref)\s+`[^`\n]+`")
ON_MAIN = re.compile(r"\bon main\b", re.I)

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
    noref, noref_files = [], []
    for rel in tracked_md(root):
        text = open(os.path.join(root, rel), encoding="utf-8", errors="replace").read()
        head = preamble(text)
        file_hash, file_escape = bool(HASH.search(head)), bool(ESCAPE.search(head))
        file_ref = bool(REF.search(head)) or bool(ON_MAIN.search(head))
        if REPO.search(text) and not (file_hash or file_escape):
            bad.append(f"{rel}: names another repo, no pin in preamble")
        elif REPO.search(text) and not (file_ref or file_escape):
            noref_files.append(rel)
        for m in CITE.finditer(text):
            name = m.group(1)
            if in_repo(root, name):
                skipped += 1
                continue
            checked += 1
            window = text[m.end():m.end() + WINDOW]
            if not (REF.search(window) or ON_MAIN.search(window) or file_ref or file_escape):
                noref.append(f"{rel}:{text[:m.start()].count(chr(10)) + 1}: "
                             f"`{name}:{m.group(2)}` names no ref")
            if HASH.search(window):
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
          f"{skipped} in-repo citations skipped (exact path or tracked filename)")
    if noref or noref_files:
        print(f"  report-only: {len(noref)} citation(s) and {len(noref_files)} file(s) "
              f"name no ref beside the hash; blocking when this reaches zero")
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
