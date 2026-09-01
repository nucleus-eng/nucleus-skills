---
name: extract-conditions
description: Read an experiment's conditions and composition out of unstructured sources — an ELN page, a protocol, meeting notes, recipe tables — into a condition table. Use when asked what conditions an experiment ran, to turn a Notion or DevNote write-up into reaction compositions, or to prepare a platemap from a page that has no wells in it. Produces a condition table, not a platemap: it never invents wells.
---

# Extract conditions

An experiment write-up records **chemistry**. A platemap records **layout**.
They are different artifacts and they usually live in different places.

This skill owns the first half: unstructured source → **condition table**.
`build-platemap` owns the second: condition table → wells.

**The boundary is the whole point.** An ELN page is never a source of layout.
Well IDs, plate format, replicate count, randomisation and edge margin are
not on the page and cannot be recovered from it. Extract what is there, then
hand over and ask for the rest — do not guess a plate.

## The condition table

One row per condition, and **it carries all six required platemap columns.**

| Column | Holds |
| --- | --- |
| `Date` | The experiment date as `yyyy-mm-dd` — fill it; it is usually recoverable |
| `Experiment` | The run — fill it; usually the page title or filename slug |
| `Well` | **Blank.** A write-up records no layout, and inventing one is fabrication |
| `Name` | The condition, named the same way every time it appears |
| `Type` | `Sample`, `Standard`, `Blank`, `Control`, `Positive Control`, `Negative Control` |
| `Rxn Volume (uL)` | Volume **per reaction**, not per master mix. Recommended, not required. |
| `<component> Vol (uL)` | Volume of a component, per reaction |
| `[<component>] (<units>)` | Concentration **in the reaction** |

**`Well` is present and empty, not absent.** The difference matters: an absent
column is not a platemap at all, while an empty one is a platemap awaiting a
layout, and `check-platemap.py` reports the second as exactly that — naming
what is missing rather than what is wrong. Dropping the column turns one
informative finding into three "required column missing" errors.

`build-platemap` consumes this directly and fills `Well`.

## 1. Read the prose, not only the tables

**The tables usually describe one condition. The prose describes all of
them.** This is the most common way an extraction goes wrong.

A page will give a single worked recipe and a sentence like "we tested a
varying range of final Mg2+ concentrations (8, 10, 12, 14 mM)". Four
conditions exist; one is written down. The other three are recoverable when
the table gives a stock concentration and a total volume:

```
volume = total * final_concentration / stock_concentration
```

and the diluent — usually water — absorbs the difference so the total holds.

**Mark every derived value as derived.** The diluent assumption in
particular is the one most likely to be wrong: the page does not say what was
adjusted to keep the volume constant.

## 2. Check what the volumes are per

**A recipe table's volumes are often for a master mix, not a reaction**, even
when the header says otherwise. A real page had a column headed
`Volume for one reaction [µL]` whose entries summed to 35 µL for a 10 µL
reaction — it was a 3× master mix with overage.

Test it against the stated concentrations, which is the check the label
cannot fake:

```
stock * volume / total  ==  stated final concentration
```

If that holds at the table's own total, the total is the basis the
concentrations were computed against. Scale to one reaction before writing
the condition table:

```bash
python3 scripts/scale-recipe.py recipe.csv --from 35 --to 10
```

Concentrations do not change when a master mix is split into aliquots. Only
volumes scale.

## 3. Pull structured facts out of names

Conditions get named in free text — `PolyP + PPK + 10 mM Mg`. A fact inside a
name cannot be filtered, sorted or plotted against. Promote it to a column:
`[Mg-Acetate] (mM) = 10`, and keep the original `Name` unchanged, because
that is the replicate key downstream.

The same applies to an annotation inside a reagent label:
`pOpen-T7-deGFP (XX conc.)` becomes a reagent plus an empty
`[pOpen-T7-deGFP] (ng/uL)` column.

## 3a. The filename is a source

Nucleus files are named `<YYYYMMDD>-<slug>` — `20250612-PPK.csv`,
`20260630-platemap-tetR-aTc.csv`. When a platemap has no `Date` column, the
date is very often in the name of the file holding it. Check there before
reporting the field as unrecoverable.

## 3b. Resolve names you do not know — do not guess, do not glossarise

Sources are full of shorthand: `MM`, `RNA ihb.`, `Optiprep`, `Sol A`. Look
them up. **Do not write a glossary** — nucleus-docs owns these and a copy
here drifts, which is the bug this repo exists to fix.

Lookup order, most specific first:

1. **nucleus-docs module specs** — authoritative for composition and
   reference concentrations. `~/src/bnext/nucleus-eng/nucleus-docs/docs/modules/`,
   falling back to `docs.nucleus.engineering` when there is no checkout.
2. **Anything construct-shaped** — hand to `verify-dna-constructs`. It owns
   construct identity, the `nucleus-eng/DNA` lookup, and the
   identity-versus-equivalence discipline that stops a name-similarity match
   being asserted as sequence identity.
3. **DevNotes** — for experiment-specific terms the docs do not carry.
4. **Ask.** Never expand an abbreviation you could not confirm.

This is not optional polish. On a real sheet the assembly tab said
`pT7-deGFP` at 3.0 µL and the platemap said `pT7-tetO-plamGFP` at 0.5 µL.
The module spec settled it — `pT7-tetO-plamGFP` is the module's reference
construct, its reference reaction uses 0.5 µL, and its reference TetR
concentration matched the platemap exactly. Three independent numbers said
the assembly tab was a stale carry-over. Guessing would have picked the
wrong reporter.

**A failed lookup decides whether you may write a zero.** A component whose
recipe you found is *transparent* — you can see everything in it, so a
substance it does not contain is genuinely absent. A component you could not
resolve is *opaque*, and anything it might contain is unknown. See
[`references/assay-and-specimen.md`](../../references/assay-and-specimen.md).

**A failed lookup is itself a finding.** `IS` and `OS` are used throughout
lab spreadsheets and are defined nowhere in nucleus-docs. That is a gap in
the docs, worth reporting, not a licence to invent a definition.

## 4. Report what is wrong, do not fix it

Source pages carry notation errors that change meaning:

- `mm` where `mM` is meant — millimetres, not millimolar. Common and easy to
  miss.
- `H20` for `H2O`.
- `x` and `×` mixed for fold-concentration.
- A component name that differs by one character between two tables.

Report these against the source. Do not silently correct a page you do not
own. Units and notation are owned by `references/devnote-style-guide.md`.

## 5. Hand over

State plainly what the source did **not** contain — normally the entire
layout. Then ask `build-platemap` for wells, giving it: the condition table,
the plate format if the source implies one, the replicate count, and the
instrument.

See `references/recipe-tables.md` for the table shapes seen in practice, and
[`references/assay-and-specimen.md`](../../references/assay-and-specimen.md)
for compartments, sub-mix expansion and its guard — shared with
`build-platemap`, which needs the same rules from the other side.
