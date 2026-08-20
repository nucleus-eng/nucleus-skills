# nucleus-skills

Claude skills for Nucleus work — DevNote authoring, docs-site maintenance,
and the migrations between them.

**Status: Phases 0 and 1 done.** All seven skills are in loadable form, and
this repo is now a Claude plugin marketplace that other repos can depend on.
Content refactoring (Phases 2-6) is still open — see `REFACTOR-PLAN.md`.
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
.claude-plugin/
  marketplace.json         the catalog other repos subscribe to
plugins/nucleus/
  .claude-plugin/
    plugin.json            the plugin manifest
  skills/                  one directory per skill, each with SKILL.md
  references/              shared material skills load on demand
extraction-sources/        raw input for the refactor; delete when done
```

One marketplace, one plugin. The plugin is not split by consumer repo
because `references/devnote-style-guide.md` is loaded by `ingest` and
`migrate` and ports its units section from `lint-docs`. Splitting those
across plugins would force either a duplicate copy of that file or a broken
reference, and removing duplicate copies is the reason this repo exists.

An unused skill costs one description line of context. Its body is only
read when the skill is actually invoked.

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
| `verify-dna-constructs` | DNA construct identity claims against `nucleus-eng/DNA` |
| `author-myst-content` | MyST authoring conventions and page status |

## Use it from another repo

Commit this to the consumer repo's `.claude/settings.json`. Claude Code
registers the marketplace and enables the plugin once someone trusts the
project folder. No install step, and nothing is copied into the consumer
repo.

```json
{
  "extraKnownMarketplaces": {
    "nucleus": {
      "source": { "source": "github", "repo": "nucleus-eng/nucleus-skills" }
    }
  },
  "enabledPlugins": {
    "nucleus@nucleus": true
  }
}
```

Updates arrive by pushing here. Consumers pick them up with
`/plugin marketplace update`.

To try it locally before committing anything:

```
/plugin marketplace add nucleus-eng/nucleus-skills
/plugin install nucleus@nucleus
```

Two things to know. Project-scope plugins load only after the workspace
trust dialog is accepted, so the skills are absent on the very first run in
a fresh clone until trust is granted. And plugin skills are namespaced by
plugin name.

## Contributing

Skills live in `plugins/nucleus/skills/<name>/SKILL.md`, and the `name:`
field must match the directory. Anything else does not load — silently.
That is the bug this repo was created to fix, so check it.

Three conventions, taken from `REFACTOR-PLAN.md` Phase 6:

- **Descriptions are triggers, not summaries.** Say when to use the skill
  and what it produces. Name the output format when a sibling skill could
  match the same words.
- **Cross-reference, never restate.** The model to copy is
  `skills/migrate-devnote/references/snags.md`, which points at
  `prepare.md §5` instead of repeating it.
- **If a copy is unavoidable, label it and say what it tracks.**
