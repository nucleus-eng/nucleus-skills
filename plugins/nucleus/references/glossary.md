# Nucleus glossary

The shared vocabulary for Nucleus docs and DevNotes. One word, one meaning.

**Derived, not copied.** The source is `nucleus-eng/compositional-biology-theory`, branch `main`,
[`89a5a58`](https://github.com/nucleus-eng/compositional-biology-theory/commit/89a5a58),
`glossary.md` — 38 rows. That repo keeps its own version and maintains it separately, by ruling:
*"create a new glossary, based on the work from category. let them maintain their own version."*
The two serve different readers and will drift on purpose.

**What was dropped, and why.** 14 of the 38 rows are the formal layer — operators, functors,
fibers, equalities. They have no surface form in either corpus, so nobody can write them wrongly,
and inventing plain-language names for them here would import the formal layer through the back
door. *"I want us to speak in simple language."* Three rows were added that the source refuses
rather than defines: **a term with a definition beats a term with a prohibition.**

**IDs name a concept, not a spelling.** `T09` stays `T09` if `Assay` is renamed. IDs match the
source so a row can be traced back. Rows added here are numbered `N01` and up.

## How this binds

**Severity is the repo's, not this file's.** Each repo's `.vale.ini` sets the level. Ruled:
**blocking in nucleus-docs, warn-only in DevNotes.** New vocabulary flows in from DevNotes, so
blocking the source would stop the glossary growing.

A refusal has one of three kinds, and only the kind is fixed here:

| Kind | Means | Suggested level |
| --- | --- | --- |
| **Collapses** | The refused word denotes something else. Using it merges two ideas that must stay apart. | error |
| **Protected** | The word is a literal string that tooling matches on. Changing it breaks a check. | error everywhere, including DevNotes |
| **Prefer** | A near-synonym. House consistency, no meaning is lost. | warning, never blocking |

**Vale rules are generated from this file**, by `scripts/generate-vale-rules.py`. A term cannot be
defined here without being enforceable, and a rule cannot exist without a row explaining it.

## Terms

### The material

| ID | Term | Definition | Where it appears |
| --- | --- | --- | --- |
| `T01` | **Formulation** | Anything that can sit in a tube. | — |
| `T02` | **Component** | A formulation below the granularity at which the corpus gives pages. Composes the same way a Module does. | rows of `# Reference Composition`; `manifest.tsv` |
| `T03` | **Module** | A formulation the corpus has chosen to name, together with the operations it declares. | `docs/modules/<name>/spec.md` |
| `T04` | **Implementation** | A Module as a particular — a named date, batch and run. A Module claims a Function; an Implementation exhibits one, and exhibiting needs a particular. | `docs/implementations/<name>/main.md` |
| `T05` | **Observation** | What a measurement emits beside its sample. | figures and tables |
| `T06` | **Process** | A procedure you choose to apply. | `docs/processes/<name>/main.md` |
| `T07` | **Function** | A behavior the thing itself produces, without anyone applying it. | `# Expected Behavior` — 36 of 36 pages carry the heading, none states a domain or codomain |
| `T08` | **Measurement** | A process whose result carries an Observation. | inside a Process page |
| `T09` | **Assay** | A Measurement considered as applied: the Process that performs one. | a readout Process page |
| `T36` | **Readout** | An accepted synonym for Measurement, normalized to it where the text makes a claim. Jon, 2026-09-08. **Settled only in that sense** — it also names the instrument (*"a weak readout"*) and sometimes the value, and those stay loose. | 162 uses in nucleus-docs |

**Process and Function differ by agency, not by structure.** A Process is applied; a Function is
entailed. `processes/colorimetric-readout/` holds one of each and is right to.

### Requirements and evidence

| ID | Term | Definition | Where it appears |
| --- | --- | --- | --- |
| `T20` | **Requirement** | A condition that must hold for something to work. Three kinds: a condition on the formulation, a condition on the function, and a budget. | `# Requirements`, 29 of 36 pages |
| `T21` | **Sensitivity** | What an object is subject to. Names no process. | scattered prose |
| `T22` | **Imposition** | What a process inflicts on what it acts upon. | scattered prose |
| `T23` | **Conflict** | A sensitivity meeting an imposition. **Computed from the two, never asserted on its own.** | asserted directly on nine pages, which is the thing to stop |
| `T24` | **Specification** | What a page asserts about a Module. | the spec page |
| `T25` | **Entailment** | B refines A, so B may stand in for A. The corpus states this in prose every time it comes up and has no name for it — *"passes molecules up to ~1 kDa … so substituting this Module for it lowers the cutoff"*. | prose in `# Requirements` and `# Expected Behavior` |
| `T28` | **Co-satisfying** | Two things stand the same way toward one specification's requirements, even where they differ elsewhere. | — |

### Identity and documentation

| ID | Term | Definition | Where it appears |
| --- | --- | --- | --- |
| `T29` | **Role** | An identity level: what a group of components does. *Elongation Factors.* | BOM and composition tables |
| `T30` | **Species** | An identity level: molecular identity. *EF-G, cholesterol.* Molar mass and sensitivity belong here. | BOM and composition tables |
| `T31` | **Item** | An identity level: catalog number. **The only level the corpus keys on.** | BOM `Part #` |
| `T32` | **Configuration** | A choice of constituents. Requirements are counted per configuration, not per species. | — |
| `T33` | **Composition** | The expression giving an object as a combination of others. | `# Reference Composition`, `spec.yml` |
| `T34` | **Constituent Module** | A Module appearing inside another Module's Composition. | `# Constituent Modules` |
| `T35` | **Context** | The subdivision of `# Expected Behavior` — the operating conditions a claim holds in. | `## Cells`, `## Gels`, `## Cytosols` |

### Added here

The source refuses these three. Each names something real, so each gets a definition instead.

| ID | Term | Definition | Where it appears |
| --- | --- | --- | --- |
| `N01` | **Protocol** | The written text of a Process. The Process is the procedure; the protocol is the document. | `# Protocol` on a process page |
| `N02` | **Data** / **Result** | The record of an Observation. The Observation is what the measurement emitted; the data is what was written down. | figures, tables, `generated/` artifacts |
| `N03` | **Sample** | A Formulation you took — a particular portion, at a particular time. | protocol steps |

## Refused spellings

Each row with **Auto: yes** becomes one generated Vale rule. `Kind` sets severity per the table
above. **Hits** is measured against `nucleus-docs` `docs/` on 2026-09-15.

| Refused | Use | Kind | Auto | Hits | Note |
| --- | --- | --- | --- | --- | --- |
| vesicle | liposome | Collapses | **yes** | 0 | GUV, SUV and LUV are distinct and must not merge |
| incompatibility | Conflict | Collapses | **yes** | 4 | All four are real — a Conflict is computed from a sensitivity and an imposition, and asserting it directly hides which half is the claim |
| `DevCell Studio` | DevStudio | Prefer | **yes** | 0 | |
| `milliQ water` | ultrapure water | Prefer | **yes** | 0 | Vendor-neutral |
| `SMixΔCP` | `SMix -CP` | Prefer | **yes** | 0 | Prefer plain characters |
| colormetric | colorimetric | Prefer | **yes** | 0 | Misspelling |
| leg | integration path | Prefer | **yes** | 0 | |
| `Chicago node` | `Chicago Node` | Prefer | **yes** | 1 | Proper noun. Case-sensitive |
| `Chicago-node` | `Chicago Node` | Prefer | **yes** | 1 | Same, hyphenated |
| `London node` | `London Node` | Prefer | **yes** | 0 | Same rule, no current violation |
| Expected Behavior | Function | Collapses | no | 36 | **A required heading on 36 of 36 pages** |
| material | Formulation | Prefer | no | many | `# Materials` is a heading and Materials Reference is a page |
| spec | Specification | Prefer | no | many | `spec.md` and `spec.yml` are filenames |
| prerequisite | Requirement | Prefer | no | 6 | All six are the `Prerequisite Documentation` heading |
| prep | Formulation | Prefer | no | 18 | `prep-consumables/` is a path; *"Prep overnight cultures"* is a step |
| constituent | Constituent Module | Protected | no | 7 | See below — Protected is about a string, not a word |
| method | Process | Collapses | no | 27 | Common English |
| demo | Implementation | Prefer | no | 52 | **Every sampled use is correct** — *"the London demo"*, *"each demo's lipid composition"* |
| part | Component | Prefer | no | 85 | *"part of"*, *"part-name"*, the BOM `Part #` column |
| unit | Module | Prefer | no | 27 | Also a measurement unit |
| block | Module | Prefer | no | 11 | *"block-pattern"*, *"building block"* |
| instance | Implementation | Prefer | no | 3 | *"in this instance"* |
| constraint | Requirement | Prefer | no | 17 | Common English |
| ingredient | Component | Prefer | no | 0 | Safe today, but the same shape as the rows above |

**A refusal is only a rule when it cannot collide with a heading, a filename or ordinary
English.** Ten of the twenty-four qualify. The rest are prose preferences, checked by reading —
which is the `style-guide` skill's job, not Vale's.

**This was measured, not assumed, and the measurement changed the answer twice.** `demo` reads
like an obvious refusal and is used correctly 52 times. Generating a rule from every refusal would
have produced roughly 250 findings, nearly all of them wrong, on a corpus that is broadly
conformant.

**The second time, measuring produced a better rule rather than deleting one.** `node → Node`
looked safe and was run against the corpus: of nine lowercase uses, **seven mean a diagram node**
— *"not yet a diagram node"*, *"its own edge into this node"*, *"the `ALG` node in the
process-dependency graph"*. A 78% false-positive rate, on a repo full of mermaid diagrams. The two
real ones both name a Node first, so the rule narrowed to `Chicago node` and `Chicago-node`:
**two hits, both violations, no false positives by construction.** 91 correctly capitalized uses
are untouched.

**Protected means do not rename the string, not do not use the word.** `# Constituent Modules` and
mermaid `classDef constituent` are matched by tooling and must not be reworded. The English word
*constituent* is fine — seven pages use it correctly, as in *"this is an Analyte, so it is not a
constituent of anything."* The source conflated the two, and a substitution rule would flag all
seven.

## Phrasings

Not term rules, and not automatable — checked by the `style-guide` skill instead.

- **"Confirmed in synthetic cytosols and in synthetic cells"** is the standard phrasing for that claim. Applying it blindly once produced *"confirmed confirmed in synthetic cytosols and in synthetic cells."*
- **Name the exact chemical species.** Write `rNTPs` or `dNTPs`, never the ambiguous `NTP`. Some Modules specify both on one page, so this is not a substitution you can automate.
- **Be precise about what a number means.** *"Raises Mg²⁺ from 8 to 18 mM"* and *"raises optimal Mg²⁺ from 8 to 18 mM"* are different claims.
- **Name the specific thing built,** using real Module names. If no Module name exists for something you keep describing, one probably should.
- **One item, one name.** American English.

## Renaming

**A rename that reaches other Nodes is not an editorial decision.** Renaming a shared term needs
collaborator consent. This applies to every row above and survives any fold-in of this file.
