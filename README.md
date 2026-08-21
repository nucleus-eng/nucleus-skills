# nucleus-skills

Claude skills for Nucleus work — DevNote authoring, docs-site maintenance,
and the migrations between them.

**Status: Phases 0-4 and 6 done.** Every skill here is in loadable form, and
this repo is a Claude plugin marketplace that other repos can depend on.
What remains is Phase 5 — removing the now-duplicated copies from the source
repos — plus a content review of the skills themselves, which has never been
done. See `REFACTOR-PLAN.md`. `PROVENANCE.md` maps every file back to where it
came from.

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

Four conventions, taken from `REFACTOR-PLAN.md` Phase 6:

- **Descriptions are triggers, not summaries.** Say when to use the skill
  and what it produces. Name the output format when a sibling skill could
  match the same words.
- **Cross-reference, never restate.** The model to copy is
  `skills/migrate-devnote/references/snags.md`, which points at
  `prepare.md §5` instead of repeating it.
- **If a copy is unavoidable, label it and say what it tracks.**
  `references/devnote-style-guide.md` does this: it says it is a port and
  asks to be kept in sync. That is the minimum bar.
- **Reference files hold detail; SKILL.md holds the flow.** `migrate-devnote`
  is the model — a short index over four reference files, loaded on demand.

## One owner per domain

This table is the contract. Content that restates another row's domain is a
bug, not untidiness. That is how the unit table came to exist twice and
disagree with itself.

| Domain | Owner |
| --- | --- |
| Live Notion → sourced outline | `notion-corpus-to-outline` |
| Raw material → draft DevNote | `ingest` |
| Curvenote DevNote → MyST registry | `migrate` |
| Published DevNote → CERN repo republish | `migrate-devnote` |
| DevNote or Notion export → nucleus-docs page | `migrate-content` |
| BOM tables, protocol PDFs, generated artifacts | `build-boms` |
| Vale, codespell, lychee, strict build | `lint-docs` |
| DNA construct identity claims | `verify-dna-constructs` |
| MyST authoring conventions, page status | `author-myst-content` |
| Prose style, notation, units | `references/devnote-style-guide.md` (a reference, not a skill) |

## Checks

```bash
python3 scripts/check-skills.py
```

Runs on every push and pull request (`.github/workflows/check-skills.yml`).
It confirms that the marketplace and plugin manifests parse and agree, that
every skill directory holds a `SKILL.md` whose `name:` matches the directory,
that no two skills claim the same name, that every skill has a
`description:`, that relative links in `plugins/` resolve, and that no stray
`skills/` directory survives at the repo root.

It is a required status check on `main`, with "require branches to be up to
date" on. That second setting matters: a PR can pass on its own branch and
still break `main` if `main` moved under it, which is exactly how two skills
came to sit at a path that ships in no plugin.

The first of those is the one that matters. A skill whose `name:` is wrong
or missing does not load, and nothing anywhere reports an error — it simply
never appears. Three skills failed that way in nucleus-docs for months.

Not yet automated: Vale over the skill files themselves. They state unit
conventions they do not currently obey.
