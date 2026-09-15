---
name: devstudio-read-from-google-drive
description: Read a specific Log, DevNote, or Docs file (or folder) from the DevStudio Shared Drive by name, URL, or file ID — a Google Doc, Sheet, .ipynb, or other uploaded file — and return either its narrative content or raw bytes for downstream processing (e.g. pandoc). Use whenever a DevStudio pipeline skill (Log(G)2DevNote(G), DevNote(G)2DevNote(M), DevNote(M)2Docs(G), Docs(G)2Docs(M)) needs to pull source content, and whenever a human points Claude at "this doc," "the log for experiment X," or a pasted Drive link. This is a staging-namespace (devstudio-) skill — see "Provenance" below before treating it as canonical.
---

# devstudio-read-from-google-drive

## Provenance

Staging skill in the `devstudio` namespace, built for the DevStudio Log/DevNote/Docs
pipeline. Not yet reconciled with any general-purpose Drive-reading skill outside this
namespace. Supersede this if/when a canonical version exists.

## Purpose

Resolve a human-given reference (a name, a pasted Drive URL, or an explicit file ID) to
a Drive `fileId`, then read that file's content in whichever form the caller needs:
narrative text for drafting/summarizing, or raw bytes for a downstream tool like pandoc.

This skill is invocation-driven, not autonomous: it acts on a single file (or a named
folder) a human points it at. It does not crawl the Shared Drive looking for work, and
it does not decide when a doc is "ready" — that's always a human call made before this
skill is invoked (see `devstudio-devnote-g-to-devnote-m` and `devstudio-docs-g-to-docs-m`
for where that gate lives).

## Step 1 — Resolve the reference to a fileId

**Never guess or construct a fileId.** If you don't already have one from a prior
`search_files` / `list_recent_files` call or an explicit ID the person typed, get one
first.

- **Pasted Drive/Docs/Sheets URL** — extract the ID directly from the URL path:
  - `https://docs.google.com/document/d/{fileId}/edit...` → Google Doc
  - `https://docs.google.com/spreadsheets/d/{fileId}/edit...` → Google Sheet
  - `https://drive.google.com/file/d/{fileId}/view...` → any other file (e.g. `.ipynb`, `.png`)
  - `https://drive.google.com/drive/folders/{fileId}` → a folder
- **A name or description** ("the log for the pH sensor experiment", "the DevNote doc
  for Cytosol-T7") — call `search_files` with a `title contains` or `fullText contains`
  clause. Scope with `parentId = '<folder id>'` whenever you already know which Node/
  experiment folder you're in — an unscoped `fullText` search across the whole Shared
  Drive is slow and can return the wrong experiment's log.
- **A folder name** (e.g. a Node folder, an experiment subfolder) — same approach,
  filtered to `mimeType = 'application/vnd.google-apps.folder'`.

If `search_files` returns more than one plausible match, list the candidates (title,
last-modified date, path if available) and ask which one, rather than guessing the most
recent.

## Step 2 — Check what you actually have before reading

Call `get_file_metadata` on the resolved `fileId` before deciding how to read it. Do not
assume a file's type — or even its role — from its name. **Do not hardcode expected
filenames anywhere in this pipeline** (e.g. "look for `log.docx`"). Real experiment
folders don't follow the template's example names literally: a log has turned up as a
Google Doc titled `lab-log`, with no `.docx` in sight, and platemaps have turned up as
plain `.tsv` files rather than `.xlsx`. Identify a file by its **role in the folder**
(the one Doc-type file is the log/narrative; the one spreadsheet-or-delimited file next
to it is probably the platemap) and its `mimeType`, never by matching a specific
filename or extension.

Also: `search_files` and `get_file_metadata` both return a `contentSnippet` field by
default for text-bearing files. **Check it before paying for a full read or download.**
It's often enough to answer "what does this say" or "is the platemap referenced in
here" — reserve `read_file_content`/`download_file_content` for when the snippet is
truncated, absent, or the caller genuinely needs the complete content (e.g. handing off
to pandoc).

Route on `mimeType`:

| mimeType | What it is | How to read it |
|---|---|---|
| `application/vnd.google-apps.document` | Native Google Doc (a log, a DevNote(G) draft, a Docs(G) draft) | `read_file_content` for narrative text; add `includeComments: true` if the caller needs to see review comments |
| `application/vnd.google-apps.spreadsheet` | Native Google Sheet (a platemap or experiment-design input) | `read_file_content` for a quick look; `download_file_content` with `exportMimeType: 'text/csv'` or the xlsx MIME type if a downstream tool needs an actual spreadsheet file |
| `application/vnd.openxmlformats-officedocument.wordprocessingml.document` | Un-converted Word file sitting as-is in Drive | `download_file_content` (no `exportMimeType` needed — it's already the target type) to get real bytes for pandoc |
| `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` | Un-converted Excel file | `download_file_content` — same reasoning |
| `application/octet-stream` with `fileExtension: ipynb`, `viewUrl` pointing at `colab.research.google.com` | A Colab-backed notebook, not a plain uploaded file | `download_file_content` — same as any other non-native type, but note: this returns the last state Colab synced back to Drive, which can lag an actively-open Colab session. If results look stale, that's why. |
| anything else (`.tsv`, `.csv`, `.png`, `.gb`, plain-upload `.ipynb`, etc.) | Uploaded raw file — Drive has no native type for these | `download_file_content` — this is the only path; `read_file_content` doesn't support these formats. |
| `application/vnd.google-apps.folder` | A folder, not a file | Don't try to read it — call `search_files` with `parentId = '<this id>'` to list its contents instead |

## Step 3 — Choose narrative vs. raw

Two different needs come up constantly in this pipeline — don't default to one when the
caller needs the other:

- **Narrative / "what does this say"** (drafting, summarizing, checking for review
  comments, deciding what's referenced in a log) → `read_file_content`. Cheaper, and the
  only way to see inline comment threads.
- **Raw bytes for a deterministic downstream tool** (pandoc, a notebook parser, an
  eventual `.csv`/`.xlsx` loader) → `download_file_content`. For Google-native types you
  must pass the `exportMimeType` you actually want (e.g.
  `application/vnd.openxmlformats-officedocument.wordprocessingml.document` for a Doc you
  want to feed to pandoc). For already-non-native types, omit `exportMimeType` — you get
  the file as-is.

If you're not sure which the caller needs, prefer narrative first — it's cheaper and
usually enough to answer "what's in this file."

## Step 4 — Handing off to pandoc (Log(G)2DevNote(G) path)

When a downstream step needs an actual Word file on disk (matching the established
Log → Claude-reads-via-Drive → pandoc → markdown pipeline), for whichever file in the
experiment folder is identified as the log/narrative Doc by Step 2's role-based check —
not by a filename match:

1. `download_file_content(fileId, exportMimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document')`
2. Decode the returned base64, write it to a scratch path (e.g. `/home/claude/`)
3. Hand off to pandoc as normal: `pandoc input.docx -o content.md --extract-media=figures/`

Don't try to reconstruct the `.docx` structure from `read_file_content`'s narrative
output — it's lossy for this purpose (tables, figure placement, and structure don't
survive it cleanly). Always go through `download_file_content` when the destination is a
deterministic converter.

## Validated against a real folder (2026-09-05)

First test run against a live (if hastily-assembled) experiment folder surfaced two
issues, both fixed above: filenames don't follow template examples literally (no
`.docx`, no `.xlsx` — a Doc titled `lab-log` and a `.tsv` platemap), and the skill was
missing the `contentSnippet` shortcut entirely. Folder-routing and mimeType-based
dispatch otherwise held up as designed.

## Known gaps (as of this skill's first draft)

- No folder-crawl / "find everything new since last time" mode yet — every call
  resolves one file or one named folder. Add this only if a real workflow needs it;
  don't build it speculatively.
- Figure-provenance (which platemap/notebook produced a given figure in a `.ipynb`'s
  output) is explicitly out of scope for this skill — that's a separate convention to be
  designed alongside `devstudio-log-to-devnote-g`, not a Drive-reading concern.
- `.ipynb` handling here is read-only and untyped — this skill hands back raw notebook
  JSON; parsing cell outputs, labels, or `glue` tags is the caller's job, not this
  skill's.
