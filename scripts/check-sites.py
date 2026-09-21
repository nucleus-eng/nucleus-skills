#!/usr/bin/env python3
"""Anchor every `| File | Line | Current | Proposed |` row of a repo's staging documents
against its working tree. Reports drift. Applies nothing.

Usage:
    check-sites.py <repo-root> <staging-glob>       e.g.  . 'tmp/STAGED-*.md'

  anchored  Current text found at the cited line          -> row is live
  drifted   found, but elsewhere -> line number is stale, text is good
  gone      not found anywhere   -> row is stale; go look
  described Current is prose about the site, not a quote  -> unanchorable by design
  malformed Current has no text left after normalizing    -> the row cannot be checked
  new       Line reads `new` and the file is absent       -> a proposed file, nothing to anchor
  exists    Line reads `new` and the file is present      -> the proposal is stale, or overwrites

Exit 0 when at least one row was read and none is gone, drifted, missing or colliding.
Exit 1 on drift. Exit 2 when it read no files or no rows: a run over nothing is not a
clean run. Never a CI gate -- the staging location is gitignored and a fresh clone has
nothing here.

The glob is required. Each repo declares its staging location in a README, and a default
here would be a second declaration that drifts. The header must read exactly
`| File | Line | Current | Proposed |`; keep the Current cell to the quoted text alone.
History: this header carried the failures behind each rule verbatim until 2026-09-21; read
it at nucleus-skills `af17385`, and the rulings in compositional-biology-theory `rulings.md`
at `e5f3316`.
"""
import re, os, sys, glob, collections

if len(sys.argv) != 3 or not os.path.isdir(sys.argv[1]):
    print("NOTHING CHECKED: usage  check-sites.py <repo-root> <staging-glob>"); sys.exit(2)
root, pattern = sys.argv[1], sys.argv[2]
os.chdir(root)

HDR  = re.compile(r'^\|\s*File\s*\|\s*Line\s*\|\s*Current\s*\|\s*Proposed\s*\|', re.I)
# Table cells escape pipes; this normaliser also unescapes them, so it is not the shared one.
NORM = lambda t: re.sub(r'\s+', ' ', re.sub(r'[>*`_]', '', t.replace('\\|', '|'))).strip()
SITE_EXT = ('.md', '.py', '.sh', '.yml', '.yaml', '.toml', '.ini')

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
        if not path.endswith(SITE_EXT): continue
        m, cur = re.match(r'^\**:?(\d+)', c[1].strip()), unquote(c[2])
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
        probe = NORM(cur)[:60]           # an empty probe matches every window, hence `malformed`
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
