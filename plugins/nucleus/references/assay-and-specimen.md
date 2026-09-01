# The assay frame and the specimen

A platemap is a **join between two descriptions**, and most of the confusion
in reading one comes from treating it as a single table.

**The assay frame** — where and when a measurement was taken. `Well`, plate
format, `Date`, `Experiment`, `Read`, `Type` (which analysis a row feeds),
`Name` (the replicate-grouping key). None of these is a claim about what is
in the well. `Well` is a position in an instrument.

**The specimen** — what is in the well, and how its parts relate. Reagents,
amounts, compartments.

They meet only in the well, and each imposes its own rules.

This file owns the assay-frame side. It is the half that instruments impose
and that no scientific model covers.

## The specimen side is owned elsewhere

As of 2026-09-01, specimen-side semantics — the compartment coordinate and
the composition operators that describe how parts of a specimen combine —
are owned by the Nucleus category-theory corpus and are **deliberately not
restated here**.

That date is the point of this paragraph. This repo exists because a
canonical table came to exist in two copies that disagreed, and a glossary
of someone else's formalism is that bug with extra steps. The corpus has no
stable published location and it moves; a paraphrase would need a maintainer
and this one would not get one. So: no operators, no symbols, no glossary.
If you need the specimen-side semantics, ask the corpus's owner, and read
the date above to judge how stale this assumption is.

What follows are consequences for **reading tables**, which is this repo's
job.

## Resolve a reagent's compartment before reading its amount

A well can hold more than one compartment — an inner solution inside a
membrane, sitting in an outer solution. When it does:

- **Volumes sum within a compartment and never across one.** A real plate had
  30 µL inside and 300 µL outside; adding them produces a number that
  describes nothing.
- **A reagent's compartment decides what its volume means.** So the
  compartment must be read first. A checker that reads amounts first has
  already discarded the information that says whether to add them.

**Resolve it per row, never per column.** A substance can sit in different
compartments in different wells. In one real plate a reagent was in the outer
solution for 25 wells and the inner solution for the 26th — and that 26th
well was the control, the row carrying the experiment's point. Resolving
compartment once per column gets exactly that row wrong, and a skipped
control is the cheapest possible failure to not notice.

Prefix compartment-specific columns so the coordinate is in the name:
`IS Optiprep Vol (uL)`, `[OS-glucose] (mM)`, `IS Volume (uL)`. A volume
column with no compartment, on a plate that has more than one, cannot be
checked against anything.

## A named sub-mix expands

A recipe may name another mix as one of its components — a master mix
entering an inner solution as a single line. Expand it, so the constituents
reach the platemap as their own columns. Left unexpanded, three or four
reagents are invisible in the record of what was in the well.

Expansion carries a **guard**: the sub-mix's own total must cover what is
drawn from it. Write the guard with the operation rather than as a footnote
about overage —

```
expand(sub-mix) -> its components
    guard: total(sub-mix) >= sum of the draws against it
```

— because a master mix is deliberately made in excess. One real sheet mixed
99 µL against 4 × 22.5 µL of draws: 9 µL of overage, 4.4 reactions' worth.
The inequality is the content. An equality there would fail on every correct
sheet.

## Two instances, one lab

The per-row compartment finding above has two known instances: a reagent in
different compartments across wells of one plate, and a reported case of one
substance existing as two pools inside one system. **Both come from the same
lab and the same chemistry.** Two instances is the minimum for a pattern, but
a third from a system sharing no chemistry with these would be worth more
than a fourth from this one. Treat the rule as well-evidenced and not yet
general.
