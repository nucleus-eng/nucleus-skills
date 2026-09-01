"""Shared definitions for the platemap scripts.

The six required columns are owned by the platemap tutorial at
docs.nucleus.engineering/guides/platemap-tutorial/. This is a port -- keep it
in sync with that page. It lives here, once, because three scripts need it,
and three copies of a definition is how two copies come to disagree.
"""

from __future__ import annotations

import csv
from pathlib import Path

REQUIRED = ["Date", "Experiment", "Well", "Name", "Type", "Rxn Volume (uL)"]
RXN_VOLUME = "Rxn Volume (uL)"

TYPES = {"Sample", "Standard", "Control", "Positive Control", "Negative Control"}
# DEFAULT_ANALYSIS_COLUMNS in the CDK's platereader.py -- kinetics runs on these only.
ANALYSED = {"Sample", "Control", "Positive Control"}

# Last row letter and last column, per plate format. 384 is the default here.
PLATES = {96: ("H", 12), 384: ("P", 24), 1536: ("AF", 48)}


def plate_rows(last_row: str) -> list[str]:
    """Row labels up to `last_row`: A..Z, then AA..AF for 1536."""
    single = [chr(c) for c in range(ord("A"), ord("Z") + 1)]
    labels = single + [f"A{c}" for c in single]
    return labels[: labels.index(last_row) + 1]


def is_blank(value) -> bool:
    return value is None or str(value).strip() == ""


def load_grid(path: Path, sheet: str | None = None) -> list[list]:
    """Read a sheet as a raw grid of cells. Handles .xlsx, .csv and .tsv."""
    if path.suffix.lower() in {".xlsx", ".xlsm"}:
        try:
            import openpyxl
        except ImportError as exc:
            raise SystemExit("error: reading .xlsx needs openpyxl (pip install openpyxl)") from exc
        book = openpyxl.load_workbook(path, data_only=True)
        worksheet = book[sheet] if sheet else book.worksheets[0]
        return [
            [worksheet.cell(r, c).value for c in range(1, worksheet.max_column + 1)]
            for r in range(1, worksheet.max_row + 1)
        ]
    delimiter = "\t" if path.suffix.lower() in {".tsv", ".tab"} else ","
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return [list(row) for row in csv.reader(handle, delimiter=delimiter)]
