#!/usr/bin/env python3
"""Report quotations in a repo's staging documents that were true when pinned and are not
true now. Resolves the same quote twice, at the pin and at the tip, and reports where they
differ.

Usage:
    check-pin-freshness.py <repo-root> <staging-glob>     e.g.  . 'tmp/staging/STAGED-*.md'

  STALE   present at the pinned hash, absent at the tip   -> the claim has expired
  CASE    present at the tip but cased differently        -> quote it as written
  GONE    absent at both                                  -> the citation is wrong, not stale
  NOPIN   absent at the tip, no hash to check             -> cannot tell stale from wrong
  fresh   present at the tip                              -> nothing to do

STALE and GONE take opposite responses: re-read and rewrite, against retract. `check-pins.py`
can only ever confirm a pin, because a pin names an immutable tree. Matching is exact after
whitespace normalisation; CASE is its own status rather than a softening. A quote attributed
to a person is a spoken ruling and is skipped; so is a quote inside a retraction, which must
fail to resolve. This resolves against LOCAL sibling checkouts and cannot see whether a
hash is reachable by anyone else -- the staging skill § Provenance states that rule. Exit 1
on STALE or GONE; exit 2 when it read nothing.
History: this header carried the failures behind each rule verbatim until 2026-09-21; read
it at nucleus-skills `af17385`, and the rulings in compositional-biology-theory `rulings.md`
at `e5f3316`.
"""
import re, os, sys, glob, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from staging_common import HASH, norm, sh, locate

if len(sys.argv) != 3 or not os.path.isdir(sys.argv[1]):
    print("NOTHING CHECKED: usage  check-pin-freshness.py <repo-root> <staging-glob>"); sys.exit(2)
ROOT, PATTERN = os.path.abspath(sys.argv[1]), sys.argv[2]
os.chdir(ROOT)

# This tool's citation form requires `.md` and a closing backtick, and its quotation range is
# 15-220 characters; check-pins.py accepts `.py`, no closing backtick, and 12-200. Kept as
# they were; raised as a question to the Editor when this file was trimmed, 2026-09-21.
CITE  = re.compile(r'`([a-z0-9][a-z0-9\-/\._]*\.md):(\d+)`')
QUOTE = re.compile(r'[*_]*"([^"]{15,220})"[*_]*')
SIBLING_NAMES = ('nucleus-docs', 'nucleus-skills', 'devnotes-repo', 'compositional-biology-theory', 'DNA')
SPOKEN = re.compile(r'\b(Jon|Julia|Mary|Anton|Sam|Ojaswita|Charlie|Surendra)\b[^."]{0,40}:\s*[*_]*$')
WITHDRAWN = re.compile(r'does not exist and never did|never did|withdrawn|retracted|'
                       r'quoted my own paraphrase|no longer exists', re.I)

SIBLINGS = ['.'] + [p for p in (locate(n, ROOT) for n in SIBLING_NAMES)
                    if p and os.path.abspath(p) != ROOT]

def owning_repo(path):
    """Which sibling tracks this path at its tip, and under what full path. A short form
    that resolves to exactly one tracked path is accepted; several is not."""
    for root in SIBLINGS:
        if sh('git', 'cat-file', '-e', f'HEAD:{path}', cwd=root)[0] == 0:
            return root, path
        hits = [h for h in sh('git', 'ls-files', f'*/{path}', cwd=root)[1].split() if h.endswith('/' + path)]
        if len(hits) == 1:
            return root, hits[0]
    return None, None

def text_at(root, ref, path):
    rc, out = sh('git', 'show', f'{ref}:{path}', cwd=root)
    return norm(out) if rc == 0 else None

STAGING = sorted(glob.glob(PATTERN))
if not STAGING:
    print(f'NOTHING CHECKED: no files match {PATTERN} under {ROOT}.'); sys.exit(2)

tally, rows = collections.Counter(), []
for sf in STAGING:
    lines = open(sf, encoding='utf-8').read().split('\n')
    for n, raw in enumerate(lines, 1):
        cite = CITE.search(raw)
        if not cite or raw.lstrip().startswith('|'):      # a table row is prose about sites
            continue
        window = ' '.join(lines[n - 1:n + 1])              # the quote sits on this line or the next
        q = QUOTE.search(window)
        if not q:
            continue
        if SPOKEN.search(window[:q.start()]):
            tally['spoken'] += 1; continue
        if WITHDRAWN.search(window):
            tally['withdrawn'] += 1; continue
        path, quote = cite.group(1), norm(q.group(1))
        root, path = owning_repo(path)
        if root is None:
            tally['norepo'] += 1; rows.append(('NOREPO ', sf, n, path, quote[:52], '')); continue
        tip = text_at(root, 'HEAD', path) or ''
        if quote in tip:
            tally['fresh'] += 1; continue
        if quote.lower() in tip.lower():
            tally['case'] += 1; rows.append(('CASE   ', sf, n, path, quote[:52], 'cased differently at tip')); continue
        h = HASH.search(window) or HASH.search(' '.join(lines[max(0, n - 12):n]))
        if not h:
            tally['nopin'] += 1; rows.append(('NOPIN  ', sf, n, path, quote[:52], 'absent at tip, no hash to check')); continue
        pinned = text_at(root, h.group(1), path)
        if pinned is None:
            tally['badhash'] += 1; rows.append(('BADHASH', sf, n, path, quote[:52], h.group(1))); continue
        if quote in pinned:
            tally['stale'] += 1; rows.append(('STALE  ', sf, n, path, quote[:52], f'true at {h.group(1)[:7]}, gone at tip'))
        else:
            tally['gone'] += 1; rows.append(('GONE   ', sf, n, path, quote[:52], f'absent at {h.group(1)[:7]} too'))

for kind, sf, n, path, quote, note in rows:
    print(f'{kind} {os.path.basename(sf)}:{n}  {path}')
    print(f'          "{quote}..."  {note}')
print('\n' + ' | '.join(f'{k} {tally[k]}' for k in
      ('stale', 'gone', 'case', 'badhash', 'nopin', 'norepo', 'spoken', 'withdrawn', 'fresh') if tally[k]))
print('\nfresh is the only status that needs nothing. nopin cannot tell stale from wrong.')
sys.exit(1 if tally['stale'] or tally['gone'] else 0)
