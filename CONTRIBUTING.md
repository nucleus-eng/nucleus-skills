# Contributing to nucleus-skills

One-page index of every convention that applies here. Each entry is one sentence
pointing to where the full rule lives — not a restatement of it.

## Before you start

Run the validator:
```bash
python3 scripts/check-skills.py
```

Required to pass before any PR can merge. See [`scripts/check-skills.py`](scripts/check-skills.py) for what it checks (name matching, no duplicates, link resolution, manifest validity, invocation references).

## File layout

Skills live in `plugins/nucleus/skills/<name>/SKILL.md`. The `name:` field in the frontmatter must match the directory name exactly — this is the one rule where a mistake is completely silent at runtime. `check-skills.py` enforces it.

## Writing a skill

**Descriptions are triggers, not summaries.** Say when to use the skill and what it produces. Full convention: [`README.md`](README.md) §"Two conventions worth stating here."

**Cross-reference, never restate.** If a copy is unavoidable, label it and say what it tracks. Full convention: [`README.md`](README.md) §"Two conventions worth stating here."

**Reference files hold detail; SKILL.md holds the flow.** Anything that could apply to more than one skill belongs in `plugins/nucleus/references/`, not inline. Model: [`plugins/nucleus/skills/migrate-devnote/SKILL.md`](plugins/nucleus/skills/migrate-devnote/SKILL.md).

## Declaring invocations

If your skill tells Claude to load and follow another skill at a specific step, declare it in the YAML frontmatter with an `invokes:` list:

```yaml
---
name: my-skill
description: ...
invokes:
  - other-skill-name   # step N: what it does here
---
```

At the call site in the skill body, add a blockquote marker:

```markdown
> **INVOKE** `other-skill-name` — one-line description of what it does at this point
```

`check-skills.py` validates that (a) every name in `invokes:` resolves to a real skill and (b) every `invokes:` entry has at least one INVOKE marker in the body and vice versa — both directions.

**`invokes:` is a potential dependency set, not an execution plan.** It declares which skills this skill *may* invoke; it does not mean "always invokes." Conditionality lives in the INVOKE marker's surrounding prose ("if the draft names a specific construct…") — not in a formal qualifier in the YAML. The `# step N: description` comment captures when the invocation fires; keep it current when you reorder steps.

For pipeline context and handoff object schemas, see [`plugins/nucleus/references/devstudio-pipeline.md`](plugins/nucleus/references/devstudio-pipeline.md).

## Staged edits

Edits to tracked files (anything that changes what a file claims) go through a staging document first, not applied directly. Full rule: [`plugins/nucleus/skills/staging/SKILL.md`](plugins/nucleus/skills/staging/SKILL.md). Staging location for this repo: declared in [`README.md`](README.md), not here. Reviewer: Jon.

## Breaking changes

When a handoff object schema changes (e.g. `manifest.json` gains a field, the figure-provenance line format changes), add a `## Breaking changes` section to your SKILL.md — under the Provenance section, above the first step. Only breaking changes belong here: ones where a downstream skill's behavior becomes incorrect without updating it.

## Promoting a staging-namespace skill

Full process: [`PROMOTION.md`](PROMOTION.md). Short version: a skill is ready when `check-skills.py` passes, it cross-references rather than restates, Jon has reviewed via the staging workflow, and its Provenance section says what it supersedes and why.

## git add hygiene

Working documents at the repo root are gitignored, but a new one is untracked (not ignored) until its name is added. `git add -A` has swept working files into unrelated commits before. **Prefer explicit paths.** Full note: [`CLAUDE.md`](CLAUDE.md) §"A note on `git add -A`."
