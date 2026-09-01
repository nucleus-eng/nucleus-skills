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
| `plugins/nucleus/skills/migrate-devnote/` | `bnext/nucleus-eng/nucleus-devnote-archive-1/.claude/skills/migrate-devnote/` | Yes, scoped to that repo |
| `plugins/nucleus/skills/build-boms/SKILL.md` | `bnext/nucleus-eng/nucleus-docs/.claude/skills/build-boms.md` | **No** |
| `plugins/nucleus/skills/lint-docs/SKILL.md` | `bnext/nucleus-eng/nucleus-docs/.claude/skills/lint-docs.md` | **No** |
| `plugins/nucleus/skills/migrate-content/SKILL.md` | `bnext/nucleus-eng/nucleus-docs/.claude/skills/migrate-content.md` | **No** |
| `plugins/nucleus/skills/verify-dna-constructs/SKILL.md` | `bnext/nucleus-eng/nucleus-docs/CLAUDE.md` (Companion DNA repository, DNA reference checking) | **No** — was never a skill |
| `plugins/nucleus/skills/author-myst-content/SKILL.md` | `bnext/nucleus-eng/nucleus-docs/CLAUDE.md` (Page status, MyST syntax conventions, Overview card dropdowns) | **No** — was never a skill |
| `plugins/nucleus/skills/extract-conditions/` | Written here, 2026-09-01. Sources: a real Notion ELN page and the platemap Yen Yu supplied for the same experiment. Not copied from anywhere. | n/a — new |
| `plugins/nucleus/skills/build-platemap/` | Written here, 2026-09-01. Sources: the platemap tutorial in `nucleus-docs`, behaviour read from `bnext/cdk` `platereader.py`, and a real stacked bench platemap. Not copied from anywhere. | n/a — new |

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
| `extraction-sources/nucleus-docs-CLAUDE.md` | `bnext/nucleus-eng/nucleus-docs/CLAUDE.md` | Holds 3 skills' worth of procedure to extract, and a block that duplicates `lint-docs.md`. **Copied from a working tree on a feature branch, not `main`** — it carries a paragraph `main` does not have, and every line number derived from it is off by six after line 243. Cite section headings, not line numbers. Delete once nucleus-docs#216 lands. |
| `extraction-sources/doc2devnote-CLAUDE.md` | `bnext/doc2devnote/CLAUDE.md` | 83 lines. Two small blocks duplicate `ingest`. |
| `extraction-sources/CERN-MIGRATION-PLAYBOOK.md` | `bnext/nucleus-eng/nucleus-devnote-archive-1/MIGRATION-PLAYBOOK.md` | The human entry point for `migrate-devnote`. Correctly a pointer doc, not a duplicate. Kept as a model for how README-to-skill pointers should read. |

## Not copied

- `moot`, `orchestrator` — third party, not Nucleus.
- `simple-english` — general writing skill, not Nucleus.
- The two `20260819-devcells-context-handoff/skills/` snapshot directories —
  byte-identical copies of skills already represented here.
- `bnext/nucleus-eng/DNA` — has no skills and no CLAUDE.md. Its rules live
  in nucleus-docs and are covered by the `verify-dna-constructs` extraction.
