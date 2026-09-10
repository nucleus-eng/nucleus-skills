---
name: devstudio-devnote-g-to-devnote-m
description: Transform a reviewed DevNote(G) Google Doc into a MyST-formatted DevNote(M) — producing main.md, curvenote.yml, and the correct directory structure for submission to the Nucleus DevNotes venue. Invoked when a TA signals a DevNote(G) is ready; consumes the figure-provenance manifest produced by devstudio-log-to-devnote-g. This is a staging-namespace (devstudio-) skill — see "Provenance" below before treating it as canonical.
---

# devstudio-devnote-g-to-devnote-m

## Provenance

Staging skill in the `devstudio` namespace. Built against three ground-truth sources:
the DevNote(G) template (Google Doc, `san-francisco-node/devnotes/devnote-template/`),
the DevNote(M) template repo (`nucleus-eng/devnote-template`, `main.md`, `curvenote.yml`,
`base.yml`), and two real G→M transformation examples (`2026-garenne-pH-sensor` and
`calpoly-team-4`). Supersede once a canonical version exists outside the devstudio
namespace.

**Not yet validated end-to-end** — scoped from real artifacts but not yet run against
a complete G→M transformation. First real test will be the cleaned-up pH sensor
DevNote(G) against `2026-garenne-pH-sensor/main.md` as the known target.

## Invocation model

A human TA signals "this DevNote(G) is done" and points Claude at:
1. The DevNote(G) Google Doc (in `san-francisco-node/devnotes/<experiment>/`)
2. The figure-provenance manifest (`manifest.json`) produced by
   `devstudio-log-to-devnote-g` — or absent if the DevNote was authored directly
   at the G stage without going through the log skill

This skill does not decide when a DevNote is ready — that's always a human call.

## Pre-flight checks before transforming anything

Before writing a single line of MyST:

- **Check for unresolved `??` markers** anywhere in the Doc — these must be resolved
  or explicitly flagged before M stage. If found, stop and surface them to the TA
  rather than transforming around them.
- **Check for `# Author's TODO` or TA meta-sections** (review coordination content,
  not DevNote content) — strip these entirely, don't carry them forward.
- **Check for malformed MyST bleeding in from the G stage** — some participants write
  `:::{figure}` syntax directly in the Doc (confirmed in the pH sensor DevNote(G)).
  Detect and repair: options on the same line as the directive opening, missing
  newlines between options, collapsed fences. Don't assume G stage content is clean
  plain text.
- **Confirm the figure-provenance manifest exists or note its absence** — if absent,
  the skill can still proceed but must flag that figure asset chains are unverified.

## Step 1 — extract frontmatter from the Specification table

Read the two-column Specification table and the Authors table at the top of the Doc.
Map fields to `curvenote.yml` and `main.md` frontmatter:

| G field | M destination | Notes |
|---|---|---|
| Title | `curvenote.yml` `title:` AND `main.md` H1 comment | Must match exactly in both places |
| Date | `curvenote.yml` `date:` | Format as `YYYY-MM-DD` |
| License | `curvenote.yml` `license:` | Default `CC-BY-4.0` if blank |
| Author Name | `curvenote.yml` `authors[].name` | One entry per row |
| Author ORCID | `curvenote.yml` `authors[].orcid` | Skip field if blank, add REVIEW flag |
| Author Email | `curvenote.yml` `authors[].email` | Required for venue submission checks |
| Author Institution | `curvenote.yml` `authors[].affiliations[].name` | |

**Keywords**: do NOT copy from the G doc — generate from article content against the
controlled vocabulary at `nucleus-skills/plugins/nucleus/resources/devnote-keywords.md`
(flagged for future build — leave `keywords:` commented out in `curvenote.yml` with a
REVIEW flag until that skill exists).

**UUID**: generate a fresh UUID for `curvenote.yml` `id:` field:
```bash
python3 -c "import uuid; print(uuid.uuid4())"
```
Never reuse an existing id from a prior draft or another DevNote.

## Step 2 — section mapping

Map DevNote(G) sections to DevNote(M) sections. The G template's section names don't
always match published DevNote conventions — transform as follows:

| DevNote(G) section | DevNote(M) section | Action |
|---|---|---|
| `# Overview` | `# Overview` | Direct, verbatim |
| `# Materials and equipment` | `# Methods` / `## Reagents` | Rename; wrap table in `:::{table}` directive |
| `# Design` | `# Design` | Include even if thin; flag if empty |
| `# Protocol` | `## [subsections]` under `# Methods` | Verbatim content; restructure headings |
| `# Results and Observations` | `# Results` | Rename; convert figures and tables to directives |
| `## Notes` or `## Failure modes` | `## Notes` or fold into `# Conclusions` | Preserve participant's heading if it communicates well; flag style inconsistency but don't force rename |
| `# What's next` | `# Conclusions and next steps` | Rename |
| `# Files to include` | Drop as a section | Content informs `curvenote.yml` resources glob; file list itself doesn't appear in `main.md` |
| `# Author's TODO` / TA meta-sections | Strip entirely | Review coordination artifacts, not content |
| Non-template sections (`# Tips and Tricks`, `# Expected behavior`, `# Performance`) | Preserve with flag | Per direct guidance: preserve participant intent, flag style inconsistency for TA review rather than forcing into template sections |

**Section rename flagging convention:**
```
<!-- RENAMED: "Results and Observations" → "Results" -->
```

## Step 3 — table conversion

For the reagents/materials table, wrap in a `:::{table}` directive with label and
center alignment:

```
:::{table} Reagents used in this experiment.
:label: tbl-reagents
:align: center
<!-- vale nucleus.magnitude-unit-spacing = NO -->
| Reagent | Product Name | Manufacturer | Catalog No. | Price | Storage Conditions | Link |
| --- | --- | --- | --- | --- | --- | --- |
| ... |
<!-- vale nucleus.magnitude-unit-spacing = YES -->
:::
```

Always add the Vale suppression comments around reagent tables — catalog numbers like
`810158C-1mg` will trigger the magnitude-unit-spacing rule as false positives.

**Missing columns**: if the G doc's reagent table is missing columns from the
seven-column schema (confirmed: pH sensor doc was missing `Catalog No.` and `Price`),
add the empty columns and flag:
```
<!-- REVIEW: Catalog No. and Price columns not present in source — add for reproducibility -->
```
Never silently drop columns that are present; never silently add data to fill missing
columns.

For the DNA/construct table, check each construct name against `nucleus-eng/DNA` via
`devstudio-verify-dna-constructs` before naming it in the table. If the construct
links to a `.gb` file in the repo, also emit a `{seqviz}` directive proximal to
the table:
```
:::{seqviz} https://github.com/nucleus-eng/DNA/blob/main/reporters/pOpen-deGFP.gb
:height: 600px
:viewer: both
:::
```
The `{seqviz}` directive accepts both local paths (`./plasmids/pOpen-deGFP.gb`) and
GitHub "view file" URLs — use the GitHub URL if the construct is in `nucleus-eng/DNA`,
local path only if a `.gb` file was explicitly included in the DevNote folder.

For protocol reaction tables, wrap in `:::{table}` with a descriptive label — no
Vale suppression needed for these unless they contain catalog-number-like strings.

## Step 4 — figure conversion

For each figure in the Results section, read the provenance fields from the figure
caption in the G doc:

```
Figure N: [caption text]
Analysis: [notebook filename]
Data: [URL or filename]
Platemap: [filename]
Construct: [.gb filename]
```

Then route to the correct MyST pattern:

**Pattern 1 — notebook cell with `#| label:` tag (preferred)**:
The skill opens the referenced notebook and confirms the label tag exists. If found:
```
:::{figure} #<cell_label>
:name: fig-<cell_label>
:align: center
:width: 75%
Caption text.
:::
```
`<cell_label>` is copied verbatim from the manifest's `cell_label` field — no reformatting,
no enforced date-slug pattern. `devstudio-log-to-devnote-g` already checked it for
collisions within its source notebook; this skill trusts that check rather than
re-deriving or renaming the label itself. `:name:` prefixes it with `fig-` only to
namespace it away from the notebook's own anchor, not to impose a naming scheme.

Also add the notebook to `curvenote.yml`'s `toc:` list if not already present.

**Pattern 2 — static PNG**:
If no notebook or no label tag found, use the static PNG path:
```
:::{figure} ./experiments/YYYYMMDD-slug/figure.png
:name: fig-slug
:align: center
:width: 75%
Caption text.
:::
```
Add `<!-- missing notebook -->` if the figure exists but no backing notebook was found.

**Pattern 3 — microscopy Vizarr viewer**:
If the `Data:` field contains a `.zarr` URL from `data.nucleus.engineering`, emit a
Vizarr widget in `main.md`. Note: **no CDK functions handle `.zarr` files** — CDK is
concerned exclusively with `.parquet` files. The zarr URL is only relevant at the MyST
stage where the `{anywidget}` + Vizarr directive streams tiles client-side. The `.parquet`
file (also typically present for microscopy experiments) is what CDK analysis notebooks
load for quantitative analysis — that's the file to confirm present in the asset chain,
not the zarr.

```
:::{anywidget} https://curvenote.github.io/widgets/widgets/vizarr-viewer.js
:class: w-full

{
    "source": "[zarr URL from Data: field]",
    "height": "600px"
}
:::
```

**Asset chain verification**: for each figure, confirm the notebook (if present)
contains a `pr.load_platereader_data(data_file, platemap_file)` or equivalent CDK
loading call. Extract `data_file` and `platemap_file` from that call. If the data URL
resolves and the platemap is present in the Drive folder, `asset_chain_complete: true`.
If either is missing, flag with a REVIEW comment in `main.md`.

**Stripping leading figure numbers from captions**: MyST auto-generates "Figure N:"
from the label — strip any "Figure 1:", "Figure 2:" prefix from the source caption.

**Cross-references in prose**: wherever the Results narrative refers to a figure
(e.g. "Figure 2 shows..."), replace with a `{ref}` cross-reference:
```
({ref}`fig-slug`)
```

**Tab-sets for parallel figures**: when two figures represent Time Series / End Point
pairs from the same experiment, wrap in a tab-set:
```
:::::{tab-set}

::::{tab-item} Time series
:sync: ts-ep-1
:::{figure} #fig-kinetics
...
:::
::::

::::{tab-item} End point
:sync: ts-ep-1
:::{figure} ./experiments/.../endpoint.png
...
:::
::::

:::::
```

## Step 5 — generate curvenote.yml and directory structure

Produce a directory structure matching the DevNote(M) template:
```
<devnote-slug>/
├── main.md
├── curvenote.yml          # extends base.yml
├── base.yml               # copied from nucleus-eng/devnote-template
├── environment.yml        # copied from nucleus-eng/devnote-template
├── experiments/
│   └── YYYYMMDD-slug/
│       ├── analysis.ipynb  # copied from Drive experiment folder
│       ├── [raw data file] # confirmed present via asset chain check
│       └── [platemap.csv]
├── figures/               # static PNGs from pandoc extraction
├── plasmids/              # .gb files from Drive folder or nucleus-eng/DNA
└── general/               # schematics and other non-results figures
```

`curvenote.yml` minimal required fields:
```yaml
version: 1
extends: base.yml
project:
  id: <generated-uuid>
  title: '<title from Specification>'
  date: '<YYYY-MM-DD>'
  authors:
    - name: <name>
      email: <email>
      orcid: <orcid>          # omit if blank
      affiliations:
        - name: <institution>
      corresponding: true      # first author by default
  # keywords:                  # REVIEW: generate from content against controlled vocabulary
  toc:
    - file: main.md
    # - file: experiments/YYYYMMDD-slug/analysis.ipynb  # add if notebook present
  downloads:
    - id: article
      title: Download Article PDF
```

**`base.yml`**: copy verbatim from `nucleus-eng/devnote-template`. Note: `base.yml`
currently references `devnotes.bnext.bio` and `github.com/bnext-bio/nucleus-developer-notes`
— these are correct as of this skill's writing. The migration of the DevNotes repo from
`bnext-bio` to `nucleus-eng` has not yet happened; do not update these URLs until that
migration is confirmed complete.

## Step 6 — hand off to devstudio-submit-to-github

This skill does **not** write directly to `nucleus-eng/nucleus-devnote-archive-1`, and
does not stage to Drive. Once the MyST directory structure is produced, it is handed
off to `devstudio-submit-to-github` (a separate skill, not yet built) which opens a
branch against the archive repo. A TA then reviews and merges the branch — the GitHub
Action fires on merge to `main`, submitting to the Curvenote venue automatically and
publishing to `devnotes.nucleus.engineering`.

## REVIEW flag conventions

Use these consistently so TAs can grep for outstanding items:

- `<!-- REVIEW: [issue] -->` — inline in main.md for content issues
- `# REVIEW: [issue]` — in curvenote.yml for config issues
- `<!-- RENAMED: "[original]" → "[new name]" -->` — section renames
- `<!-- REORDERED: moved from "[original position]" -->` — section moves
- `<!-- missing notebook -->` — figure without a backing notebook
- `<!-- STYLE: non-standard section heading "[name]" — preserved per participant intent -->` — non-template sections

## What this skill does not do

- Does not commit to GitHub — TA-mediated handoff only
- Does not generate keywords — flagged as REVIEW, deferred to a future
  keyword-autogeneration step using the controlled vocabulary at
  `nucleus-skills/plugins/nucleus/resources/devnote-keywords.md`
- Does not decide when a DevNote is ready — human TA call only
- Does not update `base.yml` URLs until the `devnotes.nucleus.engineering` migration
  is confirmed complete — flags with REVIEW instead
- Not yet validated end-to-end against a real transformation pair
