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
door. *"I want us to speak in simple language."*

**A fifteenth was dropped for the opposite reason.** `Formulation` is the source's base object and
this corpus does not say it — seven files in `nucleus-docs/docs/`, once each. *"Drop. we don't use
this language."* **Component takes its place as the base term**, which is how the corpus already
talks: a Module is a Component the corpus names.

Three rows were added that the source refuses rather than defines: **a term with a definition
beats a term with a prohibition.**

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
| `T02` | **Component** | A material with a stated identity that can be combined with other Components. Identity is given at one of three levels — Role, Species or Item. | rows of `# Reference Composition`; `manifest.tsv` |
| `T03` | **Module** | A Component the corpus names and specifies. **Composing Modules yields a Module**, which is what makes the term recursive rather than a size. | `docs/modules/<name>/spec.md` |
| `T04` | **Implementation** | A Module together with a physical operating context — a named date, batch, run and place. A Module *claims* a Function; an Implementation *exhibits* one, and exhibiting needs a particular. | `docs/implementations/<name>/main.md` |
| `T05` | **Observation** | A value a Measurement produces about a Sample. Distinct from the Sample it came from, and from the Data that record it. | figures and tables |
| `T06` | **Process** | A procedure applied to Components, producing a Component. **Applied deliberately** — that is what separates it from a Function. | `docs/processes/<name>/main.md` |
| `T07` | **Function** | A behavior a Component produces by itself, entailed by what it is rather than applied to it. | `# Expected Behavior` — 36 of 36 pages carry the heading, none states a domain or codomain |
| `T08` | **Measurement** | A Process whose product includes an Observation. | inside a Process page |
| `T09` | **Assay** | A Measurement as applied — the Process that performs one, on a stated Sample under stated conditions. | a readout Process page |
| `T36` | **Readout** | An accepted synonym for Measurement, normalized to it where the text makes a claim. Jon, 2026-09-08. **Settled only in that sense** — it also names the instrument (*"a weak readout"*) and sometimes the value, and those stay loose. | 162 uses in nucleus-docs |

**Process and Function differ by agency, not by structure.** A Process is applied; a Function is
entailed. `processes/colorimetric-readout/` holds one of each and is right to.

### Requirements and evidence

| ID | Term | Definition | Where it appears |
| --- | --- | --- | --- |
| `T20` | **Requirement** | A condition that must hold for a Module to exhibit its Function. Three kinds: a condition on the Composition, a condition on another Function, and a budget. | `# Requirements`, 29 of 36 pages |
| `T21` | **Sensitivity** | A property of a Component: the class of conditions that change it. Names no Process. | scattered prose |
| `T22` | **Imposition** | A property of a Process: the class of conditions it inflicts on whatever it acts on. | scattered prose |
| `T23` | **Conflict** | The relation holding when a Process's Imposition meets a Component's Sensitivity. **Computed from the two, never asserted on its own.** | asserted directly on nine pages, which is the thing to stop |
| `T24` | **Specification** | The set of claims that fix what a Module is: its Composition, its Requirements and its Function. A Module satisfies a Specification or it does not — which holds whether or not a page has written it down. | the spec page |
| `T25` | **Entailment** | A relation between two Specifications: B entails A when everything A requires, B also provides, so B may stand in for A. | prose in `# Requirements` and `# Expected Behavior` |
| `T28` | **Co-satisfying** | A relation between two Components with respect to one Specification: both satisfy it, whatever else differs between them. | — |

### Identity and documentation

| ID | Term | Definition | Where it appears |
| --- | --- | --- | --- |
| `T29` | **Role** | An identity level: what a group of components does. *Elongation Factors.* | BOM and composition tables |
| `T30` | **Species** | An identity level: molecular identity. *EF-G, cholesterol.* Molar mass and sensitivity belong here. | BOM and composition tables |
| `T31` | **Item** | An identity level: a specific product from a specific supplier, named by catalog number. | BOM `Part #` |
| `T32` | **Configuration** | A choice of one Component at each position in a Composition. Requirements are counted per Configuration, not per Species. | — |
| `T33` | **Composition** | What combining Components under an operator produces, and the description of that result — the identities, concentrations, locations and states of everything in it. **One term, two grammatical forms**: composing is the verb, a composition is what it leaves behind. Mixing puts the operands in one compartment; packing leaves each its own. **Composition can encode Function**, which is why it is most of what a spec page carries. | `# Reference Composition`, `spec.yml` |
| `T34` | **Constituent** | A Component contained in another Component. **Constituent Module** is the canonical case — a Module inside another Module's Composition — and `# Constituent Modules` is a protected string naming it. | `# Constituent Modules` |
| `T35` | **Context** | The operating conditions a Function claim holds in. A claim with no Context is not yet a claim about anything. | `## Cells`, `## Gels`, `## Cytosols` |

### Added here

The source refuses these three. Each names something real, so each gets a definition instead.

| ID | Term | Definition | Where it appears |
| --- | --- | --- | --- |
| `N01` | **Protocol** | The written text of a Process. The Process is the procedure; the protocol is the document. | `# Protocol` on a process page |
| `N02` | **Data** / **Result** | The record of an Observation. The Observation is what the measurement emitted; the data is what was written down. | figures, tables, `generated/` artifacts |
| `N03` | **Sample** | A portion of a Component taken at a stated time, on which a Measurement is performed. | protocol steps |

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
| material | Component | Prefer | no | many | `# Materials` is a heading and Materials Reference is a page |
| spec | Specification | Prefer | no | many | `spec.md` and `spec.yml` are filenames |
| prerequisite | Requirement | Prefer | no | 6 | All six are the `Prerequisite Documentation` heading |
| prep | Component | Prefer | no | 18 | `prep-consumables/` is a path; *"Prep overnight cultures"* is a step |
| constituent | Constituent Module | Protected | no | 7 | See below — Protected is about a string, not a word |
| method | Process | Collapses | no | 27 | Common English |
| demo | Implementation | Prefer | no | 52 | **Every sampled use is correct** — *"the London demo"*, *"each demo's lipid composition"* |
| part | Component | Prefer | no | 85 | *"part of"*, *"part-name"*, the BOM `Part #` column |
| unit | Module | Prefer | no | 27 | Also a measurement unit |
| block | Module | Prefer | no | 11 | *"block-pattern"*, *"building block"* |
| instance | Implementation | Prefer | no | 3 | *"in this instance"* |
| constraint | Requirement | Prefer | no | 17 | Common English |
| ingredient | Component | Prefer | no | 0 | Safe today, but the same shape as the rows above |
| liposome | synthetic cell | Prefer | no | many | **Contextual, so never a rule** — only where the liposome can reasonably be called a synthetic cell. Reads oddly beside row 1 and is not a contradiction: *vesicle* is always wrong, *liposome* is right until the thing is a cell |

**A refusal is only a rule when it cannot collide with a heading, a filename or ordinary
English.** Ten of the twenty-five qualify. The rest are prose preferences, checked by reading —
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

## Program names

**Not terms of the model, so they take no `T` row** — they are proper nouns, and the table above is
for things the corpus composes.

- **DevCells** is the programme. Not an event, and not a repo.
- **DevStudio** is the three-week hackathon: one particular run of the programme.

## Phrasings

Not term rules, and not automatable — checked by the `style-guide` skill instead.

- **"Confirmed in synthetic cytosols and in synthetic cells"** is the standard phrasing for that claim. Applying it blindly once produced *"confirmed confirmed in synthetic cytosols and in synthetic cells."*
- **Name the exact chemical species.** Write `rNTPs` or `dNTPs`, never the ambiguous `NTP`. Some Modules specify both on one page, so this is not a substitution you can automate.
- **Be precise about what a number means.** *"Raises Mg²⁺ from 8 to 18 mM"* and *"raises optimal Mg²⁺ from 8 to 18 mM"* are different claims.
- **Name the specific thing built,** using real Module names. If no Module name exists for something you keep describing, one probably should.
- **One item, one name** (STE 1.11). American English.

## Renaming

**A rename that reaches other Nodes is not an editorial decision.** Renaming a shared term needs
collaborator consent. This applies to every row above and survives any fold-in of this file.
