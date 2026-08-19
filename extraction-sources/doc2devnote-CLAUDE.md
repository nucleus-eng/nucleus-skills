# CLAUDE.md — doc2devnote

## What this directory is

`doc2devnote` is a Claude Code skill-based workflow for converting raw research materials into **Nucleus DevNotes** — MyST-formatted, reproducible scientific reports published to the Nucleus DevNotes registry at `devnotes.bnext.bio`.

---

## Three skills — two conversion workflows, plus one upstream step

### `/ingest` — new or unstructured content
Use when a collaborator provides raw materials: a Word doc, a Notion export, or a mixed directory of notebooks, data files, and figures. The output is a **draft** `main.md` that requires human review before publishing.

Skill definition: `.claude/skills/ingest/SKILL.md` — invoke as `/ingest`

### `/migrate` — existing Curvenote/legacy DevNotes
Use when converting a DevNote already written in the old Curvenote format (`main.md` + `curvenote.yml`) into the current MyST schema. Content is preserved verbatim — no rewriting.

Skill definition: `.claude/skills/migrate/SKILL.md` — invoke as `/migrate`

### `/notion-corpus-to-outline` — source material still live in Notion
Use before `/ingest` when there is no export to hand: the material is spread across a live workspace as a page, its comment threads, meeting-note transcripts embedded in other pages, and sibling drafts. The output is a sourced outline, not a manuscript — every claim carries a source tag, and `/ingest` takes it from there.

Skill definition: `.claude/skills/notion-corpus-to-outline/SKILL.md` — invoke as `/notion-corpus-to-outline`

**When in doubt about which to use:** if the source has a `curvenote.yml`, use migrate. If it's a Word doc, Notion export, or folder of notebooks, use ingest. If it's still live in Notion and nobody has exported it, start with notion-corpus-to-outline.

```
live Notion workspace → /notion-corpus-to-outline → sourced outline → /ingest → DevNote
```

---

## Style reference

Always consult `skills/devnote-style-guide.md` as the quality anchor for both workflows. It documents the structure, tone, section order, table formatting, and MyST directive conventions observed across the four canonical migrated DevNotes in `output-devnotes/`.

---

## Input

Place new input materials in a new numbered directory: `input-doc-N/`

Current inputs:
- `input-doc-01/` — contains two demo experiment directories (Nucleus Cytosol Demo, PURExpress Demo) and a source `.docx` draft

**Preprocessing `.docx` files before ingest:**
```bash
pandoc input.docx -o content.md --extract-media=figures/
```
This produces `content.md` and a `figures/` directory. Pass `content.md` to the ingest skill.

---

## Output

Completed DevNotes go in `output-devnotes/`. Each DevNote is a self-contained directory with:
- `main.md` — the primary MyST manuscript
- `myst.yml` — project config
- `experiments/` — analysis notebooks, platemaps, raw data, output figures
- `figures/` — standalone schematics/illustrations
- `banner.webp` — banner image
- `environment.yml` — conda environment spec

The four canonical examples are in `output-devnotes/`:
- `04_ppk/`
- `10-nucleus_cytosol_v05/`
- `11-Base_Cell/`
- `cytosol-lifetime/`

Use these as style references when running ingest.

---

## Key constraints

- The output manuscript file is always `main.md`
- Subdirectory `myst.yml` files should contain `version: 1` only — no competing project definitions
- Never rewrite or reinterpret scientific content during migration — verbatim only
- Human review is always required before a draft from ingest is published
- `collections:` frontmatter placeholders marked `REVIEW: inferred —` need manual triage before publishing
- Prose notation (units, chemical formulae, ion charges, etc.) is linted with Vale — config in `.vale.ini` and `styles/nucleus/`, ported from the `nucleus-docs` repo. Run `vale output-devnotes/[slug]/main.md` before publishing; see "Notation and units" in `skills/devnote-style-guide.md`
