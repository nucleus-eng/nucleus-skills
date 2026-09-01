#!/usr/bin/env python3
"""Turn a spatial plate grid into platemap rows, and cross-check any table.

Scientists lay plates out the way the plate looks: plate rows down the left,
plate columns across the top, well contents in the cells. That is a picture
of the plate, not a platemap -- the CDK needs one row per well.

This reads the grid, emits `Well` and `Name` rows, and -- when the same sheet
also holds a written platemap table -- compares the two. Wells present in one
and not the other are the finding worth having: a grid is what was done at
the bench, and a table missing half of it will silently analyse half the run.

    grid-to-platemap.py sheet.xlsx -o wells.tsv

Exit codes: 0 wrote the file, 1 wrote it with cross-check findings, 2 no grid.
"""

from __future__ import annotations

import argparse
import csv
import datetime
import re
import sys
from pathlib import Path

# Run from anywhere: platemap_common.py sits beside this file.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from platemap_common import PLATEMAP_COLUMNS, is_blank, load_grid  # one owner
PLATE_ROW = re.compile(r"^[A-Z]{1,2}$")



def text(value) -> str:
    if isinstance(value, datetime.datetime):
        return value.date().isoformat()
    if isinstance(value, datetime.date):
        return value.isoformat()
    return "" if value is None else str(value).strip()



def as_int(value):
    """Plate column numbers arrive as `3` or, from a spreadsheet, as `3.0`."""
    try:
        number = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    return int(number) if number == int(number) else None


def find_layers(rows: list[list]) -> list[tuple[str, int, dict[int, int]]]:
    """Find every plate grid in the sheet.

    A sheet often stacks one grid per variable -- same geometry, a different
    attribute in each -- with the attribute named in the header row's first
    cell (`[aTc] (uM)`, `lipids`, `aTc (OS/IS)`). Each layer contributes one
    column to the platemap.

    Returns (layer name, header row index, {sheet column: plate column}).
    """
    layers = []
    for index, row in enumerate(rows):
        label = text(row[0]) if row else ""
        numbered = {c: as_int(v) for c, v in enumerate(row) if c and not is_blank(v)}
        plate_columns = {c: n for c, n in numbered.items() if n is not None and 1 <= n <= 48}
        if len(plate_columns) < 3 or len(plate_columns) != len(numbered):
            continue
        if index + 1 < len(rows) and PLATE_ROW.match(text(rows[index + 1][0])):
            layers.append((label or f"layer_{len(layers) + 1}", index, plate_columns))
    return layers


def column_name(layer: str) -> str:
    """Map a layer's label to a platemap column name.

    `[aTc] (uM)` is already the concentration convention and is kept. A bare
    `<thing> (uL)` is a volume and gains the `Vol` the convention wants.
    Anything else -- `lipids`, `aTc (OS/IS)` -- is kept verbatim, because
    renaming a variable an experimenter chose loses more than it tidies.
    """
    if re.match(r"^\[.+\]\s*\(.+\)$", layer):
        return layer
    m = re.match(r"^(?P<name>.+?)\s*\(\s*u?[mµ]?[lL]\s*\)$", layer)
    if m and "vol" not in layer.lower():
        return f"{m.group('name')} Vol (uL)"
    return layer


def read_grid_wells(rows, header_index, columns) -> list[tuple[str, str]]:
    wells = []
    for row in rows[header_index + 1:]:
        label = text(row[0]) if row else ""
        if not PLATE_ROW.match(label):
            if wells:
                break
            continue
        for sheet_column, plate_column in sorted(columns.items(), key=lambda kv: kv[1]):
            value = text(row[sheet_column]) if sheet_column < len(row) else ""
            if value:
                wells.append((f"{label}{plate_column}", value))
    return wells


def find_table(rows: list[list]) -> tuple[list[str], list[dict[str, str]]] | None:
    for index, row in enumerate(rows):
        labels = [text(c) for c in row]
        if sum(1 for column in PLATEMAP_COLUMNS if column in labels) >= 3:
            header = labels
            out = []
            for line in rows[index + 1:]:
                if all(is_blank(v) for v in line):
                    break
                out.append({name: text(line[i]) if i < len(line) else ""
                            for i, name in enumerate(header) if name})
            return [h for h in header if h], out
    return None


def normalise(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", name.lower()).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("source", type=Path)
    parser.add_argument("--sheet", help="worksheet name for .xlsx input")
    parser.add_argument("-o", "--output", type=Path, help="write grid wells to this .csv or .tsv")
    args = parser.parse_args()

    if not args.source.is_file():
        print(f"error: no such file: {args.source}", file=sys.stderr)
        return 2

    rows = load_grid(args.source, args.sheet)
    layers = find_layers(rows)
    if not layers:
        print("error: no plate grid found (need a row of plate-column numbers "
              "above rows starting with a plate-row letter)", file=sys.stderr)
        return 2

    # Well -> {layer name: value}, in layer order.
    wells: dict[str, dict[str, str]] = {}
    for label, header_index, columns in layers:
        for well, value in read_grid_wells(rows, header_index, columns):
            wells.setdefault(well, {})[label] = value
    grid_wells = [(w, v.get(layers[0][0], "")) for w, v in wells.items()]
    print(f"{len(layers)} layer(s): {', '.join(name for name, _, _ in layers)}")
    print(f"grid: {len(wells)} wells across rows "
          f"{', '.join(sorted({w[0] for w in wells}))}")

    findings = []
    if len(layers) > 1:
        expected = set(wells)
        for label, header_index, columns in layers:
            present = {w for w, _ in read_grid_wells(rows, header_index, columns)}
            missing = expected - present
            if missing:
                findings.append(
                    f"layer {label!r} has no value for {len(missing)} well(s) "
                    f"({', '.join(sorted(missing)[:6])}) that other layers describe"
                )

    seen = {}
    for well, contents in grid_wells:
        seen.setdefault(normalise(contents), []).append(well)
    for contents, matched in seen.items():
        if len(matched) > 1 and "replicate" in contents:
            findings.append(
                f"grid wells {', '.join(matched)} carry identical text but name a replicate "
                f"-- one of them is probably a copy-paste of the other"
            )

    table = find_table(rows)
    if table:
        _, table_rows = table
        table_wells = {r.get("Well", "").strip(): r for r in table_rows if r.get("Well", "").strip()}
        grid_only = [w for w in wells if w not in table_wells]
        table_only = [w for w in table_wells if w not in wells]
        print(f"table: {len(table_wells)} wells")
        if grid_only:
            findings.append(
                f"{len(grid_only)} well(s) are in the grid but not in the table "
                f"({', '.join(grid_only[:8])}{', ...' if len(grid_only) > 8 else ''}) -- "
                f"the merge will drop them and analyse only the rest"
            )
        if table_only:
            findings.append(f"{len(table_only)} well(s) are in the table but not the grid: {', '.join(table_only)}")
        for well, contents in grid_wells:
            row = table_wells.get(well)
            if row and normalise(contents) != normalise(row.get("Name", "")):
                findings.append(f"{well}: grid says {contents!r}, table says {row.get('Name')!r}")
    elif len(layers) == 1:
        print("table: none found on this sheet")

    if args.output:
        layer_columns = [column_name(name) for name, _, _ in layers]
        header = PLATEMAP_COLUMNS + [c for c in layer_columns if c not in PLATEMAP_COLUMNS]
        delimiter = "\t" if args.output.suffix.lower() in {".tsv", ".tab"} else ","
        with args.output.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle, delimiter=delimiter)
            writer.writerow(header)
            for well in sorted(wells, key=lambda w: (w[0], int(w[1:]))):
                values = wells[well]
                row = []
                for column in header:
                    if column == "Well":
                        row.append(well)
                        continue
                    source = next((n for n, _, _ in layers if column_name(n) == column), None)
                    row.append(values.get(source, "") if source else "")
                writer.writerow(row)
        blank = [c for c in PLATEMAP_COLUMNS if c != "Well" and
                 not any(column_name(n) == c for n, _, _ in layers)]
        print(f"wrote {args.output} -- {', '.join(blank)} are blank "
              f"and must be filled in before this is a valid platemap")

    if findings:
        print(f"\n{len(findings)} cross-check finding(s):")
        for finding in findings:
            print(f"  [warn    ] {finding}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
