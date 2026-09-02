# nucleus-skills

A Claude plugin marketplace. One marketplace, one plugin, one directory per
skill. `README.md` holds the layout, the conventions and the ownership table;
`REFACTOR-PLAN.md` holds the work still outstanding.

## Staged edits

**This repo stages.** The rule is the `staging` skill in this repo —
`plugins/nucleus/skills/staging/SKILL.md`. Read it there; it is not restated
here, because a second copy is how the two copies it replaced came to
disagree.

Local specifics only:

- **Working documents live at the repo root**, named `<TOPIC>-STAGING.md`, and
  are gitignored. This differs from `tmp/STAGED-<date>-<topic>.md` used in
  `nucleus-docs` and `category`. **Unreconciled** — see
  `STAGING-SKILL-PLAN.md` step C.
- **Scope is the work, not the repository.** A session working here and in
  `nucleus-docs` stages in both.
- **Reviewer:** Jon.

## Before opening a PR

```bash
python3 scripts/check-skills.py
```

Required on `main`, with "require branches to be up to date" on. It catches
the failure this repo exists to fix: a `SKILL.md` whose `name:` does not match
its directory does not load, and **nothing reports an error** — it simply
never appears.

## Two conventions worth stating here

**Descriptions are triggers, not summaries.** Say when to use the skill and
what it produces.

**Cross-reference, never restate.** If a copy is unavoidable, label it and say
what it tracks.

## A note on `git add -A`

Working documents at the repo root are gitignored, but a new one is untracked
rather than ignored until its name is added. `git add -A` has swept working
files into unrelated commits three times. Prefer explicit paths.
