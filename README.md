# nucleus-skills

Claude skills for Nucleus work — DevNote authoring, docs-site maintenance,
and the migrations between them.

**Status: Phase 1 done.** All seven skills are now in loadable form. This
repo is not yet the source of truth and nothing consumes it yet — that
needs Phase 0 of `REFACTOR-PLAN.md`, which picks a distribution mechanism.
`PROVENANCE.md` maps every file back to where it came from.

## Why this repo exists

The skills were written in the repos they serve. That was the right call
at the time, but it produced four problems:

1. **Three skills never load.** `build-boms`, `lint-docs`, and
   `migrate-content` in nucleus-docs are flat `.md` files. Claude Code needs
   `skills/<name>/SKILL.md`. They were written and maintained for months and
   read by nothing. *Fixed here in Phase 1; the copies still live in
   nucleus-docs are still broken.*
2. **Content is duplicated across repo boundaries and has drifted.** The
   canonical unit table exists in two copies that now disagree — `nL`, a
   volume unit, is in the Mass row of one of them.
3. **Three skills answer to "migrate this DevNote"**, each producing a
   different artifact, and none of their descriptions says which.
4. **`notion-corpus-to-outline` has forked into two versions** with no
   cross-reference between them.

One repo makes the duplication visible and gives each rule one owner.

## Layout

```
skills/                    one directory per skill, each with SKILL.md
references/                shared material skills load on demand
extraction-sources/        raw input for the refactor; delete when done
```

## Skills

| Skill | Does |
| --- | --- |
| `notion-corpus-to-outline` | Live Notion workspace → sourced outline |
| `ingest` | Raw collaborator material → draft DevNote |
| `migrate` | Local Curvenote DevNote → MyST, verbatim |
| `migrate-devnote` | Published DevNote → recovered, rebuilt, resubmitted |
| `build-boms` | BOM tables and the lab-ready protocol pipeline |
| `lint-docs` | Vale, codespell, lychee, strict MyST build |
| `migrate-content` | DevNote or Notion export → nucleus-docs page |

## How these get used

Not decided yet. A standalone repo does not load anywhere on its own —
Claude Code reads `.claude/skills/` in the project and `~/.claude/skills/`
globally. Phase 0 of `REFACTOR-PLAN.md` picks the distribution mechanism.
Until then, keep editing the copies in the source repos.
