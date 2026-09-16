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

## Step 3 — write HTML table

Produce an HTML table suitable for embedding in a Google Doc via `create_file` with
`contentMimeType: text/html`.

Rules:
- Header row: `<th>` cells, plain text.
- Condition column headers: append ` [µL]` to the sheet name.
- `—` cells: literal em-dash, not a hyphen.
- Totals row: `<strong>` wrapping every cell value.
- No inline styles beyond bold on the Totals row — Google Doc import handles
  table styling.

```html
<table>
  <tr>
    <th>Component</th>
    <th>Stock Conc.</th>
    <th>Unit</th>
    <th>Final Conc.</th>
    <th>Unit</th>
    <th>Condition A [µL]</th>
    <th>Condition B [µL]</th>
    <th>Condition C [µL]</th>
  </tr>
  <tr>
    <td>4X SMix</td><td>4.00</td><td>×</td><td>1</td><td>×</td>
    <td>8.75</td><td>8.75</td><td>8.75</td>
  </tr>
  ...
  <tr>
    <td><strong>Total [µL]</strong></td><td></td><td></td><td></td><td></td>
    <td><strong>35</strong></td><td><strong>35</strong></td><td><strong>35</strong></td>
  </tr>
</table>
```

Write as `build-composition.html` in the log folder via `devstudio-write-to-google-drive`
(raw file — it is consumed by tools and embedded in the Doc, not edited natively).

## Step 4 — write JSON sidecar

Write `build-composition.json` alongside the HTML. This is what
`devstudio-log-to-devnote-g` reads to insert the composition table into the DevNote(G)
without reconstructing from log prose.

Schema:

```json
{
  "source_file": "20260914-tetR-module-PLA1-plasmid.xlsx",
  "conditions": ["Unregulated", "Repressed 500 nM", "Induced 500 nM"],
  "rxn_volume_ul": 30,
  "components": [
    {
      "name": "Smix",
      "stock_concentration": "3.33",
      "stock_unit": "×",
      "final_concentration": "1",
      "final_unit": "×",
      "volumes_ul": {"Unregulated": 9.009, "Repressed 500 nM": 9.009, "Induced 500 nM": 9.009}
    },
    {
      "name": "Water",
      "stock_concentration": null,
      "stock_unit": null,
      "final_concentration": null,
      "final_unit": null,
      "volumes_ul": {"Unregulated": 4.747, "Repressed 500 nM": 3.247, "Induced 500 nM": 2.497}
    }
  ],
  "warnings": []
}
```

## Integration with devstudio-log-to-devnote-g

`devstudio-log-to-devnote-g` must check for `build-composition.json` in each log
folder before reconstructing composition from log prose.

- **Found**: read the sidecar, insert the HTML table (from `build-composition.html`)
  into the `# Methods` section of the DevNote(G). Do not reconstruct composition from
  the log.
- **Not found**: reconstruct from log prose as normal, emit `⚠️ No build file found —
  composition table reconstructed from log. Verify values against original setup.`

## What this skill does not do

- Does not produce MyST syntax — `devstudio-devnote-g-to-devnote-m` converts the
  HTML table to a `:::{table}` block.
- Does not reformat to the three-column Docs schema — `devstudio-devnote-to-docs-g`
  handles that.
- Does not assign a figure label or caption — those are added by the G→M skill.
