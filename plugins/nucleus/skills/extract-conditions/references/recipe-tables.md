# Recipe table shapes

Three shapes seen in real Nucleus sources. All of them describe composition;
none of them describes layout.

## 1. Component and volume

The minimum. Used in stacked bench platemaps, below the well table.

```
Component          Sample
SMix               3
PMix               1.2
Total              10
```

Joined to wells on the condition name. `build-platemap` owns this one —
see that skill's assembly-blocks reference.

## 2. Component, input and final concentration, volume

The ELN shape. Richer, and self-checking, because the concentrations and the
volumes have to agree.

```
Component        Input conc.  Unit   Final conc.  Unit   Volume for one reaction [µL]
Energy sol-CP    3.00         ×      1            ×      11.67
Mg-Acetate       200          mM     8            mM     1.40
Water                                                    4.68
```

**Verify the basis before trusting the header.** `stock * volume / total`
must equal the stated final concentration. In the table above, 200 × 1.40 /
35 = 8 mM, so the basis is 35 µL — even though the column is headed "for one
reaction" and a reaction was 10 µL. It is a master mix.

An explicit `0` row (`Creatine phosphate ... 0 mM ... 0.00`) means
deliberately none, and is worth keeping. A component simply absent from the
table means the same thing. A component absent from *every* table, that the
prose mentions, means nobody wrote it down — and those are not the same.

## 3. Design factor columns

A binary or categorical column naming a factor rather than an amount:

```
Well   Name                      CP
A19    CP + PolyP + 8 mM Mg      1
C19    PolyP + PPK + 8 mM Mg     0
```

`CP` is not a volume, a concentration or an ID, so no naming convention
catches it. It is the experiment's design variable in shorthand.

Keep it, and **also** write the quantity it stands for — here
`[Creatine phosphate] (mM)` of 20 or 0. The flag says which arm a well is
in; the concentration says what is in the well. Analysis needs the second,
and a reader a year later needs both.

## Malformed tables

Two failures worth expecting, both from real pages:

- **A total in the wrong cell.** A `Total volume [µL]` header on one row and
  the value `35` on the next, under `Component`. Read naively, `35` is a
  reagent.
- **A calculator appended to the recipe.** A `Calculation for DNA
  concentration` block with `DNA length [bp]` and `Avg. MW of bp` inside the
  same table element. It is working, not composition. Do not emit it as
  components.
