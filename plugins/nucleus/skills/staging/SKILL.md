---
name: staging
description: Propose edits to tracked files as a staging document rather than editing them directly — the four-part format, the compatibility read against other live proposals, provenance discipline, and the one-commit fold-in. Use when applying a ruling, resolving a conflict, or making any edit that changes what a tracked file claims; when working across more than one repo; or when several agents need a shared definition of what a staged proposal is. Covers when staging is overkill.
---

# Staging

**Do not edit a tracked file directly when the edit changes what that file
claims.** Write the proposal to a staging document, resolve it there, and
apply only when the developer says to.

This skill is the single definition of that control. It was reconciled from
two copies that had drifted and that gave opposite instructions on scope.
Each repository keeps a short block naming its own working directory,
reviewer and local exceptions, and points here for the rule.

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
- A mechanical fix the developer named — a typo, a broken link, a renamed
  path — where nothing the file asserts changes.
- A new file that overturns nothing and was asked for directly.

A fourth exemption is **proposed and not yet ruled**: a fix to something the
file gets *factually wrong* — a stale line number, a value since measured.
That is not changing what a file claims, it is bringing the file to what it
already meant to claim. The hazard is that "it was wrong" is the easiest
thing for an agent to believe about a file it wants to edit, so until this
is ruled, stage it and say why you think it is an error.

## What a staging document records

Four parts:

1. **The ruling or finding**, quoted.
2. **What it overturns**, quoted from the file it contradicts. This is the
   part that earns the ceremony — an edit that silently overwrites a claim
   hides whether the claim had a rationale behind it, and **a rationale is
   what makes a false claim look checked.**
3. **The edit sites**, as a table of file, line, current text, proposed text.
4. **What it leaves open**, including questions for the developer.

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
close items in the proposal, not in the review.** A developer answering
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

## What this skill does not hold

**Repo-specific evidence, paths and file lists.** Those are arguments *from* a
repository and stay in it.

**Anything a checker already enforces.** A prose copy of a guard drifts from
the guard, and nothing then says which is right. That argument applies to this
skill about itself.
