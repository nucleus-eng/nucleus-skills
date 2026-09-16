---
name: devstudio-build-to-composition
description: Read a build file (xlsx, one sheet per condition) and produce a merged composition table as build-composition.csv — the composition schema with one volume column per condition. Use before devstudio-log-to-devnote-g, which reads the sidecar instead of reconstructing composition from log prose. Takes no user input.
---

# devstudio-build-to-composition

One job: read a build file and produce a merged composition table.

## Output format

The composition-table schema — the six columns, `—` for missing values, and the rule
that a column is never dropped to make a source table fit — is owned by
`devstudio-author-myst-content`. This skill produces that schema with the per-condition
volume columns appended:

```
<six-column schema> | [Condition A] [µL] | [Condition B] [µL] | ...
```

Each condition (sheet) in the build file becomes one volume column, headed by the
sheet name with ` [µL]` appended.

**One deliberate divergence, and what it tracks:** the totals row is rendered bold
at the G stage, where `devstudio-author-myst-content` specifies plain text. That rule
governs the MyST table in DevNote(M); the G stage is a Google Doc table, where bold is
how a totals row reads as a totals row. `devstudio-devnote-g-to-devnote-m` drops the
bold on conversion. If it stops doing so, this divergence is the thing to remove —
not to copy forward.

## Step 1 — read the build file

The build file format and the parse are owned by
[`references/build-file-format.md`](../../references/build-file-format.md).
Follow it — including how it says to flag a deviation rather than repair one.

This skill needs, per condition: the condition name, each component's stock and final
concentration with units, its per-reaction volume, and the total reaction volume.

## Step 2 — merge conditions

Align all sheets on the Component column. If a component appears in some conditions
but not others, include it in every column and write `0` for volume in conditions
where it is absent — do not silently drop the row.

Where Stock Conc. or Final Conc. differs across conditions for the same component
(e.g. DNA prep at 231 / 155 / 115 ng/µL across three conditions), write the values
slash-separated in the shared column: `231 / 155 / 115`. Use the same slash-separated
form for Final Conc. where it varies. A slash-separated value is how a variable
component announces itself; report each one to the user when the sidecar is written.

Where a component has no concentration at all (e.g. Water), all four concentration
cells take the missing-value marker from the schema owner.

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
