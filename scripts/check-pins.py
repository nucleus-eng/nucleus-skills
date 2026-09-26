#!/usr/bin/env python3
"""Resolve every pinned cross-repo citation in a repo's tracked files against the repo and
tree it names. Reports drift. Applies nothing. Never blocks a commit.

Usage:
    check-pins.py <repo-root> [-v] [name=/path ...] [default=/path]

  resolves   the pinned file exists at that hash and the cited line is in it
  drifted    the quoted text is in that file, but not at the cited line
  gone       the file is not in the tree at that hash, or the line is past its end
  norepo     the named repo, or that hash, is not available on this machine
  unquoted   resolved to a line, but our text quotes nothing to check it against
             -- the line is printed so a reader can eyeball it
  escaped    the file declares `hash unrecorded`; there is nothing to resolve

This is the valuable half of the pin check and it cannot be a guard: it needs the other repo
checked out, which a clone may not have, so it runs on demand and its silence is never
evidence. `unquoted` is a status and not a pass -- the line EXISTS, and nothing more.
Matching is exact, so a quotation lowercased at its initial reports GONE with the text
sitting at the cited line; quote exactly rather than soften the matcher. `-v` lists what
resolved. `name=/path` points a repo name at a checkout; `default=/path` resolves citations
whose pin names no repo, without writing that assumption into the corpus.
History: this header carried the failures behind each rule verbatim until 2026-09-21; read
it at nucleus-skills `af17385`, and the rulings in compositional-biology-theory `rulings.md`
at `e5f3316`.
"""
import re, os, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from staging_common import CITE, HASH, ESCAPE, WINDOW, norm, sh, preamble, tracked_md, in_repo, locate, longest_fragment

if len(sys.argv) < 2 or not os.path.isdir(sys.argv[1]):
    print("NOTHING CHECKED: usage  check-pins.py <repo-root> [-v] [name=/path] [default=/path]")
    sys.exit(2)
ROOT = os.path.abspath(sys.argv[1])

REPO  = re.compile(r"`([a-z][a-z0-9\-]*(?:/[a-z][a-z0-9\-]*)?)`")   # a candidate name; locate() decides
QUOTE = re.compile(r'[*_]*"([^"]{12,200})"[*_]*')
MORE  = re.compile(r"`:\d+`")            # a continuation citation: `page:108`, `:114`

def which_repo(tail, head, override, lead=""):
    """First token that resolves to a real repo. Tail beats lead beats preamble; the lead is
    scanned because a pin reads naturally as `repo` `page:12` at `hash`."""
    for chunk in (tail, lead, head):
        for m in REPO.finditer(chunk):
            tok = m.group(1)
            if tok.endswith((".md", ".py")):
                continue
            hit = locate(tok, ROOT, override)
            if hit:
                return tok.split("/")[-1], hit
    return None, None

def evidence(after):
    """The rest of the citation's paragraph plus an immediately following blockquote. A
    wider window charges a citation with a quotation from two paragraphs down."""
    para, rest = after.split("\n\n", 1) if "\n\n" in after else (after, "")
    nxt = rest.lstrip("\n")
    if nxt.startswith(">"):
        para += "\n" + nxt.split("\n\n", 1)[0]
    return para

def path_at(repo, h, name):
    """A page name to a path in that tree. A bare name is a directory; prefer its spec.md or main.md."""
    code, out = sh("git", "-C", repo, "ls-tree", "-r", "--name-only", h)
    if code:
        return []
    if name.endswith((".md", ".py")) and "/" in name:
        exact = [p for p in out.split() if p == name]
        return exact or [p for p in out.split() if p.endswith("/" + name)]
    base = os.path.basename(name)
    hits = [p for p in out.split() if p.endswith((".md", ".py"))
            and (("/%s/" % base) in p or os.path.splitext(os.path.basename(p))[0] == base)]
    return sorted(hits, key=lambda p: (os.path.basename(p) not in ("spec.md", "main.md"), len(p)))

def main(argv):
    override = dict(a.split("=", 1) for a in argv[2:] if "=" in a)
    verbose  = "-v" in argv[2:]
    tally, out = collections.Counter(), []
    for f in tracked_md(ROOT):
        text = open(os.path.join(ROOT, f), encoding="utf-8").read()
        head = preamble(text)          # any heading level ends it, as in check-citations.py; Jon 2026-09-21
        file_hash, file_esc = HASH.search(head), bool(ESCAPE.search(head))
        for m in CITE.finditer(text):
            name, line = m.group(1), int(m.group(2))
            if in_repo(ROOT, name):
                continue
            tail = text[m.end():m.end() + WINDOW]
            lead = text[max(0, m.start() - WINDOW):m.start()]
            here = f + ":" + str(text[:m.start()].count("\n") + 1)
            own = HASH.search(tail)            # the hash comes from the tail alone; one before
            if not own and file_esc:           # a citation usually belongs to the previous one
                tally["escaped"] += 1
                continue
            hm = own or file_hash
            if not hm:
                out.append("  NO PIN     %s  `%s:%d`" % (here, name, line)); tally["nopin"] += 1
                continue
            h = hm.group(1)
            rname, repo = which_repo(tail, head, override, lead)
            if not repo and "default" in override:
                rname, repo = "default", override["default"]
            if not repo:
                out.append("  NOREPO     %s  `%s:%d` @ %s  (%s)"
                           % (here, name, line, h[:7],
                              "pin names no repo -- incomplete pin" if not rname
                              else "repo `%s` not on this machine" % rname))
                tally["norepo"] += 1
                continue
            if sh("git", "-C", repo, "cat-file", "-e", h + "^{commit}")[0]:
                out.append("  NOREPO     %s  `%s:%d`  (%s has no commit %s)" % (here, name, line, rname, h[:7]))
                tally["norepo"] += 1
                continue
            paths = path_at(repo, h, name)
            if not paths:
                out.append("  GONE       %s  `%s:%d` @ %s  (no such page in that tree)" % (here, name, line, h[:7]))
                tally["gone"] += 1
                continue
            code, blob = sh("git", "-C", repo, "show", "%s:%s" % (h, paths[0]))
            if code:
                out.append("  GONE       %s  `%s:%d` @ %s  (%s not in that tree)" % (here, name, line, h[:7], paths[0]))
                tally["gone"] += 1
                continue
            lines = blob.split("\n")
            if line > len(lines):
                out.append("  GONE       %s  `%s:%d` @ %s  (%s has only %d lines)" % (here, name, line, h[:7], paths[0], len(lines)))
                tally["gone"] += 1
                continue
            target = lines[line - 1]
            after = evidence(text[m.end():m.end() + 600])
            qm = QUOTE.search(after)
            if qm and (CITE.search(after[:qm.start()]) or MORE.search(after[:qm.start()])):
                qm = None                      # the quotation belongs to a later citation
            if not qm:
                out.append("  UNQUOTED   %s  `%s:%d` @ %s\n               -> %s"
                           % (here, name, line, h[:7], norm(target)[:96] or "(blank line)"))
                tally["unquoted"] += 1
                continue
            probe = longest_fragment(qm.group(1))[:60]
            if probe in norm(" ".join(lines[max(0, line - 3):line + 2])):
                tally["resolves"] += 1
                if verbose:
                    out.append("  RESOLVES   %s  `%s:%d` @ %s  \"%s\"" % (here, name, line, h[:7], probe[:44]))
                continue
            where = [i + 1 for i, l in enumerate(lines) if probe in norm(l)]
            if where:
                out.append("  DRIFTED    %s  `%s:%d` @ %s -> %s  \"%s\"" % (here, name, line, h[:7], where[:3], probe[:44]))
                tally["drifted"] += 1
            else:
                out.append("  GONE       %s  `%s:%d` @ %s  \"%s\" not in that file" % (here, name, line, h[:7], probe[:44]))
                tally["gone"] += 1
    for o in out:
        print(o)
    order = ("resolves", "drifted", "gone", "unquoted", "norepo", "nopin", "escaped")
    print(" | ".join("%s %d" % (k, tally[k]) for k in order if tally[k]) or "no cross-repo citations")
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
