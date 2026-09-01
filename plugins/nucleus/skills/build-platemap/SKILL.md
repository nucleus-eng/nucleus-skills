---
name: build-platemap
description: Draft, flatten, and check Nucleus platemaps for the CDK. Use when asked to make or review a plate map or plate layout, lay out wells for a plate reader or microscope run, convert an assembly or recipe table into per-well columns, or work out why a platemap will not merge with plate reader data. Produces a CSV or TSV plus a findings report, not a notebook or a BOM.
---

# Build a platemap

A platemap records what went in each well and where. The CDK merges it into
plate reader data on the `Well` column and groups replicates on `Name`.

The column requirements are owned by the
[platemap tutorial](https://docs.nucleus.engineering/guides/platemap-tutorial/)
(source: `nucleus-docs/guides/platemap_tutorial.md`). Read it for the
authoritative list. The six required columns are restated here because every
step below depends on them — **this is a port; keep it in sync with the
tutorial**:

| Column | Holds |
| --- | --- |
| `Date` | Experiment date |
| `Experiment` | Short description of the run |
| `Well` | Alphanumeric location, e.g. `K13` |
| `Name` | What is in the well. Identical material gets an identical name. |
| `Type` | `Sample`, `Standard`, `Control`, `Positive Control`, `Negative Control` |
| `Rxn Volume (uL)` | Total liquid volume in the well |

Two reference files hold the detail:

- `references/cdk-behaviour.md` — what the CDK does that the tutorial does
  not say, including the ways a platemap fails **silently**. Read it before
  diagnosing a merge problem.
- `references/assembly-blocks.md` — the stacked platemap-plus-recipes sheet
  used at the bench, and how to flatten it into per-well columns.

## 1. Gather before drafting

Ask for what is missing; do not invent it. Read a named protocol or DevNote
instead of asking when one is supplied.

- **Instrument** — plate reader or microscope. This changes the edge rule in
  step 2, so it is not optional.
- **Plate format** — **384 unless there is evidence otherwise.** That is the
  default in this field. Infer before asking, and ask only when inference
  genuinely fails:
  - A row letter past `H` (e.g. `J`) exists only on 384. That settles it.
  - A column number past 12 does the same.
  - **Reaction volume is not evidence.** Up to roughly 50 µL is normal in a
    standard 384 well, so a 35 µL reaction says nothing about the format.
  - Ask when the evidence contradicts itself or the default — for example
    rows past `H` on a sheet that says 96 somewhere else.
- Conditions, and the reagents and volumes that make each one up.
- In-well concentrations, and artifact IDs for anything with a stock.
- Replicate count, controls, standards, total reaction volume.

## 2. Lay out the wells

- **One row per well.** Never one row per condition.
- **Identical material, identical `Name`.** The CDK groups on
  `["Name", "Read", "Well"]`, so one typo splits a replicate group in two and
  reports both halves as if they were separate conditions.
- **Keep off the plate edge.** Edge wells evaporate faster and read
  differently.
  - Plate reader — a **soft** rule. Warn, and lay out inside the margin by
    default, but an edge well is usable.
  - Microscope — a **hard** rule. Meniscus curvature at the well wall makes
    edge wells optically unusable, so this is not a trade-off to weigh.
- Prefer a centred, spaced block. `cdk.calculators.platemap_maker`
  already generates these — `generate_centered_384_well_ids` for a centred
  randomised block, `generate_384_well_ids(skip=True)` for every-other-well
  spacing. Call them rather than writing well IDs by hand.
- Write well IDs the way the reader does: **`A1`, never `A01`.** See
  `references/cdk-behaviour.md` — a leading zero silently drops the well.

## 3. Record the composition

Recommended on every platemap, and required if anyone will ever ask what was
actually in a well.

| Pattern | For |
| --- | --- |
| `<artifact> Vol (uL)` | Volume of a component in the well |
| `[<artifact>] (<units>)` | Concentration **in the well**, not of the stock |
| `<artifact> ID` | Cross-reference to a specific stock in inventory |

If the source is a stacked sheet with assembly recipes below the platemap,
flatten it — `references/assembly-blocks.md` covers the parse, the join, and
the three-state fill rule that keeps "deliberately none" apart from
"nobody wrote it down".

```bash
python3 scripts/flatten-platemap.py sheet.xlsx --sheet <name> -o flat.tsv
```

If the source is a **spatial plate grid** — plate rows down the left, plate
columns across the top, contents in the cells — convert it, and cross-check
it against any written table on the same sheet:

```bash
python3 scripts/grid-to-platemap.py sheet.xlsx -o wells.tsv
```

The grid is what happened at the bench; the table is what someone typed up
afterwards. When they disagree, the disagreement is the finding. A table
covering 7 of 20 wells will analyse a third of the run and report nothing
wrong.

### `Standard` is a trap

`Standard` means a calibration standard — fluorescein, HPTS — and those wells
are **excluded from kinetic analysis**. It is also an ordinary English word,
so it gets written for "the standard prep" or "the standard protocol". That
reads as valid vocabulary and silently drops the wells from the results. If a
`Standard` row has no concentration, it is probably a `Sample`.

## 4. Flag what is missing

**Report incomplete information; never fill it in silently.** A platemap is a
claim about what is physically in a well. A value that was assumed is not a
measurement, and the reviewer cannot tell the two apart once it is in a cell.

These are **warnings, not errors** — the analysis should still run:

- A concentration column with no value, or a placeholder like `XX conc.`,
  `TBD`, `TODO`, `?`.
- A condition with no assembly recorded at all.
- Component volumes that do not sum to `Rxn Volume (uL)`.
- A blank artifact ID where a stock was clearly used.

Promote a buried placeholder into a real column. `pOpen-T7-deGFP (XX conc.)`
as a reagent label hides the gap; `[pOpen-T7-deGFP] (ng/uL)` left empty is a
question somebody will answer.

## 5. Export

Export as **CSV or TSV** next to the data files. Both diff; `.xlsx` does not.

**Export the well table alone.** If the sheet also holds assembly blocks,
exporting the whole sheet appears to work and quietly corrupts the platemap
object the CDK hands back — see `references/assembly-blocks.md`.

## 6. Check, then hand off

```bash
python3 scripts/check-platemap.py <file> --instrument platereader --plate 384
```

The checker finds the header row by content rather than by position, so a
grid or notes sitting above the well table do not matter. It reports what it
skipped.

Three levels. **Blocking** means the CDK will silently produce wrong or
missing data. **Warn** means the analysis runs but the record is incomplete.
**Info** is cosmetic.

Then report to the reviewer, in this order:

1. The layout and why — plate format, rows and columns used, edge margin.
2. Controls, standards, and replicate counts.
3. The checker's findings.
4. **Every value that was assumed rather than supplied**, listed separately
   and last, so it cannot be skimmed past.
