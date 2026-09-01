# Platemap skills — staged work

Working document, uncommitted by design. Same role as `REFACTOR-PLAN.md`:
what is decided, what is not, and what evidence would settle it.

**Status: holding for more examples before further edits.** The three changes
in §1 are specified but deliberately unbuilt — each was derived from a single
case, and this session has repeatedly shown a single case to be a bad basis.

Current work is on `feat/build-platemap-skill`, PR #14 (draft), rebased onto
`main` at 13 skills.

---

## 1. Specified, not built

### 1.1 Prospective versus retrospective — ask before laying out

**The highest-value item, and the root cause of the only real defect found by
cold testing.**

A platemap is one of two things and the skill treats them as one:

| | Wells are | Generating them is |
| --- | --- | --- |
| **Prospective** — a plan for a run not yet done | the deliverable | correct; the point of the skill |
| **Retrospective** — a record of a run already done | facts to be recovered | fabrication |

The CDK merges on `Well` with an inner join. A generated well in a
retrospective platemap merges against whatever real data sits at that
position, or drops silently if nothing does. The analysis runs and reports
nothing wrong.

**Change:** `build-platemap` asks which, *before* step 2. The answer gates
whether wells may be generated at all. Retrospective plus no wells in the
source is a stop, not a step.

**Evidence.** A cold run on the ClpXP CSV assigned 54 well IDs. It did not
hallucinate them — it asked for instrument, plate format and replicate count,
got answers, then called `generate_centered_384_well_ids`, which
`SKILL.md` step 2 explicitly instructs it to call "rather than writing well
IDs by hand". It flagged them as assumed in its report. **The skill told it to
do this.** Confidence: high — the mechanism is documented in our own file.

**Note against self-congratulation:** this session left `Well` blank, but not
by knowing better. It never asked the three questions and stopped earlier.
Given the same answers it would have generated wells too, following the same
step. Do not record this as one agent being careful.

### 1.2 Provenance per value

Four states, recorded for every value a generated platemap carries:

| State | Meaning |
| --- | --- |
| `source` | verbatim from the input |
| `derived` | computed from the input — record the formula |
| `imputed` | inferred from context — record the context |
| `assumed` | chosen; needs human review |

**Change:** no `assumed` value ships without appearing in the handoff summary.
Mechanically checkable, unlike "did the model make this up".

Converges with the test-corpus expectation tiers in §3, reached independently
from a different direction. That convergence is the main reason to believe the
cut is in the right place.

**Open:** the checker currently sees only the output file. Provenance needs
either a sidecar written at generation time, or the checker being handed the
source. Not yet decided — see §2.1.

### 1.3 Declared transformations

A transformation that preserves concentrations is invisible to every
arithmetic check we have.

**Evidence.** The cold run's Cells rows are uniformly one third of the source:
30 µL becomes 10 µL, every component divided by exactly 3.0. Concentrations
survive — `41.2 × 0.3/30` and `41.2 × 0.1/10` both give 0.412 µM — so the
concentration columns are correct and every total balances. But the recorded
volumes are not what was pipetted: 0.1 µL of deGFP-ssrA is not a pipettable
volume, and the reaction was 30 µL, not 10.

Same class as 1.1: a schema wanting one uniform value per column, and a
transformation applied to satisfy it.

**Change:** any rescaling between the source's basis and the platemap's is
declared, and the checker flags an undeclared uniform ratio between a
condition's volumes and its stated total.

---

## 2. Open — needs more examples

### 2.1 Does the checker get to see the source?

Provenance (§1.2) and the source-had-no-Well-column test both need the input,
not just the output. Options, undecided:

- a sidecar provenance file written beside the platemap at generation time
- a `--source` argument to `check-platemap.py`
- provenance columns in the platemap itself (pollutes the artifact the CDK reads)

**What would settle it:** a case where the platemap and its source are handed
over separately, or one where the source no longer exists.

### 2.2 Is `Name` allowed to carry interpretation?

Two condition tables for the same experiment, side by side:

```
this session:  "No DNA — Sample 2"                      source-faithful, opaque
cold run:      "Bulk PURE +ClpX only (no DNA)"          interpreted, self-describing
```

Both are defensible and both were correct here. The interpreted form is more
useful to a reader and encodes a reading that could be wrong. `Name` is the
CDK's replicate-grouping key, so this is not cosmetic.

**What would settle it:** an experiment where the obvious interpretation of a
condition is wrong.

### 2.3 How big is the reference surface, really?

Three reference files for two skills is near the limit. The admission test —
*would a competent model get this wrong?* — has been applied twice and killed
one section (layered grids: a cold model handled the shape unaided). If the
next few examples each add a rule, the test is not discriminating and the
honest answer is that this belongs in nucleus-docs with an owner and a review
process, not in a skills repo.

**What would settle it:** the next five examples. Count how many add a rule.

---

## 3. Test corpus — staged

Total corpus is ~88 KB, so storage is not a constraint. Two things are.

**Disclosure.** Real bench data, some of it from a DM, some from a private
Notion workspace, in a repo other repos subscribe to. Redaction defeats the
purpose: anonymise `MM`, `IS`/`OS` and the construct names and the tests no
longer exercise the thing they exist for.

**The oracle problem.** Expected outputs would be *our* outputs. Frozen at
three points today they would have enshrined: 26 false compartment findings, a
`scale-recipe.py` false positive on ng/µL versus nM, and a liposome platemap
silently missing six components. Three hours, three wrong goldens.

| Stage | Does | Blocked by |
| --- | --- | --- |
| 0 | Decide disclosure per file. Not technical. | — |
| 1 | `tests/corpus/manifest.yaml` — origin, owner, path, shape exercised, **and the finding it was added for**. No data moved. | nothing |
| 2 | Expectations as assertions, tiered `derived` / `confirmed` / `asserted`. Only the first two may fail a build. | 1 |
| 3 | Vendor what stage 0 clears; reference the rest by path, skipped when absent. CDK fixtures referenced by commit, never copied. | 0, 1 |
| 4 | Runner and CI, printing what it skipped so a shrinking corpus is visible. | 3 |
| 5 | Synthesised adversarial cases — mutate a clean file to produce each blocking finding. Known-correct by construction, so no oracle risk. | nothing |

**Do stage 1 first and soon.** It is the part that decays fastest — the reason
each file matters is currently in one session's context and nowhere else.

Stage 5 is unblocked and independently valuable. It is also where the
"confidently wrong" cases belong: `Type: Standard` meaning "the standard prep
method" passes every syntactic check and silently drops the wells.

**Resist making this a general platemap test suite.** It is a *regression*
corpus. Each case earns its place by having caught something. Cases added
because they look representative are the ones nobody maintains.

---

## 4. Dead ends — do not re-derive

**The A1-consecutive structural tell.** Tested against four real platemaps
(`A19,A21,A23…` / `A2,A3,A4…` / `E1,E2,E3…` / `J2,J3,J4…`) — none starts at A1
or runs consecutively, while a naive fill gives `A1,A2,A3…`. Zero false
positives, and useless anyway: a model that calls the correct generator
produces a randomised centred layout indistinguishable from a real bench one.
The tell catches only naive hand-fill, which is the case least likely to cause
harm because it also looks obviously wrong. **Provenance, not shape.**

**A component glossary.** `MM`, `RNA ihb.`, `Optiprep` are owned by
nucleus-docs. A copy here drifts — the founding bug of this repo. Resolution
is a lookup step, already in `extract-conditions` §3b.

**A paraphrase of the category corpus.** No pin exists; the corpus is private
and moved during this session, leaving a stub where citations pointed. A
pointer to a moving target needs a pin and a paraphrase needs a maintainer.
`references/assay-and-specimen.md` records the dependency with a date instead.

**A reference section per new file shape.** Cold testing showed a model parses
novel spreadsheet layouts unaided; what it gets wrong is semantics. Write the
rule, not the shape.

---

## 5. Errors found in generated outputs — evidence log

Both agents made errors. Recorded because §3 stage 2 must not freeze them.

| Where | Error | Caught by |
| --- | --- | --- |
| this session | liposome platemap missing six components; `MM ⊂ IS` noticed in prose, dropped from the artifact | user review |
| this session | compartment volumes summed across a membrane — 26 false findings | user review, then category corpus |
| this session | `scale-recipe.py` false positive on ng/µL stock against nM final | own regression run |
| this session | claimed a 10.5 µL mismatch that was a transcription slip, not a source error | own re-check |
| cold run | Cells rows rescaled ÷3, undeclared | cross-comparison |
| cold run | IS and OS inverted — the 30 µL table is the inner solution; Optiprep is the tell | cross-comparison |
| cold run | 54 generated wells in a possibly-retrospective platemap | user review |

Two of seven were caught by the tooling. Five needed a human or a second
agent. That ratio is the argument for §3.

---

## 6. Elsewhere — not this repo's work

- **`Rxn Volume (uL)` is codim-0 only.** A required column well-defined only
  when a well holds one compartment, in a system whose subject includes things
  with an inside and an outside. Not a disagreement between encodings — the
  schema cannot represent it. Issue drafted; **home unknown**, local `cdk` is
  not a git checkout and `pyproject.toml` points at `bnext-bio/nucleus`, last
  pushed 2026-05-25 and described elsewhere as legacy. Needs a target.
- **Publishing the category corpus.** With Jon, via `category-55`. Not
  blocking; `assay-and-specimen.md` is written either way.
- **nucleus-docs#238** — Vale casing for inner/outer solution. Filed.
- **`IS`/`OS` are defined nowhere in nucleus-docs.** 110 uses of "outer
  solution", zero definitions of the abbreviation. A docs gap, surfaced by a
  failed lookup. Not filed.
- **Cross-skill `extract`.** Whether `ingest`, `migrate-content` and
  `notion-corpus-to-outline` should share the extraction step. Deferred to an
  end-of-session issue.
