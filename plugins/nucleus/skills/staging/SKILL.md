---
name: staging
description: Propose edits to tracked files as a staging document rather than editing them directly — the four-part format, the compatibility read against other live proposals, provenance discipline, and the one-commit fold-in. Use when applying a ruling, resolving a conflict, or making any edit that changes what a tracked file claims; when working across more than one repo; or when several agents need a shared definition of what a staged proposal is. Covers when staging is overkill.
---

# Staging

**Do not edit a tracked file directly when the edit changes what that file
claims.** Write the proposal to a staging document, resolve it there, and
apply only when the Editor says to.

This skill is the single definition of that control. It was reconciled from
two copies that had drifted and that gave opposite instructions on scope.
Each repository keeps a short block naming its own working directory,
reviewer and local exceptions, and points here for the rule.

**The Editor is whatever reviewing body is leaving comments on the staging document** —
humans, agents, or both. Where provenance needs a name for who decided something, record who
the Editor was; otherwise *the Editor* is the right word and no name is owed. A ruling names
the person who gave it; a role names who may give one.

## When it applies

**Stage it when the edit changes what a tracked file claims.**

That is wider than "when applying a ruling", which is what the two source
copies said and narrower than what sessions actually did. A session that
stages twelve files, most of them applying no ruling, is following the
practised rule; writing down the narrow one leaves nobody sure which they
are obeying.

**Scope is the work, not the repository.** Working across two repos, the
control covers both. A session that stages in one and commits freely in the
other is the failure this exists to prevent — **and that has happened.**

### When staging is overkill

Not everything is a claim. These are not staged:

- Edits inside a gitignored working directory.
- A mechanical fix the Editor named — a typo, a broken link, a renamed
  path — where nothing the file asserts changes.
- A new file that overturns nothing and was asked for directly.

A fourth exemption is **proposed and not yet ruled**: a fix to something the
file gets *factually wrong* — a stale line number, a value since measured.
That is not changing what a file claims, it is bringing the file to what it
already meant to claim. The hazard is that "it was wrong" is the easiest
thing for an agent to believe about a file it wants to edit, so until this
is ruled, stage it and say why you think it is an error.

## Where the staging document goes

**Each directory's README declares its staging location.** Take the nearest
one that does: the README of the directory you are working in, then upward,
then the repository root. If none declares one, the default is:

```
tmp/STAGED-<date>-<topic>.md
```

**Ignore the pattern, not the filename.** A convention protected one name at a
time will eventually miss one, and the miss is silent — the next staging
document simply arrives tracked. Ignore `*-STAGING.md`, or whatever shape the
declared location takes, rather than adding names as they appear.

Watch what else the glob catches. `*-PLAN.md` looks like the obvious companion
and would swallow a tracked `REFACTOR-PLAN.md`; name that kind of exception
explicitly and say why.

**Check that the location is gitignored before you write to it.** This is the
one part worth doing every time. A staging document at a tracked path is one
`git add -A` away from being committed into an unrelated change — and a
document whose whole premise is *"uncommitted by design"* is then committed,
silently, saying otherwise. If the location is not ignored, ignoring it is the
first edit to make, not an afterthought.

A repository that declares a location should say it in one place. Two
declarations drift, and this skill exists because that already happened to the
rule itself.

## What a staging document records

Four parts:

1. **The ruling or finding**, quoted.
2. **What it overturns**, quoted from the file it contradicts. This is the
   part that earns the ceremony — an edit that silently overwrites a claim
   hides whether the claim had a rationale behind it, and **a rationale is
   what makes a false claim look checked.**
3. **The edit sites**, as a table of file, line, current text, proposed text.
4. **What it leaves open**, worded as explicit questions to the Editor. A statement of what is unresolved reads as a status report and gets skimmed; a question gets answered.

## Why the ceremony is worth it

Not because a single edit might be bad. **Because more proposals are queued
than can be applied at once, and staging them makes them checkable against
each other.**

On 2026-08-31 a compatibility read of two staging documents caught one
handing work to a section of another that did not yet exist — before either
was applied. Review of a finished commit would not have found it. The common
defect is inconsistency between live proposals; a single bad edit is the one
people imagine and the rarer case.

**The compatibility read decays.** A read is valid only against the files
that existed when it ran. The newest document owes the read; documents
already written are never revised to account for it.

## A ruling is not approval to apply

Settling what is true decides what the staging document should *say*. It does
not authorise touching a file.

The same holds for answers to questions raised inside the document — **those
close items in the proposal, not in the review.** An Editor answering
question 3 has not approved questions 1 and 2.

## The commit is the fold-in

One commit, after review, whose subject is applying the staging document. Not
edit, then commit, then discuss.

If an edit lands before approval, revert it **and then remove the revert as
well**: a commit that should not have existed should not leave a revert pair
in the history.

## Provenance

Every hash, path, line number, date and word count in a staging document is a
claim. Check it before writing it; mark an estimate as estimated.

**Line numbers are the ones that rot.** They are measured against a file that
keeps moving, and a stale line number does not fail loudly — it points
confidently at the wrong place. When a document cites a range, record what it
was measured against and when. When acting on one somebody else wrote,
re-measure first.

**A cross-repo pin names three things: repo, branch and hash.** The repo is
the one the quoted text *lives in*, not the one you are standing in — a pin
records the source, never your location. The branch says which tree a reader
must stand in to see it. The hash makes it checkable after either moves.

Each part answers a failure that has happened. Two sessions read an earlier
one-sentence version as *"where I was when I took this"* and pinned the wrong
repo. A branch name and a date were given where a hash was required; a branch
moves and a date is not checkable by anything. And a hash alone is precise but
unanchored: it does not say which tree to stand in.

**A pin that names the wrong object is worse than no pin, because it looks
checkable and so nobody checks it.** A bare quote invites checking. A
malformed one ends the question.

**Edit sites partition by repo; quotations cross.** A review pass touching two
repos produces one staging document per repo, each naming the other. But a
document that overturns a claim must quote it, so a quotation reaches across
where an edit site does not — which is exactly why the quotation needs the pin
and the edit site does not.

**The hash must be reachable by the reader, not only by you.** A commit that
exists only in an unpushed local tree satisfies every part of this rule and
still cannot be checked by anyone else — push it, or say so in the pin. A
local resolver answers *can I resolve this*, which is a different question
from *can anyone*.

**A hash taken on a tree behind the remote is a hash waiting to be rewritten.**
A rebase changes it, the old one stops resolving, and nothing distinguishes a
pin that was never pushed from one that was rewritten under you. **Take the pin
after you rebase, not before.**

Verify a cross-repo hash before writing it. A dead hash has shipped three
times, and the third was inside the staging document proposing this rule:

```bash
gh api repos/<owner>/<repo>/commits/<sha> --jq .sha || echo "DEAD: <sha>"
```

**Branch on the exit code, never on whether it printed something.** On a dead
hash `gh api` exits non-zero **and writes its error to stdout**, so a
`[ -n "$output" ]` test passes on exactly the failure it was added to catch. A
sweep of 37 pins reported 37 resolving for this reason, and it was caught by
noticing that one of the "resolving" hashes belonged to the repo running the
sweep.

**Existence is not reachability, and the command above answers the first.**
`gh api .../commits/<sha>` resolves a commit that sits on no branch at all,
because objects survive branch deletion — which is why sixteen deletions broke
none of thirty-seven pins. `git ls-remote` and `git branch -r --contains`
answer whether a reader can get to it. **Verifying the hash is not verifying
the pin.**

## A staging document is signed

**By the session that wrote it, and so is an append to someone else's.** On 2026-09-13 an
unsigned append headed with a repo name and not an author reached the wrong one of three
sessions working that repo. **A heading precise enough to look sufficient is the authorship
version of a pin that names the branch and not the hash.**

**A signature carries the address, a durable id, and the date**, because no one field
survives. The address is what a reader replies to and it drifts: one session was reported
under two short names on consecutive days. The transcript id is durable and reaches nobody.
The date says which of the two to trust.

## Open questions go at the top

**Ahead of the drafted edits, each with room for a ruling written inline beside
it.** A reviewer reads a staging document once, top to bottom. With the
questions last they read every proposed edit before reaching the one thing the
drafter needs from them, and a long document buries the ask.

The block is a running ledger of decided against open, updated as rulings
arrive. **A ruling written beside its question is the record** — not a chat
reply, and not a second document.

## A staging document is `.md`, and so is every question in it

**Never a `.yml` or other data file.** A question in a data file is invisible
to the review loop: the reviewer opens documents, not sources, and a data file
carries no place for an answer to go. A genuine open question written as a
`yaml` key sat unread because of this.

The same holds in reverse — a data file may *record* that something is open,
but the question itself lives in the document.

## Retire by moving, never by deleting

**A spent staging document goes to `tmp/archive/<date>-<kind>/` with a README
row saying what became of it**, where `<kind>` names why it left: applied,
superseded, parked, absorbed. The kinds are a small closed set; inventing a
fifth to suit the document being moved defeats the point of having them.

**Move on evidence, never on the document's own header.** A header saying
"applied" is a claim by its author, and the claim has been wrong. Check the
commits.

**Carry the residue first.** A document that is finished except for three open
items is not finished; move those into a live successor before the file goes,
or they leave the queue silently. **A file whose purpose is to stop items being
lost cannot be archived while it still holds unanswered items** — archiving it
performs the failure it documents.

## Compact a document that has outlived its decision tree

**A document that absorbs carried items accretes**: what closed stays in, and a reader
cannot tell a live question from a settled one. Rewrite it down to what is still fresh — the
open questions, the findings that survive, the edit sites — and move the full version to the
archive rather than deleting it. **Say what was dropped and why**, so the compaction is
auditable rather than trusted.

**Compact after a ruling burst, not at a length.** Fold the rulings in, then sweep what they
closed. Past roughly two thousand words, check whether the length is closed items or fresh
ones.

## A document meant for a person says whether it reached them

**Delivery state goes in the document's own `#` heading** — `SENT`, `UNSENT`,
`POSTED` or `FILED` — with the date, the recipient, and a link where there is
one.

The mark is visible without opening the file, and once it is expected, **its
absence means something.** Questions that are finished, correct and undelivered
look exactly like questions that are done.

## Finding the tags

**Grep raw, case-insensitive, and name the directory:**

```bash
grep -rn -i "@claude" <path>
```

**`<path>` is load-bearing and `.` is not a substitute.** A ripgrep wrapper
honours `.gitignore` when it finds a repo root at or above where it starts, so
searching `.` from a repo root silently skips ignored directories — which is
where staging documents live. It searches an ignored path when handed that path
directly. Measured once at `0` hits against `44`.

**Never read a clean grep as "no tags" without checking the command.** Four
recorded failures are an agent hand-rolling an extractor and getting the scope
subtly wrong; a false clean ends the question where no grep at all would not.
`scripts/check-tags.py` in this repo is that extractor written once, and it
refuses to report a clean run over zero files or zero candidate strings.

**Four more checkers live beside it in `scripts/`, each taking the repo to check as its first
argument**, and `README.md` § Checks lists them. Every one exits 2 when it read nothing, and
none is a CI gate: the staging location is gitignored, and a fresh clone has nothing for them
to read.

## What this skill does not hold

**Repo-specific evidence, paths and file lists.** Those are arguments *from* a
repository and stay in it.

**Anything a checker already enforces.** A prose copy of a guard drifts from
the guard, and nothing then says which is right. That argument applies to this
skill about itself.
