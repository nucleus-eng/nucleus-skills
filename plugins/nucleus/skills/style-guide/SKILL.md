---
name: style-guide
description: Review or conform a page against whatever style guide the repo it sits in declares — the review order, where displaced content goes, and how to rewrite an internal reference. Use when authoring, editing, migrating or reviewing a documentation page, when conforming a drafted page, and when deciding where displaced content belongs.
---

This is the **procedure**. It states no rules of its own. Every rule lives in the style guide of the repo you are working in, and this skill points at it.

**If a rule seems to be missing, add it to that repo's guide — never here.** A rule stated in this skill binds every repo that installs it, and the whole point of the split is that each repo says what is true for its own corpus.

## Find the guide first

Look for `STYLE-GUIDE.md` at the repo root, then a `style-guide/` directory beside it. Read what is there and apply what you find.

**Tolerate a partial set.** Repos carry different subsets and that is correct, not a gap:

| File | Usually holds |
| --- | --- |
| `principles.md` | What these documents are for; what everything else follows from. **Read this first** — it is short, and the rest follows from it |
| `page-types.md` | The page types, and where displaced content goes. A repo with one page type has no need of it |
| `sections.md` | Every section of a page, in order |
| `conventions.md` | Terminology, figures, citations, what never appears, mechanics |

**Carry no opinion about which repo says what.** Asked to review a page, read that repo's guide and apply it. If it says meeting records belong on the page, that is correct there.

**MyST mechanics are not a style question.** Fence depth, tab-set nesting, cross-reference anchors, `.md`-not-`.html` links, figure placement — use `author-myst-content`.

## Reviewing a page

In this order. **The first step finds what is *missing*, which a read-through cannot see.** The rest find what is present and wrong.

### 1. Completeness — run the repo's checks first

Run whatever completeness checks the repo has before reading anything. They enumerate from a dependency graph, and that is the whole reason they go first: a tool can compute what *should* be on the page and compare.

**Prose review cannot do this. Reading inspects what is present, and absence has no textual signature** — a page missing half its composition reads exactly like a page whose composition is short. No amount of care recovers what was never written down.

That asymmetry fixes the order. Step 1 finds what is missing, by enumeration. Steps 2 to 4 find what is present and wrong, by reading. The other way round is a careful pass over an incomplete page.

**A scoped run only ever sees its own directory.** Run the scoped form while editing one page and the unscoped form before you finish — a page whose filename does not match the glob is invisible to a scoped run, and the check reports it only if the run covers the directory it is in.

Then by hand, against `sections.md`:

- Does every section the page needs exist? A missing requirements or implementations section is the common case.
- Does every enumerated list carry **every** item, or only the ones that were easy to find? Mark unknowns rather than omitting the row.
- Does every gap carry a tagged ask, or does it just say "not documented"?

### 2. Boundaries — is this content on the right page?

Use the repo's displacement table if it has one.

**Moving beats trimming.** When you cut a statement of what something is *not*, the content it carried usually has a home. Trimming the framing and leaving the paragraph is the common failure.

**The tell is a caption that argues with its own content** — a warning explaining that the table above is not really this thing, a note saying a figure is not really this one's. Writing one means the content is in the wrong section. Move it; do not label it.

### 3. Read every prose block

Ask the question the repo's `principles.md` sets. In a specification corpus it is usually: **does this describe the thing, or our work on the thing?**

**Do not trust a phrase search here.** This is the class that keeps surviving a pass. In one corpus a grep for the known phrases caught **none** of: *"still at the milestone-planning stage"*, *"waiting for Twist"*, *"Interim source"*, *"the 2026-08-14 meeting resolved"*, *"mitigation in progress"*, *"Figure not yet migrated"*. Every page invents new wording.

**A page with zero phrase hits is not evidence of conformance**, and a score built from phrase hits measures the phrases, not the category.

**When you find a phrasing violation, search the corpus for it before moving on.** These spread: one phrase reached three pages, an admonition reached two, a heading reached two. A sweep that introduced a phrase introduced it everywhere it fit.

### 4. Sections and prose

Check the page against `sections.md` section by section, and the wording against `conventions.md`.

## Rewriting an internal reference

Most of this text is doing real work — it is how a reader learns a number came from one unreplicated experiment. **Deleting the phrase alone makes preliminary data read as settled.** Four treatments:

1. **It hedges** — *"the source material does not specify…"* → characterise the evidence: *"not established; a single unreplicated experiment"*.
2. **It attributes** — a filename or slide number in a credits section → drop the citation, keep the person and affiliation.
3. **It dates** — *"the 2026-08-14 status meeting"* → keep the date, drop the meeting.
4. **It is a pointer for us** — *"raise on the questionnaire"* → delete, move to scratch.

## When a rule changes

**A page conformed under an older version of the rules is not conformant now.** Every rule came from reviewing a page that had already passed, so the conformed set is exactly the set most likely to violate a new one.

Re-run the whole set after any rule is added. One such pass produced twenty-two edits across nine pages that had each been called clean.

## Before you finish

Run the repo's pre-PR list.

**Verify token by token.** Diff every number, temperature, identifier and cross-link against the pre-edit file. Reading the diff is not enough: a rewrite that drops a citation can drop a real value in the same sentence.

**Some heading text is load-bearing.** Where a generator finds a section by its exact words, rewording the heading silently drops that section's content out of whatever the generator builds. Check the repo's guide for which headings those are.

**Do not rely on being careful about it.** Prefer the generator's own `--check` mode where one exists: it names every page whose block is stale or missing, which is what "silently" otherwise means. **A rule that asks an author to remember something is a rule the tool should be enforcing** — if you find a way to break the output that `--check` does not report, fix the generator rather than adding a warning back here.
