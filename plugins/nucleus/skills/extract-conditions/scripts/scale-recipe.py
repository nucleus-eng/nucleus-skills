#!/usr/bin/env python3
"""Scale a recipe between a master mix and one reaction, and verify the basis.

A recipe table's volumes are often for a master mix even when the header says
"per reaction". Concentrations do not change when a mix is split into
aliquots; only volumes do. This scales the volumes and, when the table gives
stock and final concentrations, checks which total the concentrations were
actually computed against -- that check is what the header cannot fake.

Input is a CSV or TSV with a component column and a volume column. Stock and
final concentration columns are optional but are what make the check possible.

    scale-recipe.py recipe.csv --from 35 --to 10

Exit codes: 0 scaled, 1 scaled with findings, 2 could not read the recipe.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path


def read_table(path: Path) -> tuple[list[str], list[list[str]]]:
    """Return the header and raw rows.

    Positional, not DictReader: these tables repeat the header `Unit` for the
    stock and the final concentration, and a dict silently keeps only the
    last one.
    """
    delimiter = "\t" if path.suffix.lower() in {".tsv", ".tab"} else ","
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = [list(row) for row in csv.reader(handle, delimiter=delimiter)]
    return ([c.strip() for c in rows[0]], rows[1:]) if rows else ([], [])


def unit_after(header: list[str], index: int) -> int | None:
    """A `Unit` column sits immediately right of the value it qualifies."""
    if index is not None and index + 1 < len(header) and "unit" in header[index + 1].lower():
        return index + 1
    return None


def pick(header, *wanted):
    for index, candidate in enumerate(header):
        low = candidate.lower()
        if any(w in low for w in wanted):
            return index
    return None


def number(value):
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("recipe", type=Path)
    parser.add_argument("--from", dest="source", type=float, required=True, help="total the recipe is written for")
    parser.add_argument("--to", dest="target", type=float, required=True, help="volume of one reaction")
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args()

    if not args.recipe.is_file():
        print(f"error: no such file: {args.recipe}", file=sys.stderr)
        return 2
    header, rows = read_table(args.recipe)
    if not rows:
        print(f"error: {args.recipe} has no rows", file=sys.stderr)
        return 2

    component = pick(header, "component", "reagent", "name")
    volume = pick(header, "volume", "vol")
    stock = pick(header, "input conc", "stock")
    final = pick(header, "final conc")
    if component is None or volume is None:
        print(f"error: need a component column and a volume column; saw {header}", file=sys.stderr)
        return 2

    def cell(row, index):
        return row[index].strip() if index is not None and index < len(row) else ""

    findings = []
    total = sum(n for r in rows if (n := number(cell(r, volume))) is not None)
    print(f"{len(rows)} rows, volumes sum to {total:g}")
    if abs(total - args.source) > 0.01:
        findings.append(f"volumes sum to {total:g}, not the stated basis of {args.source:g}")

    # The basis check: stock * volume / basis should equal the final
    # concentration. Only valid when both are quoted in the same unit -- a
    # ng/uL stock against a nM final needs a molar mass, which the page
    # carries in its own calculation block, not here.
    stock_unit, final_unit = unit_after(header, stock), unit_after(header, final)
    skipped = []
    if stock is not None and final is not None:
        for row in rows:
            s_, v_, f_ = number(cell(row, stock)), number(cell(row, volume)), number(cell(row, final))
            if None in (s_, v_, f_) or not s_ or not v_:
                continue
            su, fu = cell(row, stock_unit).lower(), cell(row, final_unit).lower()
            if su and fu and su != fu:
                skipped.append(f"{cell(row, component)} ({su} to {fu})")
                continue
            implied = s_ * v_ / args.source
            if abs(implied - f_) > max(0.02 * max(f_, 1), 0.02):
                other = s_ * v_ / args.target
                hint = f"; at a {args.target:g} uL basis it would be {other:.2f}" if abs(other - f_) < 0.02 else ""
                findings.append(
                    f"{cell(row, component)}: {s_:g} stock x {v_:g} uL / {args.source:g} uL = "
                    f"{implied:.2f}, but the table says {f_:g}{hint}"
                )
    if skipped:
        print(f"  basis check skipped for {len(skipped)} row(s) with mismatched units: {', '.join(skipped)}")

    scale = args.target / args.source
    print(f"scaling by {args.target:g}/{args.source:g} = {scale:.6f} (concentrations unchanged)\n")
    out_rows = []
    for row in rows:
        v = number(cell(row, volume))
        scaled = list(row)
        if v is not None:
            scaled[volume] = round(v * scale, 3)
        out_rows.append(scaled)
        print(f"  {cell(row, component):<26} {cell(row, volume):>8} -> {scaled[volume]}")

    if args.output:
        delimiter = "\t" if args.output.suffix.lower() in {".tsv", ".tab"} else ","
        with args.output.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle, delimiter=delimiter)
            writer.writerow(header)
            writer.writerows(out_rows)
        print(f"\nwrote {args.output}")

    if findings:
        print(f"\n{len(findings)} finding(s):")
        for finding in findings:
            print(f"  [warn    ] {finding}")
        return 1
    print(f"\nbasis confirmed: the concentrations were computed against {args.source:g} uL")
    return 0


if __name__ == "__main__":
    sys.exit(main())
