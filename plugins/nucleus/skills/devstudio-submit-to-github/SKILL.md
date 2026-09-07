---
name: devstudio-submit-to-github
description: Open a branch against nucleus-eng/nucleus-devnote-archive-1 and create a draft PR containing a new DevNote directory produced by devstudio-devnote-g-to-devnote-m. Invoked immediately after that skill produces its MyST output. A TA reviews and merges — the GitHub Action fires on merge to main, submitting to the Curvenote venue and publishing to devnotes.nucleus.engineering. This is a staging-namespace (devstudio-) skill — see "Provenance" below before treating it as canonical.
---

# devstudio-submit-to-github

## Provenance

Staging skill in the `devstudio` namespace. Bridges `devstudio-devnote-g-to-devnote-m`'s
MyST output to the `nucleus-eng/nucleus-devnote-archive-1` repo. Relies on GitHub
credentials already configured for the running Claude Code session — confirmed available
for 2 of 4 DevStudio TAs. Supersede once a canonical version exists outside this
namespace.

## Prerequisites

Before running, confirm:
```bash
gh auth status
git -C ~/src/nucleus-eng/nucleus-devnote-archive-1 log --oneline -1
```

If the repo isn't cloned locally:
```bash
git clone https://github.com/nucleus-eng/nucleus-devnote-archive-1.git \
  ~/src/nucleus-eng/nucleus-devnote-archive-1
```

If `gh auth` fails, stop and ask the TA to authenticate before proceeding —
don't attempt to work around missing credentials.

## Step 1 — pull latest main

Always start from a fresh main to avoid branch conflicts:
```bash
cd ~/src/nucleus-eng/nucleus-devnote-archive-1
git checkout main
git pull origin main
```

## Step 2 — create a branch

Branch naming convention: `devstudio/<devnote-slug>` where slug matches the
directory name that will be created under `devnotes/` — e.g.
`devstudio/2026-garenne-pH-sensor`.

```bash
git checkout -b devstudio/<devnote-slug>
```

Never reuse an existing branch — if one already exists for this slug, stop and
ask the TA whether to delete and recreate, or work from the existing branch.

## Step 3 — copy the DevNote directory

Copy the complete directory structure produced by `devstudio-devnote-g-to-devnote-m`
into `devnotes/<devnote-slug>/`:

```bash
cp -r /path/to/produced-devnote/ \
  ~/src/nucleus-eng/nucleus-devnote-archive-1/devnotes/<devnote-slug>/
```

Verify the expected structure is present before committing:
```bash
ls ~/src/nucleus-eng/nucleus-devnote-archive-1/devnotes/<devnote-slug>/
# Expected: main.md, curvenote.yml, base.yml, environment.yml,
#           experiments/, figures/, plasmids/ (if applicable)
```

Flag and stop if `main.md` or `curvenote.yml` are missing — these are the
minimum required for the GitHub Action to run successfully.

## Step 4 — commit

```bash
cd ~/src/nucleus-eng/nucleus-devnote-archive-1
git add devnotes/<devnote-slug>/
git commit -m "Add DevNote: <title> (<devnote-slug>)

Produced by devstudio-devnote-g-to-devnote-m from DevNote(G) draft.
REVIEW items remaining: <count> (see main.md for details).
TA: <ta-name>"
```

List the REVIEW item count in the commit message so the reviewing TA knows
at a glance whether this is clean or needs attention before merging.

## Step 5 — push and open a draft PR

```bash
git push origin devstudio/<devnote-slug>
gh pr create \
  --repo nucleus-eng/nucleus-devnote-archive-1 \
  --base main \
  --head devstudio/<devnote-slug> \
  --title "DevNote: <title>" \
  --body "$(cat << 'EOF'
## DevNote submission — DevStudio pipeline

**Slug**: <devnote-slug>
**Author(s)**: <author names from curvenote.yml>
**Date**: <date from curvenote.yml>

### REVIEW items remaining
<list any open REVIEW flags from main.md and curvenote.yml>

### Asset chain status
<list any figures with asset_chain_complete: false from manifest>

### Checklist for TA before merging
- [ ] All REVIEW flags resolved in main.md and curvenote.yml
- [ ] Corresponding author email and ORCID present in curvenote.yml
- [ ] Keywords added (currently commented out — generate from content)
- [ ] curvenote check bnext-devnotes passes all required checks
- [ ] Notebook(s) in toc are independently runnable or removed
- [ ] thumbnail set to a figure with a solid background

EOF
)" \
  --draft
```

Always open as a **draft PR** — never open as ready-for-review, and never merge.
The TA decides when it's ready to merge.

## Step 6 — run venue checks (optional but recommended)

If the Curvenote CLI is available in the session:
```bash
cd ~/src/nucleus-eng/nucleus-devnote-archive-1/devnotes/<devnote-slug>
curvenote check bnext-devnotes
```

Paste the check output into the PR description as a comment. Known non-blocking
warnings (per `submit.md`):
- `tabSet unhandled JATS conversion` — safe to ignore
- Link 403 errors from NEB, Greiner — safe to ignore
- `abstract missing from typst export` — only needed if PDF output is required

If `curvenote` isn't available, note this in the PR description so the TA knows
to run it manually before merging.

## What this skill does not do

- Does not merge the PR — always a human TA action
- Does not push to `main` directly — branch + draft PR only
- Does not run the GitHub Action — fires automatically on merge to `main`
- Does not generate keywords — still flagged as REVIEW in `curvenote.yml`
- Does not handle the `devnotes.nucleus.engineering` migration — base.yml URLs
  remain as-is until that migration is confirmed complete
- Not yet validated against a real submission — first real test will be the
  pH sensor DevNote once the full G→M→submit pipeline runs end-to-end
