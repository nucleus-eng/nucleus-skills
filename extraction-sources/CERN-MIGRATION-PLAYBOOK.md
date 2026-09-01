# DevNote migration playbook

How to move a published DevNote into this repo, make it build, and re-submit it.

The full procedure lives in the `migrate-devnote` skill, so that Claude Code
loads it on demand. This page is the human entry point. It does not repeat the
content — follow the links.

Written to support [#21](https://github.com/nucleus-eng/nucleus-devnote-archive-1/issues/21)
(finish the migration programmatically). Every command has been run against the
live site. Sources: PRs [#9](https://github.com/nucleus-eng/nucleus-devnote-archive-1/pull/9),
[#13](https://github.com/nucleus-eng/nucleus-devnote-archive-1/pull/13),
[#16](https://github.com/nucleus-eng/nucleus-devnote-archive-1/pull/16) and
[#20](https://github.com/nucleus-eng/nucleus-devnote-archive-1/pull/20).

> **Licensing gate — read first.** This repo is only for DevNotes released fully
> in the open, under CC-BY or a CERN-OHL-P equivalent. Deciding whether a DevNote
> *may* be included is a **human curation step. Never automate it.** Most
> DevNotes still to migrate come from external contributors at the Chicago and
> London nodes, so this is a live risk, not a formality.

## The pipeline

```
enumerate → curate (human) → recover source → de-bloat → repair config
   → pin the CDK → execute notebooks → validate → draft → merge to main
```

## Two rules that cause the most damage when broken

1. **`curvenote submit` never re-executes a notebook.** It renders the outputs
   already saved in the `.ipynb`. Fixing code without re-running publishes the
   old, broken outputs.
2. **Do not edit collaborator prose.** In `main.md` and notebook markdown cells,
   the only permitted edit is a hyperlink's URL.

## Where the detail lives

| Page | Covers |
|---|---|
| [Overview](./.claude/skills/migrate-devnote/SKILL.md) | The pipeline, the hard rules, the licensing gate |
| [Recover](./.claude/skills/migrate-devnote/references/recover.md) | Enumerate what is published; recover source from a MECA archive |
| [Prepare](./.claude/skills/migrate-devnote/references/prepare.md) | De-bloat the bundle; repair `curvenote.yml`; pin `nucleus-cdk` |
| [Verify and submit](./.claude/skills/migrate-devnote/references/verify-submit.md) | Execute notebooks; validate; submit; update the tracker |
| [Snags](./.claude/skills/migrate-devnote/references/snags.md) | Symptom → cause → fix; what to automate and what not to |

If something breaks and you do not know why, start with **Snags**. Most failures
here have been seen before.

## Related

- [`devnote-migration-status.md`](./devnote-migration-status.md) — which DevNotes
  exist, which are live, and which still need migrating. That file records
  **state**; the skill records **method**.
- Working in Claude Code? The skill loads itself when the task matches, or you
  can invoke it directly with `/migrate-devnote`.
