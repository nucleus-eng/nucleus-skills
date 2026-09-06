---
name: devstudio-log-to-devnote-g
description: Convert a completed DevStudio experiment folder (a Log Google Doc, a platemap, one or two analysis notebooks, raw instrument data) into a draft DevNote as a native, commentable Google Doc — following Nucleus DevNote structure, with fidelity to source content and REVIEW flags for anything uncertain. Use when a human points Claude at a specific experiment folder they've deemed ready to draft into a DevNote. This is a staging-namespace (devstudio-) skill — see "Provenance" below before treating it as canonical.
---

# devstudio-log-to-devnote-g

## Provenance

Staging skill in the `devstudio` namespace, adapted from the uploaded `ingest.md`
(a skill for turning raw collaborator materials into a DevNote) — but with one
deliberate architectural divergence, described below, to fit DevStudio's two-stage
pipeline rather than `ingest.md`'s single-stage one.

**The divergence:** `ingest.md` goes straight from raw material to MyST-formatted
`main.md` — real `:::{table}` and `:::{figure}` directives, YAML frontmatter, the whole
thing — in one pass. DevStudio's pipeline has an explicit reason to split this into two
stages: DevNote(G) exists specifically so a TA can comment on it before it's finalized,
and it's a **native Google Doc**, which does not render MyST directive syntax — a Doc
full of literal `:::{table}` text would look broken to a human reviewer, not just
unstyled. So this skill produces a **plain, well-structured draft** (Doc headings, real
Doc tables, embedded images, visible REVIEW flags) using `ingest.md`'s content rules
(fidelity, table restructuring, REVIEW-flag conventions) without its MyST serialization.
`devstudio-devnote-g-to-devnote-m` (not yet built) is responsible for turning the
reviewed draft into actual MyST syntax, applying `devstudio-author-myst-content`'s
conventions, and assigning the final frontmatter/id.

This skill is invocation-driven, like `devstudio-read-from-google-drive` and
`devstudio-write-to-google-drive`: a human points it at one specific, already-complete
experiment folder. It does not crawl the Log directory looking for finished experiments,
and it does not decide when an experiment is "done" — that's the human's call, made
before this skill is ever invoked.

## Step 1 — check for stub signals before drafting anything

Before treating a folder as ready, check it against `devstudio-author-myst-content`'s
complete-vs-stub signals: an empty analysis, a notebook that was never run, explicit
TODO markers in the log. **A live example from this pipeline's own testing**: the
folder used to validate `devstudio-read-from-google-drive` contained a log stating
"Did not get to the analysis... TODO: actually run the analysis" — a genuine stub, not
a candidate for drafting. If stub signals are present, say so and stop rather than
producing a hollow draft — this is a warning to surface, not a hard block the human
can't override, since they may have context this skill doesn't.

## Step 2 — inventory the folder, identify roles not filenames

Use `devstudio-read-from-google-drive`'s folder-scoped `search_files` plus its
role-based identification (Step 2 of that skill): don't look for `log.docx` by name —
identify the one Doc-type file as the log/narrative, the platemap by its tabular
content, the `.ipynb`s by extension/mimeType. Real experiment folders don't follow
template example names literally (confirmed during that skill's own testing: a log
turned up as a Doc named `lab-log`, a platemap as a `.tsv`).

## Step 3 — extract and preprocess the log content

Download the log Doc as real bytes and pandoc-convert, per
`devstudio-read-from-google-drive`'s Step 4:
```bash
pandoc input.docx -o content.md --extract-media=figures/
```
Then apply pandoc's notation fixups — verbatim from `ingest.md`:

- **Subscript**: `~N~` → `` {sub}`N` `` — except `~` used as "approximately" in prose
  (`~10 times`), which must NOT be converted.
- **Superscript**: `^N^` → `` {sup}`N` ``.
- **Underline**, two distinct cases: typographical (prose/captions) →
  `` {underline}`text` ``; a sequence-region marker spanning `<br>` tags with nested
  bold/italic → `<u>text</u>` (HTML, since it must survive line breaks the inline role
  can't cross).
- **Highlight**: `[text]{.mark}` → plain text + `<!-- REVIEW: highlighted in source -->`.
- **Grid table column boundaries**: pandoc word-wraps narrow Word-table columns across
  multiple lines per cell, making it easy to misparse and concatenate adjacent columns
  into one. Read each `|`-delimited column position independently across all wrapped
  lines; never merge content across `|` boundaries.

Note: since this stage's *output* is a plain Doc, not MyST, these fixups matter for
getting the eventual MyST conversion right later, but for now they mainly matter for
correctly parsing what the source table/prose actually said — apply them to your
understanding of the content even before the G(2)M stage formalizes the syntax.

## Step 4 — determine what's actually referenced (don't glob-copy the folder)

**Only artifacts explicitly referenced in the log carry forward.** Scan the converted
content for figure references, explicit platemap mentions, and data-file citations.
This is the same failure mode `migrate-devnote`'s `snags.md` warned about with resource
globs: a naive "copy everything in the experiment folder" would silently drag in
unreferenced material. Build an explicit referenced-files list from what the log
actually cites — not a directory listing.

## Step 5 — figure-provenance sidecar (corrected: asset completeness, not pattern choice)

**Revised understanding**: earlier guidance in this pipeline said to prefer static PNG
figures over notebook `glue` references because `glue` was "broken." That's an
overcorrection. A real, currently-functioning published DevNote
(`2026-garenne-pH-sensor`) uses `glue`-style figure references successfully. The actual
principle, per direct guidance: **a `glue`-style figure reference implies the full
research-asset chain — raw data, platemap, the analysis notebook — must genuinely be
present in the project.** It works when that chain is intact; it breaks when it isn't
(the likely explanation for the genuinely-broken cases seen elsewhere in the archive,
which were migrated content, not freshly-authored — migration may not have preserved
the full asset chain a glue reference depends on). DevStudio produces fresh content with
an intact chain by construction, so this specific risk is lower here than it looked.

**What this skill should actually verify**, regardless of which figure pattern gets
used downstream: for each figure carried forward, confirm its full backing chain is
present — the source notebook, the platemap it consumed, and the raw instrument data —
not just the image file. Record this in the manifest:
```json
{
  "figures": [
    {
      "filename": "kinetics-normalized.png",
      "source_notebook": "experiments/20260904-degfp-liposome/analysis.ipynb",
      "source_cell_or_section": "Cell 12 — normalized kinetics plot",
      "platemap": "platemap.tsv",
      "asset_chain_complete": true,
      "extraction_method": "pandoc --extract-media (embedded in log Doc)"
    }
  ]
}
```
- If a figure was extracted directly from the log Doc via pandoc with no clear notebook
  link, set `asset_chain_complete: false` and flag `source_notebook` as
  `REVIEW: source notebook not identified — confirm with author`. Don't guess.
- If the notebook exists but its input platemap or raw data can't be confirmed present
  in the project, that's also `asset_chain_complete: false` — flag it, since this is
  precisely the gap that causes a figure to break regardless of which reference pattern
  gets used later.

**Purpose and lifespan, both narrow and specific**: this manifest exists solely so
`devstudio-devnote-g-to-devnote-m` can construct the actual MyST connections it needs to
make — figure labels, `{ref}`/`{numref}` cross-references, and a Resources-section entry
linking a results figure back to the platemap that produced it. Once that stage has used
it to build those connections into the MyST output, **the manifest itself is no longer
needed** — it does not travel further into `curvenote.yml` or beyond, and it is not part
of the DevNote content a TA reviews. It's a one-hop handoff artifact, not a persistent
provenance record.

## Step 6 — fidelity rules (absolute, verbatim from `ingest.md`)

These override all other instructions:

- **Narrative content**: never rewrite, paraphrase, expand, or add interpretive
  language. Punctuation normalization, synonym substitution, clause restructuring, and
  omission of qualifiers are all violations even when the meaning seems preserved. When
  in doubt, copy character-for-character. **Post-draft verbatim audit**: after drafting,
  do a sentence-by-sentence comparison of Results/Conclusions against the source — these
  sections are most prone to silent paraphrasing.
- **Parameter values**: never change a numeric value, unit, concentration, volume,
  temperature, wavelength, or duration. Missing/ambiguous → `—` plus a REVIEW flag.
  Exception: adding a clearly-implied, unambiguous unit (a time column header `T = 3`
  where all values are hours) is a permitted editorial improvement, not a violation.
- **Table structure**: may restructure to the six-column schema and separate conditions
  into tab-sets (conceptually now, literal tab-sets once G2M happens) — but never drop a
  column or row. A column that doesn't map to the standard schema is retained as-is.
- **Sequences**: reproduce DNA/RNA sequences in full, inline. Never substitute with a
  pointer to Benchling or any external resource — the DevNote must be self-contained.
- **Missing sections**: if the source lacks a required section, insert
  `REVIEW: [section] not present in source — add before publishing` — do not author
  one. Section reordering is permitted, flagged: `<!-- REORDERED: moved from "[original
  position]" -->`.
- **Section naming — target common archive practice, not the blank Template's own
  labels.** Confirmed against a real published DevNote (`2026-garenne-pH-sensor`): the
  Template's `Bill of materials` and `Results and Observations` are published as
  `Reagents` and `Results`; `Design` and `Files to include` don't survive to publish at
  all in that real example. Per direct guidance: prefer whatever's common practice in
  the archive, and be consistent — so draft directly toward these real section names
  rather than the Template's, to save `devstudio-devnote-g-to-devnote-m` a remapping
  step. Renaming a source section to match is flagged:
  `<!-- RENAMED: "[original]" → "[target name]" -->`.
- **Uncertainty markers (`??`, informal "not sure" notes) may appear at this G stage —
  that's expected, not an error.** But per direct guidance: **every such marker must be
  resolved or explicitly flagged by the time content reaches DevNote(M)** — never
  silently dropped. (A real published DevNote was found to have simply deleted an
  unresolved `??`-marked table rather than flagging it — that's the wrong precedent,
  not the convention to follow. `devstudio-devnote-g-to-devnote-m` should treat any
  surviving `??`/uncertainty marker as a hard stop requiring human resolution.)

## Step 7 — construct verification

If the draft names a specific DNA construct in a composition-table row, invoke
`devstudio-verify-dna-constructs` before finalizing — don't let an unverified
construct↔file identity claim land in a draft, even a draft still pending human review.

## Step 8 — write the draft

Use `devstudio-write-to-google-drive`'s native path (this is exactly the "human will
comment on it" case that skill defaults to native for) to land the draft as a Google Doc
in the DevNote directory, alongside the figure-provenance manifest.

## Do not (verbatim from `ingest.md`)

- Invent scientific content not present in the source.
- Rewrite results to sound more significant than the source states.
- Fill in missing concentration values by inference.
- Remove negative or inconclusive results.
- Combine content from multiple experiments into a single claim unless the source does.
- Author a section that doesn't exist in the source — REVIEW flag instead.
- Drop table columns because they don't fit the standard schema.
- Silently rename section headings — always flag the rename.

## Human review checklist (adapted from `ingest.md`)

- [ ] Spot-check Results/Conclusions prose word-for-word against the source.
- [ ] Fill in all `REVIEW:` flagged fields.
- [ ] Rename extracted figures from `imageN.png` to descriptive names.
- [ ] Verify composition-table values are correct before this goes further.
- [ ] Confirm the figure-provenance manifest's notebook/platemap links are accurate,
      not just present.
- [ ] Check the Specification/Composition content is complete enough to reproduce
      the experiment.

## What this skill does not do

- Does not produce MyST syntax, frontmatter YAML, or assign a final id/uuid — that's
  `devstudio-devnote-g-to-devnote-m`, using `devstudio-author-myst-content`'s
  conventions once this draft is reviewed.
- Does not generate `curvenote.yml`/`base.yml` or run venue submission checks — a
  separate downstream skill (`submit.md` uploaded as reference).
- Does not decide an experiment is "done" — that's a human call made before invocation.
- Not yet validated against a real, actually-complete experiment folder — the one real
  folder tested so far (during `devstudio-read-from-google-drive`'s validation) turned
  out to be a stub, which is a real negative-test case (Step 1 should catch it) but not
  a positive one. Needs a real complete experiment to validate Steps 3–8.
