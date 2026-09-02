---
name: build-platemap
description: Draft, flatten, and check Nucleus platemaps for the CDK. Use when asked to make or review a plate map or plate layout, lay out wells for a plate reader or microscope run, convert an assembly or recipe table into per-well columns, or work out why a platemap will not merge with plate reader data. Produces a CSV or TSV plus a findings report, not a notebook or a BOM.
---

# Build a platemap

A platemap records what went in each well and where. The CDK merges it into
plate reader data on the `Well` column and groups replicates on `Name`.

**This skill owns layout.** If the source is an experiment write-up — an ELN
page, a protocol, meeting notes — the chemistry comes from
`extract-conditions` first, which produces a condition table with no wells in
it. That boundary is real: a write-up records composition and never records
layout, so plate format, replicate count and well IDs must be asked for, not
inferred from the page.

The column requirements are owned by the original DevNote,
`nucleus-devnote-archive-1/devnotes/2026-bhasin-platemaps/main.md`
(renamed from `2026-CERN-OHL-P`; the redirect works but will break if anything
later takes the old name). **Where the
published [platemap tutorial](https://docs.nucleus.engineering/guides/platemap-tutorial/)
disagrees with it, the DevNote wins.** Restated here because every step below
depends on it — **this is a port; keep it in sync with the DevNote**:

**Five required columns.** Absence is an error.

| Column | Holds |
| --- | --- |
| `Well` | Alphanumeric location, e.g. `K13` |
| `Date` | Experiment date, **`yyyy-mm-dd`** — never `mm/dd/yy`. `01/02/25` is a date nobody can recover: month/day or day/month, and a year with no century. |
| `Experiment` | Short description of the run |
| `Name` | A brief description of the well's contents. **Unique per condition, identical across replicates** — the second is what makes statistics possible. |
| `Type` | `Sample`, `Standard`, `Blank`, `Control`, `Positive Control`, `Negative Control` |

**Strongly recommended:** `Rxn Volume (uL)`, the total liquid volume. The
DevNote lists it among the optional columns, so its absence is a warning —
but without it nothing can check that a well's components account for its
volume.

Two places where the tutorial is the outlier and should not be followed:

- it makes `Rxn Volume (uL)` a sixth *required* column
- it omits `Blank` from the type vocabulary, which both the DevNote and the
  CDK's `blank_data()` use

Anything else is optional. The DevNote's guidance: record the variables you
control, plus any you think may influence the outcome — reagent lot numbers,
reporter identity, the experimentalist.

[`references/assay-and-specimen.md`](../../references/assay-and-specimen.md)
holds the rules shared with `extract-conditions`: the assay-frame/specimen
split, resolving a reagent's compartment before its amount, and expanding a
named sub-mix. Two skill-local reference files hold the rest:

- `references/cdk-behaviour.md` — what the CDK does that the tutorial does
  not say, including the ways a platemap fails **silently**. Read it before
  diagnosing a merge problem.
- `references/assembly-blocks.md` — the stacked platemap-plus-recipes sheet
  used at the bench, and how to flatten it into per-well columns.

## 1. Gather before drafting

Ask for what is missing; do not invent it. Read a named protocol or DevNote
instead of asking when one is supplied.

- **Is this platemap a plan or a record?** Ask this first, and ask it while
  *reading the source*, not when you get to laying out wells — by then the
  decision to generate them has already been made.

  | | Wells are | Generating them is |
  | --- | --- | --- |
  | **Prospective** — a run not yet done | the deliverable | correct; the point of step 2 |
  | **Retrospective** — a run already done | facts to recover | **fabrication** |

  A generated well in a retrospective platemap merges against whatever real
  data sits at that position, or drops the row. Both run to completion and
  report success. If the source records a completed run and contains no
  wells, **stop and say so** — the layout is not recoverable and no amount of
  care in generating it helps.

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
- Conditions, and the reagents and volumes that make each one up. From a
  write-up, this is `extract-conditions`' output — do not re-read the source.
- **Replicates per condition.** Three is usual. Reactions are assembled as a
  master mix with overage, so a `Rxn Volume (uL)` of 10 with a 35 µL recipe
  means 3 × 10 µL plus 5 µL spare — the recipe's total is not the well
  volume.
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

## 3a. Impute what is absent; flag what is present but wrong

These are two different actions and confusing them destroys data.

**Absent** — the column or cell is not there. Recover it from context, fill
it in, and list it as imputed. Leaving a recoverable field blank is not
caution; it throws away information the reviewer has to find again.

**Present but non-conforming** — a value exists and breaks a convention.
Report it. Never overwrite it. It is somebody's record of what they did.

Sources worth checking before declaring a field missing:

| Field | Recoverable from |
| --- | --- |
| `Date` | The source page's date heading, **and the filename** — Nucleus files are named `<YYYYMMDD>-<slug>` |
| `Experiment` | The page title, or the filename slug |
| `Type` | The prose. "a control CP/CK reaction" names the type of those wells |
| `Rxn Volume (uL)` | The recipe total divided by the replicate count, once overage is accounted for |
| Concentrations | Parsed out of a free-text `Name` — `PolyP + PPK + 10 mM Mg` gives `[Mg-Acetate] (mM)` of 10 |
| Replicate count | The platemap itself: wells sharing a `Name` |
| Reporter | The construct name — `plam-GFP` implies a GFP reporter |

**Never drop a column you were given.** A design-factor column like `CP` with
values `1`/`0` matches no naming convention, so it is easy to discard while
"tidying". Keep it, and add the quantity it stands for
(`[Creatine phosphate] (mM)`) beside it. The flag says which arm a well is
in; the concentration says what is in the well. They must agree, and that
agreement is worth checking.

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
python3 scripts/check-platemap.py <file> --provenance <file>.provenance.yaml
```

The checker finds the header row by content rather than by position, so a
grid or notes sitting above the well table do not matter. It reports what it
skipped.

Three levels. **Blocking** means the CDK will silently produce wrong or
missing data. **Warn** means the analysis runs but the record is incomplete.
**Info** is cosmetic.

### Write a provenance sidecar

Ship `<platemap>.provenance.yaml` beside the file. It records where each
column's values came from, and — the field that matters — whether the
platemap is a plan or a record.

```yaml
platemap_kind: prospective      # or retrospective
source:                         # where this platemap came from
  path: 20260603-clpxp.csv
  blob: 4c7c31c8707066d92291802a05fd85b7f03b9189
recipe:                         # the composition its columns derive from
  path: tmp/experiments/2026-09-05-dye-liposome-ulga.yml
  blob: a85e860f1e5b19c400aef459408e62cad7e365b9
columns:
  Date: {state: imputed, note: "from the filename"}
  Experiment: {state: source}
  Well: {state: assumed, note: "generated; the source had no Well column"}
  Name: {state: source}
  Type: {state: source}
  "[Mg-Acetate] (mM)": {state: derived, note: "stock 200 mM x volume / 35 uL"}
```

Four states: `source` verbatim, `derived` computed, `imputed` inferred from
context, `assumed` chosen and needing review.

**A path is not a pin.** `path` says where a file was; `blob` says which
version it was, and they answer different questions — a path rots, and a
digest alone cannot be looked up. `blob` is git's own digest:

```bash
git hash-object <file>
```

It depends on content alone. The same value before and after the file is
committed, in any repository, at any path, and it works in a directory with no
git history at all — so a pin taken on a spreadsheet sitting on someone's
desktop survives every move that file will make. Use git's digest rather than
a bare `sha256`: neither this repo nor nucleus-docs had any hashing precedent,
so the first choice sets it for both.

`source` and `recipe` are different claims. `source` is where this platemap
came from; `recipe` is the composition its specimen columns are *derived*
from. The checker recomputes both when the path still resolves, and reports a
mismatch — a pin nobody verifies is a comment.

**`platemap_kind: retrospective` with `Well: assumed` is a blocking finding.**
That pair is the fabrication case, and it is the only thing here a checker
can decide on its own — everything else it reports for a human.

Then report to the reviewer, in this order:

1. The layout and why — plate format, rows and columns used, edge margin.
2. Controls, standards, and replicate counts.
3. The checker's findings.
4. **Every value that was assumed rather than supplied**, listed separately
   and last, so it cannot be skimmed past.
