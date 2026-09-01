#!/usr/bin/env python3
"""Flatten a stacked platemap: assembly recipes become per-well columns.

A bench platemap often puts the well table on top and assembly recipes
underneath, joined on `Name`. This reads that sheet and writes one flat table
where every well row carries its own component volumes -- see
references/assembly-blocks.md for the format and the fill rule.

Needs openpyxl for .xlsx input; CSV and TSV input need nothing.

    flatten-platemap.py sheet.xlsx --sheet platemap-1 -o flat.tsv

Exit codes: 0 wrote the file, 2 the input could not be parsed.
"""

from __future__ import annotations

import argparse
import csv
import datetime
import sys
from collections import OrderedDict
from pathlib import Path

# Run from anywhere: platemap_common.py sits beside this file.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from platemap_common import REQUIRED, is_blank, load_grid  # one owner




def parse(rows: list[list]):
    """Split the sheet into well rows and `Name` -> recipe.

    Recipes are anchored on the literal `Component` header rather than on the
    title row, because a title row may share its row with unrelated cells.
    """
    header = [("" if h is None else str(h).strip()) for h in rows[0]]
    wells, index = [], 1
    while index < len(rows) and not all(is_blank(v) for v in rows[index]):
        wells.append(dict(zip(header, rows[index])))
        index += 1

    recipes = OrderedDict()
    for r in range(index, len(rows)):
        for c, value in enumerate(rows[r]):
            if is_blank(value) or str(value).strip() != "Component":
                continue
            title = rows[r - 1][c] if r > 0 else None
            if is_blank(title):
                continue
            per_reaction = rows[r][c + 1] if c + 1 < len(rows[r]) else None
            components, total, j = OrderedDict(), None, r + 1
            while j < len(rows) and c < len(rows[j]) and not is_blank(rows[j][c]):
                name = str(rows[j][c]).strip()
                cell = rows[j][c + 1] if c + 1 < len(rows[j]) else None
                if name.lower() == "total":
                    total = cell
                    break
                components[name] = cell
                j += 1
            recipes[str(title).strip()] = {
                "components": components,
                "total": total,
                "per_reaction_label": per_reaction,
            }
    return header, wells, recipes


def split_annotation(name: str) -> tuple[str, str | None]:
    """`pOpen-T7-deGFP (XX conc.)` -> (`pOpen-T7-deGFP`, `XX conc.`)"""
    if name.endswith(")") and "(" in name:
        base, _, annotation = name[:-1].partition("(")
        return base.strip(), annotation.strip()
    return name, None


def format_cell(value):
    if isinstance(value, datetime.datetime):
        return value.date().isoformat()
    if isinstance(value, datetime.date):
        return value.isoformat()
    return "" if value is None else value


def flatten(wells, recipes, concentration_units: str):
    components, annotated = OrderedDict(), OrderedDict()
    for recipe in recipes.values():
        for raw in recipe["components"]:
            base, annotation = split_annotation(raw)
            components.setdefault(base, None)
            if annotation:
                annotated.setdefault(base, annotation)

    volume_columns = [f"{base} Vol (uL)" for base in components]
    concentration_columns = [f"[{base}] ({concentration_units})" for base in annotated]
    header = REQUIRED + volume_columns + concentration_columns

    out = []
    for well in wells:
        recipe = recipes.get(str(well.get("Name", "")).strip())
        row = [format_cell(well.get(column)) for column in REQUIRED]
        for base in components:
            if recipe is None:
                row.append("")          # no recipe at all -> unknown, and that is a finding
                continue
            match = next(
                (v for raw, v in recipe["components"].items() if split_annotation(raw)[0] == base),
                None,
            )
            row.append(0 if match is None else match)   # in the recipe but absent -> deliberately none
        row += [""] * len(concentration_columns)
        out.append(row)
    return header, out, annotated


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("source", type=Path)
    parser.add_argument("--sheet", help="worksheet name for .xlsx input; defaults to the first")
    parser.add_argument("-o", "--output", type=Path, required=True, help="output .csv or .tsv")
    parser.add_argument("--units", default="ng/uL", help="units for promoted concentration columns")
    args = parser.parse_args()

    if not args.source.is_file():
        print(f"error: no such file: {args.source}", file=sys.stderr)
        return 2
    grid = load_grid(args.source, args.sheet)
    if not grid:
        print(f"error: {args.source} is empty", file=sys.stderr)
        return 2

    _, wells, recipes = parse(grid)
    if not wells:
        print("error: no well rows found above the first blank row", file=sys.stderr)
        return 2

    header, rows, annotated = flatten(wells, recipes, args.units)
    delimiter = "\t" if args.output.suffix.lower() in {".tsv", ".tab"} else ","
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, delimiter=delimiter)
        writer.writerow(header)
        writer.writerows(rows)

    print(f"{len(wells)} wells, {len(recipes)} recipe(s) -> {args.output} ({len(header)} columns)")
    for title, recipe in recipes.items():
        values = [float(v) for v in recipe["components"].values() if not is_blank(v)]
        total = None if is_blank(recipe["total"]) else float(recipe["total"])
        verdict = "ok" if total is not None and abs(sum(values) - total) < 0.01 else "MISMATCH"
        print(f"  {title}: {len(values)} components, sum {sum(values):g}, stated total {recipe['total']} [{verdict}]")
    missing = sorted({str(w.get("Name", "")).strip() for w in wells} - set(recipes))
    if missing:
        print(f"  no recipe for: {', '.join(missing)} -- their volume columns are blank, not zero")
    if annotated:
        print(f"  promoted to concentration columns: {dict(annotated)}")
    print(f"\nNow check it:\n  check-platemap.py {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
