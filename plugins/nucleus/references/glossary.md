# Nucleus glossary

The shared vocabulary for Nucleus docs and DevNotes. One word, one meaning.

**IDs name a concept, not a spelling.** A row keeps its ID when its term is renamed. Numbered in
reading order; a row added later takes the next free number rather than forcing a renumber.

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

**Ordered so a term is defined before it is used.** That is possible for the first nine and not
for the rest: sixteen of the twenty-five are mutually recursive, and two pairs define each other
outright — Module and Requirement, Observation and Data. Module is taken as primitive and
Composition defined from it.

### The primitives

| ID    | Term          | Definition                                                                                                                                                                                                                                                                                                                                                  | Where it appears                                                                           |
| ----- | ------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| `T01` | **Species**   | An identity level: molecular identity. *EF-G, cholesterol.* Molar mass and sensitivity are usually **stated** at this level.                                                                                                                                                                                                                                | BOM and composition tables                                                                 |
| `T02` | **Item**      | An identity level: a specific product from a specific supplier, named by catalog number.                                                                                                                                                                                                                                                                    | BOM `Part #`                                                                               |
| `T03` | **Component** | A material with a stated identity that can be combined with other Components. Identity is given at one of two levels — Species or Item.                                                                                                                                                                                                             | rows of `# Reference Composition`; `manifest.tsv`                                          |
| `T04` | **Module**    | A Component with a stated Composition, Function, and Context in which it functions. May carry Requirements for particular subcomponents or further Functions in order to operate, and may dispatch Requirements to other Modules where those supply them. **Composing Modules yields a Module**, which is what makes the term recursive rather than a size. | `docs/modules/<name>/spec.md`                                                              |
| `T05` | **Process**   | A transformation of Components into a Component. **A Protocol and a Function are both Processes**, differing by agency rather than by structure.                                                                                                                                                                                                            | `docs/processes/<name>/main.md`                                                            |
| `T06` | **Protocol**  | A Process you choose to apply.                                                                                                                                                                                                                                                                                                                              | `docs/processes/<name>/main.md`                                                            |
| `T07` | **Function**  | A Process a Module implements — entailed by the Composition of the Module itself, rather than chosen by the engineer and applied.                                                                                                                                                                                                                           | `# Expected Behavior` — 36 of 36 pages carry the heading, none states a domain or codomain |
| `T08` | **Context**   | The operating conditions a Function claim holds in. A claim with no Context is not yet a claim about anything.                                                                                                                                                                                                                                              | `## Cells`, `## Gels`, `## Cytosols`                                                       |

**Agency is what splits a Process, not structure.** A Protocol is one you choose to apply; a
Function is one a Module implements. Both are Processes, so `processes/colorimetric-readout/`
holding one of each is the layout being right rather than an exception.

### Composition

| ID | Term | Definition | Where it appears |
| --- | --- | --- | --- |
| `T09` | **Composition** | The explicit set of components constituting a Module, in addition to their concentration and physical state. Additionally, the act of combining two Modules or two Processes as well as the resulting object from said Composition | `# Reference Composition`, `spec.yml` |
| `T10` | **Constituent** | A Component contained in another Component. **Constituent Module** is the canonical case — a Module inside another Module's Composition — and `# Constituent Modules` is a protected string naming it. | `# Constituent Modules` |
| `T11` | **Implementation** | A Module together with a physical operating context — a named date, batch, run and place. A Module *claims* a Function; an Implementation *exhibits* one, and exhibiting needs a particular. | `docs/implementations/<name>/main.md` |

### Requirements and evidence

| ID    | Term              | Definition                                                                                                                                                                                                                   | Where it appears                                            |
| ----- | ----------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| `T12` | **Requirement**   | A condition that must hold for a Module to exhibit its Function. Three kinds: a condition on the Composition, a condition on another Function, and a budget.                                                                 | `# Requirements`, 29 of 36 pages                            |
| `T13` | **Sensitivity**   | A property of a Component: the class of conditions that change the Function it would otherwise exhibit. Names no Process.                                                                                                    | scattered prose                                             |
| `T14` | **Imposition**    | A property of a Process: the class of conditions it inflicts on whatever it acts on.                                                                                                                                         | scattered prose                                             |
| `T15` | **Conflict**      | The relation holding when a Process's Imposition meets a Component's Sensitivity. **Computed from the two, never asserted on its own.**                                                                                      | asserted directly on nine pages, which is the thing to stop |
| `T16` | **Specification** | The set of claims that fix what a Module is: its Composition, its Requirements and its Function. That a collection of Components implements a Module means exactly that those Components meet the Specification describing it.  | the spec page                                               |
| `T17` | **Entailment**    | A relation between two Specifications: B entails A when everything A requires, B also provides, so B may stand in for A.                                                                                                     | prose in `# Requirements` and `# Expected Behavior`         |
| `T18` | **Co-satisfying** | A relation between two Components with respect to one Specification: both satisfy it, whatever else differs between them.                                                                                                    | —                                                           |

### Measurement and its record

| ID | Term | Definition | Where it appears |
| --- | --- | --- | --- |
| `T19` | **Assay** | A Protocol whose product includes an Observation. | inside a Process page |
| `T20` | **Measurement** | A particular run of an Assay. | inside a Process page |
| `T21` | **Sample** | A portion of a Component taken at a stated time, on which a Measurement is performed. | protocol steps |
| `T22` | **Observation** | The value a Measurement produces about a Sample. Also written *result*. | figures and tables |
| `T23` | **Data** | The written record of an Observation. | figures, tables, `generated/` artifacts |
| `T24` | **Readout** | An accepted synonym for Measurement, normalized to it where the text makes a claim. **Settled only in that sense** — it also names the instrument (*"a weak readout"*) and sometimes the value, and those stay loose. | 162 uses in nucleus-docs |

## Refused spellings

Each row with **Auto: yes** becomes one generated Vale rule. `Kind` sets severity per the table
above. **Hits** is measured against `nucleus-docs` `docs/` on 2026-09-15.

| Refused | Use | Kind | Auto | Hits | Note |
| --- | --- | --- | --- | --- | --- |
| vesicle | GUV, SUV or LUV | Narrows | **yes** | 12 | GUV, SUV and LUV are distinct and must not merge. **Not a collapse** — `liposome` is itself general and has its own row below, so swapping one general word for another taught nothing. The rule flags and does not replace, because only the author knows which class it is. **The 12 are all plural**: `vesicle` singular appears 0 times, which is why the old `Collapses` rule caught none of them |
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
