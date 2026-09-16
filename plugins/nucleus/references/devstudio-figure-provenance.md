# The figure-provenance record

One record, two encodings. A figure in a DevNote has to carry where it came
from: which notebook drew it, which platemap and raw data it was drawn from.
That record is written twice by `devstudio-log-to-devnote-g` — once as JSON in
`manifest.json`, once as a line of text in the DevNote(G) Doc body.

This file owns both encodings. It exists as one file, rather than one per
encoding, because the two must agree about what the record contains: a field
documented in one and missing from the other is a figure whose data nobody can
find. That has already happened once — `data_source` was documented in the
pipeline reference and absent from the skill that writes the manifest, so the
producer emitted manifests the asset-assembly stage could not fully read.

`devstudio-pipeline.md` says which stage produces and consumes this record.
It does not restate the format; read it here.

## Why both encodings exist

`manifest.json` is machine-readable and sits beside the Doc. The inline line is
human-readable and sits *in* the Doc, immediately after the prose its figure
belongs to.

`devstudio-devnote-g-to-devnote-m` prefers the manifest, and falls back to the
inline line when the manifest is absent or when the Doc was edited after the
manifest was generated. That fallback is the whole reason for the second
encoding: a TA who adds a figure while reviewing the Doc cannot update a JSON
file they never see.

## They are not field-for-field equivalent

Calling the line "the human-readable equivalent of `manifest.json`" overstates
it. The overlap is the provenance chain; each encoding carries fields the other
does not.

| Record field | `manifest.json` key | inline key | Notes |
| --- | --- | --- | --- |
| Figure label | `cell_label` | first position, `` `fig:…` `` | Backtick-quoted in the line |
| Image file | `filename` | — | Line identifies by label, not path |
| Source notebook | `source_notebook` | `notebook:` | |
| Platemap | `platemap` | `platemap:` | Filename, never a Drive URL; `null` when absent |
| Raw data | `data_source` | `data source:` | **Spelling differs between encodings** — underscore in JSON, space inline. Unresolved: see "Open" below. |
| Caption | — | `caption: (…)` | Manifest carries no caption |
| Zarr URL | `zarr_url` | `source:` | Only in the `zarr-viewer` variant |
| Schematic path | — | `file:` | Only in the schematic variant |
| Figure pattern | `pattern` | implied by variant | |
| Narrative context | `section_context` | implied by position in the Doc | |
| Asset chain intact | `asset_chain_complete` | — | Manifest only |
| How it was extracted | `extraction_method` | — | Manifest only |
| Non-blocking notes | `findings` | — | Manifest only |

A field added to one encoding must be considered for the other, and this table
is where that decision is recorded.

## Encoding 1 — `manifest.json`

Written alongside the DevNote(G) Doc. Discarded after asset assembly; it is not
DevNote content and does not travel to the archive.

```json
{
  "figures": [
    {
      "filename": "figures/image1.png",
      "pattern": "embedded-in-doc | quarto-label | static-png | zarr-viewer",
      "cell_label": "20251212-kinetics",
      "source_notebook": "YYYYMMDD-slug/Analysis.ipynb",
      "platemap": "YYYYMMDD-slug/filename.csv",
      "data_source": "YYYYMMDD-slug/filename.txt",
      "zarr_url": "https://data.nucleus.engineering/path/to/data.zarr",
      "section_context": "Experiment 1 — pOpen-deGFP expression",
      "asset_chain_complete": true,
      "extraction_method": "notebook cell output | pandoc --extract-media",
      "findings": []
    }
  ]
}
```

Field rules:

- `pattern` — one of the four values above. `quarto-label` requires `cell_label`.
- `cell_label` — whatever string the notebook author wrote after `#| label:`.
  Never reformatted. Only flagged when two cells **in the same notebook** collide;
  labels in different notebooks never collide, because MyST scopes them per file.
- `platemap`, `data_source` — filenames, not Drive URLs. `null` when not found.
- `zarr_url` — present only when `pattern` is `zarr-viewer`. Never fetch its
  content at the G stage; just record it.
- `asset_chain_complete` — `false` when no notebook was found for an embedded
  figure, or when the platemap or raw data cannot be confirmed present.
- `findings` — non-blocking strings, e.g. a duplicate-`cell_label` warning.

## Encoding 2 — the inline provenance line

One line, written into the Doc body immediately after the prose its figure
belongs to. Named fields, **values backtick-quoted**, caption in parentheses.

```
[`fig:kinetics-exp1`, notebook:`Analysis.ipynb`, platemap:`20251104-NucleusPURE-deGFP-platemap.csv`, data source:`2025-11-04`, caption: (Translation kinetics of Cytosol and PURExpress reactions using two different pOpen-deGFP DNA preps.)]
```

**The backticks are load-bearing** — `devstudio-devnote-g-to-devnote-m` parses
this line. An un-backticked variant circulated in
`devstudio-assemble-devnote-assets` for a while; a parser written for one form
mis-reads the other. Write the quoted form.

Where a field is genuinely unknown, write `platemap: none` rather than omitting
the field.

**Zarr microscopy references:**
```
[zarr-viewer, source:`https://data.nucleus.engineering/path/to/data.zarr`, caption: (Interactive microscopy viewer.)]
```

**Schematics pre-placed in `general/`:**
```
[`fig:schematic-overview`, file:`general/schematic-overview.png`, caption: (Schematic overview.)]
```

A schematic has no notebook, platemap or data chain — it is not a data figure,
and it is referenced by path because it is placed in `general/` before the G
stage rather than extracted from the Doc.

### Legacy multi-line format

DevNote(G) Docs authored before the single-line format was standardised use a
block. `devstudio-devnote-g-to-devnote-m` still reads it; nothing writes it.

```
Figure N: [caption text]
Analysis: [notebook filename]
Data: [URL or filename]
Platemap: [filename]
```

## Open

**`data_source` versus `data source`.** The JSON key uses an underscore, the
inline key a space. Both spellings are in use across the pipeline today. Whether
that is a deliberate per-encoding convention or a typo that propagated has not
been ruled on — changing the inline spelling is a breaking change to a format
`devstudio-devnote-g-to-devnote-m` parses, so it is recorded here rather than
quietly fixed.
