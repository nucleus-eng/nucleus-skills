---
name: author-spec-yml
description: Draft the spec.yml composition source that sits beside a module's spec.md. Covers what to read, which decisions are yours and which are not, and which figures belong in the source rather than on the page. Use when a module page has no spec.yml, when a page has been edited and its source must follow, or when a checker reports drift between the two.
---

# author-spec-yml

A `spec.yml` is the machine-readable composition beside a module's `spec.md`. The page is for people. The source is the contract for tooling.

This skill does not validate. `scripts/check-spec-schema.py` already checks shape and resolves every reference. It is better at that than prose.

This skill covers the part a validator cannot: the decisions you make while writing. Four of them are not obvious. Each was learned by getting it wrong.

Read the page. Do not write a source from a DevNote. A source records what its page says. If the figures live somewhere else, fix the page first. A source written from another document validates and then disagrees with the page beside it, and `scripts/check-spec-drift.py` reports that disagreement.

## 1. Start from the composition table

Open `spec.md` and find `# Reference Composition`. Each component in that table becomes an entry under `inputs`.

1. Give each input an id in kebab-case.
2. Give it a `title` that matches how the page names it.
3. Set `page` to the relative path of that component's own page, or to `null` when it has none.

Add a comment beside a `null` page saying what the thing is. A reader who cannot follow a link needs the part number or the sequence length in the file.

```yaml
inputs:
  base-cytosol:
    title: "Base Cytosol"
    page: ../base-cytosol/spec.md
  degfp-dna:
    title: "pOpen-deGFP"
    page: null            # 2812 bp; reporters/pOpen-deGFP.gbk in nucleus-eng/DNA
```

## 2. Write one step per process the page names

Each entry in `process_steps` is one composition step. Give it an `id`, a `process`, an `operator`, its `operands`, and what it `produces`.

A process with no page gets `page: null` and a `title`. Never link to a page that does not exist. Naming a process is a claim that the process exists. 21 of 76 steps in this corpus record the gap this way instead of inventing a link.

An ordering that changes the result gets its own step. Do not record it as a note on a combined step. This was learned while writing the four gel sources. A note is invisible to every checker, and a step is not.

## 3. Do not choose the operator

`mixing` means the operands end up in one compartment. `packing` means each keeps its own.

The operator follows from the sorts of the operands. It is not a judgement call and it is not yours. Write the step with `operator:` present and fill it from the process rather than from preference. Expect `scripts/check-operator-pairs.py` to disagree if you guessed. That checker compares each pair against claims argued independently of any `spec.yml`. It reports `unknown` as its own tier rather than as a pass.

A single label over more than two operands asserts the same operator on every pair. Half the steps in this corpus carry three or more operands. If two of them plainly differ, say so in the step's `notes:` instead of picking the majority.

## 4. Delete every figure the constituent page already states

This is the rule most often got wrong, and it has one test.

Delete a `parameters` value when two things hold. The step names an operand that has a page of its own, and that page states the figure. Keep the value otherwise. An audit of thirteen parameter entries removed three on that test.

Keep a figure when it states a fact no single constituent page can state. Three kinds qualify:

- A relation between components, such as an osmolarity.
- A step's own ratio.
- A reserved slot in a pinned total, such as headroom.

Every figure you keep must also appear on the page. `scripts/check-spec-drift.py` compares the two and reports three tiers. A figure the page does not carry at all is reported as absent. Absent is the tier that means something.

## 5. Use the keys that record uncertainty

Four keys exist so that a source can say what is not settled. Use them instead of rounding, guessing, or leaving a gap silent.

| Key | Use it when | Uses today |
| --- | --- | --- |
| `page: null` | the thing has no page in this corpus | 21 of 76 steps |
| `range:` on an input | the module does not fix the value, and a band is the truth | 3 |
| `optional: true` | the module composes without this step or input | 8 |
| `open:` | a question about the source itself | 35 of 49 sources |

Questions go under `open:` and nowhere else. Do not write a question into a `notes:` field or a comment. The `open:` key is the one place tooling can find them.

An input the module does not fix is an operand with a `range:`. It is not a parameter with an invented value. This was learned by writing the value first and finding no source for it.

## 6. An empty composition is a claim

`process_steps: []` is legal and says something. It says this Module has no constituents, and that no process in this corpus produces it. Eight of the 49 sources say exactly that. They are the analytes and the purchased substrates.

`minItems: 1` was removed from `process_steps` on Jon's ruling, 2026-09-20. It had asserted that every Module is composed. That is a membership condition the model never carried.

`inputs` still carries `minProperties: 1`. So a Module with nothing going into it has to list itself as its own input. That is a known wart. It is flagged in every atom source, and it is why those eight files read oddly. Follow the existing pattern instead of working around it.

## 7. Write the header comment

Every source in this corpus opens with a comment block. It carries three things:

1. What this file is, and that `spec.md` stays for humans.
2. What `mixing` and `packing` mean, so a reader need not leave the file.
3. The reading you took where the page was ambiguous, and why.

The third earns its space. A source that silently picks one reading of an ambiguous page is a source nobody can audit.

## 8. Before you hand it over

Run these in this order. Read the output rather than the exit code.

1. `python3 scripts/check-spec-schema.py` for shape and references.
2. `python3 scripts/check-composition.py` for the page. It must name every operand of the final step that has a page, under `# Constituent Modules`. Add that section if the page lacks it.
3. `python3 scripts/check-spec-drift.py` for the figures. Every figure you kept must appear on the page.
4. `python3 scripts/check-operator-pairs.py`, which is advisory. It reports when an operator disagrees with the sorts.

A checker that reports zero of zero is not a pass. Each of these prints its populations. Make sure that the number it checked is the number you expected.
