---
name: devstudio-build-to-composition
description: Read a build file (xlsx, one sheet per condition) and produce a merged composition table — conditions as volume columns, shared Stock and Final Conc. columns — as an HTML table for Google Doc embedding and a JSON sidecar for devstudio-log-to-devnote-g. No user interaction required. Run before devstudio-log-to-devnote-g.
---

# devstudio-build-to-composition

One job: read a build file and produce a merged composition table.

## Output format

The target is a table with this column structure:

```
Component | Stock Conc. | Unit | Final Conc. | Unit | [Condition A] [µL] | [Condition B] [µL] | ...
```

Each condition (sheet) in the build file becomes one volume column. The condition
name is the column header; `[µL]` is appended. Components with no Stock or Final
concentration (e.g. Water) receive `—` in those cells. The Totals row is the last
row, bold.

This matches the DevNote(M) six-column merged schema documented in
`devstudio-author-myst-content` and visible in the cytosol documentation tab-set.

## Step 1 — read the build file

Download the `.xlsx` from Drive using `devstudio-read-from-google-drive`. Parse with
`openpyxl` (data_only=True).

For each sheet, skip sheets named `platemap` or that are empty. Find the header row
(first cell containing `Component`, case-insensitive). Extract component rows until
the `Total` row. Record:
- Component name (col 1)
- Stock concentration and unit (cols 2–3)
- Final concentration and unit (cols 4–5)
- Volume per reaction in µL (last non-null numeric column)
- Total reaction volume (from the Total row, last non-null numeric column)

## Step 2 — merge conditions

Align all sheets on the Component column. If a component appears in some conditions
but not others, include it in every column and write `0` for volume in conditions
where it is absent — do not silently drop the row.

Where Stock Conc. or Final Conc. differs across conditions for the same component
(e.g. DNA prep at 231 / 155 / 115 ng/µL across three conditions), write the values
slash-separated in the shared column: `231 / 155 / 115`. Use the same slash-separated
form for Final Conc. where it varies. Flag this in the sidecar `warnings` array —
slash-separated values signal a variable component.

Where Stock Conc. and Final Conc. are both absent for a component (e.g. Water),
write `—` in both the Stock Conc. and Final Conc. cells, and both unit cells.

## Step 3 — write CSV sidecar

Write `build-composition.csv` in the log folder via `devstudio-write-to-google-drive`
(raw file). This is what `devstudio-log-to-devnote-g` reads to insert the composition
table into the DevNote(G).

Column order: `Component`, `Stock Conc.`, `Unit`, `Final Conc.`, `Unit`, then one
column per condition named `[condition name] [µL]`. Last row is `Total [µL]`.

Example (tetR build file, 3 conditions):

```
Component,Stock Conc.,Unit,Final Conc.,Unit,Unregulated [µL],Repressed 500 nM [µL],Induced 500 nM [µL]
Smix,3.33,×,1,×,9.009,9.009,9.009
Pmix,15,mg/mL,1.8,mg/mL,3.6,3.6,3.6
tetR,10000,nM,500,nM,0,1.5,1.5
Alexa Fluor 647,—,—,—,—,0.1,0.1,0.1
Water,—,—,—,—,4.747,3.247,2.497
Total [µL],,,,,30,30,30
```

## Integration with devstudio-log-to-devnote-g

`devstudio-log-to-devnote-g` checks for `build-composition.csv` in each log folder.

- **Found**: read the CSV row by row and render as an HTML `<table>` (Totals row in
  `<strong>`, `—` cells as em-dash) for insertion into the `# Methods` section of
  the DevNote(G).
- **Not found**: emit a blocking REVIEW flag — do not reconstruct from log prose.

## What this skill does not do

- Does not produce MyST syntax — `devstudio-devnote-g-to-devnote-m` converts the
  HTML table to a `:::{table}` block.
- Does not reformat to the three-column Docs schema — `devstudio-devnote-to-docs-g`
  handles that.
- Does not assign a figure label or caption — those are added by the G→M skill.
