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

## Step 3 — generate the platemap

Produce one row per replicate per condition. Required columns first, then one pair of
columns per component:

**Required columns:**

| Column | Value |
|---|---|
| `Well` | *(empty — experimenter fills after plating)* |
| `Date` | from filename date prefix (`YYYYMMDD` → `YYYY-MM-DD`), or system clock |
| `Experiment` | filename slug (strip date prefix and extension) |
| `Name` | sheet name |
| `Type` | `[PLEASE FILL IN]` |
| `Rxn Volume (uL)` | total volume from build file |

**Per-component columns** (one pair per component, in the order they appear in the
build file):

| Column | Value |
|---|---|
| `[<Component>] (<Final unit>)` | Final concentration value |
| `<Component> Vol (uL)` | Volume per reaction |

Where Final concentration or unit is missing in the build file, write `—` for that
column value.

Well ID format: `A1` not `A01`.

## Step 4 — write and report

Write the CSV to the log folder in Drive using `devstudio-write-to-google-drive`.
Filename: `[date]-[experiment-slug]-platemap.csv`.

Report:
```
✓ [filename] written — [N] rows ([conditions] × [replicates] replicates)
  Well column is empty — fill in after plating.
  Type column is [PLEASE FILL IN] — mark controls before analysis.
```
