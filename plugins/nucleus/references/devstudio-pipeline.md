# DevStudio pipeline reference

The DevStudio pipeline converts raw experiment log folders in Google Drive into
published DevNotes on `devnotes.nucleus.engineering`. This file is the single
source of truth for the stage sequence, the handoff objects between stages, and
each stage's preconditions and postconditions. Individual skills cross-reference
this document rather than restating it.

## Stage diagram

```
Log folders (Google Drive, sf-node)
        │  human selects the folders — skill does not decide
        ▼
┌─────────────────────────────────┐
│  devstudio-log-to-devnote-g     │  produces: DevNote(G) + manifest.json
└─────────────────────────────────┘
        │  human TA reviews and comments on the Doc
        ▼
┌─────────────────────────────────┐
│  devstudio-devnote-g-to-devnote-m│  produces: main.md, curvenote.yml, directory structure
└─────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────┐
│  devstudio-assemble-devnote-assets│ downloads: notebooks, platemaps, raw data
└─────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────┐
│  devstudio-submit-to-github     │  opens: branch + draft PR against nucleus-devnote-archive-1
└─────────────────────────────────┘
        │  TA reviews and merges the PR
        ▼
GitHub Action → Curvenote venue → devnotes.nucleus.engineering

[separate track, after DevNote(M) exists:]
┌─────────────────────────────────┐
│  devstudio-devnote-to-docs-g    │  produces: Docs(G) draft Google Doc
└─────────────────────────────────┘
        │  devstudio-docs-g-to-m (not yet built)
        ▼
nucleus-eng/nucleus-docs commit
```

## Leaf skills (no downstream invocations)

These skills are invoked by others but do not themselves invoke pipeline skills:

- `devstudio-read-from-google-drive` — resolves Drive references, reads content or raw bytes
- `devstudio-write-to-google-drive` — creates native Docs or raw files in Drive
- `devstudio-author-myst-content` — MyST authoring conventions for DevNote(M) and Docs(M)
- `devstudio-submit-to-github` — branch + draft PR against the DevNote archive repo
- `devstudio-assemble-devnote-assets` — downloads supporting files into the devnote directory
- `devstudio-devnote-to-docs-g` — transforms DevNote(M) into a Docs(G) draft

## Dependency graph

```
devstudio-log-to-devnote-g
  ├── devstudio-read-from-google-drive
  ├── devstudio-write-to-google-drive
  │     └── devstudio-read-from-google-drive
  ├── devstudio-verify-dna-constructs
  │     └── devstudio-read-from-google-drive
  └── devstudio-author-myst-content

devstudio-devnote-g-to-devnote-m
  ├── devstudio-verify-dna-constructs
  │     └── devstudio-read-from-google-drive
  ├── devstudio-author-myst-content
  └── devstudio-submit-to-github
```

## Stage: Log → DevNote(G)

**Skill**: `devstudio-log-to-devnote-g`

**Preconditions**:
- Human has selected the specific Log folder(s) — skill does not crawl
- Folders are confirmed non-stubs (complete-vs-stub check, see that skill)
- Each selected folder contains a Log Google Doc (identified by role, not filename)

**Produces**:
- A native Google Doc in `san-francisco-node/devnotes/<experiment>/` titled `[DRAFT] ...`
- `manifest.json` alongside the Doc — see schema below
- Schematics pre-placed in `general/` (if present in source)

**Human gate**: TA reviews the Doc and leaves comments; signals "ready" to trigger G→M.

---

## Stage: DevNote(G) → DevNote(M)

**Skill**: `devstudio-devnote-g-to-devnote-m`

**Preconditions**:
- DevNote(G) Google Doc exists in Drive and has been reviewed by a TA
- `manifest.json` present alongside the Doc (or absent, with explicit flag)
- No unresolved `??` markers in the Doc

**Produces**:
```
<devnote-slug>/
├── main.md              — MyST body with +++ abstract, sections, figures as directives
├── curvenote.yml        — standalone (no extends: base.yml), full field set
├── lorem.mjs            — local copy (identical in every devnote)
├── base.yml             — copied verbatim from nucleus-eng/devnote-template
├── environment.yml      — copied verbatim from nucleus-eng/devnote-template
├── experiments/YYYYMMDD-slug/
│   └── (notebooks listed in curvenote.yml toc, commented out pending assembly)
├── figures/             — static PNGs from pandoc extraction
├── plasmids/            — .gb files (if construct not yet in nucleus-eng/DNA)
└── general/             — schematics and non-results figures
```

**Human gate**: `devstudio-assemble-devnote-assets` runs immediately after, then TA reviews the PR.

---

## Stage: Asset assembly

**Skill**: `devstudio-assemble-devnote-assets`

**Preconditions**:
- `main.md` and `curvenote.yml` exist at the devnote path
- `curvenote.yml` has commented-out toc entries with Drive/Colab URLs

**Produces**:
- Notebooks downloaded to `experiments/<slug>/`
- Platemaps and raw instrument data downloaded to `experiments/<slug>/`
- Toc entries in `curvenote.yml` uncommented after each successful download

---

## Stage: GitHub submission

**Skill**: `devstudio-submit-to-github`

**Preconditions**:
- `main.md` and `curvenote.yml` present (minimum for GitHub Action to run)
- `gh auth status` passes
- `nucleus-eng/nucleus-devnote-archive-1` cloned locally

**Produces**:
- Branch `devstudio/<devnote-slug>` in `nucleus-eng/nucleus-devnote-archive-1`
- Draft PR with TA checklist

**Human gate**: TA reviews and merges. GitHub Action fires on merge → Curvenote venue → published.

---

## Handoff object: manifest.json

Written by `devstudio-log-to-devnote-g` alongside the DevNote(G) Doc. Read by
`devstudio-devnote-g-to-devnote-m` to emit correct MyST figure directives, and by
`devstudio-assemble-devnote-assets` to know which files to download. Discarded after
assembly — it is not DevNote content.

```json
{
  "figures": [
    {
      "filename": "figures/image1.png",
      "pattern": "embedded-in-doc | quarto-label | static-png | zarr-viewer",
      "cell_label": "20251212-kinetics",
      "source_notebook": "YYYYMMDD-slug/Analysis.ipynb",
      "platemap": "YYYYMMDD-slug/filename.csv",
      "data_source": "YYYYMMDD-slug/filename.txt",
      "zarr_url": "https://data.nucleus.engineering/path/to/data.zarr",
      "section_context": "Experiment 1 — pOpen-deGFP expression",
      "asset_chain_complete": true,
      "extraction_method": "notebook cell output | pandoc --extract-media",
      "findings": []
    }
  ]
}
```

Field rules:
- `pattern`: one of the four string values above; `quarto-label` requires `cell_label`
- `cell_label`: whatever string the notebook author put after `#| label:` — not reformatted
- `platemap`, `data_source`: filenames, not Drive URLs; `null` if not found
- `zarr_url`: only present when `pattern` is `zarr-viewer`; never fetch content from it during G stage
- `asset_chain_complete`: `false` when no notebook found for an embedded figure, or when
  platemap/raw data cannot be confirmed present
- `findings`: list of non-blocking strings (e.g. duplicate `cell_label` warnings)

---

## Handoff object: figure-provenance line

The human-readable equivalent of `manifest.json`, written by `devstudio-log-to-devnote-g`
into the DevNote(G) Doc body (immediately after the prose each figure belongs to). Used
by `devstudio-devnote-g-to-devnote-m` when the manifest is absent or the Doc was edited
after manifest generation.

**Canonical format** (single line, named fields, backtick-quoted values):
```
[`fig:kinetics-exp1`, notebook:`Analysis.ipynb`, platemap:`20251104-NucleusPURE-deGFP-platemap.csv`, data source:`2025-11-04`, caption: (Translation kinetics of Cytosol and PURExpress reactions using two different pOpen-deGFP DNA preps.)]
```

For zarr microscopy references:
```
[zarr-viewer, source:`https://data.nucleus.engineering/path/to/data.zarr`, caption: (Interactive microscopy viewer.)]
```

For schematics pre-placed in `general/`:
```
[`fig:schematic-overview`, file:`general/schematic-overview.png`, caption: (Schematic overview.)]
```

The G→M skill also handles the older multi-line block format (for DevNote(G)s authored
before this format was standardized):
```
Figure N: [caption text]
Analysis: [notebook filename]
Data: [URL or filename]
Platemap: [filename]
```

---

## Handoff object: curvenote.yml toc comments

Written by `devstudio-devnote-g-to-devnote-m` as commented-out toc entries carrying
Drive/Colab URLs. Read by `devstudio-assemble-devnote-assets` to discover which notebooks
to download and where to place them.

```yaml
toc:
  - file: main.md
  # - file: experiments/YYYYMMDD-slug/Analysis.ipynb  # https://colab.research.google.com/drive/<ID>
  # - file: experiments/YYYYMMDD-slug/notebook.ipynb  # https://drive.google.com/file/d/<ID>/view
```

After `devstudio-assemble-devnote-assets` downloads a notebook, it uncomments the entry:
```yaml
  - file: experiments/YYYYMMDD-slug/Analysis.ipynb
```

---

## Drive scope constraint

All Drive operations in this pipeline are scoped to the `san-francisco-node/` folder in
the DevStudio Shared Drive. Skills never access other Drive locations. This constraint is
declared in each skill's invocation model, not enforced by a technical permission — it is
a convention, not a capability limit.
