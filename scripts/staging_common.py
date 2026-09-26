#!/usr/bin/env python3
"""What the staging checkers share: the citation and pin patterns, the text normaliser,
the preamble reader, the tracked-file lister, and the sibling-repo finder.

Each of these was defined two or three times across the four checkers, with small drifts
between copies. Change the definition of "a citation", "a hash" or "the preamble" here,
once -- the same argument as nucleus-docs `scripts/bom_common.py`.

Where a checker still keeps a pattern of its own, it says so beside the pattern. The one
case, check-pin-freshness.py's stricter citation and quotation forms, was ruled on
2026-09-21: "keep the stricter form."
"""
import os, re, glob, subprocess

# A cross-repo line citation: `page:12`, `dir/page.md:12`, `script.py:12`. The trailing
# backtick is not required, so `page:12`, `:14` continuation forms still match the first.
CITE   = re.compile(r"`([a-z0-9][a-z0-9\-]*(?:/[a-z0-9\-\._]+)*?(?:\.md|\.py)?):(\d+)")
HASH   = re.compile(r"`([0-9a-f]{7,40})`")
ESCAPE = re.compile(r"hash unrecorded", re.I)
WINDOW = 90            # characters after a citation in which its own hash may sit

def norm(t):
    """Whitespace-collapsed, markup-stripped text, for matching a quotation to a line."""
    return re.sub(r"\s+", " ", re.sub(r"[>*`_]", "", t)).strip()

def sh(*a, cwd=None):
    """(exit code, stdout) -- decoded leniently, because a page name can match a PNG."""
    r = subprocess.run(a, capture_output=True, cwd=cwd)
    return r.returncode, r.stdout.decode("utf-8", "replace")

def preamble(text, section=re.compile(r"^#{1,6} ", re.M)):
    """The text before the first section heading, skipping the file's own title.

    A file-level pin lives here or nowhere: a hash ten thousand words into the body is
    not a pin for a citation in the preamble. Any heading level ends it, because six
    files use `#` for sections with no `##` anywhere.
    """
    first = section.search(text)
    start = first.end() if first else 0
    m = section.search(text, start)
    return text[:m.start()] if m else text

def tracked_md(root):
    """Relative paths of every tracked .md file under root, sorted."""
    return sorted(p for p in sh("git", "ls-files", "*.md", cwd=root)[1].split() if p)

def in_repo(root, name):
    """A citation naming a file this repo holds is not cross-repo. EXACT PATHS ONLY.

    A basename fallback lived here until 2026-09-25 and it swallowed 24 of 62 cross-repo
    citations in compositional-biology-theory: `analyte-atc/spec.md` reduced to `spec.md`,
    which five local files under reference/ answer to. So the guard was blindest exactly
    where it was built to see -- a nucleus-docs module page is what a claim here cites,
    and every one of those pages is called spec.md. It reported "checked 38" and the
    number was true of what it looked at. Jon's ruling 2026-09-25: the fallback goes.

    A bare filename with no directory still resolves, because that form is common and
    unambiguous here -- but against the TRACKED FILE LIST, not against any path that
    happens to end in that name.
    """
    for cand in (name, name + ".md"):
        if os.path.exists(os.path.join(root, cand)):
            return True
    if "/" in name:
        return False
    if root not in _BASENAMES:
        _BASENAMES[root] = {os.path.basename(p) for p in tracked_md(root)}
    return name in _BASENAMES[root] or name + ".md" in _BASENAMES[root]

_BASENAMES = {}

_LOCATED = {}
def locate(name, root, override=None):
    """A sibling repo by name, searched from root's parent and under ~/src, bounded depth.

    Located, never configured: a recorded path goes stale and a search does not. Pass
    `override={name: path}` to point a name at a checkout. Negative results are cached
    too, because most candidate tokens are not repos.
    """
    name = name.split("/")[-1]
    if override and name in override:
        return override[name]
    if name in _LOCATED:
        return _LOCATED[name]
    found = None
    for base in (os.path.dirname(os.path.abspath(root)), os.path.join(os.path.expanduser("~"), "src")):
        for depth in ("", "*/", "*/*/", "*/*/*/"):
            hits = [c for c in glob.glob(os.path.join(base, depth, name)) if os.path.isdir(os.path.join(c, ".git"))]
            if hits:
                found = hits[0]
                break
        if found:
            break
    _LOCATED[name] = found
    return found

def longest_fragment(q):
    """The longest literal run of an elided quotation. `a … b` matches nothing whole."""
    parts = [norm(x) for x in re.split(r"\s*(?:\.\.\.|…|\[…\])\s*", q)]
    return max(parts, key=len) if parts else ""
