---
name: devstudio-devnote-to-docs-g
description: Transform a DevNote(M) into a Docs(G) draft Google Doc — a module specification page for nucleus-eng/nucleus-docs, mapped to the correct nucleus-docs template (functional or formulation). The output is ephemeral, intended for developer review and commenting. A separate skill (devstudio-docs-g-to-m) converts the reviewed draft into a committed MyST page. Scoped to the devstudio namespace.
---

# devstudio-devnote-to-docs-g

## Provenance

Staging skill in the `devstudio` namespace. Built against the nucleus-docs templates at
`nucleus-eng/nucleus-docs/templates/` and the real published ancestor page at
`https://docs.nucleus.engineering/docs/modules/reporter-degfp/spec/`.

The output is a Google Doc draft — ephemeral, intended for developer discussion and
commenting. Format translation from MyST to Google Doc can be loose; getting the key
information into the right section matters more than markup fidelity. A separate skill
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

**Category** determines which template is used — see Template selection below.
**Module** is the short name used in the page title (e.g. `Reporter: pOpen-deGFP`).

All Drive operations are scoped to the SF-Node folder only — never access other Drive
locations.

## Template selection

nucleus-docs has three page types with templates in
`nucleus-eng/nucleus-docs/templates/`:

| Template | File | Use for |
|---|---|---|
| Module — Functional | `module-template/spec-functional.md` | Reporter, Detector, Effector, Energy, Control — a part you add to someone else's recipe |
| Module — Formulation | `module-template/spec-formulation.md` | Base, Membrane, Chassis, Cell — something you mix |
| Implementation | `implementation-template/implementation-template.md` | A named combination of module(s) + process |
| Process | `process-template/process-make_template.md` | A step-by-step protocol for making something |

**This skill currently handles Module pages only** (functional and formulation). Implementation
and Process page types are noted here for completeness; mapping those is out of scope until
a DevNote produces content that fits them.

Determine the template from Category:

- **Functional**: Reporter, Detector, Effector, Energy, Control, Pore, Emitter
- **Formulation**: Base, Membrane, Chassis, Cell

If the Category does not map cleanly, flag it and ask the invoker to clarify.

## What this skill reads

- `main.md` — Overview text, construct names and GitHub URLs, reaction composition
  tables, figure captions, author names, DOI citations, acknowledgements
- `curvenote.yml` — Author name, ORCID, email, date, funding statement

## nucleus:docs tagging

The `<!-- nucleus:docs -->` comment tag (also accepted with a space: `<!-- nucleus: docs -->`)
placed immediately before a MyST directive selects that element for inclusion in
the Docs(G) and the final MyST commit. Two element types are supported:

### Figures

Tag placed immediately before a `:::{figure}` directive:

```myst
<!-- nucleus:docs -->
:::{figure} fig-kinetics-exp1.png
Caption text.
:::
```

**Untagged figures are silently omitted.** Multiple tagged figures are allowed per
section — they appear in the order encountered. If no figures in a Results section
are tagged, omit that section's figure placeholders entirely and add a note:

```
[Note: no figures tagged nucleus:docs in this section — add tags to main.md and regenerate if figures are needed.]
```

### Composition tables

Tag placed immediately before a `:::{table}` directive or a `:::::{tab-set}` block
containing composition tables:

```myst
<!-- nucleus:docs -->
:::{table} Nucleus Cytosol reaction composition, Experiment 2.
...
:::
```

The tagged experiment's composition becomes the **canonical reference composition**
for the docs page. Only one experiment should be tagged; if multiple are tagged,
use the first and add a `[PLEASE FILL IN — multiple compositions tagged; confirm
which is canonical]` flag. If no composition table is tagged, include all experiments
from Methods and add the same flag.

The tagged table is reformatted when writing the Docs(G) (and later the MyST):
collapse to three columns with value and unit merged into a single string:

| Component | Stock Concentration | Final Concentration in Reaction |
|---|---|---|
| PMix | 15 mg/mL | 1.8 mg/mL |
| Magnesium acetate | 200 mM | 8 mM |

Where a stock or final concentration differs across conditions within the tagged
experiment, write `varies` in italics. Where only one value exists across all
conditions, write that value. Drop all volume columns — volumes are DevNote detail,
not docs content.

Caption: `` This composition was evaluated in this [DevNote title](<url>). `` — substitute the DevNote DOI or GitHub PR URL.

## Output

A new Google Doc in `sf-node/docs-drafts/` with the title
`[DRAFT] Category: Module Name — Docs(G)`. Create it with the Drive connector's
`create_file` using HTML content so headings, tables, and bold text render correctly
in the converted Google Doc.

## Construct length fetch

For every construct row in the `## Constructs` table, extract the construct length (bp)
from the GenBank LOCUS line of the sequence file. The GitHub blob URL in the table
(e.g. `https://github.com/nucleus-eng/DNA/blob/main/reporters/pOpen-deGFP.gbk`)
maps to a `gh api` call:

```bash
gh api repos/nucleus-eng/DNA/contents/<path-in-repo> \
  --jq '.content' | base64 -d | head -1
```

The LOCUS line looks like:
```
LOCUS       pOpen-deGFP             2812 bp    DNA     circular SYN ...
```

Parse the integer immediately following the construct name (third whitespace-separated
token). If the fetch fails or the LOCUS line is absent, write
`[PLEASE FILL IN — check LOCUS line in .gbk file]` in the Length column and emit a
visible warning in the document:

```html
<p><span style="color:#cc0000;font-weight:bold">
⚠ WARNING: Could not fetch construct length for &lt;name&gt; from GitHub.
Verify bp manually against the LOCUS line in nucleus-eng/DNA.
</span></p>
```

Never use a length that appears only in the DevNote prose — it may be stale. Always
fetch from the source file.

## Section mapping — Functional module

Use this mapping when Category is Reporter, Detector, Effector, Energy, Control, Pore,
or Emitter.

### Frontmatter block

From `curvenote.yml`:

```
Title:    Category: Module Name   (e.g. "Reporter: pOpen-deGFP")
Subtitle: Module Specification
Status:   draft
```

### Overview

The Overview in a functional module spec is short — typically 1–3 sentences stating
what the module is, what it does, and what it adds to Base Cytosol. Look at the
published examples for the register:

> "The deGFP Reporter Module produces deGFP, a green fluorescent protein."
> "The TetR inducible expression module is a set of two genetic constructs that encode
> tetracycline-inducible gene expression…"

Attempt to derive this from the `# Overview` section of `main.md`. Strip `{ref}`
cross-references and MyST directives; keep plain prose. Do not copy the abstract.

**Scope check:** If the DevNote Overview describes the host system (e.g. cytosol)
rather than the module being added to it, do not attempt a rewrite — flag it:

```
[PLEASE FILL IN — DevNote Overview is cytosol-centric. Rewrite to describe the
module's function: what it is, what it does, and what it adds to Base Cytosol.
The paragraph below is the DevNote text, kept as a starting point.]
```

Then include the DevNote paragraph unchanged beneath the flag.

Add the draft attention banner after the Overview paragraph:

```
⚠️ DRAFT — This page is a work in progress and not yet ready for use.
```

Flag the schematic placeholder:

```
[PLEASE FILL IN — Insert mechanism / overview schematic here. Boxes are physical
objects; arrows are processes. Caption should describe what the schematic shows.]
```

### Reference Composition

Three tabs in order: Module Dependencies → DNA → Cytosol.

**Tab: Module Dependencies**

```
[PLEASE FILL IN — Generated by the mermaid-diagrams skill from the
# Constituent Modules section. Add that section to the MyST page before
running the generator.]
```

**Tab: DNA**

From the `## Constructs` table in `main.md`. Columns: Name (code-formatted),
Length (bp) (fetched — see Construct length fetch above), File (hyperlinked filename).
Omit the Purpose column from the DevNote.

| Name | Length (bp) | File |
|---|---|---|
| `pConstruct-Name` | *fetched* | `[filename.gbk](https://github.com/nucleus-eng/DNA/blob/main/…)` |

Purified proteins do not go in this tab. A purified protein is either a purchased
reagent (→ Materials) or has an expression construct (→ its own DNA row).

**Tab: Cytosol**

From the composition table tagged `<!-- nucleus:docs -->` in `## Methods` — see
nucleus:docs tagging above. Reformat to three columns (Component | Stock Concentration |
Final Concentration in Reaction); merge value+unit; write `varies` for values that
differ across conditions; drop volume columns. Caption links to the DevNote.

If no table is tagged, include all experiment compositions verbatim and add a
`[PLEASE FILL IN — confirm canonical composition]` flag.

### Expected Behavior

**## Cytosols**

From `# Results` in `main.md`:

- Write the narrative summary for each experiment (one paragraph each), stripping
  `{ref}` cross-references.
- For each figure in Results that is tagged `<!-- nucleus:docs -->`, write a
  placeholder (untagged figures are omitted — see Figure tagging above):

  ```
  [PLEASE FILL IN — export figure from notebook]
  Figure: <figure-name> — <caption from main.md>
  Source: <relative path to notebook>
  ```

- Add a source DevNote reference at the end of this subsection. Use the DOI if
  published; otherwise use the GitHub PR URL:

  ```
  Source DevNote: <DevNote title> — <DOI or GitHub PR URL>
  ```

**## Cells**

Omit unless `main.md` contains liposome or encapsulation data in Results (look for
"encapsulation", "liposome", or "cell" terminology). If present, map the same way as
## Cytosols — narrative, tagged figure placeholders, source DevNote reference.

### Requirements

Stub this section. If the DevNote Overview or Methods mentions T7 transcription, add:

```
Requires pT7 transcription and translation (e.g. Base Cytosol).
[PLEASE FILL IN — list any additional requirements: energy regeneration system,
specific ions, co-factors, or incompatibilities.]
```

Otherwise:

```
[PLEASE FILL IN — list functional or compositional requirements for this module.]
```

### Implementations

```
[PLEASE FILL IN] — List Implementations that use this Module. Link each to its page
in nucleus-eng/nucleus-docs. Check the existing Implementations directory for entries
that reference this construct.
```

### Materials

From the `## Reagents` table in `main.md`. Copy verbatim. If all rows are N/A (common
in early DevNotes), keep the table and add a flag above it:

```
[PLEASE FILL IN — reagent details were not available at DevNote submission time.
Fill from https://docs.nucleus.engineering/guides/materials-reference/ before publishing.]
```

### Credits

From `curvenote.yml` authors list:

```
Developed by <Name> (ORCID: XXXX-XXXX-XXXX-XXXX).
```

If multiple authors, list as "Developed by <Name> and <Name> (<Node> Node)."

### References (Google Doc only)

List DOI citations found inline in `main.md` as plain hyperlinks under a References
heading. Note that MyST auto-generates the References section from inline citations —
this heading is for Google Doc review only and must not be carried into the MyST commit.

---

## Section mapping — Formulation module

Use this mapping when Category is Base, Membrane, Chassis, or Cell.

### Frontmatter block

Same as functional: `Title`, `Subtitle: Module Specification`, `Status: draft`.

### Overview

From the `# Overview` section of `main.md`, first paragraph. A formulation Overview
states what the formulation is, what it is for, and how it differs from siblings. Draft
banner as above. No schematic placeholder needed unless the DevNote includes one.

### Reference Composition

Tabs depend on the formulation type:

- **Cytosol / Base**: Inner Solution tab — from reaction composition tables in Methods
- **Membrane**: Membrane tab — from lipid composition tables in Methods
- **Cell / Chassis**: Inner Solution → Membrane → Outer Solution (three tabs)

Copy composition tables verbatim. If the DevNote does not break down a constituent
further, keep it as a single row — do not expand it.

### Expected Behavior

Same structure as functional: `## Cytosols` and `## Cells` as applicable.

### Processes

```
[PLEASE FILL IN] — Link to the assembly process for this formulation.
Check nucleus-eng/nucleus-docs/processes/ for the relevant page.
```

### Materials

Same as functional.

### Credits

Same as functional.

### References (Google Doc only)

Same as functional.

---

## REVIEW flag convention

Use `[PLEASE FILL IN]` (all-caps, in brackets) consistently for every field that cannot
be auto-filled from the DevNote. Render in red bold in the HTML output so flags are
visually prominent in the converted Google Doc:

```html
<span style="color:#cc0000;font-weight:bold">[PLEASE FILL IN]</span>
```

For construct length fetch warnings, use the `⚠ WARNING:` prefix defined in
Construct length fetch above.

## What this skill does not do

- Does not commit to `nucleus-eng/nucleus-docs` — that is `devstudio-docs-g-to-m`
- Does not handle Implementation or Process page types (noted in Template selection)
- Does not look up module properties from databases or literature
- Does not generate plasmid map images
- Does not resolve Implementations from the nucleus-docs corpus
- Does not export figures from notebooks — figures are committed as local PNGs to
  nucleus-docs; the PR description names the source notebooks
- Does not assign a DOI to the DevNote (must be published first)
- Does not use MyST cross-references for figure embedding — xrefs are for provenance
  links only (e.g. `Data from [DevNote](<url>)`), not for embedding images across repos
