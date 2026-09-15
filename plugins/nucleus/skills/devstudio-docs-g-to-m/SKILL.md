---
name: devstudio-docs-g-to-m
description: Convert a reviewed Docs(G) draft Google Doc into a committed MyST page in nucleus-eng/nucleus-docs — creating the module directory, spec.md, updating the myst.yml TOC and modules-main.md index, running QA checks, and opening a draft PR. The upstream skill (devstudio-devnote-to-docs-g) produces the Docs(G); this skill closes the loop into the docs repo. Scoped to the devstudio namespace.
---

# devstudio-docs-g-to-m

## Provenance

Staging skill in the `devstudio` namespace. Downstream of `devstudio-devnote-to-docs-g`
in the DevStudio pipeline. Produces a draft PR against `nucleus-eng/nucleus-docs` `main`.

The output is a real commit intended for review and merge — not ephemeral. Run all QA
checks before opening the PR.

## Invocation model

```
devstudio-docs-g-to-m
Docs(G): https://docs.google.com/document/d/<id>/edit
Module: pOpen-deGFP
Category: Reporter
Directory: reporter-degfp
nucleus-docs path: /path/to/nucleus-eng/nucleus-docs
```

**Docs(G)** — the reviewed Google Doc URL produced by `devstudio-devnote-to-docs-g`.
**Module** — short display name (used in page title and credits).
**Category** — determines which template applies (see Template selection in
`devstudio-devnote-to-docs-g`). Must match the existing title format in nucleus-docs.
**Directory** — the `docs/modules/<directory>/` directory name. Follow the convention
in nucleus-docs: `<category-slug>-<module-slug>`, both lowercase and hyphenated
(e.g. `reporter-degfp`, `energy-ppk`, `detector-laci_iptg`). Do not derive this
automatically — the name must be confirmed by the invoker, since it becomes a permanent
URL.
**nucleus-docs path** — local clone of `nucleus-eng/nucleus-docs`. All file writes and
QA checks run against this clone. Default: `~/src/bnext/nucleus-eng/nucleus-docs`.

## What this skill reads

From the Docs(G):
- Export the document as HTML using the Drive connector:
  `download_file_content(fileId, exportMimeType="text/html")`
- Parse each section by its heading. All `[PLEASE FILL IN]` flags and `TODO:` markers
  that remain in the reviewed doc carry forward to the MyST as `TODO:` comments — the
  reviewer is responsible for filling them before the PR merges.

From `nucleus-docs`:
- `myst.yml` — to insert the new TOC entry
- `docs/modules/modules-main.md` — to insert the new index row

## What this skill produces

1. `docs/modules/<directory>/spec.md` — the MyST page (new file)
2. Updated `myst.yml` — one new TOC entry under the modules section
3. Updated `docs/modules/modules-main.md` — one new table row
4. A draft PR against `nucleus-eng/nucleus-docs` `main`

No images are committed. All figure references use placeholder filenames; the PR
description names which notebook each figure must be exported from.

## MyST conversion rules

Apply these rules when converting Docs(G) HTML to MyST. Do not hard-wrap prose — write
all paragraph text as a single unbroken line regardless of length (nucleus-docs
`check-formatting.py` enforces this).

### Frontmatter

```yaml
---
title: "Category: Module Name"
subtitle: "Module Specification"
status: draft
thumbnail: schematic.png
site:
    hide-toc: true
    numbered_references: false
---
```

`status: draft` — always for a new page. Remove the `thumbnail:` line only if no
schematic image is available at merge time.

### Overview

One paragraph from the Docs(G) Overview section. If the Docs(G) flags a
cytosol-centric Overview, that text is still a starting point — carry the flag forward
as a MyST comment so the reviewer sees it:

```myst
<!-- TODO: Overview is cytosol-centric — rewrite to describe the module's function
before publishing. Starting text below. -->
```

Then the paragraph text on the next line (no hard wrap).

Add the draft attention banner immediately after the paragraph:

```myst
:::{attention} 🚧 Draft
This page is a work in progress and not yet ready for use.
:::
```

For the schematic figure placeholder:

```myst
:::{figure} schematic.png
:name: fig-schematic
:align: center
:width: 75%

TODO: One sentence describing what the schematic shows.
:::
```

If no schematic exists yet, omit the `:::{figure}` block entirely and add a comment:
`<!-- TODO: Add schematic.png before publishing. -->`

### Reference Composition

Tab-set with three tabs in order: Module Dependencies → DNA → Cytosol.
Use the five-colon fence for the outer tab-set, four-colon for each tab-item, and
three-colon for directives inside:

```myst
:::::{tab-set}

::::{tab-item} Module Dependencies
<!-- gen:composition-diagram -->
<!-- /gen:composition-diagram -->
::::

::::{tab-item} DNA
:::{table}
| **Name** | **Length (bp)** | **File** |
| --- | --- | --- |
| `pConstruct-Name` | 2812 | [filename.gbk](https://github.com/nucleus-eng/DNA/blob/main/…) |
:::
::::

::::{tab-item} Cytosol
:::{table} TODO: table caption
:label: comp-<directory>-cytosol

| Component | Stock Concentration | Final Concentration | − condition (µL) | + condition (µL) |
| --- | --- | --- | --- | --- |
| TODO | TODO | TODO | TODO | TODO |
| **Total** | | | **TODO** | **TODO** |
:::
::::

:::::
```

**DNA tab rules:**
- `name` must be code-formatted with backticks
- `Length (bp)` is the value fetched from the LOCUS line (from the Docs(G)); if the
  Docs(G) carried a LOCUS name mismatch warning, forward it as a MyST comment on the
  row: `<!-- TODO: LOCUS name in .gbk is X, not Y — verify before publishing. -->`
- File links to nucleus-eng/DNA using the blob URL

**Cytosol tab rules:**
- Table label must be `comp-<directory>-cytosol` (required by `check-bom-labels.py`)
- Copy column structure from the Docs(G) verbatim; strip MyST directives that were
  flattened for the Google Doc
- If the DevNote has been published with a DOI, replace the inline table with:
  `![](xref:<devnote-key>#rc)` — where `<devnote-key>` is the key declared in
  `myst.yml`'s `references:` map. Add the key to `myst.yml` references if not present.
  Leave the inline table if no DOI exists yet.

### Expected Behavior

```myst
# Expected Behavior

## Cytosols

<narrative paragraph(s) from Docs(G) — no hard wrap>

:::::{tab-set}

::::{tab-item} Kinetics
:::{figure} cytosol-kinetics.png
<caption from Docs(G) figure placeholder>. Data in [DevNote](https://doi.org/TODO).
:::
::::

::::{tab-item} Endpoint
:::{figure} cytosol-endpoint.png
<caption>. Data from [DevNote](https://doi.org/TODO).
:::
::::

:::::

## Cells

<narrative from Docs(G), if present>

:::::{tab-set}

::::{tab-item} Image 1
:::{figure} cell-image1.png
<caption>
:::
::::

:::::
```

**Figure rules:**
- Filename is a placeholder — write the actual source notebook in the PR description
  (see PR description below), not in the spec.
- If the Docs(G) only has one figure for a context (not kinetics + endpoint), use a
  single figure directive instead of a tab-set.
- Omit the `## Cells` subsection entirely if the Docs(G) has no Cells section.

### Requirements

```myst
# Requirements

<one sentence per requirement, no stub if empty — omit section if no requirements>
```

If the Docs(G) has the T7 auto-generated stub, convert it to:

```myst
Requires pT7 transcription and translation (e.g. [Base Cytosol](../base-cytosol/spec.md)).
```

Omit `[PLEASE FILL IN]` stubs — the nucleus-docs CLAUDE.md says to omit a section
rather than stub it empty.

### Implementations

Omit this section if the Docs(G) only has the `[PLEASE FILL IN]` stub. Add it only
when the reviewer has supplied actual implementation links.

### Materials

If the Docs(G) Materials table has all N/A rows, omit the section and add a comment:

```myst
<!-- TODO: Materials table — fill from https://docs.nucleus.engineering/guides/materials-reference/ before publishing. -->
```

If any rows are populated, include the table with label `critical-materials`:

```myst
:::{table}
:label: critical-materials

| Material | Description | Manufacturer | Part # | Storage | Link |
| --- | --- | --- | --- | --- | --- |
| TODO | TODO | TODO | TODO | TODO | [link](TODO) |
:::
```

### Credits

```myst
# Credits

Developed by <Name> (<affiliation>).
```

Link ORCID where available:
`Developed by [Anton Molina](https://orcid.org/0000-0002-7253-2714) (b.next).`

### References

**Do not write a `# References` section.** MyST auto-generates it from DOI links cited
inline. Ensure every DOI that appeared in the Docs(G) References list is cited inline
in the body (Overview, Expected Behavior, etc.) using the format:

```myst
([Author et al., YYYY](https://doi.org/…))
```

or narrative form:

```myst
as shown in [Author et al., YYYY](https://doi.org/…)
```

## TOC updates

### myst.yml

Read `myst.yml`. Locate the `toc:` entry for `docs/modules/modules-main.md`. Add the
new spec as a child entry immediately after the last existing module entry in
alphabetical order within its category group:

```yaml
- file: docs/modules/<directory>/spec.md
```

### modules-main.md

Read `docs/modules/modules-main.md`. Add one row to the module table. Columns are
`Module Class | Specification | Validation`. Use `★` (preliminary/DevNote only) for
a new draft page:

```myst
| Reporter | [pOpen-deGFP](./reporter-degfp/spec.md) | ★ |
```

Insert the row in alphabetical order within the Module Class group. If the class group
does not exist yet in the table, add it in alphabetical order among classes.

## QA checks

Run these from the nucleus-docs root before committing:

```bash
python3 scripts/check-dropdowns.py
python3 scripts/check-file-placement.py
python3 scripts/check-toc.py
python3 scripts/check-dna-refs.py   # if you added a DNA table row
python3 scripts/check-formatting.py
```

Fix all errors. `check-formatting.py` runs warning-only but hard-wrapped prose creates
bad diffs — fix violations before PR.

Do not run `myst build` or `build-protocols.py` — CI handles these, and the build
requires the full conda environment. The QA scripts above are the gate.

## PR description

Open a draft PR against `nucleus-eng/nucleus-docs` `main`. Title:
`docs(modules): add draft spec for <Category>: <Module>`

Body must include:

1. **What this adds** — one sentence naming the module and that it is a draft spec
   generated from DevNote(M).
2. **Source DevNote** — title and DOI (or "DOI pending" if not yet published).
3. **TODO before merging** — bulleted list of every `[PLEASE FILL IN]` / `TODO:` that
   remains in the spec, grouped by section. Include figure exports with source
   notebook paths.
4. **QA** — confirm which checks passed.

Use `gh pr create --draft` so reviewers know it is not merge-ready.

## What this skill does not do

- Does not export figures from notebooks — name the source notebooks in the PR description
- Does not generate protocol PDFs or BOMs — that is `build-boms`
- Does not run `myst build --html` — CI runs this at deploy time
- Does not merge the PR — the reviewer confirms content before merge
- Does not update `myst.yml` references map for DevNote xrefs — add manually once the
  DevNote DOI is published
