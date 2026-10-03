# nucleus-skills

A Claude plugin marketplace. One marketplace, one plugin, one directory per
skill. `README.md` holds the layout, the conventions and the ownership table.
`REFACTOR-PLAN.md` holds the work still outstanding.

## Staged edits

**Staging is off, from 2026-10-03.** Turned off by Anton, for this repo and
for every session that reads this file. Edit tracked files directly. Do not
write a staging document and do not wait for a reviewer before applying an
edit.

The `staging` skill still exists at
`plugins/nucleus/skills/staging/SKILL.md`. It is kept because `nucleus-docs`
and `category` consume this plugin and still point at it. It is not in force
here.

Two things that rule bought are worth keeping without it:

- **Say what a change overturns.** An edit that silently overwrites a claim
  hides whether the claim had a reason behind it.
- **Line numbers, hashes and dates are claims.** Measure one before writing
  it down. A stale line number points confidently at the wrong place.

The staging documents at the repo root are gitignored and stay where they
are. They are now a record of past reasoning, not a queue.

## Before opening a PR

```bash
python3 scripts/check-skills.py
```

Required on `main`, with "require branches to be up to date" on. It catches
the failure this repo exists to fix: a `SKILL.md` whose `name:` does not match
its directory does not load, and **nothing reports an error**. It never
appears.

## Two conventions worth stating here

**Descriptions are triggers, not summaries.** Name the task that calls for
the skill. Name what the skill produces.

**Cross-reference, never restate.** A copy that cannot be avoided gets a
label. The label says what it tracks.

## A note on `git add -A`

Working documents at the repo root are gitignored, but a new one is untracked
rather than ignored until its name is added. `git add -A` has swept working
files into unrelated commits three times. Prefer explicit paths.
