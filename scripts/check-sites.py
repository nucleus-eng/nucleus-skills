#!/usr/bin/env python3
"""Check every `| File | Line | Current | Proposed |` row in a repo's staging documents
against that repo's working tree. Reports drift. Applies nothing.

  anchored  Current text found at the cited line          -> row is live
  drifted   found, but elsewhere -> line number is stale, text is good
  gone      not found anywhere   -> row is stale; go look
  described Current is prose about the site, not a quote  -> unanchorable by design
  malformed Current has no text left after normalizing    -> the row cannot be checked
  new       Line reads `new` and the file is absent       -> a proposed file, nothing to anchor
  exists    Line reads `new` and the file is present      -> the proposal is stale, or overwrites

Usage:
    check-sites.py <repo-root> <staging-glob>

    check-sites.py ~/src/compositional-biology-theory 'tmp/STAGED-*.md'
    check-sites.py ~/src/bnext/nucleus-eng/nucleus-docs 'tmp/staging/STAGED-*.md'

The glob is relative to the repo root and is REQUIRED. Each repo declares its own
staging location in a README (the `staging` skill says where), and a default here
would be a second declaration that drifts from the first. Two copies of this tool
existed for four days, 2026-09-17 to 2026-09-21, and differed in exactly that
constant.

An empty probe matches every window, so without the malformed guard a row whose Current
cell is only markup reports `anchored` against any line number, including one that does
not exist. Found 2026-09-09 by the nucleus-docs session. A probe of one or two characters
is still weak for the same reason; it is reported, not caught.

Two ways to get a clean run that means nothing, both found in practice:

  * **The header must read exactly `| File | Line | Current | Proposed |`.** Any other column
    names and the table is skipped in silence, which reads like no drift.
  * **Keep the `Current` cell to the quoted text alone.** Commentary beside the quote reports
    a false GONE, and a checker that cries wolf gets ignored.

Exit 0 when at least one row was read and none is gone or drifted. Exit 1 on drift.
**Exit 2 when it read no staging files or no rows** -- a run over nothing is not a clean
run. A message a human reads is not a status a pipeline honours. Found 2026-09-19 by the
nucleus-docs session, which had the same shape in its own check-pin-freshness.py.

This is a working-copy check, never a CI gate: the staging location is gitignored, so a
fresh clone has nothing here and a green result would verify nothing.

Merged 2026-09-21 from `compositional-biology-theory` `scripts/check-sites.py` (written
2026-09-14) and `nucleus-docs` `scripts/check-sites.py` (adapted from it 2026-09-17).
"""
import re, os, sys, glob, collections

if len(sys.argv) != 3:
    print(__doc__.split("Usage:")[1].split("The glob")[0].rstrip())
    print("NOTHING CHECKED: need <repo-root> and <staging-glob>")
    sys.exit(2)

root, pattern = sys.argv[1], sys.argv[2]
if not os.path.isdir(root):
    print(f"NOTHING CHECKED: {root} is not a directory"); sys.exit(2)
os.chdir(root)

HDR  = re.compile(r'^\|\s*File\s*\|\s*Line\s*\|\s*Current\s*\|\s*Proposed\s*\|', re.I)
NORM = lambda t: re.sub(r'\s+', ' ', re.sub(r'[>*`_]', '', t.replace('\\|', '|'))).strip()

def unquote(s):
    s = s.strip()
    while len(s) > 1 and s[0] in '`"“*' and s[-1] in '`"”*':
        s = s[1:-1].strip()
    return s

files = sorted(glob.glob(pattern))
if not files:
    print(f'NOTHING CHECKED: no files match {pattern} under {root}')
    print('The staging location is gitignored, so a fresh clone has nothing here and a')
    print('green result would verify nothing. Run this where the staging files live.')
    sys.exit(2)

tally = collections.Counter()
for sf in files:
    out, intable = [], False
    for raw in open(sf, encoding='utf-8'):
        if HDR.match(raw): intable = True; continue
        if not intable: continue
        if not raw.startswith('|'): intable = False; continue
        if set(raw.strip()) <= set('|- :'): continue
        c = [x.strip() for x in re.split(r'(?<!\\)\|', raw.strip().strip('|'))]
        if len(c) < 4: continue
        path = re.sub(r'^\[|\]\(.*$', '', unquote(c[0])).strip('`* ')
        if not path.endswith(('.md', '.py', '.sh', '.yml', '.yaml', '.toml', '.ini')): continue
        m, cur = re.match(r'^\**:?(\d+)', c[1].strip()), unquote(c[2])
        # A row proposing a NEW file writes `new` in the Line cell. It anchors to nothing and
        # is not a miss -- unless the file already exists, in which case the proposal is stale
        # or would overwrite something, and that is reported. Added 2026-09-21 when four such
        # rows in a nucleus-skills staging document reported NO FILE and failed the run.
        if c[1].strip().lower() == 'new':
            if os.path.exists(path):
                out.append(f'  EXISTS    {path}  (proposed as new, but the file is there)'); tally['exists'] += 1
            else:
                tally['new'] += 1
            continue
        if not os.path.exists(path):
            out.append(f'  NO FILE   {path}:{c[1].strip()}'); tally['nofile'] += 1; continue
        if not m or not cur or cur in ('—', '-'):
            tally['skip'] += 1; continue
        n, lines = int(m.group(1)), open(path, encoding='utf-8').read().split('\n')
        probe = NORM(cur)[:60]
        win   = lambda a, b: NORM(' '.join(lines[max(0, a):b]))
        if not probe:
            out.append(f'  MALFORMED {path}:{n}  "{cur[:44]}"'); tally['malformed'] += 1; continue
        if probe in win(n - 4, n + 4):
            tally['anchored'] += 1; continue
        where = [i + 1 for i in range(len(lines)) if probe in win(i - 1, i + 3)]
        if where:
            out.append(f'  DRIFTED   {path}:{n} -> {where[:3]}  "{cur[:44]}"'); tally['drifted'] += 1
        elif re.match(r'^(the|its)\s', cur, re.I):
            out.append(f'  DESCRIBED {path}:{n}  "{cur[:44]}"'); tally['described'] += 1
        else:
            out.append(f'  GONE      {path}:{n}  "{cur[:44]}"'); tally['gone'] += 1
    if out:
        print(os.path.basename(sf)); [print(o) for o in out]; print()

rows = sum(tally.values())
if rows == 0:
    print(f'NOTHING CHECKED: read {len(files)} staging file(s) and found 0 checkable rows.')
    print('A file with no `| File | Line | Current | Proposed |` table contributes nothing,')
    print('and the header must match exactly -- any other column names and the table is')
    print('skipped in silence, which reads like no drift.')
    sys.exit(2)

print(f'read {len(files)} staging file(s), {rows} row(s): ' + ' | '.join(
    f'{k} {tally[k]}' for k in
    ('anchored', 'drifted', 'gone', 'described', 'malformed', 'new', 'exists', 'nofile', 'skip') if tally[k]))
sys.exit(1 if tally['drifted'] or tally['gone'] or tally['nofile'] or tally['exists'] else 0)
