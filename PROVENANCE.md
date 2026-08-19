# Provenance

Where each file in this repo came from. Captured 2026-08-19.

Nothing was deleted at the source. Every file here is a copy. The source
copies are still live and still load in their own repos. Until the refactor
is complete, the source is authoritative.

## Skills

| File here | Copied from | Loads today? |
| --- | --- | --- |
| `skills/ingest/` | `bnext/doc2devnote/.claude/skills/ingest/` | Yes, scoped to doc2devnote |
| `skills/migrate/` | `bnext/doc2devnote/.claude/skills/migrate/` | Yes, scoped to doc2devnote |
| `skills/notion-corpus-to-outline/` | `bnext/doc2devnote/.claude/skills/notion-corpus-to-outline/` | Yes, scoped to doc2devnote |
| `skills/migrate-devnote/` | `bnext/nucleus-eng/2026-CERN-OHL-P/.claude/skills/migrate-devnote/` | Yes, scoped to that repo |
| `skills/_unconverted/build-boms.md` | `bnext/nucleus-eng/nucleus-docs/.claude/skills/build-boms.md` | **No** |
| `skills/_unconverted/lint-docs.md` | `bnext/nucleus-eng/nucleus-docs/.claude/skills/lint-docs.md` | **No** |
| `skills/_unconverted/migrate-content.md` | `bnext/nucleus-eng/nucleus-docs/.claude/skills/migrate-content.md` | **No** |

The three files in `_unconverted/` are flat `.md` files with only a
`description:` field. Claude Code needs `skills/<name>/SKILL.md` with a
`name:` field. These have never loaded, in any session, since they were
written. They are tracked in git in nucleus-docs and are actively
maintained, so the content is current — only the packaging is wrong.

## References

| File here | Copied from |
| --- | --- |
| `references/devnote-style-guide.md` | `bnext/doc2devnote/skills/devnote-style-guide.md` |

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
