---
name: devstudio-author-myst-content
description: Apply MyST authoring conventions when producing or reviewing DevNote(M) or Docs(M) content — fence depth, figure placement, composition-table schema, DNA sequence formatting, Vale notation rules, and dropdown hygiene. Use whenever devstudio-devnote-g-to-devnote-m or devstudio-docs-g-to-docs-m writes MyST markdown, or whenever a human asks to review MyST content for convention compliance. This is a staging-namespace (devstudio-) skill — see "Provenance" below before treating it as canonical.
---

# devstudio-author-myst-content

## Provenance

Staging skill in the `devstudio` namespace. Two source tiers, not equally authoritative:

- **DevNote(M) conventions** are sourced from `devnote-style-guide.md`, `ingest.md`, and
  `submit.md` — canonical, ground-truth material for DevNotes specifically, uploaded
  directly rather than extracted secondhand. Treat this tier as reliable.
- **Docs(M) conventions** are sourced from `nucleus-docs`' `CLAUDE.md`, extracted
  narrowly for DevStudio's needs. This file's line numbers had already drifted from an
  earlier extraction plan's citations, so content was re-located by section heading, not
  by trusting any recorded line range. Supersede when nucleus-docs' own Phase 4 skill
  extraction lands.

**A real scoping error from this skill's first draft**: composition-table formatting,
figure de-emphasis dropdowns, and page-status frontmatter were originally written as if
they applied to both DevNote(M) and Docs(M). They don't — DevNotes and Docs pages have
different, non-overlapping schemas for several of these. This revision separates the
two explicitly rather than assuming shared conventions where none were confirmed.

Out of scope entirely: process-page structure (Overview/Protocol/Downloads), the
lab-ready PDF/BOM pipeline, TOC (`myst.yml`) management for Docs, and CI wiring — those
stay with nucleus-docs and its `build-boms`/`lint-docs` skills. Also out of scope:
pandoc-conversion notation fixups (subscript/superscript/underline/highlight) and the
verbatim-fidelity rules for turning raw source material into a draft — those are
`devstudio-log-to-devnote-g`'s job (largely already written in the uploaded `ingest.md`),
not this skill's. And `curvenote.yml`/`base.yml` generation plus venue submission checks
are a separate downstream skill (uploaded as `submit.md`), not part of authoring MyST
content itself — see the note under "What this skill does not do."

---

# DevNote(M) conventions

## Composition tables — six-column schema, confirmed

DevNote composition tables use a fixed schema, confirmed by both `ingest.md` and
`devnote-style-guide.md` independently:

```
Component | Input concentration | Unit | Final concentration | Unit | Volume (µL)
```

- Directive: `:::{table} [Caption]`, with `:label:` and `:align: center`.
- Use `—` for missing/not-applicable values. Plain text only in cells — no bold, no
  inline markdown. Totals row is plain text (`Total`, not `**Total**`).
- **Never drop a column or row to fit this schema.** If a source table doesn't map
  cleanly (e.g. a 3-column Stock/Final/Volume table, or a 7-column BOM with Reagent/
  Product Name/Manufacturer/Catalog No./Price/Storage/Link), retain it as-is. Restructuring
  organization is fine; dropping data is not.
- Notes about mastermix assembly go *below* the table directive, not inside it.
- **This is a completely different schema than Docs(M)'s module composition tables**
  (see the Docs(M) section below) — don't apply Docs' one-level-flattening rule here.

## DNA/RNA sequence formatting

Break sequences longer than ~60–65 characters with `<br>` tags to prevent table
overflow — **the two source documents disagree on the exact width** (`ingest.md` says
~60, `devnote-style-guide.md` says ~65 with working code below); this hasn't been
reconciled, treat either as acceptable until it is:

```python
def reflow(text, width=65):
    text = text.replace('<br>', '')
    result = []
    count = 0
    i = 0
    while i < len(text):
        if text[i] == '<':          # skip HTML tags, don't count them
            end = text.index('>', i) + 1
            result.append(text[i:end])
            i = end
            continue
        result.append(text[i])
        count += 1
        i += 1
        if count >= width:
            result.append('<br>')
            count = 0
    return ''.join(result)
```

Content is always verbatim — this reflows line breaks only, never alters sequence
characters. Inline markup (`**promoter**`, `*terminator*`, `<u>overlap region</u>`) must
survive the reflow untouched.

## Tab-sets

- **Group ≥2 related sequential tables into a tab-set** (DNA component tables, protocol
  variant tables). Each table becomes a tab-item with a short descriptive label.
- **Place the tab-set *before* any prose that references it via `{numref}`.** A forward
  reference (prose cites the label before the tab-set defining it appears) can cause
  MyST to assign duplicate numbers to both tables. Define first, reference after.
- **Use `:sync:` keys on parallel tab-items** (e.g. Time Series / End Point pairs across
  multiple tab-sets on one page) so tabs switch together when a reader clicks one.
- **Figure/table renumbering from tab-set splitting is acceptable, not a bug.** Splitting
  one source figure into two tab-items shifts all subsequent numbering; adding labels to
  previously-unlabeled tables does too. Always use `{ref}`/`{numref}` cross-references in
  prose, never hard-coded numbers, so rendered numbers stay correct regardless of what
  the source originally numbered. Flag with a REVIEW comment only if the source's
  original reference is genuinely ambiguous.

## Fence depth — still relative, not fixed (see general note below)

- **Plain tab-set** (no extra wrapper directives): outer `{tab-set}` = `:::::` (5),
  `{tab-item}` = `::::` (4), content inside = `:::` (3).
- A real migrated DevNote (`10-nucleus_cytosol_v05/main.md`) nests `{tab-set}` →
  `{tab-item}` → `{figure}` → `{seqviz}` at 6/5/4/3 — one level deeper, because of the
  extra `{figure}` wrapper. **Count from your outermost fence, decrease by one colon per
  level** — don't assume a fixed absolute count applies regardless of actual nesting depth.
- **`{seqviz}`**: a custom directive (specific to the DevNote-archive repo's plugin set,
  not documented in `nucleus-docs`) embedding an interactive plasmid viewer from a `.gb`
  file, e.g. `:::{seqviz} ./plasmids/pOpen-deGFP.gb`. Full syntax/options not yet
  documented here — known gap.

## Figures

- **Static PNG with explicit `:name:` label, not a notebook-cell `glue` reference.** A
  `glue`-based `#fig:` reference whose backing cell was never tagged renders blank with
  no build error — confirmed as a real, currently-live issue affecting migrated DevNotes
  (`04_ppk`, `nucleus-cytosol-v05`). Static PNGs don't have this failure mode.
- **Strip any leading figure number from captions.** MyST auto-generates the "Figure N:"
  prefix from the label — a caption starting with "Figure 2: ..." double-numbers.
- **System-context figures** (a module in context of Base Cell/Developer Cell) belong in
  a `## Cells` section, not `# Overview` — Overview carries mechanism/schematic figures
  only. (Sourced from Docs(M) material — unconfirmed whether DevNotes use `## Cells` at
  all; flag if this doesn't map cleanly to a real DevNote's structure.)

## References vs. Resources — two different sections, don't conflate

- **Do not include a standalone References section.** `[](DOI)` inline links cause MyST
  to auto-generate one; a hand-written second one duplicates entries.
- **Do include a Resources section** for anything that can't be cited by DOI: Benchling
  links, Colab notebooks, software docs, sequence-compiler tools, plasmid repositories.
  These wouldn't appear in the auto-generated reference list otherwise.

## Notation and units (Vale-enforced)

Ported from `nucleus-docs`' Vale styles into the DevNote repo's own `.vale.ini` — keep
in sync with that source if a rule changes there. Run `vale main.md` before considering
a DevNote publish-ready.

- Space between magnitude and unit (`10 mL`, not `10mL`); no spaces inside compound
  units (`ng/µL`, not `ng / µL`).
- `µ` not `u` (`µL`, `µM`, `µg`, `µm`).
- `°C` with a space before it (`55 °C`), never `55C`/`55 C`/`degC`.
- Unicode superscripts for ion charges (`Mg²⁺`, `Na⁺`), not `Mg2+`.
- Unicode subscripts for chemical formulae and OD labels (`H₂O`, `OD₆₀₀`, `A₂₆₀`).
- House casing: `rpm`, `Kan`, `kDa`, `4x`/`1x` — not `RPM`, `KAN`, `KDA`, `4X`/`1X`.
- Thousands separator is a space, not a comma (`40 000 units`); numbers under 5 digits
  take no separator.
- Time abbreviations (`h`, `min`, `s`, `d`, `yr`, `mo`), not spelled out.
- Avoid a bare hyphen between two numbers before a unit — `16 mM to 18 mM` or
  `(16–18) mM`, not `16-18 mM`.
- Spaces around `+` in mixtures (`LB + Kan`, not `LB+Kan`).
- **Catalog numbers containing unit-like strings** (e.g. `810158C-1mg`) will be flagged
  by Vale's magnitude-unit-spacing rule as a false positive — suppress locally with
  `<!-- vale nucleus.magnitude-unit-spacing = NO/YES -->` around the table rather than
  altering the vendor identifier.

## Complete vs. stub — signals, not a strict gate

A complete DevNote has: a populated abstract summarizing the key finding, an Overview/
Introduction that contextualizes the work, at least one composition table with exact
concentrations, at least one results figure, a Conclusions section with a forward-looking
statement, and a working analysis notebook with all raw data committed alongside it.

Stub signals: an Overview section present but empty: an `Untitled.ipynb` notebook name
(experiment wasn't renamed after the fact); commented-out TOC entries or a commented-out
`# doi:` in `curvenote.yml`; a template file (`template-blank.md`) still present in the
repo root. None of these alone are blocking — they're signals a reviewer should notice,
not an automated pass/fail.

---

# Docs(M) conventions

*(Everything below is `nucleus-docs`-sourced, applies to `devstudio-docs-g-to-docs-m`
output, and should NOT be applied to DevNote(M) content — several of these were wrongly
cross-applied in this skill's first draft.)*

## Composition tables — one-level flattening, NOT the DevNote six-column schema

A module built from other modules (e.g. a sensing cell made of a chassis + a detector)
lists each direct constituent as a single line with its working concentration/fraction
— don't expand a constituent further into its own sub-components on the composed page;
that detail belongs on the constituent's own page. Citation-only rows with no numbers
aren't sufficient — direct constituents' working concentrations must appear.

**Mass-to-molar conversions use the functionally active stoichiometry**, not whatever
oligomeric state a reference database defaults to. When sources disagree, resolve using
literature on the specific organism/context, preferring solution-phase or functional
evidence over crystal-packing annotations. Flag the discrepancy rather than picking
silently — same "don't-guess, verify" category as `devstudio-verify-dna-constructs`.

## Page-status frontmatter — confirmed NOT part of DevNote(M)

**Verified against real content: DevNote frontmatter has no `status:` field** — checked
both `migrate`'s extraction schema and a real migrated DevNote (`title` + `abstract`
only). This convention applies to Docs(M) output only.

| `status:` value | meaning | TOC | banner |
|---|---|---|---|
| `draft` | incomplete, not ready for public consumption | `hidden: true` | 🚧 Draft banner |
| `unvalidated-published` | complete, not yet validated in current Nucleus Cytosol | normal | "Not yet validated" banner |
| `validated-published` | complete and validated | normal | none |

- Absent `status:` defaults to `validated-published` — don't add it to already-ready
  content just for explicitness.
- Field does **not** auto-render a banner — add by hand:
  ```
  :::{attention} 🚧 Draft
  This page is a work in progress and not yet ready for use.
  :::
  ```
  ```
  :::{attention} Not yet validated
  This page has not been validated in Nucleus Cytosol. <optional specifics>
  :::
  ```
- An unrelated content caveat (safety note, "not actively supported" flag) is
  independent of `status:` — its own admonition, don't conflate.

## Figure placement — secondary-figure dropdown, unconfirmed for DevNotes

When a section has one primary figure, wrap supplementary figures in a dropdown
(`:class: dropdown` on an admonition directive) titled by the *finding*, not a generic
label. The admonition type isn't fixed (`nucleus-docs` uses `{hint}`; a real DevNote used
`{tip}` for an unrelated dropdown) — but no real DevNote example of this specific
figure-de-emphasis pattern was found. Treat as Docs(M)-confirmed only.

## Dropdown hygiene

- Only keep dropdowns with real content — delete any whose only content is a
  placeholder (`- TODO`, `- None`, `- N/A`, `- TBD`).
- Found an empty dropdown? Don't silently delete or silently leave it — flag and ask:
  *"The `<Section Title>` dropdown is empty — should it be deleted, or does it need
  content?"* Wait for confirmation. (Exempt: literal template files.)
- If removing dropdowns empties an entire card block, remove the card too.

## Prose and link mechanics

- Don't hard-wrap paragraph text — one line per paragraph regardless of length, blank
  lines are the only intentional break.
- Internal links in inline HTML must use `.md` extensions, not `.html` — MyST resolves
  via source paths; `.html` 404s on the deployed site.

---

## What this skill does not do

- Does not cover process-page structure, the lab-ready PDF/BOM pipeline, or `myst.yml`
  TOC management — nucleus-docs-specific, stays there.
- Does not run as a standing CI/lint check — applies at the point
  `devstudio-devnote-g-to-devnote-m` or `devstudio-docs-g-to-docs-m` writes/reviews content.
- Does not cover `curvenote.yml`/`base.yml` generation or the 7 venue submission checks
  — that's a separate downstream skill (`submit.md` uploaded as reference). Note: the
  base.yml/curvenote.yml two-file split may get consolidated into a single artifact in
  DevStudio's own version — TBD, don't assume the two-file structure is final when that
  skill gets built.
- Does not cover pandoc-conversion notation fixups or source-fidelity rules — that's
  `devstudio-log-to-devnote-g`'s scope (`ingest.md` uploaded as reference, largely
  reusable as-is).
- Does not yet document DevNote-only directives beyond `{seqviz}`'s existence.

## Validated (2026-09-05)

Checked against real migrated content in `nucleus-devnote-archive-1`, then substantially
corrected again against uploaded ground-truth material (`devnote-style-guide.md`,
`ingest.md`, `submit.md`):

- **Fence depth**: confirmed relative/incremental, not fixed.
- **`status:` frontmatter, composition-table schema, secondary-figure dropdowns**: all
  three were originally mis-scoped as applying to both DevNote(M) and Docs(M) — now
  split, with DevNote(M)'s six-column schema and Docs(M)'s one-level-flattening rule
  confirmed as genuinely different schemas, not a formatting variant of the same rule.
- **`{seqviz}`**: real, in active use, uncovered by `nucleus-docs`.
- **Tab-set mechanical build test**: attempted via `mystmd`, inconclusive — the real
  check (`myst build --html --strict`) needs `api.mystmd.org`, unreachable from this
  sandbox. The reachable `--md` export path doesn't support tab-set round-tripping at
  all (errored identically across three colon schemes), so it validated nothing about
  tab-set correctness either way. A plain dropdown built cleanly via the same path.
  Real validation needs Claude Code, not this environment.
- **DNA sequence wrap width**: unreconciled disagreement between sources (~60 vs ~65
  chars) — flagged, not resolved.

Net effect of this revision: roughly half of the DevNote-side content was either
wrongly scoped or unconfirmed before being checked against real, canonical material.
Worth remembering as a pattern — source-derived conventions need validation before
being trusted, and "extracted from a real repo" isn't the same bar as "confirmed by the
team that owns the convention."
