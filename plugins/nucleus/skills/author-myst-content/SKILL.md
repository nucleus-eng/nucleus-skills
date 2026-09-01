---
name: author-myst-content
description: Author or review a nucleus-docs page in MyST — fence and tab-set nesting depth, figure placement, composition-table depth, page-status frontmatter and banners, and the empty-dropdown policy. Use when writing a new process page, module spec, or implementation page, when editing an existing one, or when a page renders wrong and the cause looks like fence depth.
---

# Author MyST content

Conventions for pages under `docs/` in nucleus-docs. For the tools that check a page after you write it, see `lint-docs`. For BOM tables and download cards, see `build-boms`.

## Page structure

Pages use MyST admonition nesting with `:::` fences. Process pages follow a consistent structure:

1. Frontmatter (`title:`)
2. `# Overview` with an `:::::::{card}` block containing nested dropdowns for Notes, Prerequisites, Hazardous Materials, Critical Materials, Genetically Encoded Components, Composition, and References
3. `# Protocol` with `##` subsections and checklist steps (`- [ ]`)
4. `# Downloads` grid with cards linking to PDF lab protocol and Bill of Materials

Protocol steps use `- [ ]` checkboxes and `:::{hint}` dropdowns for extended notes. Cross-references use MyST `{ref}` syntax for same-page targets and standard markdown links for cross-page references.

## Syntax rules

**Internal links in inline HTML must use `.md` extensions, not `.html`.** MyST resolves internal links via the source `.md` paths. Using `.html` in an `<a href="...">` tag produces a 404 on the deployed site. This applies to all inline HTML links (e.g. version badges, quick-link pills) — always write `href="./path/to/page.md"`, never `href="./path/to/page.html"`.

**Tab-set fence depth.** Tab-sets require a consistent three-level nesting: the outer `{tab-set}` uses `:::::` (5 colons), each `{tab-item}` inside uses `::::` (4 colons), and figures or admonitions inside a tab-item use `:::` (3 colons). Mismatched colon counts are a common source of rendering failures.

**Secondary figures.** Within a section that has a primary figure (e.g. a performance plot), de-emphasize supplementary or supporting figures by wrapping them in a `::::{hint} <descriptive title>` block with `:class: dropdown`. The dropdown title should describe the finding, not just label the figure (e.g. `::::{hint} The Emitter Cell causes E. coli to express GFP in response to IV-HSL`). This keeps the primary figure prominent while keeping supporting context one click away. When there are multiple parallel secondary figures (e.g. the same experiment across several conditions), use a hybrid: a single dropdown wrapping a tab-set, so readers open one drawer and switch between conditions with tabs. The outer hint uses 7 colons, the `{tab-set}` inside uses 6, each `{tab-item}` uses 5, and figures inside use 3 — consistent with the tab-set nesting rules above.

**System-context figure placement (module specs).** A figure showing the module in the context of the Base Cell or Developer Cell belongs in the `## Cells` section, not `# Overview`. The Overview section should carry mechanism and schematic figures only.

## Composition tables

**Composition table depth for composed modules.** Some module specs are themselves a composition of other modules — e.g. a chassis made of a cytosol and a membrane, a sensing cell made of a chassis and a detector, a cascade made of a sensing cell, an effector, and a reporter. For these pages, the default is to flatten the Composition/Reference table **one level deep**: list each direct constituent module as a single line item with its working concentration or fraction in the combined recipe (e.g. `Base Cytosol: <amount>`, `Chicago Membrane: <amount>`). Do not expand a constituent module further into its own sub-components (e.g. don't break Base Cytosol down into its ~100 individual PURE-system components on the composed page) — that level of detail belongs on the constituent's own spec page. The full composition is a mathematically well-defined, fully collapsible object all the way down to base components, so a page can show that full expansion if it is genuinely useful, but one level of flattening is the expected default for readability. Citation-only rows with no numbers are not sufficient — the direct constituents' working concentrations should always appear.

## Page status (draft / published)

Every content page has a maturity `status`, declared as a frontmatter field. This keeps stub or unvalidated pages from misrepresenting themselves on the public site without a heavyweight build-exclusion mechanism (nucleus-docs issue #74; #57 may later add build-time exclusion keyed off this same field).

| `status:` value | meaning | TOC | banner |
| --- | --- | --- | --- |
| `draft` | incomplete; not ready for public consumption | must be `hidden: true` (keep out of the sidebar) | **Draft** banner (below) |
| `unvalidated-published` | complete and publicly visible, but not yet validated in the current Nucleus Cytosol | normal | **Not yet validated** banner (below) |
| `validated-published` | complete and validated; ready | normal | none |

- **Absent `status:` is treated as `validated-published`** — do not churn the ~50 ready pages. Only `draft` and `unvalidated-published` pages need an explicit field.
- **Templates ship with `status: draft`** so a new page can't accidentally appear validated; the author changes it to `unvalidated-published` or `validated-published` when ready.
- `hidden: true` in the `myst.yml` TOC is used for *every* non-sidebar child page. It is a navigation setting, **not** a maturity signal. Do not read it as one.
- The `status:` field does **not** auto-render anything — add the matching banner by hand when you set `draft` or `unvalidated-published`. The two standard banners:

```
:::{attention} 🚧 Draft
This page is a work in progress and not yet ready for use.
:::
```

```
:::{attention} Not yet validated
This page has not been validated in Nucleus Cytosol. <optional specifics, e.g. "Expected performance data below is from PURExpress cells.">
:::
```

A page may also carry an unrelated content caveat (e.g. aHly's "not actively supported" BSL-2 note) — that is independent of `status:` and stays as its own admonition.

## Empty dropdown policy

The process template includes all possible dropdown sections as a starting point. **When authoring or reviewing a process page, only keep dropdowns that have real content.** Delete any dropdown whose only content is a placeholder (e.g. `- TODO`).

The template uses `- TODO` as the scaffold placeholder — this is intentional so contributors know which sections need to be filled in. **`check-dropdowns.py` (and CI) will fail if any `- TODO`, `- None`, `- N/A`, or `- TBD` placeholder-only list survives outside `templates/`.** Before opening a PR, run:

```bash
python3 scripts/check-dropdowns.py
```

**When editing or reviewing a process page**, scan for empty dropdowns matching this pattern and flag them:

```
::::::{<type>} <Section Title>
:class: dropdown
:icon: false

- TODO

::::::
```

If you find one, flag it and ask the developer: **"The `<Section Title>` dropdown is empty — should it be deleted, or does it need content?"** Wait for confirmation before making any changes. Do not silently leave placeholder content in committed files, but also do not silently delete it. The template file (`templates/process-template/process-make_template.md`) is the only file exempt from this rule.

**If all dropdowns in the Important Information card are removed**, the containing card block should also be removed:

```
:::::::{card}
:header: **Important Information**

Please read this section carefully. It contains important notes, resources, and safety information. Not all information included here is included in the lab-ready protocol.

:::::::
```

Again, confirm with the developer before deleting the card.
