---
name: notion-corpus-to-outline
version: 1.0.0
description: |
  Turn a Notion corpus — a page plus its comment threads, meeting-note
  transcripts, and sibling draft documents — into a sourced outline. Use when
  asked to read a Notion page and its comments, pull raw meeting transcripts,
  mine a set of related drafts, reconcile scattered feedback, or produce an
  outline or brief from any of that. Also use when the user says "read the
  comments", "check the transcripts", "what did we decide", "pull framing from
  the other pages", or points at a Notion page and asks what it should say.
  Covers the Notion tool flags that hide content by default, the failure modes
  of transcript garble and misattributed comments, and how to separate sourced
  collation from genuine synthesis.
license: MIT
compatibility: claude-code
---

# Notion corpus to outline

Reading a Notion corpus well is mostly a matter of knowing what the tools hide by default, and of keeping three kinds of writing apart: what sources say, what follows from them, and what the outline should be.

Everything below was learned by getting it wrong first.

---

## 1. Mechanics that are not obvious

### The default flags hide most of the content

- **`notion-fetch` without `include_transcript: true` gives you an AI summary and the words `Transcript omitted`.** The summaries paraphrase. They strip exactly the quotable phrasing you need. Always fetch the raw transcript when the goal is the words people used.
- **`include_transcript: true` returns every meeting-note block on the page**, not just the one a URL anchor points at. A page anchor does not isolate a block. One fetch per page, not one per session.
- **`notion-get-comments` needs `include_all_blocks: true` and `include_resolved: true`.** The defaults hide most threads. A page that looks like it has three comments often has twelve.
- **`notion-fetch` with `include_discussions: true`** shows where threads are anchored in the body, which is how you tell whether a rewrite will destroy them.

### Large fetches

A big transcript fetch will exceed the token limit and get persisted to a file. **Do not slice it blindly.** Extract the `<transcript>` sections with a regex first — that turned a 130k-character fetch into about 21k of actual transcript per session.

### Finding the rest of the corpus

Follow the **ancestor path** on any page to find its siblings. A page in a database usually has four or five relatives that were written in the same week and contain the same decisions phrased differently. That is how the related drafts get found.

### Writing back

`notion-update-page` with `command: "update_content"` and `content_updates: [{old_str, new_str}]` is a string replace, same shape as `Edit`. Use it for targeted changes. Use `replace_content` only when the whole body changes.

Notion markup worth knowing:

```
<details><summary>Toggle title</summary>…</details>
<callout icon="⚠️" color="yellow_bg">…</callout>
<mention-date start="2026-08-12"/>
<empty-block/>
```

Prefix machine-written toggle summaries with something like `CLAUDE` so humans can tell authorship at a glance.

**Notion auto-links bare domains** in the text you write (`b.next` becomes a link). It will re-apply this on every edit. Do not fight it.

---

## 2. Failure modes, all of them observed

### Do not assume who wrote a comment

Comment authors come back as UUIDs. Resolve them with `notion-get-users`. **The page author is often not the commenter, and the commenter is often the person who asked you to read the page.** One session assumed twelve threads were the co-author's; all twelve were the user's own.

### Transcripts garble proper nouns — flag, never repair silently

Cross-reference against the workspace user list and against the papers. Observed in one session: "Slum v1" was the Sloan grant; "Stephanie Duke" and "Biology's Indicator" were Stéphane Leduc's *La Biologie Synthétique*; "Zhanar" and "Gennar" were the same unlocated paper; two similarly-named people were repeatedly merged into one.

**Keep a "names to correct" section in the outline.** Silently fixing a name loses the evidence that the transcript is unreliable there.

### Rewriting a page destroys the comments anchored to it

Not "orphans" — **destroys**. Notion deletes a block's comments along with the block.

Before any `replace_content`:

1. Fetch all threads with both flags on and **write them verbatim to a local file.**
2. Put a collapsed copy on the page itself, with a table showing where each one landed.
3. Put a dated callout at the top saying what happened and pointing at the toggle.
4. Tell the user the real cost before doing it, not the softened version.

### Re-fetch comments live and diff against a recorded baseline

People keep commenting while you work. Record a baseline count with a timestamp, and re-check immediately before you act on it. In one session three arrived mid-work and two of them were corrections to claims already written down.

### Check what has already been decided

Several vocabulary and framing decisions in a corpus will have been settled weeks earlier in a different document and never propagated. Search for them before proposing anything new. Proposing a decision that was already made — differently — costs credibility that is hard to get back.

---

## 3. Judgment

### Keep three files, not one

| File | Contains | Test |
|---|---|---|
| Sourced collation | Quotes and framing, tagged by origin | Every line traces to a source |
| Synthesis | Claims that appear in **no** source | Every claim names what it bridges |
| Outline | What the piece should say | Every bullet carries a source tag |

Keeping them apart is what stops restatement being smuggled in as insight. If they are one file, everything becomes "findings" and nothing can be checked.

### Verify that the synthesis produced something

State the number of claims that appear in no source. **If the answer is zero, say the step failed.** Do not present a good collation as a synthesis.

### Give every claim its strongest objection

Write the objection to actually bite, so the human can kill the claim in ten seconds. This is the single highest-value habit in the whole workflow: in one session, two of nine claims were substantially changed by the user on first read, and one was killed outright — all because the objection was right there next to the claim.

### Prefer events to conclusions

The recurring complaint that "the details aren't there" has one structural cause: documents organised as conclusions cannot contain detail. Organise by dated event and the specifics arrive for free. *"Development was stalled on DNA-encoded TetR, but we launched forward quickly once we switched to purified proteins"* carries more than a page of characterisation.

When the corpus is thin on events, say so plainly and name who could supply one.

### Route deferred material, do not park it

An appendix that says "cut" loses things. An appendix that says "cut — goes to piece 4, because it needs a citation" keeps them. Every deferred item should name its destination. Reserve "genuinely parked" for the few things that really have nowhere to go, and list them separately so the difference is visible.

### The framing-caveat callout

When old comments are still valid on content but stale on framing, do not delete them and do not silently apply them. Write a callout above them saying **which half holds**:

> The context and motivation in these comments still hold. The framing guidance does not, because …

This is the general solution to "some of these are only relevant to the version I wrote yesterday."

### When a correction lands, propagate it and sweep

A single correction usually invalidates text in three or four files. Apply it everywhere, then run a mechanical sweep for the dead phrasing:

```
grep -rn "the dead claim\|its variants" *.md
```

Expect the sweep to return only your own correction notices. Anything else is a file you forgot. **Documents in an active project go stale within the hour** — run the sweep before any step that generates new work from old files, because a stale input propagates into work nobody thinks to re-check.

### Do not let a superseded claim survive as a hedge

When a claim is wrong, mark it dead in place — struck through, with the correction next to it. Deleting it silently means somebody re-derives it next week. This also applies to your own reasoning: if you inferred something the corpus never said, say that you inferred it.

---

## 4. Prior art and conventions

### There may be tooling already

Check for it before building anything. In one workspace, `doc2devnote` (`github.com/antonrmolina/doc2devnote`) already turned Google Docs into DevNotes with Claude, and a whole session existed to generate test cases for it.

### The `CONTEXT.md` convention

A ten-line file at the root of the work: who is involved and what they are doing, why this session exists, and a Resources list of every Drive folder, Notion page and repo. Cheap, and it is the difference between a session that starts cleanly and one that spends its first hour orienting.

### Put findings where the team already reads

Local markdown files are fine for working notes. Conclusions belong back in Notion, as dated toggle blocks. A session that writes everything locally has done the work somewhere nobody will look.

### Record the empty shells

Follow parent and grandparent project pages for inherited context — and when they turn out to be empty, write that down so nobody checks twice.

---

## 5. Order of operations

1. **Orient.** Fetch the page. Follow the ancestor path to find siblings. Write a `CONTEXT.md`.
2. **Get everything, with the flags on.** Comments with both flags; transcripts raw, one fetch per page. Resolve author UUIDs.
3. **Record a baseline.** Thread count and timestamp.
4. **Collate, tagged by source.** Organise by what the language *does*, not by which page it came from. Flag where two documents say the same thing differently.
5. **Synthesise, in a separate file.** Claims that appear in no source, each with its sources, what changes if true, and its strongest objection. State the count.
6. **Stop. Let the human read it.** The outline's framing depends on what survives. This is a real gate — expect claims to be killed here, and expect the corpus's own instinct to catch over-claiming that you missed.
7. **Re-fetch comments and diff.** Then outline, every bullet source-tagged, every deferred item routed.
8. **Preserve, then write back.** Archive the threads, then update Notion with a dated callout explaining what changed.
