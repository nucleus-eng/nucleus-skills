---
name: author-spec-yml
description: Write or edit a `spec.yml`, the machine-readable composition source that sits beside a Module's `spec.md` in nucleus-docs. Use when adding a source to a Module page that has none, when a page edit changes a figure the source repeats, when choosing between `mixing` and `packing`, when deciding whether a number belongs in the source or on a constituent page, or when a source must declare `refines`, `sensitivities`, `impositions`, `requires` or `measured_by`. Covers the draft-from-the-page workflow, the four rules an author cannot infer, and which checker catches which mistake. Authoring only — the validator is `scripts/check-spec-schema.py` and this skill does not duplicate it.
---

# Authoring a `spec.yml`

A `spec.yml` is the machine-readable composition beside a Module's `spec.md`. The prose
`# Constituent Modules` list stays for people; this file is the contract for tooling.

**A validator already exists and you must not rebuild it.** `scripts/check-spec-schema.py`
checks the file against `scripts/spec-yml-schema.yml` plus five things a schema cannot express:
the `module` key equals its directory, every operand names an input or an earlier product, no two
steps produce the same id, `abstract:` names a real directory under `docs/processes/`, and every
`page:` resolves on disk. Run it. This skill is about what it cannot check.

## Draft from the page, then delete

Do not write a source from scratch. Read the Module's `spec.md` and transcribe:

1. One `inputs` entry per row of the composition table. Give it a `page:` when the row links to
   a Module, and `page: null` when it does not.
2. One `process_steps` entry per process the page names. Use `page: null` where the page names
   no process.
3. Every figure the page states, as a `parameters` entry on the step it belongs to.
4. `operator:` present and **unfilled**. See the next section.

**A draft that is 80 percent right and says which 20 percent needs a person beats emitting
nothing.** Then delete under rule 2 below.

## Four rules you cannot infer from the schema

### 1. `operator` is not a free choice. It follows from the sorts

Use `mixing` when the operands end in one compartment and `packing` when each keeps its own.
`scripts/check-operator-pairs.py` compares your value against a table seeded from claims argued
independently of any `spec.yml`, and it will disagree with a guess. It is advisory and it prints
`unknown is not a pass` for sort-pairs no claim covers, which is most of them.

**Never guess it to make a diagram look right.** If you cannot tell, leave the step out and ask.

**One case decides itself and is easy to get backwards.** A step that puts an enzyme in the same
compartment as its substrate produces a readout with no off state. That is correct only when
something else in the Module provides the gate. `detector-theophylline` mixes CPRG with a
LacZ-encoding template and is right, because its riboswitch holds the ribosome binding site
closed. `reporter-lacz` did the same thing and was wrong, because nothing else gated it, and its
own page said so: *"LacZ converts CPRG on contact, so a reaction colocalizing both is in the ON
state."* **Ask what supplies the off state before you write `mixing`.**

### 2. The `parameters` rule is operational

**Delete a value when the step names an operand that has a page of its own and that page states
the figure. Keep it otherwise.** An audit removed three of thirteen on that test.

**Read the comment before deleting the key it sits on.** One value carried a working range rather
than a restatement, and it was safe to delete only because its constituent page stated the same
range in different words.

### 3. A number belongs in the source when no single constituent page can state it

A relation like an osmolarity that must match across a membrane. A step's `ratio`. A `headroom`
slot. Those are properties of the composition, not of any part, so no part's page can carry them.

**A figure for an operand with no page at all also stays**, and that the operand has no page is
the finding rather than the duplication.

### 4. `page: null` is a recorded gap, not a failure

It says nobody has written that page yet. It is used freely and it is honest. **Do not invent a
page to fill it, and do not write a page to satisfy a checker** — a check that demands a referent
and then gets one has verified that a path resolves, not that the relation is true.

## Where a source says more than its composition

| Key | Carries | Watch for |
| --- | --- | --- |
| `refines` | the class this Module belongs to | must be the **immediate** parent, and must name a directory in this repo. A class page in another repo can never be the target |
| `sensitivities` | what an object is sensitive to | a property of the **object** |
| `impositions` | what a step imposes | a property of the **step** |
| `requires` | what must hold for a step to run | a property of the **morphism**, checked for reachability |
| `measured_by` | the process that reads this Module out | **name the process that actually measures it** |

**A Conflict is never written.** `scripts/check-conflicts.py` computes it from a sensitivity
meeting an imposition. Declare the two halves and let it derive the third.

**`measured_by` is the one that goes wrong quietly.** `reporter-degfp` declared a colorimetric
readout whose own page scopes itself to a chromogenic substrate hydrolyzed by a reporter enzyme.
deGFP has neither and is read on fluorescence channels. The path resolved, so every check passed.

## A class page gets a source too, and it is not empty

An abstract class composes **abstract constituents**: operands that carry `page: null` because no
page in the corpus describes a generic one. Thirteen of the fourteen sourced classes name inputs and twelve run a step.

**So `process_steps: []` is not what a class looks like.** Write the composition at the grain the
class shares, and put what the members disagree about in `open:` rather than in the inputs.

## Two traps that cost real time

**Resolve an operand to its page, never to its key.** Two keys can name one module —
`membrane-chicago` and `membrane-popc-chol-chicago` did. Anything that counts members by key
sees two where there is one and reports a design decision nobody made.
`scripts/check-input-aliases.py` finds these, advisorily, and 137 of 219 keys carry `page: null`
and cannot collide yet, so a green run counts the identified ones and nothing else.

**Never put a quotation in a `.yml`.** Vale's `TokenIgnores` exempts quoted spans in `.md` and
**does not apply to `.yml` at all**. A quotation that is fine on the page will fail CI in the
source. Cite the page that carries it instead.

## Finish the job

**Give the page a diagram, or the source is invisible where a reader looks.** Add the
`gen:composition-diagram` markers inside the `# Reference Composition` tab-set and run
`python3 scripts/render-composition.py <path>/spec.yml --embed`. **Never hand-edit generated
mermaid**; fix the generator and regenerate. A Module whose composition is a single box gets no
diagram at all.

**Then run `scripts/check-composition-tabs.py`.** A diagram makes an omission visible: a page
whose graph contains a membrane and has no Membrane tab reads as *this Module has no membrane*
rather than *we did not write it down*. **A composition tab carries a table, not a sentence
pointing elsewhere.**

**Then the rest**, all from the repo root:

```bash
python3 scripts/check-spec-schema.py
python3 scripts/check-composition.py
python3 scripts/check-spec-drift.py
```

`check-spec-drift.py` is the one that catches a page edit invalidating its own source. It reports
three tiers and only the top one is agreement.

## What none of this checks

**No checker compares a figure in your source against the same figure in the page's prose table
by value.** `check-spec-schema.py` checks shape and references, `check-composition.py` compares
which modules are named and never what they are named at, and `check-spec-drift.py` asks whether
a figure still appears rather than whether it agrees. **If the page says 5 nM and your source
says 50 nM, nothing will tell you.** That is the live gap in this layer and it is why rule 2
exists: a figure you deleted cannot drift.
