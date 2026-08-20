---
name: ingest
description: Convert raw research materials (Word docs, Notion exports, mixed notebook/data directories) from external collaborators into a draft Nucleus DevNote for human review. Use when a collaborator hands over unstructured source content, as opposed to an existing Curvenote-format DevNote (see the migrate skill for that case).
---

# Nucleus DevNote Ingest Skill

## Purpose

Convert raw research materials from external collaborators into a draft
Nucleus DevNote (`index.md`) suitable for human review and publication.
Unlike the migrate skill, ingest involves restructuring and interpreting
source content — the output is a draft, not a verbatim copy. Human review
is always required before publishing.

## Reference

Always use `references/devnote-style-guide.md`, alongside the skills in this plugin, (repo root) as the quality anchor.
The target output should match the structure, tone, and conventions
observed in the migrated DevNotes. When in doubt, refer to a specific
migrated example.

## Input types

### Type 1 — Word document (Google Doc export)
Preprocess before running the skill:
```bash
pandoc input.docx -o content.md --extract-media=figures/
```
This produces:
- `content.md` — the narrative content with figures replaced by
  `![](figures/imageN.png)` references
- `figures/` — directory containing extracted embedded images

Pass `content.md` to the skill. Note the figure filenames so they
can be renamed to meaningful names during review.

### Type 2 — Notion markdown export
Notion exports produce a `.md` file with a sibling directory of assets.
Preprocess:
- Strip Notion-specific artifacts: checkbox syntax (`- [ ]`),
  callout blocks (`> 💡`), toggle blocks
- Flatten any Notion database table exports (CSV files in the export)
- Pass the cleaned markdown to the skill alongside the asset inventory

### Type 3 — Mixed directory (notebooks + data + docs)
Inventory the directory first:
- List all `.ipynb`, `.md`, `.docx`, `.csv`, `.xlsx`, `.gb`, `.png` files
- Identify the primary narrative source (usually a `.md` or `.docx`)
- Note data files separately — these inform the Specification section
  and may trigger MyST directive suggestions

Pass the narrative content + file inventory to the skill.

## Preprocessing checklist

Before running the skill, confirm:
- [ ] Narrative content is in plain markdown (pandoc conversion done
      if source was .docx)
- [ ] Figures extracted to `figures/` directory
- [ ] File inventory prepared (list of all data files, notebooks,
      sequence files)
- [ ] Any existing frontmatter or metadata noted (title, authors,
      date, institution)

## Fidelity rules

These rules are absolute and override all other instructions:

**Narrative content:** Never rewrite, paraphrase, expand, or add
interpretive language to prose from the source. If the source says
"to test whether X", the output says "to test whether X" — not
"to determine whether X" or "to confirm whether X". Preserve the
author's words. You may move prose between sections but you may
not change it.

**Parameter values:** Never change a numeric value, unit,
concentration, volume, temperature, wavelength, or duration
from the source. Copy exactly as stated. If a value is missing
or ambiguous, use — and add a REVIEW flag.

**Table structure:** You may restructure tables to the Nucleus
six-column schema and separate conditions into tab-sets. The
organization of data may change. The data itself does not.

## Skill prompt

Use this prompt, substituting the bracketed sections with actual content:

---

You are converting raw research materials into a Nucleus DevNote.

## Fidelity rules (absolute — override all other instructions)

<paste the "Fidelity rules" section from this skill here, verbatim — the
prompt has to stand on its own once it leaves this file>

## Quality reference

A good DevNote has the following properties (from the Nucleus style guide):
- A one-sentence description that summarizes the key finding
- A Context section that motivates the work and situates it in
  the Nucleus platform
- A Methods section with at least one composition table using
  the standard six-column schema:
  Component | Input concentration | Unit | Final concentration | Unit | Volume (µL)
- A Results section with at least one figure reference and a
  paragraph interpreting the result
- A Specification section that distills the key protocol parameters
  a reader would need to reproduce the result
- Formal scientific prose, past tense for experimental actions,
  present tense for conclusions
- Quantitative results stated with precision and units

A complete DevNote can be described in one sentence. If the source
material doesn't support a one-sentence summary, the DevNote may
not be ready to publish.

## Source materials

**File inventory:**
[List all files in the directory: name, type, brief description]

**Narrative content:**
[Paste content.md from pandoc conversion, or cleaned Notion markdown]

**Existing metadata (if found):**
[Title, authors, date, institution, any frontmatter from source]

## Task

1. Generate a complete `index.md` with correct frontmatter
2. Map source content to DevNote section structure:
   - Context (background and motivation)
   - Methods (protocol, composition tables, instrument settings)
   - Results (figures, interpretation)
   - Specification (reproducible parameter summary)
3. Reformat composition/reaction tables to the standard six-column
   schema where possible. Use `—` for missing values. Do not bold
   table cells — use plain text only, including totals rows.
4. Convert figure references to MyST figure directives:
   :::{figure} figures/[filename].png
   :label: fig-[slug]
   :width: 75%
   [Caption from source]
   :::
5. Suggest appropriate MyST directives for data files:
   - `.gb` or `.dna` files → suggest seqviz directive, flag for review
   - `.csv` files → note as candidate for composition.csv or
     platemap.csv following Nucleus naming convention
   - `.xlsx` files → note as candidate for results.xlsx
6. Flag any fields that require human review using:
   REVIEW: [reason]

## Frontmatter schema

```yaml
---
title: [concise, specific title]
description: |
  [one to two sentence summary of key finding — verbatim from source
  abstract if present, otherwise synthesized]
date: [from source metadata or REVIEW: not found]
authors:
  - name: [from source]
    affiliation: [from source]
    email: [from source or REVIEW: missing]
keywords:
  - [3-6 keywords relevant to the work]
license: CC-BY-4.0
thumbnail: figures/[most representative figure filename]
collections:
  - REVIEW: inferred — [suggested collection based on content]
id: dn-[year]-ccby-[slugified-title]
---
```

Note on license: use CC-BY-4.0 as default for external collaborator
submissions. Flag as REVIEW if the content contains protocol-level
specifications or formulations that may warrant CERN-OHL-P-2.0.

## Do not

- Invent scientific content not present in the source materials
- Rewrite results to sound more significant than the source states
- Fill in missing concentration values by inference
- Remove negative or inconclusive results
- Combine content from multiple experiments into a single claim
  unless the source explicitly does so

## Flag format

For any field or section that cannot be confidently generated from
the source:
```
REVIEW: [specific reason — what is missing, what decision is needed]
```

Examples:
- `thumbnail: "REVIEW: figure file needs to be renamed from image1.png"`
- `collections: "REVIEW: inferred — nucleus-core, cal-poly"`
- In Results: `REVIEW: source figure embedded in Word doc —
  extract figures/image1.png and rename to figures/[descriptive-name].png`

---

## Output structure

```
[devnote-slug]/
├── index.md          # generated by this skill — requires human review
├── myst.yml          # minimal project config
├── figures/          # extracted from source (rename from imageN.png
│   └── *.png         # to descriptive names during review)
├── [data files]      # copied from source with Nucleus naming convention
│   ├── composition.csv    # if reaction composition data present
│   ├── platemap.csv       # if well layout data present
│   └── results.csv        # if quantitative results present
└── [notebooks]       # copied from source if present
    └── analysis.ipynb
```

### `myst.yml` format

```yaml
version: 1
project:
  title: [title]
  toc:
    - file: index.md
    - file: analysis.ipynb  # if present
```

Do NOT include `site:` in the subdirectory myst.yml.
Do NOT include `project.id`.

## Known gaps and human review checklist

After running the skill, the human reviewer should:

- [ ] Fill in all `REVIEW:` flagged fields
- [ ] Rename extracted figures from `image1.png` to descriptive names
      matching the figure directive references in `index.md`
- [ ] Verify composition table column values are correct — do not
      publish concentration values that haven't been confirmed
- [ ] Confirm license — upgrade to CERN-OHL-P-2.0 if content
      includes Nucleus-compatible protocol specifications
- [ ] Assign collections once collection taxonomy is defined
- [ ] Confirm the one-sentence description accurately represents
      the key finding
- [ ] Check that the Specification section is complete enough for
      a reader to reproduce the experiment
- [ ] Run `myst build` locally to confirm figures render correctly
      before pushing to the content repo
- [ ] Run `vale index.md` (or `main.md`) and fix any flagged notation
      issues — see "Notation and units" in the style guide

## Table formatting rules

Composition tables must follow the standard Nucleus schema:

| Component | Input concentration | Unit | Final concentration | Unit | Volume (µL) |
| --- | --- | --- | --- | --- | --- |

Rules:
- Use `—` for missing or not-applicable values
- Plain text only in table cells — no bold, no inline markdown
- Totals row as plain text: `Total` not `**Total**`
- Notes about mastermix assembly go below the table directive,
  not inside it
- If source table uses non-standard columns (e.g. Bill of Materials
  format), reconstruct from protocol text rather than copying columns

## Differences from migrate skill

| | migrate | ingest |
| --- | --- | --- |
| Source | Existing DevNote | Raw research materials |
| Content | Verbatim | Restructured |
| Section mapping | Preserve as-is | Map to Context/Methods/Results/Specification |
| Quality bar | Already published | Draft — requires human review |
| Figure handling | Copy paths as-is | Extract from Word doc, flag for renaming |
| Table handling | Verbatim | Reconstruct to standard schema |
| Output | Near-publishable | Draft for review |

## Observations from first ingest test (Cal Poly, April 2026)

The source was a Word doc following a DevNote-adjacent lab manual
template (CHEM 471). Key observations:

- Source already had DevNote-like structure (Overview, Protocol,
  Results) — mapping to Context/Methods/Results/Specification
  was straightforward
- Composition table had only three columns (Stock, Final, Volume)
  rather than six — reconstructed with `—` for missing values
- Bill of Materials table present but not mappable to Nucleus schema —
  ignored, components carried into composition table from protocol
- Figure embedded in Word doc as `media/image1.png` — needs
  extraction via pandoc `--extract-media` flag
- Stock concentrations for commercial kits (PURExpress Solution A/B)
  are proprietary and should be recorded as `—`
- Two authors with institutional emails — both included in frontmatter
- Source referenced a lab manual rather than primary literature —
  flagged but not blocking for publication