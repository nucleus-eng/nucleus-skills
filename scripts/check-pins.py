#!/usr/bin/env python3
"""Resolve every pinned cross-repo citation against the repo and tree it names.

Moved to `nucleus-skills` 2026-09-21 from `compositional-biology-theory` `scripts/`. The
only change is that the repo to check is an argument.
Reports drift. Applies nothing. Never blocks a commit.

  resolves   the pinned file exists at that hash and the cited line is in it
  drifted    the quoted text is in that file, but not at the cited line
  gone       the file is not in the tree at that hash, or the line is past its end
  norepo     the named repo, or that hash, is not available on this machine
  unquoted   resolved to a line, but our text quotes nothing to check it against
             -- the line is printed so a reader can eyeball it
  escaped    the file declares `hash unrecorded`; there is nothing to resolve

A GONE IS NOT ALWAYS DRIFT. The match is exact, so a quotation lowercased at its
initial to read inside a sentence -- "the cutoff is..." against the page's "The
cutoff is..." -- reports GONE with the text sitting at the cited line. One
character, and the report is indistinguishable from a real miss. Found
2026-09-17 on reference/membrane-pore/spec.md:127. Quote exactly and restructure
the sentence around the capital; do not soften the matcher, because a loose
matcher turns the valuable half into a proxy.

THIS IS THE VALUABLE HALF AND IT CANNOT BE A GUARD. Guard 5 lives in
scripts/check-citations.py and checks only that a hash is *present*; it runs on
every commit because presence is decidable from this repo alone. Resolving a pin
needs the other repo checked out at the right commit, which a clone may not have,
so it runs on demand and its silence is never evidence. Same split as guard 2,
which checks marker vocabulary and never marker accuracy. Jon's ruling 2026-09-14,
"agree" -- and the name is his too: "check-pins.py is more direct. I prefer it."

WHY `unquoted` IS A STATUS AND NOT A PASS. Most citations in this corpus give a
line number and no quotation. For those, this tool can confirm the line EXISTS and
nothing more -- it cannot confirm the line still says what the claim needs. That is
the exact failure guard 5 was written after: signature.md's london-cascade:129 was
a real line in a real file for five days while pointing at a table header. So an
`unquoted` result is a prompt to go look, never a verdict. CLAUDE.md: "A string
match is not on that list. It is a prompt to go look, never a verdict."

USAGE. `check-pins.py <repo-root>`, `-v` to list what resolved as well as what did not,
or `check-pins.py <repo-root> name=/path` to point a repo name at
a checkout, or `check-pins.py <repo-root> default=/path` to resolve citations whose pin names no
repo -- which answers "would these resolve if I assumed the obvious repo" without
writing that assumption into the corpus.

REPOS ARE LOCATED, NOT CONFIGURED. The named repo is searched for by name under a
few roots, so this cannot go stale the way a recorded path would; pass `name=path`
as an argument to override. Reads the tree on each run -- check-sites.py's shape.
"""
import re, os, sys, subprocess, collections, glob

# The repo to check is the FIRST argument, not the directory this file sits in: since
# 2026-09-21 this tool lives in `nucleus-skills` and runs against any sibling repo.
if len(sys.argv) < 2 or not os.path.isdir(sys.argv[1]):
    print("NOTHING CHECKED: usage  check-pins.py <repo-root> [-v] [name=/path] [default=/path]")
    sys.exit(2)
ROOT = os.path.abspath(sys.argv[1])
os.chdir(ROOT)

CITE   = re.compile(r"`([a-z0-9][a-z0-9\-]*(?:/[a-z0-9\-\._]+)*?(?:\.md|\.py)?):(\d+)")
HASH   = re.compile(r"`([0-9a-f]{7,40})`")
ESCAPE = re.compile(r"hash unrecorded", re.I)
SECTION= re.compile(r"^## ", re.M)
# A candidate repo name, not a verdict: `nucleus-docs`, or the name half of
# `nucleus-eng/nucleus-docs`. Which candidate is real is decided by locate(),
# because "does a repo by this name exist" is decidable and "does this token look
# like a repo" is not -- `membrane-pore/spec` matches every shape rule there is.
REPO   = re.compile(r"`([a-z][a-z0-9\-]*(?:/[a-z][a-z0-9\-]*)?)`")
QUOTE  = re.compile(r'[*_]*"([^"]{12,200})"[*_]*')
# A continuation citation: `\`atc-sensing-cell:108\`, \`:114\`` cites two lines and
# quotes the second. Without this the quote is charged to the first and reported
# as drift.
MORE   = re.compile(r"`:\d+`")
WINDOW = 90
NORM   = lambda t: re.sub(r"\s+", " ", re.sub(r"[>*`_]", "", t)).strip()


def sh(*a):
    """Bytes, decoded leniently. A page name can match a PNG in the other tree."""
    r = subprocess.run(a, capture_output=True)
    return r.returncode, r.stdout.decode("utf-8", "replace")


def header(t):
    m = SECTION.search(t)
    return t[:m.start()] if m else t


def tracked_md():
    return sorted(sh("git", "ls-files", "*.md")[1].split())


def in_repo(name):
    for cand in (name, name + ".md"):
        if os.path.exists(cand) or glob.glob("**/" + os.path.basename(cand), recursive=True):
            return True
    return False


def locate(name, override):
    """Find a sibling repo by name. Bounded depth beats a recorded path.

    Negative results are cached too: most candidate tokens are not repos, and
    this runs against every citation in the corpus.
    """
    name = name.split("/")[-1]
    if name in override:
        return override[name]
    if name in locate.cache:
        return locate.cache[name]
    home, found = os.path.expanduser("~"), None
    for root in (os.path.dirname(os.path.abspath(ROOT)), os.path.join(home, "src")):
        for depth in ("", "*/", "*/*/", "*/*/*/"):
            for c in glob.glob(os.path.join(root, depth, name)):
                if os.path.isdir(os.path.join(c, ".git")):
                    found = c
                    break
            if found:
                break
        if found:
            break
    locate.cache[name] = found
    return found
locate.cache = {}


def which_repo(tail, head, override, lead=""):
    """First candidate token that resolves to a real repo. Tail beats lead beats
    preamble. `lead` is the 90 characters BEFORE the citation, because a pin reads
    naturally as `nucleus-docs` `page:12` at `hash` and scanning only forward
    reported `norepo` on every correctly-written one -- six here, 2026-09-18."""
    for chunk in (tail, lead, head):
        for m in REPO.finditer(chunk):
            tok = m.group(1)
            if tok.endswith((".md", ".py")):
                continue
            hit = locate(tok, override)
            if hit:
                return tok.split("/")[-1], hit
    return None, None


def evidence(after):
    """The block a citation's quotation can live in: the rest of its paragraph,
    plus an immediately following blockquote.

    Reaching further finds quotations belonging to other sentences. `atc-cascade:136`
    is followed by a TABLE, and a 400-character window charged it with a quotation
    from two paragraphs down, reporting `gone` against a citation that is fine.
    Found by hand 2026-09-14, the second false positive of the same kind.
    """
    para, rest = after.split("\n\n", 1) if "\n\n" in after else (after, "")
    nxt = rest.lstrip("\n")
    if nxt.startswith(">"):
        para += "\n" + nxt.split("\n\n", 1)[0]
    return para


def longest_fragment(q):
    """A quotation elided with … matches nothing literally. Probe its longest run.

    Four of this corpus's quotations are elided. Matching the whole string reports
    `gone` for every one of them, which would make the tool cry wolf on exactly the
    careful citations -- the ones that quoted enough to be checkable.
    """
    parts = [NORM(x) for x in re.split(r"\s*(?:\.\.\.|…|\[…\])\s*", q)]
    return max(parts, key=len) if parts else ""


def path_at(repo, h, name):
    """Resolve a page name to a path in that tree. A bare name is a directory."""
    code, out = sh("git", "-C", repo, "ls-tree", "-r", "--name-only", h)
    if code:
        return []
    if name.endswith((".md", ".py")) and "/" in name:
        # A citation gives a tail of the path, not the path: `encapsulate-suv/main.md`
        # is `docs/processes/encapsulate-suv/main.md` in the tree. Take it as written
        # if it is there, else match the suffix.
        exact = [p for p in out.split() if p == name]
        return exact or [p for p in out.split() if p.endswith("/" + name)]
    base = os.path.basename(name)
    hits = [p for p in out.split() if p.endswith((".md", ".py"))
            and (("/%s/" % base) in p or os.path.splitext(os.path.basename(p))[0] == base)]
    # A directory page is `<name>/spec.md` or `<name>/main.md`; prefer those over
    # an incidental file that merely shares the basename.
    return sorted(hits, key=lambda p: (os.path.basename(p) not in ("spec.md", "main.md"), len(p)))


def main(argv):
    override = dict(a.split("=", 1) for a in argv[2:] if "=" in a)
    verbose  = "-v" in argv[2:]
    tally, out = collections.Counter(), []
    for f in tracked_md():
        text = open(f, encoding="utf-8").read()
        head = header(text)
        file_hash = HASH.search(head)
        file_esc  = bool(ESCAPE.search(head))
        for m in CITE.finditer(text):
            name, line = m.group(1), int(m.group(2))
            if in_repo(name):
                continue
            tail = text[m.end():m.end() + WINDOW]
            # The repo is scanned on BOTH sides. A pin reads naturally as
            # `nucleus-docs` `page:12` at `hash` -- repo first -- and scanning only
            # forward made every one of those report `norepo`. Six in this corpus on
            # 2026-09-18, all of them correctly written. The hash still comes from
            # `tail` alone, because a hash BEFORE a citation usually belongs to the
            # previous one and charging it here is how a pin comes to name the wrong
            # tree.
            lead = text[max(0, m.start() - WINDOW):m.start()]
            here = f + ":" + str(text[:m.start()].count("\n") + 1)
            # The escape outranks a file-level hash, exactly as guard 5 does since
            # 2026-09-14: a file that says its pin is unrecorded is taken at its
            # word over a hash that happens to sit in its preamble.
            own = HASH.search(tail)
            if not own and file_esc:
                tally["escaped"] += 1
                continue
            hm = own or file_hash
            if not hm:
                out.append("  NO PIN     %s  `%s:%d`" % (here, name, line))
                tally["nopin"] += 1
                continue
            h = hm.group(1)
            rname, repo = which_repo(tail, head, override, lead)
            if not repo and "default" in override:
                rname, repo = "default", override["default"]
            if not repo:
                # Two different results wearing one word. A pin carries repo,
                # branch and hash (CLAUDE.md § Provenance); one that names no repo
                # is an incomplete pin and a finding. One that names a repo this
                # machine lacks is this tool's limit, and says nothing about it.
                out.append("  NOREPO     %s  `%s:%d` @ %s  (%s)"
                           % (here, name, line, h[:7],
                              "pin names no repo -- incomplete pin" if not rname
                              else "repo `%s` not on this machine" % rname))
                tally["norepo"] += 1
                continue
            if sh("git", "-C", repo, "cat-file", "-e", h + "^{commit}")[0]:
                out.append("  NOREPO     %s  `%s:%d`  (%s has no commit %s)"
                           % (here, name, line, rname, h[:7]))
                tally["norepo"] += 1
                continue
            paths = path_at(repo, h, name)
            if not paths:
                out.append("  GONE       %s  `%s:%d` @ %s  (no such page in that tree)"
                           % (here, name, line, h[:7]))
                tally["gone"] += 1
                continue
            code, blob = sh("git", "-C", repo, "show", "%s:%s" % (h, paths[0]))
            if code:
                out.append("  GONE       %s  `%s:%d` @ %s  (%s not in that tree)"
                           % (here, name, line, h[:7], paths[0]))
                tally["gone"] += 1
                continue
            lines = blob.split("\n")
            if line > len(lines):
                out.append("  GONE       %s  `%s:%d` @ %s  (%s has only %d lines)"
                           % (here, name, line, h[:7], paths[0], len(lines)))
                tally["gone"] += 1
                continue
            target = lines[line - 1]
            # A quotation only belongs to this citation if no other citation sits
            # between them. `\`atc-sensing-cell:108\`, \`:114\`` quotes the SECOND
            # line; attributing it to the first reported a drift that is not there.
            # Verified by hand 2026-09-14 before this guard existed.
            after = evidence(text[m.end():m.end() + 600])
            qm    = QUOTE.search(after)
            if qm and (CITE.search(after[:qm.start()])
                       or MORE.search(after[:qm.start()])):
                qm = None
            if not qm:
                out.append("  UNQUOTED   %s  `%s:%d` @ %s\n               -> %s"
                           % (here, name, line, h[:7], NORM(target)[:96] or "(blank line)"))
                tally["unquoted"] += 1
                continue
            probe = longest_fragment(qm.group(1))[:60]
            if probe in NORM(" ".join(lines[max(0, line - 3):line + 2])):
                tally["resolves"] += 1
                if verbose:
                    out.append("  RESOLVES   %s  `%s:%d` @ %s  \"%s\""
                               % (here, name, line, h[:7], probe[:44]))
                continue
            where = [i + 1 for i, l in enumerate(lines) if probe in NORM(l)]
            if where:
                out.append("  DRIFTED    %s  `%s:%d` @ %s -> %s  \"%s\""
                           % (here, name, line, h[:7], where[:3], probe[:44]))
                tally["drifted"] += 1
            else:
                out.append("  GONE       %s  `%s:%d` @ %s  \"%s\" not in that file"
                           % (here, name, line, h[:7], probe[:44]))
                tally["gone"] += 1
    for o in out:
        print(o)
    order = ("resolves", "drifted", "gone", "unquoted", "norepo", "nopin", "escaped")
    print(" | ".join("%s %d" % (k, tally[k]) for k in order if tally[k]) or "no cross-repo citations")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
