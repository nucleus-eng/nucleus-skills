# What the CDK does with a platemap

Behaviour read from `cdk/src/cdk/analysis/cytosol/platereader.py` and
confirmed by running the loader. None of this is in the
[platemap tutorial](https://docs.nucleus.engineering/guides/platemap-tutorial/),
which is why it is written down here rather than cross-referenced.

Line numbers are from the version read on 2026-09-01. Treat them as a hint,
not an address.

## The merge is an inner join, and that is the whole problem

`load_platereader_data` merges the platemap into the reader data with
`data.merge(platemap, on="Well")` (line 163). Pandas defaults to an inner
join, so **any well that does not match is dropped with no error and no
warning.** Nothing downstream can tell the difference between a well you
excluded on purpose and a well you lost to a typo.

Every blocking rule in `check-platemap.py` exists because of this line.

### `A1`, never `A01`

The BioTek reader builds its `Well` values as `str(int(s[1:]))` (line 488),
which strips leading zeros. It emits `A1`. A platemap written `A01` matches
nothing and loses every one of those wells at the merge.

### `B:1` is fine

`read_platemap` strips `:` from `Well` before returning (line 197), so the
`B:1` style found in older platemaps still merges.

## Types

`DEFAULT_ANALYSIS_COLUMNS = ["Sample", "Control", "Positive Control"]`
(line 52). Kinetic analysis runs on those three only. A well typed
`Standard` or `Negative Control` is loaded and then not analysed, which is
correct. A well typed `sample` in lower case is not in the list either, and
that is not correct — it is simply absent from the results.

`blank_data()` defaults to `blank_type="Blank"` (line 522). `Blank` **is** in
the DevNote's vocabulary and is used by the CDK's own test fixtures. The
published tutorial omits it, which makes the tutorial the outlier — treat
`Blank` as a legitimate type.

`Type` is optional in practice. Two call sites warn and carry on when the
column is absent (lines 1084, 1346).

## Grouping

Kinetics groups on `["Name", "Read", "Well"]` (line 1062), and warns and
appends `Well` if you leave it out (line 1080). `Name` is therefore the
replicate key. Two wells of the same material with different names are two
conditions as far as every downstream summary is concerned.

## What the loader accepts

- `.csv`, `.tsv` and `.xlsx` all load (lines 174–184). The tutorial says CSV
  or TSV; prefer those two, because they diff and `.xlsx` does not.
- Columns named `Unnamed:*` are dropped (line 188), so a trailing comma on
  every row is harmless.
- `Row` and `Column` columns are dropped from the platemap before the merge
  (lines 156–161). Including them is harmless and pointless — the reader
  derives its own.

## The returned platemap is not the merged one

`load_platereader_data` returns `PlateReaderData(data, platemap)` (line 165),
where `platemap` is the **raw parsed file**, not the merged result. Rows
dropped by the inner join are still in it.

This matters for the stacked sheets described in `assembly-blocks.md`. A
whole-sheet export gives a `platemap` object whose `Type` column contains
component volumes (`'0.5'`, `'1.2'`, `'4.0'`) rather than types. `data` is
correct; anything reading `platemap` directly is not.
