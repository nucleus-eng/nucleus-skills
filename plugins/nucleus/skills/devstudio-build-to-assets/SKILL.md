---
name: devstudio-build-to-assets
description: Convert a build file (xlsx with one sheet per condition) into a Nucleus-compatible platemap CSV — recommended format with per-component concentration and volume columns, Well column left empty for the experimenter to fill after plating. Run before an experiment or before devstudio-log-to-devnote-g.
---

# devstudio-build-to-assets

One job: read a build file and produce a Nucleus-compatible platemap CSV.

## Input

An `.xlsx` build file in the tetR-module format: one sheet per condition, header row
containing `Component`, `Input concentration`, `Unit`, `Final concentration`, `Unit`,
`Volume for one reaction [µL]`. A total volume row appears below the last component row.

## Step 1 — read the build file

Download the `.xlsx` from Drive using `devstudio-read-from-google-drive`. Parse with
`openpyxl` (data_only=True to get computed values, not formulas).

For each sheet:
1. Skip sheets named `platemap` or that are empty.
2. Find the header row: the row whose first non-null cell contains `Component`
   (case-insensitive). Everything above is metadata; everything below is data.
3. Extract component rows until the first row whose first cell contains `Total`
   (case-insensitive) — that row holds the total reaction volume; stop there.

## Step 2 — prompt for replicates

```
Found [N] conditions: [list sheet names]
Rxn volume: [N] µL (from build file)

How many replicates per condition? (1–3)
```

Wait for the response. Accept 1, 2, or 3.

## Step 3 — hand off to build-platemap

Pass the extracted conditions to `build-platemap`, which owns layout and column
conventions. Provide:

- **Conditions**: one entry per sheet — name, per-component final concentrations and
  volumes, total reaction volume
- **Replicate count**: from Step 2
- **Derived metadata**: Date (from filename prefix or clock), Experiment (filename slug)

`build-platemap` handles well IDs, column naming (`[<Component>] (<unit>)`,
`<Component> Vol (uL)`), the provenance YAML sidecar, and `check-platemap.py`.

Write the output CSV to the log folder in Drive using `devstudio-write-to-google-drive`
once `build-platemap` produces it.
