#!/usr/bin/env python3
"""Every cross-repo line citation carries a pin, or says it has none.

Usage:
    check-citations.py <repo-root> [--repos=nucleus-docs,nucleus-skills,nucleus-eng]

Moved to `nucleus-skills` 2026-09-21 from `compositional-biology-theory` `scripts/`, where
it was guard 5. The only change is that the repo names are an argument.

Guard 3 checks that a `#fragment` names an anchor that exists. Nothing checked a
cross-repo *line number*, and on 2026-09-14 that cost three broken citations in
tracked files. The worst had been wrong for five days and passed every commit:
`signature.md` cited `london-cascade:129`, correct when written at
`nucleus-docs` `8508cb3` and pointing at a table header ever since.

A pin is repo, branch and hash (CLAUDE.md § Provenance). This checks only that a
**hash** is present: within 90 characters of the citation, or once in the file's
preamble, which is where a reader looks for one and where the two working
file-level pins sit. It does not check that the
hash resolves — that is `check-pins.py` beside this file, which needs the other repo
checked out and so cannot block a commit. The split is deliberate and matches
guard 2, which checks marker *vocabulary* and never marker accuracy.

THE ESCAPE. A citation may say `hash unrecorded` instead. Some read-trees cannot
be recovered: on 2026-09-14 `review-poset-draft.md`'s could only be *bounded*, by
finding a claim of its own that one tree satisfies and the next refutes. Without
an escape the guard offers only "invent a pin" or "block forever", and inventing
provenance is the failure the pin rule exists to prevent. So a file may record
that its pin is unrecorded, and the guard takes that as an answer. Whether the
bound beside it is any good is a review-time question, not a check's.

THE ESCAPE IS TESTED BEFORE THE FILE-LEVEL HASH, and the order is load-bearing.
The first version tested `file_hash` first, and `review-poset-draft.md` — the
escape's own worked example — passed on it rather than on the escape, because its
preamble names `a70a594` and `0452492` while reasoning about them. That let the
guard accept `0452492`, the pin that was retracted for asserting what it refutes,
and the escape became decorative: deleting "hash unrecorded" changed nothing.
A per-citation hash still wins, because that is a real pin for that citation.
Found by `category-4b` 2026-09-14; Jon: "agree, do this one."

DATED RECORDS ARE NOT EXEMPT, alone among the guards. Guard 1 and guard 3 skip
them because those files are frozen and stay as written. A pin is not part of what
a record asserts — it is how a reader finds what the record read — and Jon ruled
2026-09-14 that "freeze should freeze data, not metadata. we should keep location
and tags and pointers live." So adding a hash to a frozen record strengthens its
claim instead of updating it, and the exemption's argument does not reach here.
"""
import pathlib, re, subprocess, sys

CITE = re.compile(r"`([a-z0-9][a-z0-9\-]*(?:/[a-z0-9\-\._]+)*?(?:\.md|\.py)?):(\d+)")
HASH = re.compile(r"`[0-9a-f]{7,40}`")
ESCAPE = re.compile(r"hash unrecorded", re.I)
WINDOW = 90
SECTION = re.compile(r"^#{1,6} ", re.M)
# The repos whose names trigger the widened check. Passed in, because the list is a
# property of the collaboration and not of this tool: a repo that cites `devnotes-repo`
# needs it in the list, and a hard-coded list is a second declaration that drifts.
# `--repos a,b,c`; the default is the three names this tool was written against, so a
# call with no flag behaves as guard 5 did before 2026-09-21.
DEFAULT_REPOS = "nucleus-docs|nucleus-skills|nucleus-eng"


def header(text):
    """A file-level pin lives in the preamble, before the first section heading.

    A hash *anywhere* in the file will not do. `review-poset-draft.md` is 14,109
    words and mentions a commit in its body; that is not a pin for a citation ten
    thousand words away. The two file-level pins that actually work — the frozen
    class spec's attention block and `free-parameters-are-tuples.md`'s opening
    line — are both in the preamble, which is also the only place a reader looks
    for one.

    The boundary matches any heading level. It read `^## ` until 2026-09-18, and
    six tracked files use `#` for their sections with no `##` anywhere — so for
    those it returned the whole file and a hash in the body counted as a pin,
    which is the failure the paragraph above rules out. Found while pinning files
    for the previous commit; fixing it made nine more files fail. A file's own
    title is a heading too, so the scan starts after the first one.
    """
    first = SECTION.search(text)
    start = first.end() if first else 0
    m = SECTION.search(text, start)
    return text[:m.start()] if m else text


def tracked_md(root):
    out = subprocess.run(["git", "ls-files", "*.md"], cwd=root,
                         capture_output=True, text=True).stdout
    return [root / p for p in out.split() if p]


def in_repo(root, name):
    """A citation naming a file this repo holds is not cross-repo."""
    for cand in (name, name + ".md"):
        if (root / cand).exists():
            return True
        # bare filename, any directory
        if list(root.glob("**/" + pathlib.Path(cand).name)):
            return True
    return False


def main(argv):
    repos = DEFAULT_REPOS
    args = []
    for a in argv[1:]:
        if a.startswith("--repos="):
            repos = "|".join(re.escape(r) for r in a[len("--repos="):].split(",") if r)
        else:
            args.append(a)
    if not repos:
        print("NOTHING CHECKED: --repos= is empty, so the widened check would fire on nothing")
        return 2
    REPO = re.compile(repos)
    root = pathlib.Path(args[0] if args else ".").resolve()
    bad, checked, skipped, escaped = [], 0, 0, 0
    for f in tracked_md(root):
        text = f.read_text(encoding="utf-8", errors="replace")
        head = header(text)
        file_hash = bool(HASH.search(head))
        file_escape = bool(ESCAPE.search(head))
        # Variant A, Jon's ruling 2026-09-18. A file that *names* another repo
        # carries a pin in its preamble, or the escape. Until now the guard saw
        # only `file:line` citations, so a claim about another repo's page
        # content naming no line passed untouched: `draft-issue-224-comment.md`
        # carried four rows of present-tense claims with no repo, branch, hash
        # or read date, and was wrong within 13 days. Presence, never accuracy —
        # guard 2's split. A file that merely mentions a repo answers with the
        # escape, which is the correct answer and not a loophole.
        if REPO.search(text) and not (file_hash or file_escape):
            bad.append(f"{f.relative_to(root)}: names another repo, no pin in preamble")
        for m in CITE.finditer(text):
            name = m.group(1)
            if in_repo(root, name):
                skipped += 1
                continue
            checked += 1
            tail = text[m.end():m.end() + WINDOW]
            if HASH.search(tail):
                continue
            if file_escape:
                escaped += 1
                continue
            if file_hash:
                continue
            line = text[:m.start()].count("\n") + 1
            bad.append(f"{f.relative_to(root)}:{line}: `{name}:{m.group(2)}` has no hash")
    for b in bad:
        print("UNPINNED CITATION", b)
    print(f"checked {checked} cross-repo citations, {escaped} on a declared escape, "
          f"{skipped} in-repo citations skipped")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
