---
name: devstudio-check-platemap
description: Check the platemap files in a DevStudio DevNote before its pull request is marked ready. Runs build-platemap's check-platemap.py on each one, then reads the findings against main.md. Use after devstudio-assemble-devnote-assets has put the assets in the tree, when a platemap comes back from the Drive, or when a TA asks whether a platemap is safe to merge with plate reader data. Produces a findings list, and a labeled admonition in main.md for each finding a person must answer. It never edits a platemap.
invokes:
  - devstudio-read-from-google-drive   # step 1: fetch a Sheet as CSV
---

# devstudio-check-platemap

A script does the checking. This skill runs it and then reads what it found.

`build-platemap` owns the checker, the column rules and the three finding
levels. Read its section 6 first. Do not restate any of it here.

## Step 1 — find the platemaps

List the CSV and TSV files under `experiments/` that `main.md` points at, or
that sit beside the log it came from. Then open the first rows of each one.

A platemap has a `Well` column. Skip any file without one:

- `build-composition-*.csv` is a composition table. It is not a platemap.
- A grid of numbers under well letters is plate reader output.

Do not decide by file name. On 2026-10-11 a file called `PLA-CPR-CPRG.csv` in
`devnote-op-20261001-luv-gel-pla` held absorbance readings, and the checker
reported five blocking findings against it. Say which files you skipped and why.

If the only copy is a Google Sheet, fetch it through
`devstudio-read-from-google-drive` and export the one tab as CSV. Do not read
it through a native conversion. A conversion can turn a number into text and
nothing reports it.

> **INVOKE** `devstudio-read-from-google-drive` — fetch the platemap as raw CSV bytes

If you found no platemap, say so. That is a finding, not a pass.

## Step 2 — run the checker

```bash
python3 <plugin>/skills/build-platemap/scripts/check-platemap.py <file> \
  --instrument <platereader|microscope> --plate <96|384>
```

Take the instrument and plate size from `main.md`. If it does not say, ask.
Add `--provenance <file>.provenance.yaml` when that sidecar sits beside the file.

Exit code 0 means clean, 1 means findings, 2 means the check could not run.
**Exit 2 is not a pass.** Report it as a failure. Record the line the checker
prints for the file, for example `9 wells, 15 columns`, so a clean result shows
what it read. A clean result over zero wells is not clean.

## Step 3 — read the findings against `main.md`

Ask three questions. Do not add more.

1. **Is this a platemap at all?** A file that fails on every required column
   is usually not one. Drop it from the list and say why. Do not repair it.
2. **Does each warning fit the design?** An edge-well warning on a small
   layout the log chose on purpose is a note. If the log does not say it was
   chosen, ask the author. For a missing `Rxn Volume (uL)`: if the build file
   or `build-composition-*.csv` gives the reaction volume, name that source in
   the finding. Do not add the column.
3. **Does the platemap agree with `main.md`?** Compare, and do not recompute:
   - `Date` and `Experiment` against the experiment folder name.
   - Every well or condition `main.md` names, against the `Well` and `Name` columns.
   - The concentrations and units in the composition table, against the
     composition columns. Report a difference. Do not pick a side.
   - If `main.md` uses `{platemap}`: each name in `:fields:` must match a
     column header exactly. The plugin logs an unknown name and skips it, so a
     misspelled name drops out of the hover text with no build error.

## Step 4 — report

Give a table: file, level, finding, and who must answer.

For each finding that needs the author or a TA, add one admonition in
`main.md` beside the platemap's own table or directive. Name it
`flags-platemap-<experiment>-<n>`. A person closes it by answering it, as for
any other gap in `devstudio-devnote-g-to-devnote-m`. This skill never wraps
one in a comment itself.

Do not edit the platemap, its sidecar or any composition table. A change to
the data is a human's decision.

## What this skill does not do

- It does not lay out or rebuild a platemap. That is `build-platemap`.
- It does not check a platemap against the CDK's own loader. The checker
  applies the CDK's requirements; a clean run is not a merge test.
- It does not fill missing fields from an inventory list. That direction is
  noted in `devstudio-verify-dna-constructs` and is still deferred.
- It is not a CI gate. It needs the files and a person to read them.
