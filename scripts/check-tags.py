#!/usr/bin/env python3
"""Report review tags in staging documents, by file, addressee and kind.

Issue #32: four of ten recorded failure modes are an agent hand-rolling a tag
extractor and getting the scope subtly wrong, then reading a clean result as
"no tags". A false-clean grep is worse than no grep, because it ends the
question. This is the extractor, written once.

  TAG       `@Name:` at a point in the text -- a mark someone left
  MENTION   `` `@Name` `` backticked, or listed with others -- prose ABOUT the
            convention, not a use of it. Four of twelve strings in the corpus
            this was written against.
  RECORDED  a tag quoted inside a ruling block that answers it

**It cannot tell an answered tag from an unanswered one, and neither can a
human reading the file.** The convention says a tag is cleared by deleting it,
so an undeleted tag is open by definition -- and where that convention is not
kept, nothing in the text distinguishes the two. This tool reports what is
there and says which question it is not answering. See the closing summary.

Usage:
    python3 scripts/check-tags.py <dir> [<dir>...]
    python3 scripts/check-tags.py --names claude,jon,anton <dir>

Exit 0 when it read at least one file and found no TAG rows. Exit 1 when TAG
rows exist. **Exit 2 when it read no files or no candidate strings** -- a run
over nothing is not a clean run, which is the failure this tool exists to stop
and the one its own guard must not repeat.
"""
import re, os, sys, glob, argparse, collections

DEFAULT_NAMES = "claude,jon,anton,editor"

def classify(line, names_re):
    """TAG, MENTION or RECORDED for one line already known to contain a name."""
    if re.search(r'\*\*(RULED|CLEARED)\b', line):
        return "RECORDED"
    # A backticked name is prose about the convention: `@Claude`, `@Jon` or `@Anton`.
    if re.search(rf'`@(?:{names_re})`', line, re.I):
        return "MENTION"
    # `@Name:` or `@Editor(node):` -- a colon after the name is someone addressing someone.
    if re.search(rf'@(?:{names_re})\s*(?:\([a-z]+\))?\s*:', line, re.I):
        return "TAG"
    return "MENTION"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dirs", nargs="*", default=["tmp/staging"])
    ap.add_argument("--names", default=DEFAULT_NAMES,
                    help=f"comma-separated addressees (default: {DEFAULT_NAMES})")
    a = ap.parse_args()
    names_re = "|".join(n.strip() for n in a.names.split(",") if n.strip())
    name_pat = re.compile(rf'@(?:{names_re})\b', re.I)

    files, candidates = 0, 0
    rows = collections.defaultdict(list)
    for d in (a.dirs or ["tmp/staging"]):
        for p in sorted(glob.glob(os.path.join(d, "**", "*.md"), recursive=True)):
            files += 1
            for n, line in enumerate(open(p, errors="replace"), 1):
                if not name_pat.search(line):
                    continue
                candidates += 1
                kind = classify(line, names_re)
                who = name_pat.search(line).group(0)
                rows[kind].append((p, n, who, line.strip()[:78]))

    if files == 0:
        print(f"NOTHING CHECKED: no .md files under {', '.join(a.dirs)}.")
        print("A run over zero files is not a clean run. Name the staging directory.")
        return 2
    if candidates == 0:
        print(f"NOTHING CHECKED: read {files} file(s), found 0 strings matching @({names_re}).")
        print("Either the directory holds no tags, or --names does not cover the")
        print("convention in use here. Both look identical from inside this tool, so")
        print("it refuses to report a clean run rather than guess which.")
        return 2

    for kind in ("TAG", "RECORDED", "MENTION"):
        for p, n, who, text in rows[kind]:
            print(f"{kind:9} {p}:{n}  {who}  {text}")

    print(f"\nread {files} file(s), {candidates} candidate string(s)")
    print(" | ".join(f"{k} {len(rows[k])}" for k in ("TAG", "RECORDED", "MENTION") if rows[k]))
    print("\nTAG is a mark that is still in the text. It is NOT a count of unanswered")
    print("marks: a tag with its answer written beneath it reads identically to one")
    print("nobody has touched. The convention resolves that by deleting a tag when it")
    print("is addressed -- where that is kept, TAG means open; where it is not, this")
    print("number is an upper bound and a human has to read them.")
    return 1 if rows["TAG"] else 0

if __name__ == "__main__":
    sys.exit(main())
