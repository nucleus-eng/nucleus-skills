#!/usr/bin/env python3
"""Check a platemap against the Nucleus CDK's requirements.

Three levels, and the split between the first two is the point:

  blocking  The CDK will silently produce wrong or missing data. The merge is
            an inner join, so an unmatched well is dropped with no error at
            all. You cannot trust the analysis.
  warn      The analysis runs correctly, but the record is incomplete. The
            science is missing something; the code is not.
  info      Cosmetic, or handled by the loader.

Standard library only, so it runs in any checkout. Export .xlsx to CSV or TSV
first -- that is what you should be committing next to the data anyway.

Exit codes: 0 clean, 1 findings, 2 the check could not run.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

# Run from anywhere: platemap_common.py sits beside this file.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from platemap_common import (  # one owner for these -- see platemap_common.py
    ANALYSED, PLATES, REQUIRED, RXN_VOLUME, TYPES, is_blank, plate_rows,
)
# `<artifact> Vol (uL)`, but not the required `Rxn Volume (uL)` itself.
VOL_COL = re.compile(r"^(?P<name>.+?)\s+vol(?:ume)?\s*\(\s*u?[mµ]?l\s*\)$", re.I)
CONC_COL = re.compile(r"^\[(?P<name>.+?)\]\s*\((?P<units>.+?)\)$")
ID_COL = re.compile(r"^(?P<name>.+?)\s+ID$", re.I)
WELL = re.compile(r"^(?P<row>[A-Z]+)(?P<col>\d+)$")
# `N/A` is deliberately NOT here. In a platemap it means "not applicable to
# this well" -- no liposome, no second compartment -- which is data, the text
# form of the deliberate zero. Treating it as a missing value buries a real
# finding under a warning per well.
PLACEHOLDER = re.compile(r"(?:^|\b)(?:XX+|TBD|TODO|\?+|<[^>]*>)(?:\b|$)", re.I)

# A well can hold more than one compartment: an inner solution encapsulated
# in a membrane, sitting in an outer solution. Their volumes do not add up to
# anything meaningful.
COMPARTMENT = re.compile(r"^\[?(IS|OS)[\s\-]", re.I)
DATE_PREFIX = re.compile(r"^(\d{6,8})[-_](.+)$")


class Report:
    def __init__(self) -> None:
        self.items: list[tuple[str, str]] = []

    def add(self, level: str, message: str) -> None:
        self.items.append((level, message))

    def count(self, level: str) -> int:
        return sum(1 for lv, _ in self.items if lv == level)


def read_grid(path: Path) -> list[list[str]]:
    delimiter = "\t" if path.suffix.lower() in {".tsv", ".tab"} else ","
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return [list(row) for row in csv.reader(handle, delimiter=delimiter)]


def find_header(grid: list[list[str]]) -> int:
    """Find the row that names the platemap columns.

    Do not assume row 1. A bench sheet often puts a spatial plate grid, or
    notes, above the well table -- and a header found by position rather than
    by content reports every required column as missing, which is a true
    statement about the wrong row.
    """
    best, best_score = 0, -1
    for index, row in enumerate(grid):
        labels = {str(cell).strip() for cell in row}
        score = sum(1 for column in REQUIRED if column in labels)
        # A near-miss on the volume column still marks the header row.
        if score and any(
            str(cell).strip().lower().endswith("volume (ul)")
            or str(cell).strip().lower() == "volume (ul)"
            for cell in row
        ):
            score += 1
        if score > best_score:
            best, best_score = index, score
    return best if best_score >= 3 else 0


def rows_from(grid: list[list[str]], header_index: int) -> tuple[list[str], list[dict[str, str]]]:
    header = [str(cell).strip() for cell in grid[header_index]]
    out = []
    for row in grid[header_index + 1:]:
        out.append({name: (row[i] if i < len(row) else "") for i, name in enumerate(header) if name})
    return [h for h in header if h], out


def as_number(value):
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def split_blocks(rows: list[dict], fieldnames: list[str]) -> tuple[list[dict], int]:
    """Return the well rows, and how many rows sat below the first blank one.

    A stacked sheet puts assembly recipes under the platemap. Everything from
    the first fully blank row on is a different table -- see
    references/assembly-blocks.md.
    """
    for index, row in enumerate(rows):
        if all(is_blank(row.get(f)) for f in fieldnames):
            return rows[:index], len(rows) - index
    return rows, 0


def column_roles(fieldnames: list[str]) -> tuple[list[str], list[str], list[str]]:
    volumes, concentrations, ids = [], [], []
    for name in fieldnames:
        if name is None or name == RXN_VOLUME:
            continue
        if CONC_COL.match(name):
            concentrations.append(name)
        elif VOL_COL.match(name):
            volumes.append(name)
        elif ID_COL.match(name):
            ids.append(name)
    return volumes, concentrations, ids


def check_wells(rows, plate, instrument, margin, report):
    last_row, last_col = PLATES[plate]
    limit = {name: index for index, name in enumerate(plate_rows(last_row))}

    edge_level = "blocking" if instrument == "microscope" else "warn"
    edge_rows, edge_cols, off_plate = [], [], []

    for row in rows:
        well = str(row.get("Well", "")).strip().replace(":", "")
        match = WELL.match(well)
        if not match:
            report.add("blocking", f"well {well!r}: not an alphanumeric well ID -- will not merge")
            continue
        letters, digits = match.group("row"), match.group("col")
        if digits != str(int(digits)):
            report.add(
                "blocking",
                f"well {well!r}: leading zero. The reader emits {letters}{int(digits)}, "
                f"so this well is dropped by the merge",
            )
            continue
        column = int(digits)
        if letters not in limit or column < 1 or column > last_col:
            report.add("blocking", f"well {well!r}: outside a {plate}-well plate (max {last_row}{last_col})")
            off_plate.append(well)
            continue
        index = limit[letters]
        if index < margin or index > limit[last_row] - margin:
            edge_rows.append(well)
        elif column <= margin or column > last_col - margin:
            edge_cols.append(well)

    # 384 is the default format in this field. If wells fall off a smaller
    # plate but would sit on a 384, say so rather than only reporting the
    # failure -- the flag is more likely wrong than the platemap.
    if plate != 384 and off_plate:
        fits = [w for w in off_plate
                if (m := WELL.match(w)) and m.group("row") <= "P" and int(m.group("col")) <= 24]
        if fits:
            report.add(
                "info",
                f"{len(fits)} of those well(s) are valid on a 384-well plate, which is the "
                f"default format -- if that is the plate, re-run with --plate 384",
            )

    for wells, axis in ((edge_rows, "row"), (edge_cols, "column")):
        wells = list(dict.fromkeys(wells))  # a duplicated well is its own finding
        if wells:
            report.add(
                edge_level,
                f"{len(wells)} well(s) within {margin} of a plate edge by {axis} "
                f"({', '.join(wells[:6])}{', ...' if len(wells) > 6 else ''}) -- "
                + (
                    "meniscus curvature makes edge wells optically unusable"
                    if instrument == "microscope"
                    else "edge wells evaporate faster and read differently"
                ),
            )


def check_missing_information(rows, volumes, concentrations, ids, report):
    """Warn level by definition: the analysis runs, the record is incomplete."""
    for column in concentrations + ids:
        blanks = [r["Well"] for r in rows if is_blank(r.get(column))]
        if len(blanks) == len(rows):
            report.add("warn", f"{column!r} is empty on every row -- this experiment needs it")
        elif blanks:
            report.add("warn", f"{column!r} is empty on {len(blanks)} row(s): {', '.join(blanks[:6])}")

    for row in rows:
        for column, value in row.items():
            if column and not is_blank(value) and PLACEHOLDER.search(str(value)):
                report.add(
                    "warn",
                    f"well {row.get('Well')}: {column!r} holds the placeholder {str(value).strip()!r}",
                )

    if not volumes:
        return

    compartments = sorted({m.group(1).upper() for c in volumes + concentrations
                           if (m := COMPARTMENT.match(c))})
    if len(compartments) > 1:
        report.add(
            "info",
            f"this platemap describes {len(compartments)} compartments per well "
            f"({', '.join(compartments)}) -- component volumes are not summed against "
            f"{RXN_VOLUME}, which describes one compartment, not the whole well",
        )
        return

    for row in rows:
        present = [as_number(row[c]) for c in volumes if not is_blank(row.get(c))]
        target = as_number(row.get(RXN_VOLUME))
        if not present:
            report.add(
                "warn",
                f"well {row.get('Well')} ({row.get('Name')}): no assembly recorded, but "
                f"{RXN_VOLUME} claims {row.get(RXN_VOLUME)} -- volumes unaccounted for",
            )
            continue
        if None in present:
            report.add("warn", f"well {row.get('Well')}: a volume column is not a number")
            continue
        total = sum(present)
        if target is not None and abs(total - target) > 0.01:
            report.add(
                "warn",
                f"well {row.get('Well')} ({row.get('Name')}): components sum to {total:g} uL "
                f"but {RXN_VOLUME} is {target:g}",
            )


def check_consistency(rows, report):
    by_experiment = defaultdict(list)
    for row in rows:
        by_experiment[str(row.get("Experiment", "")).strip()].append(row)

    for experiment, group in by_experiment.items():
        dates = {str(r.get("Date", "")).strip() for r in group}
        if len(group) > 2 and len(dates) == len(group):
            report.add(
                "warn",
                f"experiment {experiment!r}: {len(group)} rows with {len(dates)} distinct "
                f"dates, one per row -- this is the shape of a fill-down artifact",
            )

    # Experiment names that differ only in their leading date token.
    suffixes = defaultdict(set)
    for experiment in by_experiment:
        match = DATE_PREFIX.match(experiment)
        if match:
            suffixes[match.group(2)].add(match.group(1))
    for suffix, prefixes in suffixes.items():
        if len(prefixes) > 1:
            report.add(
                "warn",
                f"experiment {suffix!r} appears under {len(prefixes)} different date "
                f"prefixes ({', '.join(sorted(prefixes))}) -- likely one experiment, two labels",
            )

    # Same Name, different composition.
    composition = defaultdict(set)
    tracked = [c for c in (rows[0] if rows else {}) if c and c not in REQUIRED]
    for row in rows:
        key = tuple((c, str(row.get(c, "")).strip()) for c in tracked)
        composition[str(row.get("Name", "")).strip()].add(key)
    for name, variants in composition.items():
        if len(variants) > 1:
            report.add(
                "warn",
                f"name {name!r} has {len(variants)} different compositions -- identical "
                f"material must use an identical name, or these are different conditions",
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("platemap", type=Path)
    parser.add_argument("--plate", type=int, default=384, choices=sorted(PLATES))
    parser.add_argument(
        "--instrument",
        default="platereader",
        choices=["platereader", "microscope"],
        help="microscope makes the edge-margin rule blocking rather than a warning",
    )
    parser.add_argument("--edge-margin", type=int, default=1, help="rows/columns to keep clear of the edge")
    args = parser.parse_args()

    if not args.platemap.is_file():
        print(f"error: no such file: {args.platemap}", file=sys.stderr)
        return 2
    if args.platemap.suffix.lower() in {".xlsx", ".xls"}:
        print("error: export to CSV or TSV first -- .xlsx does not diff", file=sys.stderr)
        return 2

    try:
        grid = read_grid(args.platemap)
    except (OSError, UnicodeDecodeError, csv.Error) as exc:
        print(f"error: could not read {args.platemap}: {exc}", file=sys.stderr)
        return 2
    if len(grid) < 2:
        print(f"error: {args.platemap} has no data rows", file=sys.stderr)
        return 2

    report = Report()
    header_index = find_header(grid)
    fieldnames, rows = rows_from(grid, header_index)
    if header_index:
        report.add(
            "info",
            f"the column header is on line {header_index + 1}; the {header_index} line(s) "
            f"above it are a different table and were not checked",
        )

    rows, trailing = split_blocks(rows, fieldnames)
    if trailing:
        report.add(
            "info",
            f"{trailing} row(s) below a blank row are a second table (assembly blocks) "
            f"and were not checked as wells -- export the well table alone",
        )
    if not rows:
        print("error: no well rows above the first blank row", file=sys.stderr)
        return 2

    for column in fieldnames:
        if column.startswith("Unnamed:") or column in {"Row", "Column"}:
            report.add("info", f"{column!r} is dropped by the CDK loader")

    missing = [c for c in REQUIRED if c not in fieldnames]
    for column in missing:
        report.add("blocking", f"required column {column!r} is missing")

    for column in [c for c in REQUIRED if c in fieldnames]:
        blanks = [str(r.get("Well", "?")) for r in rows if is_blank(r.get(column))]
        if blanks:
            report.add("blocking", f"required column {column!r} is empty on {len(blanks)} row(s): {', '.join(blanks[:6])}")

    if "Well" in fieldnames:
        check_wells(rows, args.plate, args.instrument, args.edge_margin, report)
        counts = Counter(
            (str(r.get("Date", "")).strip(), str(r.get("Experiment", "")).strip(), str(r.get("Well", "")).strip())
            for r in rows
        )
        repeated = [(w, e, n) for (_, e, w), n in sorted(counts.items()) if n > 1]
        for well, experiment, count in repeated[:5]:
            report.add(
                "blocking",
                f"well {well!r} appears {count} times in experiment {experiment!r} -- "
                f"duplicates multiply rows at the merge",
            )
        if len(repeated) > 5:
            report.add("blocking", f"...and {len(repeated) - 5} further duplicated well(s)")

    if "Type" in fieldnames:
        seen = Counter(str(r.get("Type", "")).strip() for r in rows)
        for value, count in sorted(seen.items()):
            if value in TYPES:
                continue
            if value == "Blank":
                report.add("warn", f"Type 'Blank' on {count} row(s): used by blank_data() but absent from the tutorial's vocabulary")
            else:
                report.add("blocking", f"Type {value!r} on {count} row(s) is outside the vocabulary {sorted(TYPES)}")
        if not any(str(r.get("Type", "")).strip() in ANALYSED for r in rows):
            report.add("warn", f"no row has an analysed type {sorted(ANALYSED)} -- kinetics will return nothing")

        # `Standard` means a calibration standard -- fluorescein, HPTS -- and
        # those wells are excluded from kinetic analysis. It is also an
        # ordinary English word, so it gets used for "the standard protocol"
        # or "the standard prep". That reads as valid and silently drops the
        # wells from the results.
        standards = [r for r in rows if str(r.get("Type", "")).strip() == "Standard"]
        if standards:
            has_concentration = any(
                CONC_COL.match(c) or "concentration" in c.lower() for c in fieldnames
            )
            if not has_concentration:
                report.add(
                    "warn",
                    f"{len(standards)} row(s) typed 'Standard' with no concentration column. "
                    f"'Standard' means a calibration standard and those wells are excluded "
                    f"from kinetics -- if it means 'the standard method' here, these are "
                    f"Samples and they will silently vanish from the results",
                )

    if RXN_VOLUME in fieldnames:
        for row in rows:
            value = as_number(row.get(RXN_VOLUME))
            if value is None:
                report.add("blocking", f"well {row.get('Well')}: {RXN_VOLUME} {row.get(RXN_VOLUME)!r} is not a number")
            elif value <= 0:
                report.add("blocking", f"well {row.get('Well')}: {RXN_VOLUME} is {value:g}")

    volumes, concentrations, ids = column_roles(fieldnames)
    if not concentrations and not volumes:
        report.add("info", "no composition columns -- the tutorial recommends recording what is in each well")
    check_missing_information(rows, volumes, concentrations, ids, report)
    if not missing:
        check_consistency(rows, report)

    order = {"blocking": 0, "warn": 1, "info": 2}
    if not report.items:
        print(f"OK  {len(rows)} wells, {len(fieldnames)} columns, no findings")
        return 0

    print(f"{args.platemap}: {len(rows)} wells, {len(fieldnames)} columns\n")
    for level, message in sorted(report.items, key=lambda item: order[item[0]]):
        print(f"  [{level:<8}] {message}")
    print(
        f"\n{report.count('blocking')} blocking, {report.count('warn')} warn, "
        f"{report.count('info')} info"
    )
    return 1 if report.count("blocking") or report.count("warn") else 0


if __name__ == "__main__":
    sys.exit(main())
