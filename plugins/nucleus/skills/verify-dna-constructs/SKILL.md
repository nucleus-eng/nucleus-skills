---
name: verify-dna-constructs
description: Verify that a DNA construct named in nucleus-docs matches a real sequence file in nucleus-eng/DNA. Use before naming a construct in a protocol step, before adding or editing a Designs table row, and when running or interpreting `scripts/check-dna-refs.py`. Covers the cross-repo rules, the GitHub API fallback, and the identity-versus-equivalence distinction.
---

# Verify DNA constructs

Sequence files for every plasmid and construct referenced in nucleus-docs live in a separate repository: **[nucleus-eng/DNA](https://github.com/nucleus-eng/DNA)** (local path: `~/src/nucleus-eng/DNA`). This skill covers how to check a construct claim against that repo.

## Repository layout

The DNA repo stores GenBank (`.gb`) files organized by part type:

```
DNA/
├── PURE/
│   ├── cloning/      # pOpen entry vectors for all PURE system proteins
│   └── expression/   # pET28a expression vectors for PURE system proteins
├── assembly/         # MoClo backbone (pOpen-pOpenv3-MCL0)
├── RBS/              # Ribosome binding site and UTR parts
├── promoters/        # Level-matched T7 promoter library (PURET7-1 through -10)
├── reporters/        # Fluorescent protein and chromoprotein reporters
├── terminators/      # T7 terminator variants
└── detectors/        # LacI/TetR circuits and quorum sensing components
```

## Checking the DNA repo's current state

The DNA repo evolves independently — always verify its current state before writing or editing content that references specific constructs. Use a tiered approach:

1. **Session start** — when beginning any work that involves DNA construct references, check recent activity in the DNA repo:
   ```bash
   git -C ~/src/nucleus-eng/DNA log --oneline -5
   ```
   Commit messages will tell you if the structure or contents have changed since you last worked with it.

2. **Before naming a specific construct** — before writing a protocol step that references a construct by filename (e.g., `pOpen-PURET7-3`), confirm the file exists:
   ```bash
   ls ~/src/nucleus-eng/DNA/promoters/pOpen-PURET7-3.gb
   ```
   If the file is missing, flag it to the developer — do not invent construct names or create placeholder references.

3. **If folder structure is uncertain** — if you are unsure which subdirectory a part type lives in, read the DNA repo's README (`~/src/nucleus-eng/DNA/README.md`). The README is maintained as the canonical description of the repo structure.

4. **If `~/src/nucleus-eng/DNA` is not on this machine** — use the GitHub API as a fallback to browse the repo or inspect construct files without cloning:
   ```bash
   # Browse a directory (e.g. detectors/)
   gh api "repos/nucleus-eng/DNA/contents/detectors" --jq '.[].name'
   # Decode a GenBank file and read the LOCUS line for construct length
   gh api "repos/nucleus-eng/DNA/contents/detectors/pOpen-LacI-IPTG.gb" --jq '.content' | base64 -d | grep "^LOCUS"
   ```

## Key rules when working across both repos

- **Do not create or store `.gb` sequence files in nucleus-docs.** All DNA sequences belong in the DNA repo.
- **Construct names in protocol pages must match actual filenames** in the DNA repo (e.g., a step that says "use `pOpen-PURET7-3`" corresponds to `promoters/pOpen-PURET7-3.gb`). Verify before writing.
- **Cross-repo links** in doc pages should point to the GitHub URL of the `.gb` file in `nucleus-eng/DNA`, not to a local path.
- **Changes to the DNA repo are out of scope for nucleus-docs PRs.** If a construct referenced in a source page is not found in `nucleus-eng/DNA`, add an `:::{attention}` block in the spec noting the gap, e.g.: "Construct `pT7-aHly` is not yet in `nucleus-eng/DNA` (originated in `bnext-bio/nucleus`). Do not link to the legacy repo — flag for follow-up so the construct can be submitted to `nucleus-eng/DNA` before this page is used at the bench." DNA constructs referenced in a DevNote SHOULD be submitted to `nucleus-eng/DNA` before or alongside migration; if they are not present at migration time, apply the attention block and flag.

## Identity is a claim, not a guess

**Construct↔file identity is a claim, not a guess.** Never place a construct in a Designs table because its name resembles a filename in `nucleus-eng/DNA`. A Designs-table row asserts *this is that sequence* — it requires evidence, minimally that the row's `Length (bp)` equals the target file's GenBank `LOCUS` length (`python3 scripts/check-dna-refs.py` checks this). If the source content's construct differs from the Nucleus construct in any way — tag, backbone, promoter, codon usage, species variant — that is **equivalence, not identity**, and belongs in the block below, never as a Designs-table row. This is the specific failure mode ("greedy linking") that motivated nucleus-docs issue #120: a name-similarity match getting asserted as sequence identity.

```
:::{attention} Nucleus equivalent — not the cited sequence
The data on this page was generated with <cited construct> from <source>. The nearest
Nucleus construct is [pOpen-X](https://github.com/nucleus-eng/DNA/blob/main/<path>).
It is functionally equivalent but **not sequence-identical** (<the difference>).
:::
```

## Running `check-dna-refs.py`

**Run `python3 scripts/check-dna-refs.py` before opening a PR if you added or edited a Designs table** (any table with a `Length (bp)` / construct-name row linking into `nucleus-eng/DNA`). This is a different failure mode than link checking: a link can 404-free and still assert the wrong sequence — the motivating case was `reporter-degfp/spec.md` claiming 2789 bp for a construct that is actually 2812 bp after a correction in the DNA repo. `check-links.py` cannot see that; this script diffs the docs' bp claim against the target file's GenBank `LOCUS` line.

```bash
python3 scripts/check-dna-refs.py                        # all of docs/
python3 scripts/check-dna-refs.py docs/modules/<module>/ # one module
```

Local-only (reads `~/src/nucleus-eng/DNA` directly, or `$NUCLEUS_DNA_REPO`) — not run in CI, since CI has no DNA-repo checkout.

Three levels:

| Level | Meaning |
| --- | --- |
| **blocking** | Wrong bp, missing file, or a link into the legacy `bnext-bio/nucleus` repo. Real errors. |
| **warn** | Construct name doesn't obviously relate to the target's `LOCUS` name or filename. Often a benign alias, but exactly the shape of a greedy link — confirm it's intentional before dismissing. |
| **info** | Nothing to verify — a `.dna` SnapGene file with no parseable length, or a row with no bp cell. |

It checks length, not sequence — a same-length, different-sequence swap is not detectable by this tool.
