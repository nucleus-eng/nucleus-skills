---
name: migrate
description: Convert an existing Nucleus DevNote from the old Curvenote/mixed format (main.md + curvenote.yml) into the current MyST schema for the internal DevNotes registry, verbatim, with no content rewriting. Output is index.md plus a minimal myst.yml. Use when the source has a curvenote.yml and the destination is the internal registry; use migrate-devnote instead when the DevNote is already published on the Curvenote venue and is being recovered and republished there, and ingest for raw or unstructured materials.
---

# Nucleus DevNote Migration Skill

## Purpose

Convert existing Nucleus DevNotes from their original Curvenote/mixed format into a clean MyST-based publishing format suitable for the Nucleus DevNotes registry. The migration preserves all scientific content verbatim while updating structure, metadata, and configuration to the new schema.

## Input

Each source DevNote is a directory containing:
- `main.md` — primary manuscript file with inline MyST frontmatter
- `curvenote.yml` — project metadata, author info, dates, toc, license
- `experiments/` — subdirectories per experiment, each containing analysis notebooks (.ipynb), platemaps (.csv), raw data (.txt, .xpt), and output figures (.png)
- `figures/` — standalone illustration/schematic figures
- `plasmids/` (optional) — sequence files (.gb, .dna)
- `general/` (optional) — shared resources (plasmid files, reference PDFs)
- `banner.webp` — banner image
- `environment.yml` — conda environment spec
- `lorem.mjs`, `seqviz.mjs` — MyST plugins (site-level, do not migrate)
- `package.json`, `package-lock.json` — npm dependencies (do not migrate)
- `src/` — shared analysis library code (do not migrate unless referenced by notebooks)
- `base.yml` (optional) — shared project defaults that curvenote.yml extends

## Migration rules

### Verbatim content

Copy all technical content verbatim from `main.md`. Do not rewrite, restructure, summarize, or interpret any scientific content. Every sentence, table row, figure directive, tab-set, equation, cross-reference label, and code cell must appear in the output exactly as it appears in the source. Preserve all MyST directives including `:::{figure}`, `:::{table}`, `:::::{tab-set}`, `:::{seqviz}`, and all `:label:`, `:align:`, `:width:`, `:name:`, `:sync:` options.

### Structure

Preserve existing section structure exactly. Do not rename, reorder, merge, or split sections. Heading levels (H1, H2, H3) must match the source. Subsection anchors like `(Results)=` must be carried over.

### Technical data

Copy all data files, figure files, and notebooks into the migrated directory, preserving their relative paths from the source. Files to copy:
- `.ipynb` analysis notebooks
- `.csv` platemaps and data files
- `.xlsx` data files
- `.txt` and `.xpt` raw instrument output files
- `.png`, `.svg` figures
- `.gb`, `.dna` sequence files

Files to skip:
- Any file larger than 10 MB (flag in the migration report)
- `_build/`, `.cache/`, `node_modules/`, `__pycache__/`, `.ipynb_checkpoints/` directories
- `.DS_Store`, `.gitignore`, `.git/`, `.git.disable/`
- `banner.webp` (site-level asset, not required in migrated directory)
- `lorem.mjs`, `seqviz.mjs` (plugins configured at site level)
- `package.json`, `package-lock.json`
- `src/` library code unless explicitly referenced
- `template.yml`, `template-blank.md`, `template-example.md` (scaffolding files)

### Primary file

The migrated DevNote must have `index.md` as its primary file.

- If the source primary file is already markdown (`main.md`): rename it to `index.md` and prepend the new frontmatter block. The body of the file (everything after the closing `---` of the original frontmatter) is copied verbatim.
- If the source is primarily a notebook (`.ipynb`): create a minimal `index.md` that introduces the DevNote and embeds the notebook using `See {embed}`notebook-name.ipynb` for the full analysis.`

## Frontmatter schema

```yaml
---
title: [extracted from existing title/frontmatter]
description: |
  [extracted from existing abstract or first paragraph — verbatim if possible]
date: [extracted from existing metadata or inferred from file dates — flag if uncertain]
authors:
  - name: [extracted or "REVIEW: missing"]
    affiliation: [extracted or "REVIEW: missing"]
    email: [extracted or "REVIEW: missing"]
keywords: [extracted from existing tags/keywords or inferred — flag if inferred]
license: [extracted or default CC-BY-4.0 — flag if uncertain]
thumbnail: [path to most representative figure — flag if uncertain]
collections:
  - [inferred from content — flag if uncertain]
id: dn-[year]-[license-short]-[slugified-title]
---
```

**Field extraction guidance:**
- `title`: from `main.md` frontmatter `title:` field; fall back to `curvenote.yml` `project.title`
- `description`: from `main.md` frontmatter `abstract:` field verbatim; if absent, use first paragraph of body
- `date`: from `curvenote.yml` `project.date`; if absent check `base.yml`; if absent flag with "REVIEW: not found in source" and use file modification date as a hint
- `authors`: from `curvenote.yml` `project.authors`; flatten affiliations array to first affiliation name string
- `keywords`: from `curvenote.yml` `project.keywords`; if absent infer from content and flag
- `license`: from `curvenote.yml` `project.license`; default `CC-BY-4.0` if unset
- `thumbnail`: path to the most representative output figure (e.g., a kinetics plot or the primary result figure); flag as "REVIEW: uncertain" if ambiguous
- `collections`: infer from DevNote content topic; always flag as "REVIEW: inferred — ..."
- `id`: construct as `dn-[4-digit-year]-[license-slug]-[title-slug]` where license slug is `cc-by-4` for CC-BY-4.0

## Flag format

For any field that cannot be confidently extracted from source metadata, use:

```
fieldname: "REVIEW: [reason]"
```

Examples:
- `date: "REVIEW: not found in source metadata, file date 2025-11-13"` 
- `collections: "REVIEW: inferred — Nucleus DevNotes / Cytosol"`
- `thumbnail: "REVIEW: uncertain — multiple candidate figures"`

## Output structure

```
migrated/
└── [devnote-dirname]/
    ├── index.md          # Primary file with new frontmatter + verbatim body
    ├── myst.yml          # Minimal project config with toc
    ├── figures/          # Copied from source
    ├── experiments/      # Copied from source (notebooks, CSVs, PNGs, raw data)
    │   └── [exp-date-name]/
    │       ├── analysis.ipynb
    │       ├── [platemap].csv
    │       ├── [kinetics].png
    │       └── data/
    │           └── [raw instrument files]
    └── plasmids/         # Copied from source (if present)
        ├── *.gb
        └── *.dna
```

### `myst.yml` format

```yaml
version: 1
project:
  title: [title]
  toc:
    - file: index.md
    - file: [notebook path].ipynb  # one entry per notebook in toc order
```

Do NOT include `site:` in subdirectory myst.yml. Do NOT include `project.id`. Do NOT copy the full curvenote.yml structure.

### Integration into a content repo

When copying a migrated DevNote directory into an existing MyST content repo (e.g., `devnotes-cern-2026/`), **strip the subdirectory `myst.yml` to just `version: 1`**:

```yaml
version: 1
```

A subdirectory `myst.yml` with any `project:` content causes MyST to register it as a competing project, producing flat slugs (`/analysis`, `/analysis-1`) instead of folder-prefixed paths (`/ppk/analysis`). The root repo's `myst.yml` controls the TOC for all DevNotes.

### `#fig:` notebook figure references

The `#fig:name` cross-reference syntax (used in `index.md` to embed figures from notebooks) requires notebook output cells to have a matching label. **If the notebooks have unlabeled `display_data` outputs — no `glue` calls and no `label` in cell metadata — all `#fig:` references will render as blank/missing images in the published site.**

Before migrating a DevNote that uses `#fig:` syntax, check whether the notebook outputs are labeled:

```python
import json
nb = json.load(open("analysis.ipynb"))
for i, cell in enumerate(nb["cells"]):
    for o in cell.get("outputs", []):
        print(i, o.get("metadata", {}))
```

If no output has a `label` key in its metadata, the `#fig:` references are broken. Fix options (choose one):

**Option A — Label notebook output cells** (preserves `#fig:` syntax):
Add `label: fig:name` to the output cell's metadata in the notebook JSON. This is the cleanest fix if the notebooks will be re-run.

**Option B — Replace `#fig:` with static PNG references** (simpler, works without re-running notebooks):
Export each figure as a PNG (run notebook locally, save output), commit the PNG, then rewrite the `index.md` figure directive:
```
# Before (broken if unlabeled)
:::{figure} #fig:kinetics-exp1

# After (static file)
:::{figure} ./experiments/20250610-name/kinetics.png
```

**Option C — Add `--execute` to CI build**:
Add `myst build --execute --html` to the deploy workflow and install all notebook dependencies in CI. This is complex and slow; only viable if the computational environment is reproducible.

Option B is the pragmatic default for already-committed DevNotes with no label infrastructure.

## Post-migration QA

Run `vale index.md` (or `main.md`) against the migrated manuscript and fix any flagged notation issues — see "Notation and units" in `references/devnote-style-guide.md`. Since migration is verbatim, pre-existing notation issues in the source are expected; fixing them is a formatting change, not a content rewrite, and is in scope here.

## What to ignore

- `.git/`, `.git.disable/` directories
- `_build/`, `.cache/`, `node_modules/`, `__pycache__/`, `.ipynb_checkpoints/`
- `banner.webp` (site asset)
- `lorem.mjs`, `seqviz.mjs`, `package.json`, `package-lock.json`
- `src/` shared library code (unless a notebook explicitly imports from it and the import path must be preserved)
- `template.yml`, `template-blank.md`, `template-example.md`
- `base.yml` (only read for metadata extraction; do not copy)
- `LICENSE.md`, `README.md` (project-level docs, not part of the DevNote content)
- `.DS_Store`, `.gitignore`
- Files larger than 10 MB (flag in migration report)
- PDF lab notebook entries attached as downloads (flag path; do not copy if >10 MB)
