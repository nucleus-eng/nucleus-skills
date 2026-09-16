# The build file

A build file is the experimentalist's record of what was set up: one `.xlsx`
per experiment, **one sheet per condition**. It is the authoritative source for
both the platemap and the composition table, and the only source for either.

This file owns the format and the parse. `devstudio-build-to-assets` and
`devstudio-build-to-composition` both read build files and both point here
rather than restating the rules — they were written as two copies that
immediately disagreed about which columns were required.

## The canonical format

Named for `20260914-tetR-module-PLA1-plasmid.xlsx`, the file this format was
confirmed against. Row 1 is a title (`PURE reaction setup`); row 2 is the
header; component rows follow; a `Total volume [µL]` row closes the sheet.

| Header | Holds |
| --- | --- |
| `Component` | Reagent name. Free text; may carry a lot number, e.g. `Pmix (08-02)`. |
| `Input concentration` | Stock concentration. Published as **`Stock Conc.`** — the build file and the composition table use different names for this column. |
| `Unit` | Unit for the input concentration. |
| `Final concentration` | In-well concentration. Note the trailing space in the real header (`Final concentration `). |
| `Unit` | Unit for the final concentration. Second column of this name — match by position, not by name. |
| `Volume for one reaction [µL]` | Per-reaction volume. |

The sheet name is the condition name and is carried through verbatim.

**Components with no concentration** — water, a dye added by volume — leave
all four concentration cells empty. That is expected, not a gap to flag.

## The parse

1. Download the `.xlsx` as raw bytes via `devstudio-read-from-google-drive` —
   no `exportMimeType`. Parse with `openpyxl`, `data_only=True`, so computed
   values come through instead of formula strings.
2. Skip sheets that are empty or named `platemap`. An empty `platemap` sheet
   is common in partially-set-up files and is not an error.
3. Find the header row: the first row whose first non-null cell contains
   `Component` (case-insensitive, whitespace-stripped). Everything above it is
   title or metadata.
4. Read component rows until the first row whose first cell contains `Total`
   (case-insensitive). That row holds the total reaction volume.
5. Take the per-reaction volume from the last non-null numeric column, not a
   fixed index — trailing empty columns are common.

## Deviations from the canonical format

Real build files predate this format. Two shapes have been seen and both
should be parsed where possible and flagged, never silently accepted:

- **Volume-only** — `Components`, `Stock Concentration`, `Volume to add (uL)`,
  with no final concentration and often no stock values either. Parse the
  components and volumes; flag that concentrations are absent.
- **Conditions as row groups** — a condition label in column A with its
  component rows beneath, several groups to a sheet, rather than one sheet per
  condition. Treat each group as a condition; flag the deviation.

Header spellings observed in the wild, all mapping to
`Volume for one reaction [µL]`: `Volume to add (uL)`, `Volumn to add (uL)`
(sic), `Volume (µL)`.

**Flag, do not repair.** A missing concentration is a fact about the
experiment record; inferring one puts a number in a DevNote that nobody
measured.
