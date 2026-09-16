---
name: devstudio-log-to-devnote-g
description: Convert a human-selected set of one or more DevStudio Log folders (each holding a Log Google Doc, and where present a platemap, analysis notebooks, and raw instrument data) into a single draft DevNote as a native, commentable Google Doc — following Nucleus DevNote structure, synthesizing across the set when it spans a continuous narrative, with fidelity to source content and explicit flags for anything uncertain or missing. Use when a human selects the specific folder(s) they've deemed ready to draft into a DevNote. This is a staging-namespace (devstudio-) skill — see "Provenance" below before treating it as canonical.
invokes:
  - devstudio-read-from-google-drive   # steps 2, 3, 5: folder search, pandoc download, notebook inspection
  - devstudio-write-to-google-drive    # step 8: write the draft Doc and manifest
  - devstudio-verify-dna-constructs    # step 7: construct identity check before naming in draft
  - devstudio-author-myst-content      # step 1: complete-vs-stub signals
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

## Breaking changes

**Figure-provenance line format** (affects `devstudio-devnote-g-to-devnote-m`): the
format changed from a multi-line block to a single-line structured format (see Step 4).
The G→M skill handles both; new DevNote(G) docs always use the single-line format.

**`manifest.json` schema additions**: `asset_chain_complete` and `findings` fields were
added; older manifests without them are treated as `asset_chain_complete: false`.

## Step 1 — check for stub signals before drafting anything

> **INVOKE** `devstudio-author-myst-content` — read complete-vs-stub signals before treating the selected set as ready

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

> **INVOKE** `devstudio-read-from-google-drive` — folder-scoped `search_files` plus role-based file identification for each folder in the set

For each folder in the human-selected set, use `devstudio-read-from-google-drive`'s
folder-scoped `search_files` plus its role-based identification (Step 2 of that skill)
— don't look for `log.docx` by name, identify the one Doc-type file as the log/
narrative, the platemap by its tabular content, the `.ipynb`s by extension/mimeType.

**Issue the listings for all selected folders together, not one folder at a time.** The
listings do not depend on each other, and a six-folder set otherwise pays six round-trips
in series before any drafting starts. One listing per folder also types every file in it
— see that skill's Step 2 on why no follow-up metadata call is needed for a file that
arrived this way.

**Then synthesize, don't just concatenate.** When the set spans multiple dated logs
telling one continuous story (confirmed as the real shape during this pipeline's own
testing — six days of iterating on the same degradation-tag characterization,
referencing prior days' results directly: "It seems like... too little," "Therefore, we
try to..."), order chronologically and carry the narrative thread through — a later
entry's course-correction only makes sense in light of an earlier entry's finding. Don't
draft each folder's content as an isolated block.

**Date label cross-check** (loud and resilient — do not soften or skip):

Every asset filename that carries a date prefix must be checked against the experiment
folder's date. This is one of the most common and consequential mislabeling errors in
the DevStudio workflow — data from a later session filed under an earlier experiment
folder, or vice versa. Get this wrong and the DevNote links the wrong data to the
wrong experiment.

For every file in every asset subfolder, extract any leading date string
(`YYYYMMDD` or `YYYY-MM-DD`) and compare it to the experiment folder's date:
- **Match**: no flag needed.
- **Mismatch**: raise a blocking REVIEW flag — bold, at the top of the draft's
  REVIEW section, not buried inline:

  `⚠️ REVIEW (date mismatch): [filename] carries date [20251107] but experiment folder is [EXP-sy-20251104]. Confirm which is correct before proceeding — wrong date = wrong data linked to wrong experiment.`

Apply this check to every dated file: platemaps, raw data files, notebooks, and
analysis outputs. If more than one file mismatches, list all of them together at the
top rather than scattering individual flags through the doc.

Do not resolve the mismatch yourself. Do not assume the folder date or the filename
date is authoritative. Surface both values and stop — this is a human call.

Real experiment folders don't follow template example names literally (confirmed
during `devstudio-read-from-google-drive`'s own testing: a log turned up as a Doc named
`lab-log`, a platemap as a `.tsv`) — role-based identification, not filename matching,
applies to every folder in the set.

## Step 2.5 — produce Specification and Authors tables

Always place a Specification table and an Authors table at the top of the draft Google
Doc, matching the DevNote(G) template structure. These are required headers even when
the source Log doc has no equivalent tables (which is the common case for raw logs).

**Specification table** — write blank rows for any field not found in the source:

| Field | Value |
|---|---|
| Title | [value from source Specification table only, or `[PLEASE FILL IN]`] |
| Date | [value from source, or `[PLEASE FILL IN]`] |
| License | CERN-OHL-P-2.0; CC-BY-4.0 |

**Do not infer the title from document headings, folder names, or experiment labels.**
The title must come from the Specification table's Title row. If it is blank or absent,
use `[PLEASE FILL IN]`. You may add a comment noting candidate text found in the doc
(e.g. `<!-- Candidate title from first heading: "pOpen-deGFP expression in Nucleus
Cytosol and PURExpress" — QC to confirm -->`), but never adopt it silently as the title.
A wrong title in a DevNote is a serious error; the conservative default is always blank.

**Authors table** — write one blank row when no authors are found in the source:

| Name | ORCID | Email | Institution |
|---|---|---|---|
| [extracted, or `[PLEASE FILL IN]`] | `[PLEASE FILL IN]` | `[PLEASE FILL IN]` | `[PLEASE FILL IN]` |

Use `[PLEASE FILL IN]` (all-caps, in brackets) as the placeholder text in every blank
cell. Per Step 7.5, the draft is written as HTML — render these in red bold so they
appear red in the converted Google Doc automatically:
```html
<span style="color:#cc0000;font-weight:bold">[PLEASE FILL IN]</span>
```

Do not author or fabricate any field — a blank placeholder is always correct when the
value is unknown. License defaults to `CERN-OHL-P-2.0; CC-BY-4.0` (the template
default) without flagging, since this is a safe, policy-driven default.

## Step 3 — extract and preprocess the log content

> **INVOKE** `devstudio-read-from-google-drive` — Step 4: download the log Doc as `.docx` bytes for pandoc (`--extract-media` required)

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

Then apply pandoc's notation fixups. **These rules are owned here.** Earlier
revisions labelled them "verbatim from `ingest.md`"; the `ingest` skill in this
repo contains none of them, so the citation pointed at nothing and stopped
anyone asking where they came from. If they are ever needed by a second skill,
move them to a reference both point at rather than copying them.


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

**Inspect each notebook once, before presenting the figure list.** The prompt below
reports each figure's label status, so inspection has to precede it. One download and one
cell scan per notebook, recording both the `#| label:` tags and the file-loading calls —
Step 5 classifies figures from that record rather than re-reading the notebook, and the
data-file rule later in this step reads the loading calls from it.

**Figure selection is always explicit — do not carry all figures forward by default.**
After inventorying all figures found (embedded in doc + asset folder), present the list
to the user and ask which to include in the DevNote(G) before writing the draft.
Format the prompt as:

```
Found N figures across the selected log(s):
  1. figures/image1.png — embedded in doc, § "Results", notebook: Analysis.ipynb, label: fig:kinetics-exp1
  2. figures/image2.png — embedded in doc, § "Results", notebook: Analysis.ipynb (no #| label:)
  3. figures/Kinetics2.png — asset folder, notebook: Analysis.ipynb (cell 8, no #| label:)
  4. figures/endpoint.png — asset folder, notebook: Analysis.ipynb (cell 11, no #| label:)

Which figures should be included in the DevNote(G)? (reply with numbers, e.g. "1, 3")
```

Wait for the user's selection before proceeding. Only include the selected figures in
the draft and manifest. The question is not "is this figure cited in prose"
but "does this figure have an intact asset chain" — and the human decides whether to
include it, not the skill. Do not glob-copy the entire folder indiscriminately — but
do not require a prose citation that will never appear.

**How figures appear in the DevNote(G) draft**: each selected figure is represented
as a single structured line in the Results section, immediately after the prose it
belongs to:

**The line format is owned by [`references/devstudio-figure-provenance.md`](../../references/devstudio-figure-provenance.md)** — including the zarr-viewer and schematic
variants, and the rule that values are backtick-quoted. Write it exactly as that
reference gives it; `devstudio-devnote-g-to-devnote-m` parses the line, so an
unquoted variant does not round-trip.

Use it consistently — do not embed figures as `📷 Figure N:` blocks or
`<!-- Figure N -->` comments.

**Zarr URLs from `data.nucleus.engineering` are microscopy data references — always include them.**
Any URL matching `https://data.nucleus.engineering/**.zarr` found anywhere in a log doc
(inline text, comment, `@claude` instruction, or otherwise) is a legitimate microscopy
data reference left by the author — include a Vizarr viewer entry in the figure list
alongside any embedded microscopy image, recorded with `pattern: zarr-viewer` in the
manifest and as the zarr variant of the provenance line, immediately after the
microscopy figure line. Both forms are in the provenance reference.

Do not require the URL to appear outside an `@claude` comment — the author's intent to
include it is the signal, regardless of how they communicated it. Never fetch content
from the URL at this stage; just record it.

**Schematics and non-data figures belong in `general/`, not embedded in the Doc.**
A schematic (overview diagram, construct map, workflow illustration) is not a data
figure — it has no backing notebook, no platemap, no asset chain. These must be
pre-placed in the devnote's `general/` directory as named files (e.g.
`general/schematic-overview.png`, `general/construct-diagram.png`) before the G stage
is considered complete. In the DevNote(G) draft, reference the schematic by its
intended `general/` path rather than embedding the image in the Doc body — the
schematic variant of the provenance line, in the provenance reference.

**Why**: images embedded in the Google Doc body are invisible to `read_file_content`
and require pandoc extraction (a slow, fragile step). Pre-placed named files in
`general/` are immediately available to the G→M skill without extraction. If a
schematic is currently embedded in the Log Doc rather than pre-placed, flag it as
a blocking REVIEW item:

```
⚠️ REVIEW (schematic not pre-placed): A schematic figure was found embedded in
the Log Doc but has not been placed in general/. Extract it (via pandoc --extract-media
or manual download) and save it as general/schematic-<name>.png before proceeding —
the G→M skill cannot embed Doc-body images in main.md.
```

Do not attempt to pandoc-extract a schematic during this skill's run just to include
it — the extract step belongs to the author's preparation workflow, not the TA's
ingest workflow.

**Do not extract instrument metadata from raw data files into the draft.** Reader
serial numbers, measurement modes (Ex/Em wavelengths, gain settings), read intervals,
and similar instrument-level parameters belong in the linked raw data file — not in the
DevNote narrative. If an instrument parameter is directly stated in the Log Doc (not
inferred from a data file), it may be included. But do not open `.txt` data files and
copy their headers into the draft.

**Only link data files actually referenced by the analysis notebook.** The single
notebook pass above records the file-loading calls (`load_platereader_data`, `read_csv`,
`open()`, etc.) alongside the `#| label:` tags — take the filenames from that record
rather than re-opening the notebook. Only those files get linked in
the DevNote draft. Do not link every file found in the experiment folder — a raw output
file that the notebook doesn't load adds noise and may mislead reproducers.

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

**Figure pattern priority — always try quarto-label first.**

For every figure, inspect the associated notebook for `#| label:` tags before
classifying it as static-png. Notebook inspection is mandatory, not optional. The
pattern classification must reflect what's actually in the notebook, not a conservative
default:

| Priority | Pattern | When | MyST reference |
|---|---|---|---|
| 1 (default) | **`#\| label:` Quarto cell tag** | Notebook exists AND has a `#\| label:` tag on the output cell | `:::{figure} #<cell_label>` |
| 2 (fallback) | **Static PNG path** | Notebook exists but no `#\| label:` tag found — flag: `REVIEW: add #\| label: to cell [N] to enable quarto-label pattern` | `:::{figure} ./figures/name.png` |
| 3 (legacy) | **`#fig:` glue reference** | Older notebooks using the `glue` API | `:::{figure} #fig:name` |
| — | **No notebook** | No notebook found at all | static-png + `<!-- missing notebook -->` |

**How to inspect**:

> **INVOKE** `devstudio-read-from-google-drive` — download the notebook to scan for `#| label:` tags

Read from the single notebook pass taken in Step 4 — labels and file-loading calls are
recorded together there. **Download each notebook at most once per run**; a notebook
already inspected for this run is not re-fetched. Where no pass has been taken yet,
download via `devstudio-read-from-google-drive` and scan each code cell's source for
lines beginning with `#| label:`. The label value
is everything after `#| label: ` on that line. Map each labeled cell to its
corresponding figure by position (a plot cell's output is the figure produced by that
cell) or by filename match between `savefig(...)` calls and asset-folder PNG names.

When a notebook has `#| label:` tags, record `pattern: "quarto-label"` and the
`cell_label` value in the manifest. When it doesn't, record `pattern: "static-png"`
and raise the REVIEW flag asking the author to add them — quarto-label is strongly
preferred for all new DevNote content.

**`cell_label` is whatever string the notebook author put after `#\| label:` — not a
required format.** `20251212-kinetics` is a good label because it's descriptive and
sorts chronologically, not because a date-prefixed slug is enforced here. People are
inconsistent about naming conventions even when told to follow one, and a rejected or
silently-reformatted label is friction with no real payoff — MyST only needs the anchor
to resolve, which any string satisfies.

The actual risk flexibility trades for is **collision, not format** — two figures in
the same notebook sharing a `cell_label` produce an ambiguous MyST anchor. Check for
duplicate `cell_label` values **within the same notebook** and record a finding (not a
block) when found:
```
"findings": ["cell_label 'fig1' is used by two figures in this notebook — MyST anchors must be unique per notebook, disambiguate before DevNote(M)"]
```
A generic label like `fig1` is still valid; flag it only if it collides, not because
it's uninformative.

**Labels from different notebooks never collide with each other.** If notebook A has
`#| label: fig:kinetics` and notebook B (a separate file) also has `#| label: fig:kinetics`,
this is not a collision — MyST scopes labels to the file that defines them. Only flag
a collision when two cells within the *same* notebook share the same label string.
Do not assume two notebooks are identical in content just because they share a filename —
always inspect each notebook independently.

For figures extracted from the log Doc via pandoc (embedded inline), they arrive as
static PNGs. Record the section heading they appeared under as their narrative context.

Record each figure in `manifest.json` alongside the draft. **The schema is owned by
[`references/devstudio-figure-provenance.md`](../../references/devstudio-figure-provenance.md)**
— write every field it lists, including `data_source`, which
`devstudio-assemble-devnote-assets` needs to resolve the raw data file. An earlier
revision of this skill carried its own field list, omitted `data_source`, and so
produced manifests the assembly stage could not fully read.

That reference also owns the inline provenance line written into the Doc body
(Step 4) — the two are one record in two encodings, and a field added to either
has to be considered for the other.

Set `asset_chain_complete: false` when: (a) no notebook found for an embedded figure —
also flag inline in the draft with `<!-- missing notebook -->`, following the convention
used in `module-Clpxp-Cytosol/main.md` by the author themselves; (b) notebook exists
but platemap or raw data can't be confirmed present; (c) a `#fig:` glue reference has
no matching `label` in notebook cell metadata.

**Purpose and lifespan**: this manifest exists solely so `devstudio-devnote-g-to-devnote-m`
can construct the correct MyST figure references. Once consumed by that stage, it is
discarded — it is not DevNote content and does not travel further.

## Step 6 — fidelity rules (absolute; adapted from `ingest.md`, with divergences marked)

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
- **Table structure**: restructure to the canonical schemas below — but never drop a
  column or row. A column that doesn't map to the standard schema is retained as-is.

  **This diverges from `ingest`, which is not a copy of it.** `ingest/SKILL.md`
  instructs the opposite for an unmappable table: *"If source table uses
  non-standard columns (e.g. Bill of Materials format), reconstruct from protocol
  text rather than copying columns"*, and its own worked example records doing
  exactly that. The two skills disagree; which rule is right has not been ruled
  on. Retaining the column is the conservative choice at the G stage, where a
  human still reviews the draft — but do not read this as `ingest`'s rule.

  **Reagents/materials table** (7-column schema — note `ingest` specifies six;
  the seventh is `Link`, added for DevStudio and not inherited. Always produce,
  even if the source has no reagents section): always include this table under `# Materials and equipment`.
  If the source has reagent data, populate it. If the source has no reagents section,
  produce a blank row:
  ```
  | Reagent | Product Name | Manufacturer | Catalog No. | Price | Storage Conditions | Link |
  | [PLEASE FILL IN] | [PLEASE FILL IN] | [PLEASE FILL IN] | N/A | N/A | N/A | |
  ```
  For any column not present in the source: use `N/A` as the default value (do not
  flag missing values as REVIEW — `N/A` is an acceptable published state). The one
  exception: if Catalog No. is missing and the reagent is critical for reproducibility,
  add a REVIEW flag asking the author to locate it. Storage Conditions defaults to `N/A`
  when not specified — this is expected and does not require a flag.

  **Constructs/nucleic acids table** (always produce as a separate table under
  Materials, distinct from the reagents table):
  ```
  | Name | Sequence | Purpose |
  ```
  Link to the `.gb` file or GitHub URL in the Name column where available (confirmed by
  `devstudio-verify-dna-constructs`). If no constructs are present in the experiment,
  omit this table — do not produce an empty one.

  **Reaction composition tables** — sourced from the build file only:

  For each log folder, check for `build-composition.csv` (written by
  `devstudio-build-to-composition`). Composition tables do not live in log
  files — the build file is the only source.

  *Build sidecar found*: read the CSV row by row and render it as an HTML
  `<table>` for insertion into the `# Methods` section under the log's
  experiment heading. How that table presents — including the totals row,
  where the G stage diverges deliberately from the MyST rule in
  `devstudio-author-myst-content` — is stated once in
  `devstudio-build-to-composition`. Follow it there; do not re-decide it here.
  Emit a note:
  ```
  <!-- Composition table sourced from build file: [filename of .xlsx] -->
  ```

  *Build sidecar not found*: do not attempt to reconstruct from log prose.
  Emit a blocking REVIEW flag:
  ```
  ⚠️ REVIEW (missing build file): No build-composition.csv found for
  [log folder name]. Composition table cannot be produced. Run
  devstudio-build-to-composition on the build file for this experiment
  before proceeding.
  ```

  In a multi-log DevNote, each log folder has its own sidecar. Each table
  appears under its log's experiment heading. Do not merge tables from
  different log folders.
- **Sequences**: reproduce DNA/RNA sequences in full, inline. Never substitute with a
  pointer to Benchling or any external resource — the DevNote must be self-contained.
- **Required sections always present**: the following sections must always appear in
  the draft, sourced from the template, regardless of whether the source log contains
  them:
  - `# Overview` — blank with `[PLEASE FILL IN]` if absent in source
  - `# Materials and equipment` — always present (reagents table always generated, see above)
  - `# Protocol` — blank with `[PLEASE FILL IN]` if absent in source
  - `# Results and Observations` — blank with `[PLEASE FILL IN]` if absent in source
  - `# Notes` — always include, even if blank: `[PLEASE FILL IN]`
  - `# What's next` — always include, even if blank: `[PLEASE FILL IN]`

  If the source lacks a section, do not author one — insert `[PLEASE FILL IN]` as the
  body. Section reordering is permitted, flagged: `<!-- REORDERED: moved from "[original
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

> **INVOKE** `devstudio-verify-dna-constructs` — verify construct↔file identity before any construct name lands in a composition table row

If the draft names a specific DNA construct in a composition-table row, run this check
before finalizing — don't let an unverified construct↔file identity claim land in a
draft, even a draft still pending human review.

## Step 7.5 — draft formatting: links, red text, and HTML content

**Write the draft as HTML** (pass `contentMimeType: text/html` to `create_file`).
Drive auto-converts HTML to a native Google Doc, preserving inline styles including
text color. This is the mechanism for red author reminders — not a manual step.

**Red text rule**: every `[PLEASE FILL IN]` placeholder and every author-action
reminder must be wrapped in a red bold span:
```html
<span style="color:#cc0000;font-weight:bold">[PLEASE FILL IN]</span>
```
This applies to: Specification table blank cells, Authors table blank cells, blank
section bodies, and any inline REVIEW prompt addressed to the author. REVIEW flags
that are informational (e.g. flagging a data gap for QC awareness, not requiring
author action) may remain in black.

**Link display**: wherever a Drive file is referenced, use an HTML anchor with the
filename as display text — never show the raw Drive URL or file ID in the visible body:
```html
<a href="https://drive.google.com/file/d/FILE_ID/view">Analysis.ipynb</a>
```
For GitHub links, use the construct name as display text:
```html
<a href="https://github.com/nucleus-eng/DNA/blob/main/reporters/pOpen-deGFP.gbk">pOpen-deGFP.gbk</a>
```
File IDs belong in the manifest JSON only, not in the human-facing document.

This applies to: constructs table Name column, reagent Link column, data/platemap
references in figure captions, and any asset cross-references in the narrative.

## Step 8 — write the draft

> **INVOKE** `devstudio-write-to-google-drive` — native-Doc path: creates a commentable Google Doc in the DevNote directory and writes the figure-provenance manifest alongside it

Use `devstudio-write-to-google-drive`'s native path (this is exactly the "human will
comment on it" case that skill defaults to native for) to land the draft as a Google Doc
in the DevNote directory, alongside the figure-provenance manifest.

## Do not (extends `ingest.md`'s list; the last three are DevStudio's own)

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
- [ ] Confirm the licence. The Specification table defaults to
      `CERN-OHL-P-2.0; CC-BY-4.0` without flagging, which is a safe default and not
      a decision — a human still has to make the decision. `ingest` asks for the
      same confirmation; dropping it from this checklist meant nobody ever saw the
      licence question.

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
