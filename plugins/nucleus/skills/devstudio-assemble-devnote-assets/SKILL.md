# devstudio-assemble-devnote-assets

## Provenance

Staging skill in the `devstudio` namespace. Fills the gap between
`devstudio-devnote-g-to-devnote-m` (which writes the MyST structure) and a future
`devstudio-submit-to-github` skill (which opens the archive PR). This skill downloads
the supporting files that make the devnote buildable locally and on curvenote.

## Invocation model

Run after G→M has produced a complete `main.md` and `curvenote.yml`. Point it at the
target devnote directory. It reads those files to discover what needs to be fetched,
downloads what it can, updates `curvenote.yml`, and reports everything it could not
resolve.

```
devstudio-assemble-devnote-assets
Target: /path/to/devnotes/devnote-sy-20251104-20251107/
```

## What this skill downloads

### Required — notebooks (blocks curvenote build without these)

Notebooks must be present at the paths declared in `curvenote.yml`'s `toc:` list
before `curvenote check` or `curvenote submit` can resolve quarto-label figure
references. The toc entries are commented out by G→M with inline Colab/Drive URLs;
this skill downloads each one and uncomments its entry.

**How to find them**: read `curvenote.yml` and extract every commented-out toc line
that contains a URL in the format:
```yaml
# - file: experiments/YYYYMMDD-slug/Analysis.ipynb  # https://colab.research.google.com/drive/<ID>
# - file: experiments/YYYYMMDD-slug/notebook.ipynb  # https://drive.google.com/file/d/<ID>/view
```

Parse the Drive ID:
- Colab URL `https://colab.research.google.com/drive/<ID>` → ID is the path segment after `/drive/`
- Drive file URL `https://drive.google.com/file/d/<ID>/view` → ID is between `/d/` and `/view`

Download each notebook with `download_file_content` using `exportMimeType: application/json`
(Colab notebooks are Google-native files; `application/json` exports the raw `.ipynb`
JSON). Decode the base64 result and write to the `file:` path. Create the subdirectory
if it does not already exist.

After a successful download, uncomment the toc line in `curvenote.yml`:
```yaml
# Before:
# - file: experiments/20251104-NucleusPURE_deGFP/Analysis.ipynb  # https://colab.research.google.com/drive/1JpkX...

# After:
- file: experiments/20251104-NucleusPURE_deGFP/Analysis.ipynb  # https://colab.research.google.com/drive/1JpkX...
```

### Optional — platemaps (needed only if notebook must re-execute)

If a notebook's cell outputs are already saved (the common case for Colab notebooks),
curvenote renders figures from those saved outputs without re-executing. In that case,
platemaps and raw data files are not needed locally.

Download platemaps only when the TA explicitly requests it or when a notebook download
succeeds but its outputs are empty (indicating re-execution will be needed). Platemap
Drive URLs appear in main.md as:
```
Platemap: [filename.csv](https://drive.google.com/file/d/<ID>/view)
```

Download with `download_file_content` (no exportMimeType — CSV is not a Google-native
file), decode base64, write to the same `experiments/YYYYMMDD-slug/` directory as the
notebook.

### Required — raw instrument data files (blocks notebook re-execution without these)

Raw data files (`.txt`, `.parquet`, etc.) must be present alongside the notebook so
that the notebook can be re-executed. Even when a notebook has saved outputs (meaning
curvenote can build the site without running cells), the devnote must be self-contained:
a reader who downloads it and runs the notebook locally will get file-not-found errors
if data files are absent.

Find raw data Drive URLs in `main.md` — they appear on the same `Platemap: ... | Raw
data: ... | Analysis: ...` line as the platemap, either as hyperlinks or in comments.
Download each with `download_file_content` (no `exportMimeType` — these are non-Google-
native files; the connector exports them as-is). Write to the same `experiments/<slug>/`
directory as the notebook, keeping the filename the notebook uses to load the file (scan
the notebook for `load_platereader_data`, `read_csv`, `open()`, or equivalent calls to
confirm the expected filename).

If a raw data file cannot be found on Drive or its Drive URL is not recorded in
`main.md`, flag it:
```
⚠️ Raw data file not found — notebook at experiments/<slug>/Analysis.ipynb references
<filename> but no Drive URL is available. Obtain from the author and place at
experiments/<slug>/<filename>.
```

### Not needed — seqviz GitHub references

`:::{seqviz} https://github.com/nucleus-eng/DNA/blob/main/...` directives resolve
at build time. No local copy required.

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

1. **Read `curvenote.yml`** — collect all commented-out toc entries with URLs.
2. **Read `main.md`** — collect platemap and raw data Drive URLs from experiment header lines.
3. **For each notebook URL**:
   - Extract Drive ID.
   - Call `download_file_content` with `exportMimeType: application/json`.
   - Decode base64 content.
   - Create `experiments/<slug>/` directory if needed.
   - Write decoded content to the `file:` path.
   - Verify the written file is valid JSON (`.ipynb` is JSON).
   - Check whether cell outputs are present — if all code cells have empty `outputs`,
     flag: `⚠️ notebook has no saved outputs — re-execution will be needed; consider
     downloading platemap and data files`.
   - Uncomment the toc entry in `curvenote.yml`.
4. **For each raw data file URL**:
   - Extract Drive ID.
   - Call `download_file_content` (no `exportMimeType`).
   - Decode base64 content.
   - Write to `experiments/<slug>/<filename>` — filename must match what the notebook loads.
5. **For each platemap URL** (if not already local):
   - Same as raw data — download and write to `experiments/<slug>/` directory.
6. **Report**:
   - ✅ Downloaded: list each file path and source URL.
   - ⚠️ Empty outputs: list notebooks with no saved cell outputs.
   - ❌ Failed: list any file that could not be fetched, with the error.
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

- **401/403 on Drive download**: the file may not be shared. Surface the URL, ask
  the TA to check sharing permissions on the Drive file.
- **File not valid JSON after decode**: notebook may have exported in wrong format.
  Try `download_file_content` without `exportMimeType` as a fallback (some Drive
  files export as plain text correctly without an explicit type).
- **Experiments directory doesn't match slug**: create it; log the creation so the TA
  can verify the directory name is correct.

## What this skill does not do

- Does not commit to GitHub — TA-mediated handoff only.
- Does not run `devstudio-verify-dna-constructs` — flag it as a REVIEW item.
- Does not decide which notebooks are needed — it downloads everything declared in
  the `curvenote.yml` toc comments.
