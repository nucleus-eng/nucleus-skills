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

## An expanded sub-mix replaces itself

Once a named sub-mix is expanded, **its own volume column must go.** Leaving
both means the well's components sum to the reaction volume plus the sub-mix,
and every row fails arithmetic for a reason that looks like a recipe error.

The roll-up still carries information — that 3.33 µL of a premade 3× solution
was pipetted, not nine separate reagents. Keep it as **provenance, not a
volume**: a `Premix` column naming the solution and its fold. Then the parts
are the only things summed, and the record still says what was on the bench.

`check-platemap.py` names the culprit when this happens: if the excess over
the stated total equals one volume column exactly, it says so, because a
sub-mix counted twice is by far the most common cause.

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

A well can hold an inner solution inside a membrane, sitting in an outer
solution, and then `Rxn Volume (uL)` describes one compartment rather than
the well. The rules for reading that — resolve the compartment before the
amount, per row — are owned by
[`references/assay-and-specimen.md`](../../../references/assay-and-specimen.md),
because `extract-conditions` needs them too.

## Absence has three states, and this is provenance

This is a **reading convention, not domain structure.** The test: it would be
true of any spreadsheet in any domain. It records how strong a claim a cell
makes, which is provenance — so it lives here, in the skill, and not in a
semantics file. Filing this kind of rule as domain structure is how a shared
reference becomes a junk drawer.

| Cell | Claim |
| --- | --- |
| an explicit `0` | there is none, and someone says so |
| `N/A` | the question does not apply to this well |
| blank | nobody made a claim |

`N/A` is data. In these sheets it means "no liposome in this bulk control",
"no compartment to name". Treating it as a missing value buries the real
findings under one warning per well — it did exactly that, thirteen times,
before this was written down.
