# Stacked platemaps: wells on top, assembly below

A common bench format puts two tables in one sheet:

- **Block A**, from row 1 — the platemap. One row per well, the six required
  columns.
- **Block B**, below a blank row — assembly recipes. One block per condition:
  a title row, a `Component | <per-reaction>` header, component volumes, then
  a `Total` row.

The two are joined on `Name`. A recipe's title matches a `Name` value in
block A exactly, by string equality, with nothing enforcing it.

```
Date       Experiment      Well  Name           Type              Rxn Volume (uL)
2026-09-01 20260901-...    E1    Nucleus PURE   Sample            10
...

Rxn Volume 10                    Nucleus PURE
                                 Component        Sample
                                 SMix             3
                                 PMix             1.2
                                 ...
                                 Total            10
```

## Do not export the whole sheet

`read_platemap` accepts a whole-sheet export without error. The assembly rows
have no `Well` value, so the inner merge discards them and `data` comes out
right — but the `platemap` object handed back to the caller keeps them, with
component volumes sitting in the `Type` column. See
[`cdk-behaviour.md`](cdk-behaviour.md).

The format survives by accident, not by design. **Export block A alone.**

## Parsing

Split block A at the first fully blank row.

**Anchor recipes on the literal `Component` header, not on the title row.**
A title row may share its row with unrelated cells — in a real file, the row
carrying the first recipe's title also carried a loose `Rxn Volume | 10` in
two other columns, which defeats any rule of the form "a title is a row with
one value in it". Given a cell reading `Component` at `(r, c)`:

- the title is `(r-1, c)`
- the per-reaction volume column is `c+1`
- components run down column `c` from `r+1` until a blank cell or `Total`

The second column header is often `Sample`. Read it as "volume per reaction",
not as a `Type` — it collides with the type vocabulary and means something
else. If it is genuinely naming a type, it will disagree with the `Type`
column of the wells it belongs to; flag that rather than resolving it.

A loose `Rxn Volume | <n>` restates the `Rxn Volume (uL)` column. Drop it. A
second copy of a value is somewhere for the two to disagree.

## Flattening

Give each unique component its own column, `<component> Vol (uL)`, and put
that condition's volume on every well row of that condition. Keep component
names verbatim — do not quietly rename `Nucleus free H2O` to `Water`.

**The fill rule has three states, and collapsing any two of them loses the
finding:**

| Case | Value | Means |
| --- | --- | --- |
| Component is in this condition's recipe | the volume | measured |
| Condition has a recipe, this component is not in it | `0` | deliberately none |
| Condition has no recipe at all | *blank* | **nobody wrote it down** |

The zeros are what make each row sum to `Rxn Volume (uL)`. The blanks are the
finding: a condition claiming a 10 µL reaction volume while accounting for
none of it. In the stacked form that gap is a recipe block that is not there,
which nobody sees. Flattened, it is an empty row.

Split annotations off reagent names and promote them to real columns:
`pOpen-T7-deGFP (XX conc.)` becomes a `pOpen-T7-deGFP Vol (uL)` column plus
an empty `[pOpen-T7-deGFP] (ng/uL)` column. A placeholder inside a label is
invisible; an empty column with a unit on it is a question.

## When not to flatten

Flattening produces a dense matrix. Two conditions sharing three reagents
give nine columns, six of them zero. Twenty conditions over forty reagents
give a very wide, very sparse sheet that is worse to read than the lookup it
replaced. Past roughly a dozen components, keep the recipes as a separate
file keyed on `Name` and export only block A.

## Layered plate grids

A microscopy sheet often stacks one plate grid per variable — same geometry,
a different attribute in each, named in the header row's first cell:

```
Experiment          2   3   4        [aTc] (uM)      2       3
A            tetR-aTc ...            A           0.625  0.3125
D                 aTc ...            D           0.625  0.3125

aTc (OS/IS)         2   3            lipids          2       3
A                  OS  OS            A            POPC    POPC
D                  OS  OS            D             N/A     N/A
```

Each layer becomes one column. `grid-to-platemap.py` finds them all and
writes the wide table. Layer names that already follow a convention are kept
(`[aTc] (uM)`); a bare `<thing> (uL)` gains the `Vol` the convention wants;
anything else is kept verbatim, because renaming a variable an experimenter
chose loses more than it tidies.

A layer that is missing wells the other layers describe is a finding — it
means one attribute was not recorded for part of the plate.

## Two compartments in one well

A synthetic cell is an **inner solution (IS)** inside a membrane, sitting in
an **outer solution (OS)**. The well holds both. This breaks two assumptions
that hold everywhere else:

- **`Rxn Volume (uL)` describes one compartment, not the well.** A real plate
  had 30 µL IS and 300 µL OS. Summing component volumes against a single
  total is meaningless — `check-platemap.py` detects `IS`/`OS` columns and
  skips the sum rather than reporting a false mismatch on every row.
- **A reagent has a location as well as an amount.** A column like
  `aTc (OS/IS)` says *which side of the membrane* the aTc went. That is not a
  concentration or a volume, and no naming convention catches it. Keep it.

Prefix compartment-specific columns: `[OS-glucose] (mM)`,
`IS Volume (uL)`, `OS Volume (uL)`.

## `N/A` is data

In these sheets `N/A` means "not applicable to this well" — no liposome in a
bulk-solution control, no compartment to name. It is the text form of the
deliberate zero from the fill rule above, **not** a missing value. Do not
treat it as a placeholder; doing so buries the real findings under one
warning per well.
