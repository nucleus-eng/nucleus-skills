---
name: migrate-devnote
description: Migrate a published DevNote from the Curvenote venue into this repo, make it build, and re-submit it. Use when moving DevNotes into devnotes/, recovering a DevNote's source from a MECA archive, finishing the migration in issue #21, fixing a live DevNote that is not yet in the repo, or debugging a DevNote that fails curvenote check, fails its Typst PDF export, or raises ModuleNotFoundError for cdk in live compute.
---

# Migrate a DevNote

Move a published DevNote into this repo, make it build, and re-submit it.

Every command in the reference files has been run against the live site.
Sources: PRs #9, #13, #16, #20, and the session history in
`devnote-migration-status.md`.

## Licensing gate — read first

This repo is **only** for DevNotes released fully in the open, under CC-BY or a
CERN-OHL-P equivalent. Deciding whether a DevNote *may* be included is a
**human curation step. Never automate it.** Ask the user, and wait.

Most DevNotes still to migrate come from external contributors at the Chicago
and London nodes, so this is a live risk, not a formality.

**Apply the gate per file as well as per DevNote.** A correctly-licensed
DevNote can still carry files that must not be republished. `fwm-aria-d1` is
CC-BY-4.0, but its `data/**/*` glob dragged in 31 PDFs — four third-party
journal papers and an internal meeting-notes file, none referenced by anything
that renders. Before committing any recovered bundle, list what it carries and
ask about anything you did not expect:

```bash
find <devnote> -type f \( -iname '*.pdf' -o -iname '*.doc*' -o -iname '*.xls*' \
  -o -iname '*meeting*' -o -iname '*note*' -o -iname '*copy of*' \) | sort
```

Then check whether each hit is referenced at all. Unreferenced third-party
material is the clearest case to raise, and dropping it changes nothing that
builds.

## The pipeline

```
enumerate → curate (human) → recover source → de-bloat → repair config
   → pin the CDK → execute notebooks → validate → draft → merge to main
```

## Two rules that cause the most damage when broken

1. **`curvenote submit` never re-executes a notebook.** It renders the outputs
   already saved in the `.ipynb`. Fixing code without re-running publishes the
   old, broken outputs. Always re-execute and commit the outputs.
2. **Do not edit collaborator prose.** In `main.md` and notebook *markdown*
   cells, the only permitted edit is a hyperlink's URL. Visible words stay
   byte-identical. Code cells and `curvenote.yml` are fair game. If prose is
   stale, say so in the PR instead of fixing it.

## Reference files

Read the one you need, when you need it. Do not read all four up front.

| File | Covers |
|---|---|
| `references/recover.md` | Enumerate what is published; recover source from a MECA archive |
| `references/prepare.md` | De-bloat the bundle; repair `curvenote.yml`; pin `nucleus-cdk` |
| `references/verify-submit.md` | Execute notebooks; validate; submit; update the tracker |
| `references/snags.md` | Symptom → cause → fix table; what to automate and what not to |

If something breaks and you do not know why, go to `references/snags.md` first.
Most failures here have been seen before.

## State lives elsewhere

`devnote-migration-status.md` at the repo root records which DevNotes exist,
which are live, and which still need migrating. This skill records **method**;
that file records **state**. Update it whenever you migrate a DevNote, and
regenerate its counts rather than editing them by hand.
