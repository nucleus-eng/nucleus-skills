---
name: devstudio-devnote-to-docs-g
description: Transform a DevNote(M) into a Docs(G) draft Google Doc — a module specification page for nucleus-eng/nucleus-docs. The output is ephemeral, intended for developer review and commenting. A separate skill (devstudio-docs-g-to-m) converts the reviewed draft into a committed MyST page. Scoped to the devstudio namespace.
---

# devstudio-devnote-to-docs-g

## Provenance

Staging skill in the `devstudio` namespace. Built against the module spec template at
`nucleus-eng/nucleus-docs/templates/module-template/spec.md` and the real published
ancestor page at `https://docs.nucleus.engineering/docs/modules/reporter-degfp/spec/`.

The output is a Google Doc draft — ephemeral, intended for developer discussion and
commenting. Format translation from MyST to Google Doc can be loose; getting the key
information into the right place matters more than markup fidelity. A separate skill
(`devstudio-docs-g-to-m`) converts the reviewed draft into a MyST commit against
`nucleus-eng/nucleus-docs`.

## Invocation model

Point the skill at a DevNote(M) directory and name the target module:

```
devstudio-devnote-to-docs-g
DevNote(M): /path/to/devnotes/devnote-sy-20251104-20251107/
Module: pOpen-deGFP
Category: Reporter
SF-Node folder ID: 1d2QuOtPDdSxuF1z7NlRt-MtJdNKgNI7s
```

**Category** follows the title format from `spec.md`: Reporter, Energy, Base, Control, etc.
**Module** is the short name that will appear in the page title (e.g. `Reporter: pOpen-deGFP`).

All Drive operations are scoped to the SF-Node folder only — never access other Drive
locations.

## What this skill reads

- `main.md` — Overview text, construct names and GitHub URLs, reaction composition
  tables, figure captions, author names, DOI citations, acknowledgements
- `curvenote.yml` — Author name, ORCID, email, date, funding statement

## Output

A new Google Doc created in the sf-node Drive folder (e.g. `sf-node/docs-drafts/`) with
the title `[DRAFT] Category: Module Name — Docs(G)`. Write it using the Drive connector's
`create_file` with HTML content so headings, tables, and bold text render correctly in
the converted Google Doc.

## Section mapping — DevNote(M) → Docs(G)

### Frontmatter

From `curvenote.yml`:

```
Title: Category: Module Name   (e.g. "Reporter: pOpen-deGFP")
Subtitle: Module Specification
Status: draft
```

### Overview

From the `# Overview` section of `main.md`. Use the first paragraph only — the Overview
in a module spec is one paragraph stating what the module is, what it does, and key
parameters. Strip `{ref}` cross-references and MyST directives; keep plain prose. Do not
use the abstract.

Add the Draft attention banner verbatim:

```
⚠️ DRAFT — This page is a work in progress and not yet ready for use.
```

### Designs

From the `## Constructs` table in `main.md`. Map each row:

| Constructs column | Designs table column |
|---|---|
| Name | Name (code-formatted) |
| Sequence link (GitHub URL) | File (hyperlinked filename) |
| Purpose | — (omit; not in Designs table) |

Extract the construct length (bp) from the GitHub URL by fetching the `.gbk`/`.gb` file
from `nucleus-eng/DNA` and reading the LOCUS line. If fetch fails, write `[PLEASE FILL IN]`.

Proteins table: write "None" unless `main.md` references a purified protein component.

### Maps

Flag only — write a REVIEW comment:
```
[PLEASE FILL IN] — Generate a plasmid map image from the .gb file
(SnapGene / Benchling) and insert here as a figure with caption.
```

No map image will be available from the DevNote alone.

### Properties

The Properties table (excitation max, emission max, MW, etc.) comes from literature and
databases, not from the DevNote. Write placeholder rows for the most common Reporter
properties and flag each:

| Property | Value | Source |
|---|---|---|
| Excitation max (nm) | [PLEASE FILL IN] | |
| Emission max (nm) | [PLEASE FILL IN] | |
| MW (kDa) | [PLEASE FILL IN] | |

Do not fabricate values. If the DevNote's Overview mentions a specific property value
inline (e.g. "expressed at 488 nm"), transcribe it and note the DevNote as the source —
but flag for literature verification.

### Cytosols / experimental data

From `# Methods` and `# Results` in `main.md`. This section is the richest mapping from
DevNote content:

- **Reaction composition**: copy the composition tables from Methods verbatim. Lazy
  format is fine — plain table rows, no MyST directives.
- **Figures**: for each figure reference in Results, write a placeholder:
  ```
  [Figure: kinetics-exp1 — Translation kinetics of Cytosol and PURExpress reactions...]
  Source: experiments/20251104-NucleusPURE_deGFP/Analysis.ipynb
  ```
  The actual figure images are not available without running the notebooks — flag each
  as `[PLEASE FILL IN — export figure from notebook]`.
- **Cited DevNote**: add a reference line at the end of this section:
  ```
  Source DevNote: [DevNote title](https://doi.org/TODO) — [PLEASE FILL IN DOI once published]
  ```

### Cells

Omit unless `main.md` contains liposome encapsulation data (look for "encapsulation",
"liposome", or "cell" terminology in Results). If present, map the same way as Cytosols.

### Implementations

Write a stub — the implementations list requires knowledge of the nucleus-docs corpus
that is out of scope for this skill:

```
[PLEASE FILL IN] — List Implementations that use this Module. Link each to its page
in nucleus-eng/nucleus-docs. Check the existing Implementations directory for entries
that reference this construct.
```

### Credits

From `curvenote.yml` authors list. Format as:
```
- Name (ORCID: XXXX-XXXX-XXXX-XXXX)
```

### References

List DOI citations found inline in `main.md` (the `https://doi.org/...` links with
author/year strings). These will auto-generate in the MyST output — in the Google Doc
just list them as plain hyperlinks under a References heading.

## REVIEW flag convention

Use `[PLEASE FILL IN]` (all-caps, in brackets) consistently for every field that cannot
be auto-filled from the DevNote. In the HTML output, render these in red bold so they
appear visually prominent in the converted Google Doc:

```html
<span style="color:#cc0000;font-weight:bold">[PLEASE FILL IN]</span>
```

## What this skill does not do

- Does not commit to `nucleus-eng/nucleus-docs` — that is `devstudio-docs-g-to-m`
- Does not look up Properties values from databases or literature
- Does not generate map images
- Does not resolve Implementations from the nucleus-docs corpus
- Does not export figures from notebooks
- Does not assign a DOI to the DevNote (must be published first)
