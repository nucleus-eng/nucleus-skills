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

One row per condition. No `Well` column, by design.

| Column | Holds |
| --- | --- |
| `Name` | The condition, named the same way every time it appears |
| `Type` | `Sample`, `Standard`, `Control`, `Positive Control`, `Negative Control` |
| `Rxn Volume (uL)` | Volume **per reaction**, not per master mix |
| `<component> Vol (uL)` | Volume of a component, per reaction |
| `[<component>] (<units>)` | Concentration **in the reaction** |

`build-platemap` consumes this directly: it adds `Date`, `Experiment` and
`Well` and writes one row per well.

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

See `references/recipe-tables.md` for the table shapes seen in practice.
