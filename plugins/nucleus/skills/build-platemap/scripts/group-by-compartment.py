#!/usr/bin/env python3
"""Group a harmonized platemap into build-condition table(s) by compartment.

A cytosol-only plate has no membrane -- one table, the whole thing. A plate
running an encapsulated (in-cells) system has three compartments (`IS`, `MB`,
`OS` -- see references/assay-and-specimen.md) and needs three tables, because
a column from one compartment plotted or averaged against a column from
another describes nothing (assay-and-specimen.md's summing rule, one level
up: same problem, table shape instead of arithmetic).

This is the harmonized-platemap-to-DevNote handoff step. It does not flatten,
lay out, or check a platemap -- run flatten-platemap.py / grid-to-platemap.py
/ check-platemap.py first. This script only reads what those produced.

Standard library only. Exit codes: 0 clean, 1 findings, 2 the check could
not run.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from platemap_common import COMPARTMENT_COL, PLATEMAP_COLUMNS  # noqa: E402

# Words in a Name / Experiment column that suggest an in-cells (encapsulated)
# system even if no MB/OS-prefixed column made it into the sheet. A mismatch
# between this and the structural signal (prefixed columns) is worth a
# finding, not a silent override in either direction -- the sheet is what a
# person is claiming, the prose is what they meant, and they can disagree.
ENCAPSULATION_WORDS = ("liposome", "guv", "vesicle", "proteinosome")


def read_rows(path: Path) -> tuple[list[str], list[dict]]:
    with path.open(newline="") as f:
        sniffed = csv.Sniffer().sniff(f.readline(), delimiters=",\t")
        f.seek(0)
        reader = csv.DictReader(f, dialect=sniffed)
        rows = list(reader)
        return reader.fieldnames or [], rows


def classify_columns(fieldnames: list[str]) -> dict[str, list[str]]:
    """Bucket columns into cytosol/membrane/outer_solution/shared."""
    buckets: dict[str, list[str]] = {
        "shared": [], "cytosol": [], "membrane": [], "outer_solution": []
    }
    compartment_to_bucket = {
        "IS": "cytosol", "MB": "membrane", "OS": "outer_solution"
    }
    for col in fieldnames:
        m = COMPARTMENT_COL.match(col)
        if m:
            buckets[compartment_to_bucket[m.group("compartment")]].append(col)
        elif col in PLATEMAP_COLUMNS:
            buckets["shared"].append(col)
        else:
            # Unprefixed composition column (e.g. plain `<artifact> Vol
            # (uL)`). On a cytosol-only plate this is correct as-is. On an
            # in-cells plate it is ambiguous -- flagged below, not guessed.
            buckets["shared"].append(col)
    return buckets


def mentions_encapsulation(rows: list[dict]) -> bool:
    text_cols = ("Name", "Experiment")
    for row in rows:
        for col in text_cols:
            val = (row.get(col) or "").lower()
            if any(word in val for word in ENCAPSULATION_WORDS):
                return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("platemap", type=Path, help="Harmonized platemap CSV/TSV")
    ap.add_argument("-o", "--out-prefix", type=Path, default=None,
                     help="Write table(s) to <prefix>-<compartment>.csv "
                          "(default: alongside the input, same stem)")
    ap.add_argument("--manifest", action="store_true",
                     help="Print the grouping manifest as JSON to stdout "
                          "instead of / in addition to writing tables")
    args = ap.parse_args()

    if not args.platemap.exists():
        print(f"error: {args.platemap} not found", file=sys.stderr)
        return 2

    fieldnames, rows = read_rows(args.platemap)
    if not fieldnames:
        print(f"error: could not read a header row from {args.platemap}",
              file=sys.stderr)
        return 2

    buckets = classify_columns(fieldnames)
    has_membrane_cols = bool(buckets["membrane"] or buckets["outer_solution"])
    encapsulation_mentioned = mentions_encapsulation(rows)

    findings = []
    if has_membrane_cols and not encapsulation_mentioned:
        findings.append(
            "MB/OS-prefixed columns are present but no row's Name/Experiment "
            "mentions liposome/GUV/vesicle/proteinosome -- confirm this is "
            "really an in-cells system before treating it as one."
        )
    if encapsulation_mentioned and not has_membrane_cols:
        findings.append(
            "Name/Experiment mentions liposome/GUV/vesicle/proteinosome but "
            "no MB- or OS-prefixed column exists -- the membrane composition "
            "may be missing from this platemap rather than absent from the "
            "experiment."
        )

    mode = "in_cells" if has_membrane_cols else "cytosol_only"
    stem = args.out_prefix or args.platemap.with_suffix("")

    if mode == "cytosol_only":
        tables = {"cytosol": fieldnames}
    else:
        tables = {
            "cytosol": buckets["shared"] + buckets["cytosol"],
            "membrane": buckets["shared"] + buckets["membrane"],
            "outer_solution": buckets["shared"] + buckets["outer_solution"],
        }
        for name, cols in tables.items():
            if len(cols) == len(buckets["shared"]):
                findings.append(
                    f"'{name}' table has no compartment-specific columns of "
                    f"its own -- only assay-frame columns. Check the {name} "
                    f"composition was recorded."
                )

    manifest = {
        "mode": mode,
        "source": str(args.platemap),
        "tables": {name: {"columns": cols, "path": str(stem) + f"-{name}.csv"}
                   for name, cols in tables.items()},
        "findings": findings,
    }

    for name, cols in tables.items():
        out_path = Path(manifest["tables"][name]["path"])
        with out_path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)

    if args.manifest:
        print(json.dumps(manifest, indent=2))
    else:
        print(f"mode: {mode}")
        for name, info in manifest["tables"].items():
            print(f"  {name}: {len(info['columns'])} columns -> {info['path']}")
        for finding in findings:
            print(f"finding: {finding}")

    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
