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
import subprocess
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

# Run from anywhere: platemap_common.py sits beside this file.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from platemap_common import (  # one owner for these -- see platemap_common.py
    ANALYSED, PLATES, PLATEMAP_COLUMNS, RECOMMENDED, REQUIRED, RXN_VOLUME,
    TYPES, is_blank, plate_rows,
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
# The DevNote mandates yyyy-mm-dd and warns against mm/dd/yy and dd/mm/yy by
# name, "that can cause confusion due to differences in use by country".
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}(?:[ T]\d{2}:\d{2}(?::\d{2})?)?$")
SEPARATED = re.compile(r"^(\d{1,4})[/.\-](\d{1,2})[/.\-](\d{1,4})$")


class Report:
    def __init__(self) -> None:
        self.items: list[tuple[str, str]] = []

    def add(self, level: str, message: str) -> None:
        self.items.append((level, message))

    def count(self, level: str) -> int:
        return sum(1 for lv, _ in self.items if lv == level)


def read_provenance(path: Path) -> dict:
    """Read a provenance sidecar.

    JSON, or the small subset of YAML these files need, so the checker keeps
    its standard-library-only promise. PyYAML is used when available.
    """
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json" or text.lstrip().startswith("{"):
        import json
        return json.loads(text)
    try:
        import yaml
        return yaml.safe_load(text) or {}
    except ImportError:
        pass
    # Minimal YAML: top-level `key: value`, and two-level blocks whose entries
    # are `name: {a: x, b: y}` or `name: value`. Enough for this sidecar.
    def fields(value):
        out = {}
        for part in value.strip("{}").split(","):
            if ":" in part:
                k, _, v = part.partition(":")
                out[k.strip()] = v.strip().strip("\"'")
        return out

    out, block, name = {}, None, None
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line.startswith((" ", "\t")):
            key, _, value = line.partition(":")
            key, value = key.strip(), value.strip()
            if value:
                out[key] = value.strip("\"'")
                block = None
            else:
                block = out.setdefault(key, {})
            continue
        if block is None:
            continue
        key, _, value = line.strip().partition(":")
        key, value = key.strip().strip("\"'"), value.strip()
        block[key] = fields(value) if value.startswith("{") else (value.strip("\"'") if value else {})
    return out


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
        score = sum(1 for column in PLATEMAP_COLUMNS if column in labels)
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

    # A reagent's compartment decides what its volume means, so resolve the
    # coordinate BEFORE reading the amount -- and per row, not per column. A
    # substance can sit in different compartments in different wells; in one
    # real plate `[aTc]` was ambient in 25 wells and interior in the 26th,
    # which was the control. Skipping the sum entirely (the earlier fix here)
    # traded false findings for no coverage at all.
    by_compartment: dict[str, list[str]] = defaultdict(list)
    for column in volumes:
        match = COMPARTMENT.match(column)
        by_compartment[match.group(1).upper() if match else ""].append(column)

    columns_present = [c for c in (rows[0] if rows else {}) if c]
    totals = {}
    for compartment in by_compartment:
        if not compartment:
            continue
        for column in columns_present:
            m = re.match(rf"^{compartment}\s+Volume\s*\(\s*u?[mµ]?[lL]\s*\)$", column, re.I)
            if m:
                totals[compartment] = column

    named = sorted(c for c in by_compartment if c)
    if len(named) > 1:
        report.add(
            "info",
            f"{len(named)} compartments per well ({', '.join(named)}) -- volumes are summed "
            f"within each, never across, because {RXN_VOLUME} describes one compartment",
        )
        # In a multi-compartment plate, a volume column with no compartment
        # cannot be summed against anything: nothing says which side of the
        # membrane it is on.
        for column in by_compartment.get("", []):
            report.add(
                "warn",
                f"{column!r} names no compartment on a plate that has {', '.join(named)} -- "
                f"prefix it (e.g. 'IS {column}') so it can be checked",
            )

    for row in rows:
        for compartment, columns in sorted(by_compartment.items()):
            target_column = totals.get(compartment)
            if len(by_compartment) > 1 and not target_column:
                continue          # no stated total for this compartment; nothing to check against
            # A compartment's own total is not one of its components.
            parts = [c for c in columns if c != target_column]
            if not parts:
                # This compartment has a stated total and no component columns
                # at all -- an outer solution given only as a concentration,
                # for instance. That is a fact about the schema, not about a
                # row, so it is not reported once per well.
                continue
            values = {c: as_number(row[c]) for c in parts if not is_blank(row.get(c))}
            target = as_number(row.get(target_column) if target_column else row.get(RXN_VOLUME))
            where = f" in {compartment}" if compartment else ""
            if not values:
                if target is not None:
                    report.add(
                        "warn",
                        f"well {row.get('Well')} ({row.get('Name')}): no assembly recorded{where}, "
                        f"but {target_column or RXN_VOLUME} claims {target:g} -- volumes unaccounted for",
                    )
                continue
            if None in values.values():
                report.add("warn", f"well {row.get('Well')}: a volume column{where} is not a number")
                continue
            if target is None:
                continue
            total = sum(values.values())
            if abs(total - target) > 0.01:
                # A named sub-mix expanded into its parts must not also be
                # counted as itself. When the excess equals one column exactly,
                # that column is almost always the un-dropped roll-up.
                excess = total - target
                culprit = next((c for c, v in values.items() if abs(v - excess) < 0.01), None)
                hint = (f" -- the excess is exactly {culprit!r}; if that is a sub-mix whose "
                        f"components are also listed, it is being counted twice") if culprit else ""
                report.add(
                    "warn",
                    f"well {row.get('Well')} ({row.get('Name')}): components{where} sum to "
                    f"{total:g} uL but {target_column or RXN_VOLUME} is {target:g}{hint}",
                )


def check_pin(label, pin, report):
    """Check a `{path, blob}` pin.

    `path` is where the file was; `blob` is what it was. Both are needed and
    they answer different questions -- a path rots, and a digest alone cannot
    be looked up. `blob` is git's own digest, from `git hash-object`, which
    depends on content alone: it is the same before and after the file is
    committed, in any repository, at any path, and works in a directory with
    no git history at all.

    When the path still resolves here, the digest is recomputed. A mismatch
    means the file moved on after the pin was taken, which is the whole reason
    to record one.
    """
    if isinstance(pin, str):
        report.add("warn", f"provenance {label!r} is a bare path, not a pin -- add a `blob:` "
                           f"from `git hash-object`, or nothing records which version this was")
        return
    if not isinstance(pin, dict):
        return
    path, blob = str(pin.get("path", "")).strip(), str(pin.get("blob", "")).strip()
    if not blob:
        report.add("warn", f"provenance {label!r} names a path but no `blob:` -- a path says "
                           f"where, not which version")
        return
    if not path:
        report.add("info", f"provenance {label!r} has a blob but no path -- the identity is "
                           f"recorded, but nothing says where to look")
        return
    target = Path(path)
    if not target.is_file():
        report.add("info", f"provenance {label!r} points at {path!r}, which is not here -- the "
                           f"blob still identifies it, so this is not an error")
        return
    try:
        actual = subprocess.run(["git", "hash-object", str(target)],
                                capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return          # git absent, or it declined; the pin is simply unverified
    if actual != blob:
        report.add(
            "warn",
            f"provenance {label!r} pins {blob[:12]} but {path!r} is now {actual[:12]} -- the "
            f"file changed after the pin was taken, so what this platemap was derived from is "
            f"not what is there now",
        )


def check_provenance(rows, fieldnames, provenance, report):
    """Check a platemap against a sidecar recording where each value came from.

    Four states. `source` is verbatim, `derived` is computed from the input,
    `imputed` is inferred from context, `assumed` is chosen and needs review.

    The rule that matters is the one joining provenance to the kind of
    platemap: a **retrospective** platemap records a run that already
    happened, so its wells are facts. Generating them is fabrication, and a
    fabricated well either mislabels a real row or drops it. That combination
    -- retrospective, and `Well` assumed -- is the only blocking finding here.
    """
    kind = str(provenance.get("platemap_kind", "")).strip().lower()
    columns = provenance.get("columns") or {}

    # `source` is where this platemap came from. `recipe` is the composition
    # its specimen columns derive from. Different claims, both worth pinning.
    for label in ("source", "recipe"):
        if label in provenance:
            check_pin(label, provenance[label], report)
    if kind not in {"prospective", "retrospective"}:
        report.add(
            "warn",
            "provenance does not say whether this platemap is prospective (a plan, where "
            "generating wells is the deliverable) or retrospective (a record, where wells "
            "are facts) -- without that, an invented well cannot be told from a real one",
        )

    states = {}
    for column in fieldnames:
        entry = columns.get(column)
        state = str((entry or {}).get("state", "")).strip().lower() if isinstance(entry, dict) else str(entry or "").strip().lower()
        states[column] = state
        if not state:
            report.add("warn", f"{column!r} has no provenance entry -- nothing records where its values came from")
        elif state not in {"source", "derived", "imputed", "assumed"}:
            report.add("warn", f"{column!r} has provenance state {state!r}, which is not one of source/derived/imputed/assumed")

    if kind == "retrospective" and states.get("Well") == "assumed":
        note = (columns.get("Well") or {}).get("note", "")
        report.add(
            "blocking",
            f"this platemap is retrospective and its wells are marked 'assumed' -- the wells "
            f"of a completed run are facts to be recovered, not generated. A generated well "
            f"merges against whatever real data sits at that position, or drops silently"
            + (f" ({note})" if note else ""),
        )

    assumed = sorted(c for c, st in states.items() if st == "assumed")
    if assumed:
        report.add(
            "info",
            f"{len(assumed)} column(s) are marked 'assumed' and need review before this is "
            f"trusted: {', '.join(assumed)}",
        )


def check_pipettable(rows, volumes, minimum, report):
    """Flag volumes too small to pipette.

    A recipe rescaled to a different basis keeps its concentrations, so every
    arithmetic check still passes -- but the volumes stop being things anyone
    can measure. A 0.1 uL draw is the visible symptom of a transformation
    nobody declared.

    Reported at info, not warn, and that is deliberate. A column may hold a
    volume nobody ever pipetted -- the components of an expanded sub-mix are
    drawn once as the mix, not individually -- and nothing in the platemap
    distinguishes those from a direct draw. Only provenance knows. So this
    raises a question rather than making a claim.
    """
    offenders = defaultdict(list)
    for row in rows:
        for column in volumes:
            value = as_number(row.get(column))
            if value is not None and 0 < value < minimum:
                offenders[column].append((str(row.get("Well", "?")) or "?", value))
    for column, hits in sorted(offenders.items()):
        smallest = min(v for _, v in hits)
        report.add(
            "info",
            f"{column!r} is below {minimum:g} uL on {len(hits)} row(s), smallest {smallest:g}. "
            f"If that is a direct draw it is hard to pipette accurately, and a recipe rescaled "
            f"from a larger basis is the usual cause -- concentrations survive a rescaling, "
            f"volumes do not. If it is a component of an expanded sub-mix, ignore this",
        )


def check_substituted_zeros(rows, volumes, concentrations, report):
    """Find zeros that may be false claims of absence.

    A `0` asserts there is none. That is only true when the whole recipe is
    visible. If a row draws on an opaque component -- a commercial kit whose
    contents are not recorded anywhere -- then a substance missing from the
    itemised list may still be in the well, and the honest value is blank.

    This needs no registry of kit names. The signature is structural: a column
    that is zero in some rows and real in others, where the zero rows all
    contain something the real rows never do. That something is a substitute,
    and the zero is a question rather than a fact.
    """
    def value(row, column):
        return as_number(row.get(column))

    # substitute component -> the columns it may be silently supplying
    # Concentration columns only. A VOLUME of 0 is a fact about pipetting --
    # a NEB reaction really does contain 0 uL of SMix, even though it contains
    # small molecules by another route. A CONCENTRATION of 0 is a claim about
    # what is in the well, and that is the claim an opaque component falsifies.
    # A fold unit (`x`, `1x`, `3.33x`) is a PRODUCT's dilution, not a
    # substance's presence. "0x Sol A" in a reaction that uses no Sol A is a
    # fact, not a claim about contents. Only molar and mass units describe
    # what is in the well.
    def is_fold(column):
        m = CONC_COL.match(column)
        return bool(m) and m.group("units").strip().lower() in {"x", "\u00d7", "fold"}

    suspects: dict[str, list[str]] = defaultdict(list)
    for column in concentrations:
        if is_fold(column):
            continue
        zero_rows, real_rows = [], []
        for row in rows:
            v = value(row, column)
            if v is None:
                continue
            (zero_rows if v == 0 else real_rows).append(row)
        if not zero_rows or not real_rows:
            continue
        for other in volumes:
            if other == column:
                continue
            if not all((value(r, other) or 0) > 0 for r in zero_rows):
                continue
            if not all((value(r, other) or 0) == 0 for r in real_rows):
                continue
            share = min((value(r, other) or 0) / (as_number(r.get(RXN_VOLUME)) or 1)
                        for r in zero_rows)
            if share < 0.05:
                continue        # a trace component substitutes for nothing
            # The relation is otherwise symmetric -- each column looks like the
            # other's substitute. A substitute supplies more than it replaces,
            # so break the tie on volume.
            suspects[other].append(column)
            break

    # The relation can still look mutual across a volume/concentration pair.
    # Keep the side that explains more, and drop the mirror.
    for candidate in list(suspects):
        for rival, columns in suspects.items():
            if rival != candidate and candidate in columns and len(columns) > len(suspects[candidate]):
                del suspects[candidate]
                break

    for other, columns in sorted(suspects.items()):
        shown = ", ".join(columns[:4]) + (", ..." if len(columns) > 4 else "")
        report.add(
            "warn",
            f"{len(columns)} column(s) are 0 only on rows containing {other!r}, which no other "
            f"row has ({shown}). If {other!r} supplies them, those zeros claim an absence that "
            f"is not true -- blank means unknown, 0 means none",
        )


def check_date_format(rows, report):
    """Dates must read the same way in every country.

    `11/19/25` happens to resolve -- 19 is not a month -- but `01/02/25` does
    not, and no later reader can recover which was meant. The record is wrong
    in a way that cannot be repaired, which is why an ambiguous date is worth
    saying more loudly than a merely non-standard one.
    """
    seen = Counter(str(r.get("Date", "")).strip() for r in rows if not is_blank(r.get("Date")))
    if not seen:
        return

    shapes = set()
    for value, count in sorted(seen.items()):
        if ISO_DATE.match(value):
            shapes.add("yyyy-mm-dd")
            continue
        match = SEPARATED.match(value)
        if not match:
            shapes.add("other")
            report.add("warn", f"Date {value!r} on {count} row(s) is not yyyy-mm-dd")
            continue
        first, second, third = match.groups()
        shapes.add("separated")
        problems = []
        if len(first) <= 2 and int(first) <= 12 and int(second) <= 12:
            problems.append(
                f"{first}/{second} could be month/day or day/month, and no later reader "
                f"can tell which was meant"
            )
        if len(third) <= 2:
            problems.append(f"the year {third!r} has no century")
        detail = "; ".join(problems) if problems else "the DevNote asks for yyyy-mm-dd"
        report.add(
            "warn" if problems else "info",
            f"Date {value!r} on {count} row(s): {detail}",
        )

    if len(shapes) > 1:
        report.add(
            "warn",
            f"{len(shapes)} different date formats in one platemap ({', '.join(sorted(shapes))}) "
            f"-- whichever is right, they cannot all be",
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
    tracked = [c for c in (rows[0] if rows else {}) if c and c not in PLATEMAP_COLUMNS]
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
    parser.add_argument(
        "--provenance",
        type=Path,
        help="sidecar recording where each column's values came from, and whether this "
             "platemap is prospective or retrospective",
    )
    parser.add_argument(
        "--min-volume",
        type=float,
        default=0.2,
        help="smallest reliably pipettable volume in uL (default 0.2)",
    )
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

    # A condition table is a legitimate intermediate artifact -- extract-conditions
    # produces one, with no Well column by design, because a write-up records
    # chemistry and never records layout. Say that once, rather than reporting
    # every row as a broken well.
    wells_blank = "Well" in fieldnames and all(is_blank(r.get("Well")) for r in rows)
    if wells_blank:
        report.add(
            "blocking",
            f"every 'Well' is empty across {len(rows)} rows -- this is a condition table, "
            f"not a platemap. It needs a layout: plate format, replicate count, and wells",
        )

    missing = [c for c in REQUIRED if c not in fieldnames]
    for column in missing:
        report.add("blocking", f"required column {column!r} is missing")
    for column in RECOMMENDED:
        if column not in fieldnames:
            report.add(
                "warn",
                f"{column!r} is missing -- the DevNote lists it as optional, but without it "
                f"nothing can check that a well's components account for its volume",
            )

    for column in [c for c in PLATEMAP_COLUMNS if c in fieldnames]:
        if column == "Well" and wells_blank:
            continue        # already reported once, above
        blanks = [str(r.get("Well", "?")) or "?" for r in rows if is_blank(r.get(column))]
        if blanks:
            report.add("blocking", f"required column {column!r} is empty on {len(blanks)} row(s): {', '.join(blanks[:6])}")

    if "Well" in fieldnames and not wells_blank:
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

    if "Date" in fieldnames:
        check_date_format(rows, report)

    if args.provenance:
        if not args.provenance.is_file():
            print(f"error: no such provenance file: {args.provenance}", file=sys.stderr)
            return 2
        try:
            provenance = read_provenance(args.provenance)
        except ValueError as exc:
            print(f"error: could not read {args.provenance}: {exc}", file=sys.stderr)
            return 2
        check_provenance(rows, fieldnames, provenance, report)

    volumes, concentrations, ids = column_roles(fieldnames)
    check_pipettable(rows, volumes, args.min_volume, report)
    if not concentrations and not volumes:
        report.add("info", "no composition columns -- the tutorial recommends recording what is in each well")
    check_missing_information(rows, volumes, concentrations, ids, report)
    check_substituted_zeros(rows, volumes, concentrations, report)
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
