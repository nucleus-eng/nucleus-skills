---
name: devstudio-write-to-google-drive
description: Create, move, rename, duplicate, or share a Google Drive file for the DevStudio Log/DevNote/Docs pipeline — a new native Doc or Sheet, a raw uploaded file, or a re-parented existing file. Use whenever a DevStudio pipeline skill (Log(G)2DevNote(G), DevNote(G)2DevNote(M), DevNote(M)2Docs(G), Docs(G)2Docs(M)) needs to produce or relocate Drive content. Pairs with devstudio-read-from-google-drive for round-trip verification. This is a staging-namespace (devstudio-) skill — see "Provenance" below before treating it as canonical.
---

# devstudio-write-to-google-drive

## Provenance

Staging skill in the `devstudio` namespace, built for the DevStudio Log/DevNote/Docs
pipeline. Not yet reconciled with any general-purpose Drive-writing skill outside this
namespace. Supersede this if/when a canonical version exists.

## Resolving destinations

Use `devstudio-read-from-google-drive`'s Step 1 (resolve a name/URL/ID to a `fileId`) for
finding the destination folder — that logic isn't repeated here. Never guess a
`parentId`; resolve it first.

## Decision 1 — native or raw?

This is the load-bearing choice for anything this skill creates. Default by pipeline
stage, don't leave it to the caller's discretion:

- **Native (Google Doc/Sheet)** for anything a human will comment on before a "done"
  signal: `DevNote(G)` drafts, `Docs(G)` drafts, any platemap a TA is meant to review.
  Native is required here, not just preferred — `read_file_content`'s `includeComments`
  only works on native `application/vnd.google-apps.*` types. Write raw here and review
  comments become invisible to every downstream skill, silently, with no error.
- **Raw (actual `.docx`/`.xlsx`/`.csv` bytes)** for anything whose only consumer is a
  deterministic tool with no human review step in between (e.g. a platemap about to be
  validated against `nucleus-cdk`'s loader, with no TA reading it first). Going through a
  native round-trip here risks silent type coercion (a numeric cell becoming text, a
  format shift) with no error to flag it — see the platemap-lifecycle note (pinned,
  revisit when building `devstudio-check-platemaper`).

**Mechanics**, both via `create_file`:
- Native: pass `textContent` with `contentMimeType` set to the *source* format you're
  converting from (e.g. `text/plain` for prose destined to become a Doc, `text/csv` for
  data destined to become a Sheet) and leave `disableConversionToGoogleType` unset —
  Drive auto-converts by default.
- Raw: pass the real target `contentMimeType` (e.g.
  `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`) and set
  `disableConversionToGoogleType: true` explicitly. Don't rely on the default — the
  default is conversion, so raw always requires this flag.

## Decision 2 — there is no in-place content update

`update_file` only changes `title` and `parentId`. There is no tool here that rewrites
an existing file's content — not for a Doc, not for a Sheet, not for anything. This
matters for any skill (this one included) that's tempted to describe its job as
"updating" or "correcting" an existing file's content:

- **A pure move/rename** (e.g. `DevNote(M)2Docs(G)`'s "docs page is just a file move"
  case) is genuinely `update_file(fileId, parentId=...)` — content is untouched, this is
  cheap and safe.
- **Anything that changes content** — a corrected platemap, a regenerated draft — must
  be a **new file** via `create_file`, placed in the target folder via `parentId`. It
  does not overwrite the source.

Because of this, any skill that writes a content-changed version of something that
already exists in the same folder **must pick an explicit naming convention up front**
(e.g. a `-validated` suffix, or moving the original into a `raw/` or `originals/`
subfolder first). Drive does not prevent two files from sharing an identical title in
the same folder — it will silently allow it. Never let this skill write a title that
exactly matches an existing sibling unless the calling skill has explicitly decided
that's the intended convention.

## Other operations

- **Duplicate**: `copy_file(fileId, parentId?, title?)` — for template-seeding (e.g.
  instantiating a new experiment folder from the canonical template), not for producing
  corrected content.
- **Share**: `share_file(fileId, emailAddress, role)` — grants access; roles are
  `writer` > `commenter` > `reader`, descending. Use the least privilege that satisfies
  the need (a TA reviewing a draft needs `commenter`, not `writer`).
- **Check who has access**: `get_file_permissions(fileId)` before sharing, to avoid
  redundant grants or silently escalating someone's existing role.
- **Trash**: `trash_file(fileId)` moves to trash, not permanent deletion — but this skill
  should never trash a file it did not itself create in the same session without
  explicit confirmation from the calling context. Cleanup of this skill's own test/scratch
  artifacts is fine; touching anything else is not this skill's call to make.

## Round-trip verification (do this before anything else consumes this skill)

1. `create_file` a small native Doc with known `textContent` in a scratch folder.
2. Hand the returned `fileId` to `devstudio-read-from-google-drive` and confirm
   `read_file_content` returns the same content back.
3. Repeat with a raw file (`disableConversionToGoogleType: true`, e.g. a small CSV) and
   confirm `download_file_content` returns matching bytes.
4. `trash_file` both scratch artifacts once confirmed.

Don't consider this skill validated until both native and raw round-trip, since the two
paths have genuinely different mechanics (auto-convert vs. explicit opt-out) and a pass
on one says nothing about the other.

## Validated (2026-09-05)

Both paths round-tripped byte-for-byte (raw verified via base64 decode, not just visual
inspection). One quirk found: `create_file`'s response `fileSize` is unreliable for a
freshly auto-converted native file (reported `"1"` for real content) — the raw path's
`fileSize` was accurate. Don't use `fileSize` from a native `create_file` response as a
content sanity check; read the file back instead.
