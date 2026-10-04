---
name: devstudio-assemble-devnote-assets
description: Download the supporting files a DevNote(M) needs to build. These are notebooks, platemaps, raw instrument data, and DNA construct files. They come from the DevStudio Shared Drive into the devnote directory. What belongs to each figure is resolved from main.md's own figure-provenance lines, or from the manifest.json cache beside it. Invoked once a human reviews the links in main.md, and it hands off to devstudio-submit-to-github, which opens the draft archive PR. This is a staging-namespace (devstudio-) skill — see "Provenance" below before treating it as canonical.
---

# devstudio-assemble-devnote-assets

## Provenance

Staging skill in the `devstudio` namespace. Fills the gap between
`devstudio-devnote-g-to-devnote-m` (which writes the MyST structure) and a future
`devstudio-submit-to-github` skill (which opens the archive PR). This skill downloads
the supporting files that make the devnote buildable locally and on curvenote.

## Ground truth and source hierarchy

`main.md` is the single source of truth for what assets belong to each
experiment. Its structured figure-provenance lines, in the figure blocks
`devstudio-log-to-devnote-m` writes directly, name the notebook, platemap,
and raw data file for every figure. **The line format is owned by
[`references/devstudio-figure-provenance.md`](../../references/devstudio-figure-provenance.md)**.
Values are backtick-quoted. An unquoted variant does not match what
`devstudio-log-to-devnote-m` writes.

`manifest.json` stays, as a sidecar document beside `main.md`. It is a
cache, kept for debugging and for later review, and it tracks these eleven
fields per figure:

```
filename, pattern, cell_label, source_notebook, platemap, data_source,
zarr_url, section_context, asset_chain_complete, extraction_method, findings
```

`main.md` is authoritative over the sidecar when the two disagree, because
`main.md` is what a reviewer edits.

`main.md`'s REVIEW comment blocks for asset verification, where present,
still carry local file paths rather than Drive URLs, and still get stripped
before submission. That convention is unchanged.

## Invocation model

Run once `main.md` exists and carries figure-provenance lines, and a human
has reviewed those links. Provide:
- The target devnote directory, containing `main.md`
- The sf-node experiment Drive folder (scoped to `san-francisco-node/` only — never
  access other Drive locations)

The DevNote(G) Google Doc URL drops from the required inputs. There is no
longer a separate Doc this skill falls back to.

```
devstudio-assemble-devnote-assets
Target: /path/to/devnotes/devnote-sy-20251104-20251107/
SF-Node folder ID: 1d2QuOtPDdSxuF1z7NlRt-MtJdNKgNI7s
```

## What this skill downloads

### Notebooks — required (blocks curvenote build)

Notebooks must be present at the paths declared in `curvenote.yml`'s `toc:` list.
The toc entries are commented out by `devstudio-log-to-devnote-m` with
inline Colab or Drive URLs. This skill downloads each one and uncomments its
entry.

**How to find them**: read `curvenote.yml` and extract every commented-out toc line
carrying a URL. **The comment format is owned by [`references/devstudio-curvenote-toc.md`](../../references/devstudio-curvenote-toc.md)**, including why an entry stays
commented until its download succeeds.

Parse the Drive ID out of the URL per the extraction table in that reference.

Download each notebook with `download_file_content` using `exportMimeType: application/json`
(Colab notebooks are Google-native; `application/json` exports the raw `.ipynb` JSON).
Decode base64, create the subdirectory if needed, write to the `file:` path.

After a successful download, uncomment the toc entry in `curvenote.yml`.

### Platemaps and raw instrument data — required for self-contained devnote

Even when a notebook has saved cell outputs (meaning curvenote can render without
re-executing), the devnote must be self-contained. A reader who downloads it and runs
the notebook locally will get file-not-found errors if data files are absent.

**How to find filenames**: read the figure-provenance lines directly from
`main.md`. Each figure's line names the notebook, platemap, and raw data
file. All are filenames, never Drive URLs, and a field reads `none` when the
asset was not found. The line format is specified in
[`references/devstudio-figure-provenance.md`](../../references/devstudio-figure-provenance.md).

If `manifest.json` is present, you can read it as a faster path to the same
filenames. Prefer `main.md`'s own lines when the two disagree. `main.md` is
what a reviewer edits, and the manifest is not.

**How to get Drive IDs**: once you have the filename, search the sf-node Drive folder
for it by name using `search_files`. Scope the search to the experiment subfolder that
matches the slug (e.g., `20251107-NucleusPURE_deGFP_MgSweep`). Extract the Drive file
ID from the result.

**How to download**: call `download_file_content` with no `exportMimeType` (CSV and
instrument data files are non-Google-native; the connector exports them as-is). Decode
base64 and write to `experiments/<slug>/<filename>`. The filename must match what the
notebook uses to load the file — confirm by scanning the notebook for `read_csv`,
`load_platereader_data`, `open()`, or equivalent calls.

**If a file cannot be found on Drive**:
```
⚠️ Raw data file not found — notebook at experiments/<slug>/Analysis.ipynb references
<filename> but it could not be located in Drive. Obtain from the author and place at
experiments/<slug>/<filename>.
```

**Skip if already present locally** — if the file already exists at the target path,
do not re-download. Report it as already present.

### Not needed — seqviz GitHub references

`:::{seqviz} https://github.com/nucleus-eng/DNA/blob/main/...` directives resolve at
build time. No local copy required.

### Not needed — zarr microscopy data

`:::{anywidget}` Vizarr blocks reference zarr URLs from `data.nucleus.engineering` that
stream tiles client-side at render time. No local copy needed.

## Prerequisite — seqparse

The shared seqviz plugin at `../../plugins/seqviz/seqviz.mjs` requires `seqparse` to
be installed. Check once per run:

```bash
ls ../../plugins/seqviz/node_modules/seqparse 2>/dev/null || \
  (cd ../../plugins/seqviz && npm install seqparse)
```

If the `plugins/seqviz/` directory is missing `package.json`, run
`npm init -y && npm install seqparse` there first. This is a shared dependency — it
only needs to be installed once per clone, not once per devnote.

## Step-by-step

1. **Read `curvenote.yml`** — collect all commented-out toc entries with Drive/Colab URLs
   (notebooks only).
2. **Read the figure-provenance lines in `main.md`** — collect platemap and raw
   data filenames per figure. `manifest.json` in the same directory carries the
   same filenames and is faster to read. Prefer `main.md` when the two disagree.
3. **For each notebook**:
   - Extract Drive ID from the toc comment URL.
   - Call `download_file_content` with `exportMimeType: application/json`.
   - Decode base64, create `experiments/<slug>/` if needed, write to the `file:` path.
   - Verify the file is valid JSON.
   - Check whether cell outputs are present — if all code cells have empty `outputs`,
     flag: `⚠️ notebook has no saved outputs — re-execution will be needed`.
   - Uncomment the toc entry in `curvenote.yml`.
4. **For each platemap and raw data file** (from manifest or G doc):
   - Skip if already present locally.
   - Search Drive experiment folder for the filename using `search_files`.
   - Extract Drive ID from the result.
   - Call `download_file_content` (no `exportMimeType`).
   - Decode base64, write to `experiments/<slug>/<filename>`.
5. **Report**:
   - ✅ Downloaded: list each file and source Drive ID.
   - ✅ Already present: list files skipped because they existed locally.
   - ⚠️ Empty outputs: list notebooks with no saved cell outputs.
   - ❌ Failed: list files that could not be fetched, with the error.
   - Reminder: run `curvenote check` after assembly to confirm references resolve.

## DNA construct files

If `main.md` references a seqviz GitHub URL (`nucleus-eng/DNA`), no action is needed —
the file resolves at build time. If `main.md` references a local `dna/` path,
check `nucleus-eng/DNA` for a filename match (fuzzy — tolerate `.gb` vs `.gbk`
extension differences and minor casing). If found, surface the GitHub URL and ask the
TA to confirm, then switch the directive to the GitHub URL pattern (preferred). If not
found, flag that the `.gb`/`.gbk` file must be placed at `dna/<filename>` manually
and noted for future inclusion in `nucleus-eng/DNA`.

## Error handling

- **401/403 on Drive download**: file may not be shared. Surface the URL, ask the TA
  to check permissions.
- **File not found by name search**: filename in manifest may not match Drive filename
  exactly — try a fuzzy search (strip date prefix, tolerate underscores vs hyphens).
  If still not found, flag for manual retrieval.
- **File not valid JSON after decode**: notebook exported in wrong format — retry
  `download_file_content` without `exportMimeType` as a fallback.
- **Experiments directory doesn't match slug**: create it; log the creation so the TA
  can verify the directory name.

## What this skill does not do

- Does not commit to GitHub — TA-mediated handoff only.
- Does not run `devstudio-verify-dna-constructs` — flag it as a REVIEW item.
- Does not decide what belongs in a DevNote. `main.md`'s figure-provenance
  lines are the record of that, and this skill only fetches what they name.
- Does not decide which notebooks are needed — downloads everything in `curvenote.yml`
  toc comments.

## Hand off to `devstudio-submit-to-github`

Once every asset named in `main.md` is in the tree, hand off to
`devstudio-submit-to-github`. That skill opens the branch and opens its pull
request as a GitHub draft, against `main`.

Opening the pull request is all that is needed for a preview. It triggers
the existing `draft.yml` workflow, which posts a Curvenote preview link to
the pull request. Observed working against `devstudio-board`'s copy of that
workflow on 2026-10-03: its `on: pull_request` block names no `types:`, so
GitHub applies its default set, and a draft pull request fires `opened` in
the same way a ready one does.

The pull request opens here rather than at first cut so that the first
preview a reviewer reads renders its figures.
