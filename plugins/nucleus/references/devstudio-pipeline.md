# DevStudio pipeline reference

The DevStudio pipeline converts raw experiment log folders in Google Drive into
published DevNotes on `devnotes.nucleus.engineering`. This file owns the pipeline's
**topology**: the stage sequence, which skill invokes which, each stage's
preconditions and postconditions, and the human gates between them. Individual
skills cross-reference this document rather than restating it.

It names the handoff objects that pass between stages but does not define their
formats — those sit one layer below, in their own references. See "Handoff
objects" near the end of this file.

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

## Handoff objects — formats live one layer below

This file says which stage produces and consumes each handoff object. It does
**not** give their formats. A wire format changes far more often than the stage
sequence does — the figure-provenance line has already gone from a multi-line
block to a single line — and holding both here meant every format revision
touched the topology document, while the formats themselves had no owner.

| Object | Produced by | Consumed by | Format |
| --- | --- | --- | --- |
| Figure-provenance record — `manifest.json` and its inline Doc line | `devstudio-log-to-devnote-g` | `devstudio-devnote-g-to-devnote-m`, `devstudio-assemble-devnote-assets` | [`devstudio-figure-provenance.md`](devstudio-figure-provenance.md) |
| `curvenote.yml` toc comments | `devstudio-devnote-g-to-devnote-m` | `devstudio-assemble-devnote-assets` | [`devstudio-curvenote-toc.md`](devstudio-curvenote-toc.md) |

The JSON and the inline line are two encodings of one record and are documented
together, deliberately: they must agree about what the record contains, and when
they were documented apart a field ended up in one and not the other.

---


## Drive scope constraint

All Drive operations in this pipeline are scoped to the `san-francisco-node/` folder in
the DevStudio Shared Drive. Skills never access other Drive locations. This constraint is
declared in each skill's invocation model, not enforced by a technical permission — it is
a convention, not a capability limit.
