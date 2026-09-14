# devstudio-assemble-devnote-assets

## Provenance

Staging skill in the `devstudio` namespace. Fills the gap between
`devstudio-devnote-g-to-devnote-m` (which writes the MyST structure) and a future
`devstudio-submit-to-github` skill (which opens the archive PR). This skill downloads
the supporting files that make the devnote buildable locally and on curvenote.

## Ground truth and source hierarchy

The **DevNote(G) Google Doc** is the single source of truth for what assets belong to
each experiment. Its structured figure-provenance lines (written by
`devstudio-log-to-devnote-g`) name the notebook, platemap, and raw data file for every
figure:

```
[`fig:kinetics-exp2`, notebook:Analysis.ipynb, platemap:20251107-NucleusPURE-deGFP-MgSweep-platemap.csv, data source:20251107-cytation3-pure-timecourse-gfp-MgSweep-biotek-cdk.txt, caption: (...)]
```

The **manifest.json** (written alongside the G doc by `devstudio-log-to-devnote-g`) is
the structured, machine-readable cache of those same lines. Use it when present — it is
faster than re-parsing the G doc. If the G doc was edited after the manifest was
generated (filenames corrected, a figure added), re-read the G doc and treat it as
authoritative over the manifest.

**`main.md` is not a source for asset discovery.** The `<!-- REVIEW: assets — ... -->`
comment blocks in main.md contain local file paths (not Drive URLs) and serve as a
human audit trail that is stripped before submission. Never parse main.md to find Drive
URLs or determine which files to download.

## Invocation model

Run after G→M has produced a complete `main.md` and `curvenote.yml`. Provide:
- The target devnote directory
- The DevNote(G) Google Doc URL (used if manifest.json is absent or outdated)
- The sf-node experiment Drive folder (scoped to `san-francisco-node/` only — never
  access other Drive locations)

```
devstudio-assemble-devnote-assets
Target: /path/to/devnotes/devnote-sy-20251104-20251107/
DevNote(G): https://docs.google.com/document/d/<ID>/edit
SF-Node folder ID: 1d2QuOtPDdSxuF1z7NlRt-MtJdNKgNI7s
```

## What this skill downloads

### Notebooks — required (blocks curvenote build)

Notebooks must be present at the paths declared in `curvenote.yml`'s `toc:` list.
The toc entries are commented out by G→M with inline Colab/Drive URLs; this skill
downloads each one and uncomments its entry.

**How to find them**: read `curvenote.yml` and extract every commented-out toc line
containing a URL:
```yaml
# - file: experiments/YYYYMMDD-slug/Analysis.ipynb  # https://colab.research.google.com/drive/<ID>
# - file: experiments/YYYYMMDD-slug/notebook.ipynb  # https://drive.google.com/file/d/<ID>/view
```

Parse the Drive ID:
- Colab URL `https://colab.research.google.com/drive/<ID>` → segment after `/drive/`
- Drive file URL `https://drive.google.com/file/d/<ID>/view` → segment between `/d/` and `/view`

Download each notebook with `download_file_content` using `exportMimeType: application/json`
(Colab notebooks are Google-native; `application/json` exports the raw `.ipynb` JSON).
Decode base64, create the subdirectory if needed, write to the `file:` path.

After a successful download, uncomment the toc entry in `curvenote.yml`.

### Platemaps and raw instrument data — required for self-contained devnote

Even when a notebook has saved cell outputs (meaning curvenote can render without
re-executing), the devnote must be self-contained. A reader who downloads it and runs
the notebook locally will get file-not-found errors if data files are absent.

**How to find filenames**: read `manifest.json` in the target devnote directory. Each
figure entry has `platemap` and `data_source` fields naming the files:

```json
{
  "filename": "figures/kinetics.png",
  "platemap": "20251107-NucleusPURE-deGFP-MgSweep-platemap.csv",
  "data_source": "20251107-cytation3-pure-timecourse-gfp-MgSweep-biotek-cdk.txt",
  "source_notebook": "Analysis.ipynb",
  "section_context": "Experiment 2 — Mg²⁺ sweep"
}
```

If `manifest.json` is absent, read the DevNote(G) Google Doc and parse figure-provenance
lines directly:
```
[`fig:label`, notebook:Analysis.ipynb, platemap:filename.csv, data source:filename.txt, caption: (...)]
```

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
2. **Read `manifest.json`** in the target devnote directory — collect platemap and raw
   data filenames per figure. If absent, read the DevNote(G) Google Doc and parse
   figure-provenance lines directly.
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
the file resolves at build time. If `main.md` references a local `plasmids/` path,
check `nucleus-eng/DNA` for a filename match (fuzzy — tolerate `.gb` vs `.gbk`
extension differences and minor casing). If found, surface the GitHub URL and ask the
TA to confirm, then switch the directive to the GitHub URL pattern (preferred). If not
found, flag that the `.gb`/`.gbk` file must be placed at `plasmids/<filename>` manually
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
- Does not parse `main.md` to discover asset Drive URLs — main.md is derivative.
- Does not decide which notebooks are needed — downloads everything in `curvenote.yml`
  toc comments.
