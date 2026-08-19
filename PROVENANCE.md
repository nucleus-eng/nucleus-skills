# Provenance

Where each file in this repo came from. Captured 2026-08-19.

Nothing was deleted at the source. Every file here is a copy. The source
copies are still live and still load in their own repos. Until the refactor
is complete, the source is authoritative.

## Skills

| File here | Copied from | Loads today? |
| --- | --- | --- |
| `plugins/nucleus/skills/ingest/` | `bnext/doc2devnote/.claude/skills/ingest/` | Yes, scoped to doc2devnote |
| `plugins/nucleus/skills/migrate/` | `bnext/doc2devnote/.claude/skills/migrate/` | Yes, scoped to doc2devnote |
| `plugins/nucleus/skills/notion-corpus-to-outline/` | `bnext/doc2devnote/.claude/skills/notion-corpus-to-outline/` | Yes, scoped to doc2devnote |
| `plugins/nucleus/skills/migrate-devnote/` | `bnext/nucleus-eng/2026-CERN-OHL-P/.claude/skills/migrate-devnote/` | Yes, scoped to that repo |
| `plugins/nucleus/skills/build-boms/SKILL.md` | `bnext/nucleus-eng/nucleus-docs/.claude/skills/build-boms.md` | **No** |
| `plugins/nucleus/skills/lint-docs/SKILL.md` | `bnext/nucleus-eng/nucleus-docs/.claude/skills/lint-docs.md` | **No** |
| `plugins/nucleus/skills/migrate-content/SKILL.md` | `bnext/nucleus-eng/nucleus-docs/.claude/skills/migrate-content.md` | **No** |

The "Loads today?" column describes the **source** copies, not the copies
here. The three nucleus-docs skills were imported as flat `.md` files with
only a `description:` field, which is why they had never loaded in any
session since they were written. Phase 1 converted the copies in this repo
to `SKILL.md` with a `name:` field. The originals in nucleus-docs are
unchanged and still do not load.

Their bodies are unmodified. Only the frontmatter was rewritten: a `name:`
field added, and `description:` reworded to state when to use the skill
rather than what it covers.

## References

| File here | Copied from |
| --- | --- |
| `plugins/nucleus/references/devnote-style-guide.md` | `bnext/doc2devnote/skills/devnote-style-guide.md` |

Not a skill. A shared quality anchor that `ingest` and `migrate` both load
on demand.

## Extraction sources

Raw material to mine during the refactor. These are not content this repo
owns. Delete them when the extraction is done.

| File here | Copied from | Why it is here |
| --- | --- | --- |
| `extraction-sources/nucleus-docs-CLAUDE.md` | `bnext/nucleus-eng/nucleus-docs/CLAUDE.md` | 424 lines. Holds 3 skills' worth of procedure that must be extracted, and ~130 lines that duplicate `lint-docs.md`. Line numbers in `REFACTOR-PLAN.md` refer to this file. |
| `extraction-sources/doc2devnote-CLAUDE.md` | `bnext/doc2devnote/CLAUDE.md` | 83 lines. Two small blocks duplicate `ingest`. |
| `extraction-sources/notion-corpus-to-outline-global-fork.md` | `~/.claude/skills/notion-corpus-to-outline/SKILL.md` | The other half of a two-way fork. Must be reconciled against `skills/notion-corpus-to-outline/SKILL.md`. |
| `extraction-sources/CERN-MIGRATION-PLAYBOOK.md` | `bnext/nucleus-eng/2026-CERN-OHL-P/MIGRATION-PLAYBOOK.md` | The human entry point for `migrate-devnote`. Correctly a pointer doc, not a duplicate. Kept as a model for how README-to-skill pointers should read. |

## Not copied

- `moot`, `orchestrator` — third party, not Nucleus.
- `simple-english` — general writing skill, not Nucleus.
- The two `20260819-devcells-context-handoff/skills/` snapshot directories —
  byte-identical copies of skills already represented here.
- `bnext/nucleus-eng/DNA` — has no skills and no CLAUDE.md. Its rules live
  in nucleus-docs and are covered by the `verify-dna-constructs` extraction.
