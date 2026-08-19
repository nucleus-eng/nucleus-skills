# Refactor plan

Goal: every Nucleus rule has exactly one owner, every skill loads, and the
skills stay correct without hand-syncing copies.

Findings this plan acts on come from an audit run on 2026-08-19 across
nucleus-docs, doc2devnote, 2026-CERN-OHL-P, DNA, and `~/.claude/skills`.

The phases are ordered by dependency. Phase 0 is a decision, not work, and
blocks everything that ships. Phases 1–3 are safe to do in any order.
Phase 5 must come last — it deletes content from the source repos, and it
is only safe once the replacements load.

---

## Phase 0 — Decide how repos consume this one (BLOCKING)

A standalone repo loads nowhere. Claude Code reads `.claude/skills/` in the
project directory and `~/.claude/skills/` globally. Nothing else. Until this
is decided, this repo is a filing cabinet.

Three real options:

| Option | How | Cost | Works for teammates |
| --- | --- | --- | --- |
| **Plugin marketplace** *(recommended)* | Add `.claude-plugin/marketplace.json`; each repo installs the plugin | One-time setup, then `git pull` | Yes |
| Git submodule | Submodule this repo into each consumer's `.claude/skills/` | Submodule friction on every clone | Yes |
| Sync script | A script copies skills into each repo's `.claude/skills/` | Copies drift again — the problem we are fixing | Yes, but reintroduces drift |

Recommend the plugin marketplace. It is the mechanism designed for this,
it survives `git pull`, and it does not put generated copies back in the
consumer repos. Reject the sync script — it recreates the exact failure
this refactor exists to remove.

**Decision needed before Phase 4 ships.** Phases 1–3 are useful regardless.

---

## Phase 1 — Make the three dead skills load

The highest-value fix in the plan and the cheapest. Roughly 21k of
maintained pipeline knowledge is currently unreachable.

For each of `build-boms`, `lint-docs`, `migrate-content`:

1. Move `skills/_unconverted/<name>.md` → `skills/<name>/SKILL.md`.
2. Add a `name:` field to the frontmatter, matching the directory.
3. Rewrite `description:` to say **when to use it**, not just what it covers.
   The current descriptions read as summaries. A description is a trigger —
   it is the only thing the model sees before deciding to load the skill.
4. Delete `skills/_unconverted/`.

Draft descriptions:

- **build-boms** — "Generate lab-ready protocol PDFs, BOM PDFs, and
  materials CSVs from process and module spec pages. Use when adding or
  editing a `bom-<slug>` table, adding a download button, debugging
  `build-protocols.py` or `check-bom-labels.py`, or when a generated file
  is missing or stale."
- **lint-docs** — "Run and interpret Vale, codespell, lychee, and the strict
  MyST build. Use before opening a PR or committing content, and when any
  of those tools reports an error you need to interpret or justify
  suppressing."
- **migrate-content** — "Migrate content into nucleus-docs from a Notion
  markdown export or a Curvenote DevNote. Use when moving source material
  into `docs/`, and for the table, admonition, citation, figure, and DNA
  construct conventions that migration must satisfy."

**Verify:** open a session in nucleus-docs and confirm all three appear in
the skill list. This is the only proof that matters — the format failure
was silent for months precisely because nobody checked.

---

## Phase 2 — Fix the conflicts

These are wrong content, not just untidy content. Do them before anything
that copies text around.

### 2.1 The canonical unit table disagrees with itself

Two copies, drifted in both directions:

| Row | `lint-docs.md:62-63` | `nucleus-docs/CLAUDE.md:358-359` |
| --- | --- | --- |
| Volume | `nL`, `µL`, `mL`, `L` | `µL`, `mL`, `L` |
| Mass | **`nL`**, `µg`, `mg`, `g`, `kg` | `µg`, `mg`, `g`, `kg` |

`nL` is a volume unit in the Mass row. Neither copy is correct.

Fix: the correct table has `nL` in Volume and not in Mass. Correct it in
`lint-docs`, which becomes the single owner. Two further drift artifacts in
the same block: `lint-docs.md:70` reads `ousands-separator` (truncated
"thousands"), and the ppm/ppb row wording differs between copies. Fix both.

The third copy, `references/devnote-style-guide.md:140-155`, is a
deliberate port and says so. Re-sync it after the fix and keep the
"keep this in sync" note — that file is the one place in the whole set that
handles duplication honestly.

### 2.2 Three skills answer to "migrate this DevNote"

| Skill | Input | Output |
| --- | --- | --- |
| `migrate` | Local `main.md` + `curvenote.yml` | `index.md`, MyST, internal registry |
| `migrate-devnote` | DevNote published on the Curvenote venue | `main.md` + `curvenote.yml`, resubmitted to Curvenote |
| `migrate-content` | A DevNote or Notion export | A nucleus-docs module spec page |

`migrate` and `migrate-devnote` collide hardest: `migrate` says "use when
the source has a `curvenote.yml`", and `migrate-devnote` is also about
Curvenote — but one moves away from that format and the other stays on it.
Today the only disambiguator is which repo you are standing in. Once this
repo serves all of them, that disambiguator is gone.

Fix: add the destination to each `description:`. One clause each.

- `migrate` — "…into the current MyST schema for the internal DevNotes
  registry (output: `index.md`)."
- `migrate-devnote` — "…keeping the Curvenote `main.md`/`curvenote.yml`
  format, for republication through the Curvenote venue."
- `migrate-content` — "…into a nucleus-docs module spec or process page."

Do not merge them. The three pipelines are genuinely different.

### 2.3 Citation brackets differ across a boundary a skill crosses

DevNotes use `[[Wang *et al.* 2019](url)]`
(`references/devnote-style-guide.md:138`). nucleus-docs uses single
brackets. `migrate-content` moves content across exactly that boundary and
never mentions the change, so a migration carries the wrong punctuation
through silently.

Fix: add the conversion to `migrate-content`'s DOI bullet (line 17), which
already handles the adjacent bare-`[](10.xxxx)` case.

---

## Phase 3 — Remove the duplication

### 3.1 Reconcile the `notion-corpus-to-outline` fork

Two versions, ~90% identical prose, neither a superset, and — unlike every
other duplication found — **neither references the other**. Already
drifting on details ("20k" vs "about 21k characters" for the same
measurement).

| Only in the doc2devnote copy | Only in the global copy |
| --- | --- |
| Pipeline framing (ends where `ingest` begins) | Packaging frontmatter (`version`, `license`, `compatibility`) |
| `devnote-style-guide` as the quality anchor | A "prior art" section naming doc2devnote as an example |
| Step 9: hand off to `/ingest` | Concrete named transcript-garble examples |

Fix: keep the general version as canonical, since it already describes
itself as generic. Fold in the named examples — they teach the failure mode
better than the anonymized paraphrases do. Reduce the Nucleus copy to a
thin scoped shim: the pipeline framing, the style-guide anchor, and the
`/ingest` handoff, plus a pointer to the general skill for the mechanics.

### 3.2 De-duplicate inside `ingest/SKILL.md`

The fidelity rules appear twice, byte-identical: at lines 66-85 under
`## Fidelity rules`, and again at 94-110 inside the `## Skill prompt` block.
Two places to update, no note tying them together.

Fix: if the prompt block must stay copy-paste self-contained, keep both but
add a sync note — the pattern `devnote-style-guide.md` already uses.
Otherwise have the prompt reference the section by name.

### 3.3 Make `migrate-content` defer on BOMs

`migrate-content.md:10` restates the `bom-<slug>` mechanism and the
inline-vs-CSV agreement rule that `build-boms.md:11,20` owns. Its
cross-reference says "see the lab-ready protocol pipeline section below" —
but `build-boms` is a separate skill, not a section of the same document.

Fix: replace with a one-line pointer to `build-boms`.

### 3.4 Fix the stale pointer

`references/devnote-style-guide.md:71` points at `migrate.md`, which does
not exist. Should be `skills/migrate/SKILL.md`.

---

## Phase 4 — Extract the skills still trapped in CLAUDE.md

Line numbers refer to `extraction-sources/nucleus-docs-CLAUDE.md`.

| New skill | Source | Notes |
| --- | --- | --- |
| `verify-dna-constructs` | lines 62-121 + 409-418 | Tiered cross-repo verification, GitHub API fallback, the attention-block template, and `check-dna-refs.py`. The script is documented in no skill today. |
| `author-myst-content` | lines 208-266 | MyST conventions — fence depth, figure placement, composition-table flattening, mass-to-molar stoichiometry — plus the empty-dropdown policy. |
| `page-status` | lines 154-180 | Draft/published frontmatter and banner snippets. Small. Fold into `author-myst-content` unless it earns its own trigger. |

Also fold, rather than extract:

- lines 182-190 (template placeholder cleanup) → into `migrate-content`.
- lines 376-407 (lychee blame-partitioning, "what it does not catch") →
  into `lint-docs`. The CLAUDE.md copy is **richer** than the skill's here.
  Move it before deleting anything, or the detail is lost.

`verify-dna-constructs` is the one that matters most. The DNA repo has no
skills and no CLAUDE.md of its own, so today all DNA knowledge reaches an
agent only through nucleus-docs.

---

## Phase 5 — Strip the source repos (LAST)

Only after Phases 1–4 ship and load. Deferred by decision on 2026-08-19:
do not touch CLAUDE.md until the skill refactor is done.

**nucleus-docs/CLAUDE.md**

- Delete 290-418 — the Vale, codespell, lychee, and strict-build reference.
  Already in `lint-docs`, near-verbatim, and line 420 already tells the
  agent to invoke that skill. Salvage 376-407 first (Phase 4).
- Delete the extracted blocks: 62-121, 154-190, 208-266.
- Keep: repo identity, dev commands (9-58), content model and file
  placement (123-144), TOC management (146-152), the no-hard-wrap rule
  (196-206), the external references map (272-274), PR workflow (422-424).
- Keep the pointers to `build-boms`, `migrate-content`, and `lint-docs`.
  They will finally work.

**doc2devnote/CLAUDE.md** — trim 47-51 (the pandoc command) and 82 (the
Vale call). Both are duplicated in `ingest`. Low priority.

**Source `.claude/skills/` directories** — remove once the distribution
mechanism from Phase 0 is live and verified. Not before.

Ship as one PR per repo, after the skills load.

---

## Phase 6 — Make it stay clean

### Scope boundaries

One owner per domain. This table is the contract. Anything that restates
another row's content is a bug.

| Domain | Owner |
| --- | --- |
| Live Notion → sourced outline | `notion-corpus-to-outline` |
| Raw material → draft DevNote | `ingest` |
| Curvenote DevNote → MyST registry | `migrate` |
| Published DevNote → CERN repo republish | `migrate-devnote` |
| DevNote or Notion export → nucleus-docs page | `migrate-content` |
| BOM tables, protocol PDFs, generated artifacts | `build-boms` |
| Vale, codespell, lychee, strict build | `lint-docs` |
| DNA construct identity claims | `verify-dna-constructs` |
| MyST authoring conventions, page status | `author-myst-content` |
| Prose style, notation, units | `references/devnote-style-guide.md` (reference, not a skill) |

### Conventions to write down in the README

- **Descriptions are triggers, not summaries.** Say when to use the skill
  and what it produces. Name the output format when a sibling skill could
  match the same words.
- **Cross-reference, never restate.** The model to copy is
  `migrate-devnote/references/snags.md`, which points at `prepare.md §5`
  instead of repeating it. The model to avoid is nucleus-docs/CLAUDE.md
  reproducing `lint-docs.md` and then telling you to load `lint-docs.md`.
- **If a copy is unavoidable, label it.** `devnote-style-guide.md:142` says
  it is a port and asks for sync. That is the minimum bar.
- **Reference files hold detail; SKILL.md holds the flow.**
  `migrate-devnote` does this well — a 75-line index over four reference
  files, loaded on demand.

### Checks worth automating

1. Every `skills/*/` has a `SKILL.md` with `name:` matching the directory.
   This one check would have caught the dead-skill bug on day one.
2. No two skills declare the same `name:`.
3. Internal links resolve. Would have caught the stale `migrate.md` pointer.
4. Vale over the skill files themselves — they state unit conventions they
   do not currently obey.

---

## Order of work

1. Phase 1 — convert the three dead skills, verify they load.
2. Phase 2 — fix the unit table, the migrate collision, the citation gap.
3. Phase 3 — reconcile the fork, remove the internal duplication.
4. Phase 0 — decide distribution. Needed before Phase 4 ships.
5. Phase 4 — extract the three new skills.
6. Phase 6 — README conventions and the CI checks.
7. Phase 5 — strip the source repos. One PR each. Last.

Phase 1 alone recovers three working skills. Everything after that is
consolidation.
