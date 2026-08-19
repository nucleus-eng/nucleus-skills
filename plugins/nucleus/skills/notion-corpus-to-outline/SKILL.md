---
name: notion-corpus-to-outline
description: Read a live Notion workspace — a page plus its comment threads, meeting-note transcripts, and sibling drafts — and produce a sourced outline. Use when the source material is still in Notion rather than exported, when the user says "read the comments", "check the transcripts", "what did we decide", or points at a Notion page and asks what it should say. This is the step upstream of ingest: it produces the structured, source-tagged draft that ingest turns into a DevNote.
---

# Notion Corpus to Outline Skill

## Purpose

Turn a live Notion corpus into a sourced outline.

The ingest skill accepts "a Notion export" as an input type. That works when someone has already exported the content. It does not work when the material is still spread across a live workspace — a page, twelve comment threads, four sibling drafts, and a dozen meeting-note transcripts that only exist as blocks inside other pages.

This skill covers that case. It ends where ingest begins:

```
live Notion workspace  ->  /notion-corpus-to-outline  ->  sourced outline  ->  /ingest  ->  DevNote
```

**Scope: reading and structuring. Not writing prose.** The output is an outline where every claim carries a source tag, not a draft manuscript.

## Reference

Use `skills/devnote-style-guide.md` as the quality anchor for anything that will become a DevNote. This skill produces the layer above that — the outline the style guide is then applied to.

---

## 1. Mechanics that are not obvious

### The default flags hide most of the content

- **`notion-fetch` without `include_transcript: true` returns an AI summary and the words `Transcript omitted`.** The summaries paraphrase and strip the quotable phrasing. Always fetch the raw transcript when the goal is the words people used.
- **`include_transcript: true` returns every meeting-note block on the page**, not just the one a URL anchor points at. A page anchor does not isolate a block. One fetch per page, not one per meeting.
- **`notion-get-comments` needs `include_all_blocks: true` and `include_resolved: true`.** The defaults hide most threads. A page that appears to have three comments often has twelve.
- **`notion-fetch` with `include_discussions: true`** shows where threads are anchored in the body. Use it to find out whether a rewrite will destroy them.

### Large fetches

A transcript-heavy fetch will exceed the token limit and be persisted to a file. **Do not slice it blindly.** Extract the `<transcript>` sections with a regex first — this routinely cuts a 130k-character fetch to around 20k of actual transcript.

### Finding the rest of the corpus

Follow the **ancestor path** on any page to find its siblings. A page in a database usually has several relatives written the same week, containing the same decisions phrased differently. That is how the related drafts get found, and it is the step most often skipped.

### Writing findings back

`notion-update-page` with `command: "update_content"` and `content_updates: [{old_str, new_str}]` is a string replace, the same shape as `Edit`. Use it for targeted changes; use `replace_content` only when the whole body changes.

Notion markup worth knowing:

```
<details><summary>Toggle title</summary>…</details>
<callout icon="⚠️" color="yellow_bg">…</callout>
<mention-date start="2026-08-12"/>
<empty-block/>
```

Prefix machine-written toggle summaries with `CLAUDE` so humans can tell authorship at a glance.

**Notion auto-links bare domains** in text you write, and re-applies this on every edit. Do not fight it.

---

## 2. Failure modes

Every item here has been hit in practice.

### Do not assume who wrote a comment

Comment authors come back as UUIDs. Resolve them with `notion-get-users`. **The page author is often not the commenter**, and the commenter is often the person who asked you to read the page. One session assumed a dozen threads belonged to a co-author; all of them belonged to the requester.

### Transcripts garble proper nouns — flag, never repair silently

Cross-reference against the workspace user list and against any cited papers. Observed failures: a grant name rendered as a nonsense word; a French book title rendered as a person's name; two similarly-named colleagues collapsed into one person; a cited paper's author name transcribed two different ways in the same session, and never located as a result.

**Keep a "names to correct" section in the outline.** Silently fixing a name destroys the evidence that the transcript is unreliable at that point.

### Rewriting a page destroys the comments anchored to it

Not "orphans" — **destroys**. Notion deletes a block's comments along with the block.

Before any `replace_content`:

1. Fetch all threads with both flags on and **write them verbatim to a local file.**
2. Put a collapsed copy on the page itself, with a table showing where each thread landed.
3. Put a dated callout at the top explaining what happened and pointing at the toggle.
4. Tell the user the real cost before doing it, not the softened version.

### Re-fetch comments live and diff against a baseline

People keep commenting while you work. Record a baseline count with a timestamp and re-check immediately before acting on it. Corrections arriving mid-session are common, and they tend to invalidate work already done.

### Check what has already been decided

Vocabulary and framing decisions are often settled weeks earlier in a different document and never propagated. Search for them before proposing anything new. Proposing a decision that was already made, differently, is expensive.

---

## 3. Judgment

### Keep three files, not one

| File | Contains | Test |
|---|---|---|
| Sourced collation | Quotes and framing, tagged by origin | Every line traces to a source |
| Synthesis | Claims that appear in **no** source | Every claim names what it bridges |
| Outline | What the document should say | Every bullet carries a source tag |

Keeping them apart is what stops restatement being smuggled in as insight. Merged into one file, everything becomes "findings" and nothing can be checked.

### Verify that the synthesis produced something

State the number of claims that appear in no source. **If the answer is zero, say the step failed.** Do not present a good collation as a synthesis.

### Give every claim its strongest objection

Write the objection to actually bite, so a human can kill the claim in ten seconds. This is the highest-value habit in the workflow. In one session it caused two of nine claims to be substantially rewritten on first read and one to be discarded — all because the objection sat next to the claim instead of being left implicit.

### Prefer events to conclusions

The recurring complaint that "the details aren't there" has one structural cause: **documents organised as conclusions cannot contain detail.** Organise by dated event and the specifics arrive for free. One dated sentence about what stalled and what unstalled it carries more than a page of characterisation.

When the corpus is thin on events, say so plainly and name who could supply one.

### Route deferred material, do not park it

An appendix that says "cut" loses things. An appendix that says "cut — goes to document X, because it needs a citation" keeps them. Every deferred item should name its destination. Reserve "genuinely parked" for the few items with nowhere to go, and list them separately so the difference is visible.

### The framing-caveat callout

When old comments are still valid on content but stale on framing, do not delete them and do not silently apply them. Write a callout above them stating **which half holds**:

> The context and motivation in these comments still hold. The framing guidance does not, because …

This is the general solution to "some of these only apply to the version I wrote yesterday."

### Propagate corrections, then sweep

A single correction usually invalidates text in three or four files. Apply it everywhere, then sweep mechanically for the dead phrasing:

```bash
grep -rn "the dead claim\|its variants" *.md
```

Expect the sweep to return only your own correction notices. Anything else is a file you forgot. **Working documents go stale within the hour** — sweep before any step that generates new work from old files, because a stale input propagates into work nobody thinks to re-check.

### Do not let a superseded claim survive as a hedge

When a claim is wrong, mark it dead in place — struck through, with the correction beside it. Deleting it silently means somebody re-derives it next week. This applies to your own reasoning too: if you inferred something the sources never said, say that you inferred it.

---

## 4. Conventions worth adopting

### The `CONTEXT.md` file

Ten lines at the root of the work: who is involved and what they are doing, why this session exists, and a Resources list of every Drive folder, Notion page and repo. It is the difference between a session that starts cleanly and one that spends its first hour orienting.

### Put findings where the team already reads

Local markdown is fine for working notes. Conclusions belong back in Notion as dated toggle blocks. A session that writes everything locally has done its work somewhere nobody will look.

### Record the empty shells

Follow parent and grandparent project pages for inherited context. When they turn out to be empty, write that down so nobody checks twice.

---

## 5. Order of operations

1. **Orient.** Fetch the page. Follow the ancestor path to find siblings. Write a `CONTEXT.md`.
2. **Get everything, with the flags on.** Comments with both flags; transcripts raw, one fetch per page. Resolve author UUIDs.
3. **Record a baseline.** Thread count and timestamp.
4. **Collate, tagged by source.** Organise by what the language *does*, not by which page it came from. Flag where two documents say the same thing differently.
5. **Synthesise, in a separate file.** Claims that appear in no source, each with the sources it bridges, what changes if true, and its strongest objection. State the count.
6. **Stop. Let the human read it.** A real gate, not a formality — expect claims to be killed here.
7. **Re-fetch comments and diff.** Then outline: every bullet source-tagged, every deferred item routed.
8. **Preserve, then write back.** Archive the threads, then update Notion with a dated callout explaining what changed.
9. **Hand off to `/ingest`** if the outline is destined to become a DevNote.
