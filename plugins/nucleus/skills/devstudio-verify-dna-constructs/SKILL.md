---
name: devstudio-verify-dna-constructs
description: Verify that a DNA construct named in a DevStudio composition table actually corresponds to the sequence file it's claimed to match — by length against the GenBank LOCUS line, not by filename resemblance. Use whenever devstudio-log-to-devnote-g or devstudio-devnote-m-to-docs-g drafts or edits a Composition/Designs table row that names a specific construct, or whenever a human asks "does this construct check out." This is a staging-namespace (devstudio-) skill, narrowly scoped from nucleus-docs' broader construct-verification conventions — see "Provenance" below before treating it as canonical.
---

# devstudio-verify-dna-constructs

## Provenance

Staging skill in the `devstudio` namespace, extracted narrowly from `nucleus-docs`'
`CLAUDE.md` (the DNA-repo verification sections and `check-dna-refs.py`'s identity
rules) for DevStudio's own composition-table needs — not a full port of that content.
The source `CLAUDE.md`'s line numbers have already drifted from what an earlier
extraction plan cited, so this was written by re-locating content by section heading,
not by trusting any previously-recorded line range. Supersede this when nucleus-docs'
own Phase 4 skill extraction lands.

Scope, deliberately narrower than the source material: this skill verifies constructs
named in DevStudio-authored content (Log(G)2DevNote(G) drafts, DevNote(M)2Docs(G)
output). It does not attempt nucleus-docs' full-corpus sweep, its BOM/protocol-pipeline
integration, or its CI wiring — those stay with nucleus-docs.

## The rule this exists to enforce

**Construct↔file identity is a claim, not a guess.** Never place a construct in a
Composition or Designs table because its name resembles a filename in the DNA repo. A
table row asserts *this is that sequence* — that requires evidence, minimally that the
row's stated length (bp) matches the target file's GenBank `LOCUS` length. If the actual
construct differs from the nearest Nucleus construct in any way — tag, backbone,
promoter, codon usage, species variant — that's equivalence, not identity, and belongs
in a caveat note, never as a table row asserting identity. This is the specific failure
mode ("greedy linking") the source material was built to catch: a name-similarity match
getting asserted as sequence identity.

**Checks length, not sequence.** A same-length, different-sequence swap is not
detectable this way — this is a floor, not a full verification.

## Step 1 — locate the DNA repo

Note: "local" here means a git clone of the *canonical* `nucleus-eng/DNA` repo on
whatever filesystem this skill is running from — a different thing from the
current-Drive-folder check in Step 2. Don't conflate the two.

Check for a git clone of the canonical repo first:
```bash
git -C ~/src/nucleus-eng/DNA log --oneline -5
```
If present, this also tells you whether the repo's structure or contents have changed
recently — worth a glance before trusting anything you already know about its layout.

If no clone exists, fall back to fetching the raw file directly — **prefer this
over the GitHub contents API**; the API's unauthenticated rate limit (60 requests/hour)
was hit during this skill's own testing, while raw fetches were not rate-limited:
```bash
curl -s "https://raw.githubusercontent.com/nucleus-eng/DNA/main/<part-type>/<construct-name>.gb" \
  | grep "^LOCUS"
```
Use the contents API only if you need directory listings rather than a known file path:
```bash
curl -s "https://api.github.com/repos/nucleus-eng/DNA/contents/<part-type>/<construct-name>.gb" \
  | jq -r '.content' | base64 -d | grep "^LOCUS"
```

## Step 2 — confirm the file exists before naming it, and don't conflate two different kinds of "missing"

Before a draft names a specific construct (e.g. `pOpen-PURET7-3`), confirm it against
two places — the canonical `nucleus-eng/DNA` repo, and **the Drive folder this skill is
currently pointed at, scoped to that folder only**:

- **Canonical repo check** (Step 1's method): does `<construct-name>.gb` exist in
  `nucleus-eng/DNA`?
- **Current-folder check**: using `devstudio-read-from-google-drive`'s folder-scoped
  `search_files(parentId='<this experiment/DevNote folder's id>')` — not a broader
  search, not a search across other experiments or the wider Shared Drive — does a
  `.gb` file or an explicit construct reference for this name already exist in this
  specific folder? This is deliberately narrow: it answers "is this construct already
  accounted for in what I'm currently working on," not "does this construct exist
  anywhere in DevStudio."

Three outcomes, each a different warning:

- **In the canonical repo** → proceed to Step 3's identity/length check, regardless of
  whether it's also in the current folder.
- **Not in the canonical repo, but present in the current folder** (e.g. a `.gb` file
  someone added alongside this experiment, not yet submitted upstream) → ⚠️ **Warn the
  editor**: *"`<construct>` is used in this folder but not yet in `nucleus-eng/DNA` —
  flag for submission before or alongside migration."* This is the expected, benign
  case for a construct that's new this DevStudio run.
- **Not in the canonical repo, and not in the current folder either** → ⚠️ **Warn the
  editor, more sharply**: *"Construct `<name>` is not in `nucleus-eng/DNA` and no
  matching file was found in this folder — likely a typo, a missing upload, or an
  unaddressed gap, not just a pending submission."* This is the case most likely to be
  an actual mistake rather than a known-pending item, and should read as more urgent
  than the previous case.

**In every case: do not invent a construct name, do not substitute a plausible-looking
neighbor, and do not silently drop the reference.** All three outcomes besides a clean
canonical-repo match are warnings for a human to resolve — never a decision this skill
makes on its own. And regardless of outcome, if the file is found in the canonical repo,
that always takes priority for the identity check in Step 3 — the current-folder check
only matters when the canonical repo doesn't have it.

## Step 3 — verify identity, not resemblance

For each construct actually named with a bp claim in a Composition/Designs table row:

1. Pull the target file's `LOCUS` line (Step 1).
2. Extract the sequence length from it.
3. Compare against the row's stated `Length (bp)`.
4. **Match → identity holds.** Proceed.
5. **Mismatch → this is a real error, not a formatting nit.** Do not silently correct
   the number in the draft — flag it to the human with both values (row's claim vs.
   file's actual length) and let them resolve which is wrong, since a bp mismatch can
   mean the draft has the wrong number *or* the DNA repo has since been corrected out
   from under an existing citation.
6. **Name doesn't obviously relate to the file's `LOCUS` name or filename** (a warn-tier
   case, not blocking) — often a benign alias, but this is exactly the shape of a greedy
   link. Surface it and ask for confirmation rather than silently accepting or silently
   rejecting.
7. **Nothing to verify** (no parseable length, or a table cell with no bp value at all)
   — no action needed; this isn't an error.

## What this skill does not do

- Does not verify sequence identity beyond length — a same-length swap passes this
  check and would need actual sequence comparison to catch.
- Does not run as a standing CI check — this is invoked per-draft, at the point
  `devstudio-log-to-devnote-g` or `devstudio-devnote-m-to-docs-g` produces or edits a
  table row naming a construct, not as a corpus-wide sweep.
- Does not decide whether a missing construct should be submitted to `nucleus-eng/DNA`
  — that's a human call; this skill's job stops at flagging the gap clearly.

## Validated (2026-09-05)

Ran all three cases against the real `nucleus-eng/DNA` repo (no live DevStudio
composition table exists yet, so this validates the mechanism, not a real draft):

- **Match**: `pOpen-PURET7-3`, claimed 2953 bp — `LOCUS` confirms 2953 bp exactly. Pass.
- **Mismatch**: same construct, a claimed 2789 bp against the real 2953 bp — correctly
  a blocking discrepancy under this skill's rule, not something to silently correct.
- **Invented name**: `pOpen-PURET7-99` — doesn't exist; correctly caught before it could
  land in a draft.
- **Notable real-world case**: `pOpen-LacI-IPTG.gb` — the exact construct name
  `nucleus-docs`' own `CLAUDE.md` cites as its worked example for the GitHub-API
  fallback — does not exist in the current DNA repo, checked both via a fresh shallow
  clone and directly on GitHub (missing in both — the genuine-gap case). The real file
  is `pOpen-lacI.gb` (2877 bp, no `-IPTG` in the name). This is a live example of
  source-material drift, not a contrived test case, and it's exactly the failure mode
  Step 2 exists to catch: confirm existence before naming, never substitute a
  plausible-looking neighbor.

**Not yet tested**: Step 2's current-folder check (the branch that distinguishes
"used in this DevStudio folder but not yet upstream" from "missing everywhere") — all
of today's runs went straight against the canonical repo with no Drive folder in the
loop. Needs a real experiment folder with a construct in exactly that state to validate
properly; note this as open until then rather than assuming it works because the
canonical-repo half did.
