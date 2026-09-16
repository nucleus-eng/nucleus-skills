---
name: devstudio-build-to-assets
description: Convert a build file (xlsx with one sheet per condition) into a Nucleus-compatible platemap CSV — recommended format with per-component concentration and volume columns, Well column left empty for the experimenter to fill after plating. Run before an experiment or before devstudio-log-to-devnote-g.
---

# devstudio-build-to-assets

One job: read a build file and produce a Nucleus-compatible platemap CSV.

## Step 1 — read the build file

The build file format and the parse are owned by
[`references/build-file-format.md`](../../references/build-file-format.md).
Follow it — including how it says to flag a deviation rather than repair one.

This skill needs, per condition: the condition name, each component's final
concentration and per-reaction volume, and the total reaction volume.

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

Everything downstream of that handoff — well IDs, per-component column naming, the
required and recommended columns, the provenance sidecar, `check-platemap.py` — is
`build-platemap`'s. Do not restate its conventions here; they have one owner and it
is not this skill.

Write the output CSV to the log folder in Drive using `devstudio-write-to-google-drive`
once `build-platemap` produces it.
