---
name: devstudio-log-to-devnote-g
description: Convert a human-selected set of one or more DevStudio Log folders (each holding a Log Google Doc, and where present a platemap, analysis notebooks, and raw instrument data) into a single draft DevNote as a native, commentable Google Doc — following Nucleus DevNote structure, synthesizing across the set when it spans a continuous narrative, with fidelity to source content and explicit flags for anything uncertain or missing. Use when a human selects the specific folder(s) they've deemed ready to draft into a DevNote. This is a staging-namespace (devstudio-) skill — see "Provenance" below before treating it as canonical.
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
`devstudio-write-to-google-drive` — but **the invocation unit is a human-curated set of
one or more Log folders, not a single fixed folder.** Confirmed against the actual
DevStudio workflow: many logs accumulate during a session, and once something is ready
to become a DevNote, a participant selects a specific set ("directory x, y, and z") to
combine into one draft. No fixed granularity should be assumed — a selected folder might
represent one day, several days, or something else entirely; **the human's selection is
authoritative regardless of what it structurally represents.** This skill does not
crawl the Log directory looking for finished work, and does not decide what counts as
"done" or "one experiment" — both are human calls made before invocation.

(A related, explicitly out-of-scope need: an actual interface for TAs/participants to
make this selection and interact with Claude. Recognized as necessary, not designed
here — a separate concern from this skill's own logic.)

## Step 1 — check for stub signals before drafting anything

Before treating the *selected set* as ready, check each folder against
`devstudio-author-myst-content`'s complete-vs-stub signals: an empty analysis, a
notebook that was never run, explicit TODO markers in the log. **A live example from
this pipeline's own testing**: the folder used to validate `devstudio-read-from-google-
drive` contained a log stating "Did not get to the analysis... TODO: actually run the
analysis" — a genuine stub, not a candidate for drafting. If stub signals are present in
any selected folder, say so and stop rather than producing a hollow draft — this is a
warning to surface, not a hard block the human can't override, since they may have
context this skill doesn't.

**Critical: do not trust `contentSnippet` as a stub signal.** The Drive connector's
`search_files` returns a `contentSnippet` for text-bearing files, but a blank snippet
does not mean a blank file — this is a connector rendering artifact, confirmed against
real DevStudio logs (`LOG-sy-20251107` returned a blank snippet but contained a full,
well-structured experiment log). Always call `read_file_content` before concluding a
log is empty or a stub.

**Also check the set as a whole for asset-chain gaps, not just per-folder stub
signals.** A live example from this pipeline's own testing: six real, non-stub log
entries spanning six dated folders had **zero platemaps, notebooks, or raw instrument
data anywhere in any of the six folders**. One entry even contained an unmistakable
figure caption with no backing figure or data file anywhere in the project. This is not
a stub signal (the narrative content is real and substantial) — it's a distinct, equally
important gap: **flag missing supporting assets explicitly**, separately from
stub-checking, per direct guidance that this must be surfaced rather than silently
drafted around.

## Step 2 — inventory each selected folder, then synthesize across the set

For each folder in the human-selected set, use `devstudio-read-from-google-drive`'s
folder-scoped `search_files` plus its role-based identification (Step 2 of that skill)
— don't look for `log.docx` by name, identify the one Doc-type file as the log/
narrative, the platemap by its tabular content, the `.ipynb`s by extension/mimeType.

**Then synthesize, don't just concatenate.** When the set spans multiple dated logs
telling one continuous story (confirmed as the real shape during this pipeline's own
testing — six days of iterating on the same degradation-tag characterization,
referencing prior days' results directly: "It seems like... too little," "Therefore, we
try to..."), order chronologically and carry the narrative thread through — a later
entry's course-correction only makes sense in light of an earlier entry's finding. Don't
draft each folder's content as an isolated block.

Real experiment folders don't follow template example names literally (confirmed
during `devstudio-read-from-google-drive`'s own testing: a log turned up as a Doc named
`lab-log`, a platemap as a `.tsv`) — role-based identification, not filename matching,
applies to every folder in the set.

## Step 3 — extract and preprocess the log content

Download the log Doc as real bytes and pandoc-convert, per
`devstudio-read-from-google-drive`'s Step 4. **The `--extract-media` flag is required,
not optional** — confirmed against real DevStudio logs (`LOG-sy-20251104`,
`LOG-sy-20251107`): figures in these logs are embedded inline in the Google Doc, not
referenced as separate files. They are invisible to `read_file_content` and only
discoverable via pandoc extraction. `--extract-media` is the primary figure-discovery
mechanism for this pipeline:

```bash
pandoc input.docx -o content.md --extract-media=figures/
```

After extraction, `content.md` will contain `![](figures/imageN.png)` at the exact
position in the narrative where each figure appears — this is how you know both what
figures exist and where they sit in the document structure (which experiment section
they belong to).

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

## Step 4 — figure and asset inventory

**The "explicitly referenced in prose" rule from `ingest.md` does not apply to
DevStudio logs.** Confirmed against real logs from two different experimentalists:
neither writes explicit figure citations ("see Figure 1", "as shown below") in their
log narratives. Figures appear in two ways depending on log style:

- **Embedded inline in the Doc** (confirmed for `sy`-style logs): discovered via
  pandoc `--extract-media` in Step 3. The figure's position in `content.md` (which
  section heading it appears under) is its own reference — the figure *is* the
  observation record for that section.
- **In the asset subfolder** (confirmed for `yh`-style logs that lack inline figures):
  inventory the asset subfolder — platemap `.csv`, raw instrument data, analysis
  `.ipynb` — and treat all figures produced by the notebook as associated with this
  experiment.

**For all figures, regardless of source:** treat them as carrying forward unless the
human explicitly says otherwise. The question is not "is this figure cited in prose"
but "does this figure have an intact asset chain." Do not glob-copy the entire folder
indiscriminately — but do not require a prose citation that will never appear.

**The `<!-- missing notebook -->` convention**: if a figure exists (embedded or in the
asset folder) but no analysis notebook can be found in the project, flag it inline in
the draft as:
```
<!-- missing notebook -->
```
This is the convention used in the real published `module-Clpxp-Cytosol` DevNote by
the author themselves when a figure's backing notebook was absent — use it rather than
inventing a new flag.

## Step 5 — figure-provenance sidecar

**Three confirmed figure patterns in real DevStudio DevNotes** — record which pattern
each figure uses in the manifest, since `devstudio-devnote-g-to-devnote-m` needs this
to construct the correct MyST reference:

| Pattern | When to use | MyST reference | Asset chain requirement |
|---|---|---|---|
| **`#\| label:` Quarto cell tag** (preferred) | Notebook exists with a `#\| label:` tag on the plot cell | `:::{figure} #<cell_label>` | Notebook + platemap + raw data all present |
| **Static PNG path** | Pre-committed PNG, or notebook with saved output but no label tag | `:::{figure} ./figures/name.png` | PNG must exist; notebook optional but preferred |
| **`#fig:` glue reference** | Older notebooks using the `glue` API | `:::{figure} #fig:name` | Notebook with matching `label` in cell metadata — **currently broken in several archive DevNotes** where the glue tag is missing; prefer `#\| label:` for new content |

**`cell_label` is whatever string the notebook author put after `#\| label:` — not a
required format.** `20251212-kinetics` is a good label because it's descriptive and
sorts chronologically, not because a date-prefixed slug is enforced here. People are
inconsistent about naming conventions even when told to follow one, and a rejected or
silently-reformatted label is friction with no real payoff — MyST only needs the anchor
to resolve, which any string satisfies.

The actual risk flexibility trades for is **collision, not format** — two figures in
the same notebook sharing a `cell_label` produce an ambiguous MyST anchor. Check for
duplicate `cell_label` values within a `source_notebook` and record a finding (not a
block) when found:
```
"findings": ["cell_label 'fig1' is used by two figures in this notebook — MyST anchors must be unique per notebook, disambiguate before DevNote(M)"]
```
A generic label like `fig1` is still valid; flag it only if it collides, not because
it's uninformative.

For figures extracted from the log Doc via pandoc (embedded inline), they arrive as
static PNGs. Record the section heading they appeared under as their narrative context.

Record each figure in the manifest alongside the draft:
```json
{
  "figures": [
    {
      "filename": "figures/image1.png",
      "pattern": "embedded-in-doc",
      "section_context": "Experiment 1 — pOpen-deGFP expression in Nucleus Cytosol",
      "source_notebook": "REVIEW: source notebook not identified — confirm with author",
      "platemap": null,
      "asset_chain_complete": false,
      "extraction_method": "pandoc --extract-media"
    },
    {
      "filename": "figures/kinetics.png",
      "pattern": "quarto-label",
      "cell_label": "20251212-kinetics",
      "source_notebook": "20251212-ClpXP/20251212-analysis.ipynb",
      "platemap": "20251212-ClpXP/20251212-ClpXP.csv",
      "asset_chain_complete": true,
      "extraction_method": "notebook cell output"
    }
  ]
}
```

Set `asset_chain_complete: false` when: (a) no notebook found for an embedded figure —
also flag inline in the draft with `<!-- missing notebook -->`, following the convention
used in `module-Clpxp-Cytosol/main.md` by the author themselves; (b) notebook exists
but platemap or raw data can't be confirmed present; (c) a `#fig:` glue reference has
no matching `label` in notebook cell metadata.

**Purpose and lifespan**: this manifest exists solely so `devstudio-devnote-g-to-devnote-m`
can construct the correct MyST figure references. Once consumed by that stage, it is
discarded — it is not DevNote content and does not travel further.

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
- Steps 3–8 not yet validated end-to-end against a real complete experiment. Validated
  against real Drive folders to confirm the design decisions above (two experimentalist
  styles, figure patterns, asset-chain gaps, contentSnippet false negatives), but an
  actual draft has not yet been produced and checked against the target DevNote. That
  validation step is the next priority.
