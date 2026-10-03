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
┌───────────────────────────────────┐
│  devstudio-log-to-devnote-g       │  produces: main.md, curvenote.yml,
│                                   │  the empty tree, manifest.json
└───────────────────────────────────┘
        │  human reviews the links in main.md
        ▼
┌───────────────────────────────────┐
│  devstudio-assemble-devnote-assets│  downloads: notebooks, platemaps, raw data
└───────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────┐
│  devstudio-submit-to-github       │  opens: branch + draft PR against
│                                   │  devstudio-board
└───────────────────────────────────┘
        │  draft.yml posts a Curvenote preview link to the PR
        ▼
┌───────────────────────────────────┐
│  review cycle, repeated           │
│  a short Doc carries live gaps    │
│  devstudio-devnote-g-to-devnote-m │  folds the answers back into main.md
└───────────────────────────────────┘
        │  zero live admonitions, then a human marks the PR ready
        ▼
TA merges → GitHub Action → Curvenote venue → devnotes.nucleus.engineering

[separate track, after DevNote(M) exists:]
┌─────────────────────────────────┐
│  devstudio-devnote-to-docs-g    │  produces: Docs(G) draft Google Doc
└─────────────────────────────────┘
        │  devstudio-docs-g-to-m (not yet built)
        ▼
nucleus-eng/nucleus-docs commit
```

**The loop is the point.** Before 2026-10-03 this was a straight line through
a Google Doc that held the whole draft. Now `main.md` is written first and
the Doc carries only the gaps still open. Each review cycle closes some of
them. A DevNote is ready when none are left.

**Destination follows provenance.** Content originating in the
DevStudio-Event Google Drive lands in `nucleus-eng/devstudio-board`.
Everything else lands in `nucleus-eng/nucleus-devnote-archive-1`, which stays
the primary archive. Every `devstudio`-namespaced skill takes the first
branch. A general-purpose skill such as `nucleus:migrate-devnote` takes the
second, and must not be swept into a repo-wide rename.

## Leaf skills (no downstream invocations)

These skills are invoked by others but do not themselves invoke pipeline skills:

- `devstudio-read-from-google-drive` — resolves Drive references, reads content or raw bytes
- `devstudio-write-to-google-drive` — creates native Docs or raw files in Drive
- `devstudio-author-myst-content` — MyST authoring conventions for DevNote(M) and Docs(M)
- `devstudio-submit-to-github` — branch + draft PR against `devstudio-board`
- `devstudio-devnote-g-to-devnote-m` — folds a reviewer's answers back into `main.md`
- `devstudio-devnote-to-docs-g` — transforms DevNote(M) into a Docs(G) draft

## Dependency graph

```
devstudio-log-to-devnote-g
  ├── devstudio-read-from-google-drive
  ├── devstudio-verify-dna-constructs
  │     └── devstudio-read-from-google-drive
  └── devstudio-author-myst-content

devstudio-assemble-devnote-assets
  └── devstudio-submit-to-github

devstudio-devnote-g-to-devnote-m
  (invokes nothing)
```

## Stage: Log → main.md

**Skill**: `devstudio-log-to-devnote-g`

**Preconditions**:
- Human has selected the specific Log folder(s) — skill does not crawl
- Folders are confirmed non-stubs (complete-vs-stub check, see that skill)
- Each selected folder contains a Log Google Doc (identified by role, not filename)

**Produces**, in a working copy of `nucleus-eng/devstudio-board` under `devnotes/`:
```
<devnote-slug>/
├── main.md              — MyST body, every gap a live admonition
├── curvenote.yml        — the measured first-cut field set, see that skill's Step 8.5
├── manifest.json        — figure-provenance sidecar, stays beside main.md
├── experiments/         — empty
├── figures/             — empty
├── plasmids/            — empty
└── general/             — schematics pre-placed, if present in source
```

This stage does not open a branch and does not open a pull request.

**Human gate**: a human reviews the links in `main.md`, which fires asset
assembly.

---

## Stage: Asset assembly

**Skill**: `devstudio-assemble-devnote-assets`

**Preconditions**:
- `main.md` exists and carries figure-provenance lines
- A human has reviewed those links
- `curvenote.yml` has commented-out toc entries with Drive or Colab URLs

**Produces**:
- Notebooks downloaded to `experiments/<slug>/`
- Platemaps and raw instrument data downloaded to `experiments/<slug>/`
- Toc entries in `curvenote.yml` uncommented after each successful download

**Hands off** to `devstudio-submit-to-github` once the tree is full.

---

## Stage: GitHub submission

**Skill**: `devstudio-submit-to-github`

**Preconditions**:
- The asset tree is full — the pull request opens after assets land, so that
  the first preview a reviewer reads renders its figures
- `gh auth status` passes
- `nucleus-eng/devstudio-board` cloned locally

**Produces**:
- Branch `devstudio/<devnote-slug>` in `nucleus-eng/devstudio-board`
- Draft PR with TA checklist
- A Curvenote preview link, posted by `draft.yml`. That workflow's
  `on: pull_request` block names no `types:`, so a draft pull request fires
  `opened` in the same way a ready one does.

---

## Stage: review cycle, repeated

**Skill**: `devstudio-devnote-g-to-devnote-m`

**Preconditions**:
- `main.md` carries live admonitions
- A short Doc for this cycle carries a reviewer's replies, matched by each
  admonition's `:name:` label

**Produces**:
- Replies appended inside the admonitions they answer
- Resolved admonitions wrapped in an HTML comment rather than deleted
- Frontmatter assigned once no live gap is left

**Human gate**: a human marks the pull request ready. The TA then reviews and
merges, and the GitHub Action fires on merge to `main`.

---


## Handoff objects — formats live one layer below

This file says which stage produces and consumes each handoff object. It does
**not** give their formats. A wire format changes far more often than the stage
sequence does — the figure-provenance line has already gone from a multi-line
block to a single line — and holding both here meant every format revision
touched the topology document, while the formats themselves had no owner.

| Object | Produced by | Consumed by | Format |
| --- | --- | --- | --- |
| Figure-provenance record — `manifest.json` and its inline line in `main.md` | `devstudio-log-to-devnote-g` | `devstudio-assemble-devnote-assets` | [`devstudio-figure-provenance.md`](devstudio-figure-provenance.md) |
| `curvenote.yml` toc comments | `devstudio-log-to-devnote-g` | `devstudio-assemble-devnote-assets` | [`devstudio-curvenote-toc.md`](devstudio-curvenote-toc.md) |
| Live admonitions in `main.md`, and the short Doc generated from them | `devstudio-log-to-devnote-g` | `devstudio-devnote-g-to-devnote-m` | no reference yet — the Doc generator is not built |

The inline line now lives in `main.md`'s own figure blocks rather than in a
Google Doc body. `main.md` is authoritative over the sidecar when the two
disagree, because `main.md` is what a reviewer edits.

The JSON and the inline line are two encodings of one record and are documented
together, deliberately: they must agree about what the record contains, and when
they were documented apart a field ended up in one and not the other.

---


## Drive scope constraint

All Drive operations in this pipeline are scoped to the `san-francisco-node/` folder in
the DevStudio Shared Drive. Skills never access other Drive locations. This constraint is
declared in each skill's invocation model, not enforced by a technical permission — it is
a convention, not a capability limit.
