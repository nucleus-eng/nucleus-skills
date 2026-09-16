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

## Read the template first

**The page structure is owned by nucleus-docs, not by this skill.** Read the
template from the clone before writing anything. The clone path is already an
invocation parameter, so nothing new is needed:

```
<nucleus-docs path>/templates/module-template/spec-functional.md
<nucleus-docs path>/templates/module-template/spec-formulation.md
```

Choose by Category. **`devstudio-devnote-to-docs-g`'s "Template selection"
section owns that mapping** — the same Category picked the Docs(G) archetype
upstream, and the two stages must not disagree about which template a module
belongs to. Read it there; it is deliberately not repeated here.

For a module that could plausibly go either way, the template states the tiebreak
itself: the split is not where the module sits in the composition tree, it is
whether the page documents a recipe or a function.

Fill the template's sections in the order it gives them, keeping its comments
until their instruction has been carried out. **Do not reproduce the template
here or work from memory of it** — it changes, and a copy in this file is how
a page ends up shaped like a template that no longer exists. It has already
split once: `nucleus-docs` replaced the single `spec.md` with these two
archetypes.

## MyST conversion rules

These are the decisions the template does not make — they are about turning
Docs(G) HTML into MyST, not about what a module page contains.

Do not hard-wrap prose — write all paragraph text as a single unbroken line
regardless of length. `check-formatting.py` reports hard-wrapped lines but is
warning-only, so this will not fail CI; hard-wrapped prose still produces bad
diffs, so fix it before opening the PR.

**Tag cleanup:** Strip all `<!-- nucleus:docs -->` comment lines from the MyST output.
These tags are DevNote authoring markers and must not appear in the committed spec.

**Flags carry forward:** every `[PLEASE FILL IN]` and `TODO:` left in the reviewed
Docs(G) becomes a `TODO:` comment in the MyST, and every one of them is listed in
the PR description. A flag that survives into the spec without appearing in the PR
body is a flag nobody will action.

### Frontmatter

Template owns it. Two values this skill supplies:

- `title:` — `"Category: Module Name"`, matching the existing title format in
  nucleus-docs. Must match Category exactly; it is user-visible and permanent.
- `status:` — always `draft` for a new page. The template's comment explains when
  it moves to `unvalidated-published` and `validated-published`, and which status
  banner pairs with each. Follow that; the banner and the field must agree.

### Composition tables

**Use the template's Cytosol-tab schema.** Ruled 2026-09-16: where the template
and the devstudio corpus disagreed on this table, nucleus-docs is authoritative.
The template's columns are Component, Stock Concentration, Final Concentration,
then **one volume column per condition**:

```
| Component | Stock Concentration | Final Concentration | − TODO (µL) | + TODO (µL) |
```

This replaces the three-column "flattened, no volume columns" form this skill
previously specified. Values that differ across conditions are still written
*varies* in italic; that was never in dispute.

The one-level-deep rule still holds and is the template's own: list each direct
constituent with its working concentration, and do not re-expand a constituent
into its own sub-components — that belongs on the constituent's page.

**Table label:** follow the template's placeholder, `comp-<something>`. Earlier
revisions of this skill required `comp-<directory>-cytosol` and attributed that
requirement to `check-bom-labels.py`. **That attribution was false** —
`check-bom-labels.py` contains no `comp-` rule at all; it governs `bom-<slug>`
labels, a different prefix for the lab-ready BOM pipeline. No published spec
matches the old pattern either. Do not reinstate it.

**Inline, not transclusion:** write the table inline; do not use MyST xref
transclusion (`xref:`) even when the source DevNote has a DOI. Inline is the
established pattern in nucleus-docs and switching a page to transclusion is a
human's call, not this skill's.

**Caption:** name the source DevNote —
`This composition was evaluated in this [DevNote title](url).`

### DNA tab

The template gives the table shape. Two rules it depends on this skill to honour:

- `Length (bp)` is an **identity claim**, not a label — it must equal the target
  file's GenBank `LOCUS` length. If the Docs(G) carried a LOCUS mismatch warning,
  forward it as a comment on the row rather than dropping it:
  `<!-- TODO: LOCUS name in .gbk is X, not Y — verify before publishing. -->`
- Do not add a row because a construct name resembles a filename in
  `nucleus-eng/DNA`. Name similarity is not identity. `devstudio-verify-dna-constructs`
  owns this distinction and the Nucleus-equivalent block to use instead.

### Figures

The template says where each kind of figure goes. What this skill decides:

- **Only figures present in the Docs(G) are included.** The Docs(G) already carries
  the curated set, tagged `<!-- nucleus:docs -->` in the source DevNote(M). Do not
  re-add figures that were left out upstream.
- **Filenames are placeholders.** Name the source notebook for each figure in the
  PR description, not in the spec. Figures are committed as local PNGs beside
  `spec.md` — never referenced by MyST cross-reference, or the page stops being
  self-contained at build time.
- **Captions carry provenance:** append `Data from [DevNote title](url).` using the
  DOI where published, otherwise the GitHub PR URL from the Docs(G) Source DevNote
  line.
- Where a context has only one figure, use a single `:::{figure}` rather than a
  tab-set of one.

### Sections with nothing to say

nucleus-docs' CLAUDE.md prefers an omitted section to an empty stub. Omit any
template section whose Docs(G) content is only `[PLEASE FILL IN]`, and leave a
comment naming what is missing so it is recoverable:

```myst
<!-- TODO: Materials table — fill from https://docs.nucleus.engineering/guides/materials-reference/ before publishing. -->
```

The exception is a context that was *tested and not written up* — the template
asks for that to be stated plainly in an `:::{attention}` block rather than
omitted, because an absent section reads as "not applicable" when the truth is
"not yet documented".

### References

**Do not write a `# References` section.** MyST generates it from DOI links cited
inline. Ensure every DOI in the Docs(G) References list is cited inline in the body
— narrative (`as shown in [Author et al., YYYY](https://doi.org/…)`) or
parenthetical (`([Author et al., YYYY](https://doi.org/…))`). A DOI that appears
only in a list nobody writes will not appear on the page at all.


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

- Does not export figures from notebooks — name the source notebooks in the PR description;
  figures are committed as local PNGs to the module directory in a follow-up commit
- Does not use MyST cross-references for figure embedding — xrefs are for provenance
  links only; images must be local PNGs to be self-contained at build time
- Does not generate protocol PDFs or BOMs — that is `build-boms`
- Does not run `myst build --html` — CI runs this at deploy time
- Does not merge the PR — the reviewer confirms content before merge
- Does not update `myst.yml` references map for DevNote xrefs — add manually once the
  DevNote DOI is published
