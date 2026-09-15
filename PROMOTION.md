# Promoting a staging-namespace skill to canonical

Skills in the `devstudio-` namespace carry a Provenance section marking them
as staging — not yet reconciled with the canonical skills they were adapted from,
and not yet owned by a domain row in the README ownership table.

## What "canonical" means

A canonical skill:
- Has no "staging-namespace" language in its `description:` or `## Provenance`
  section
- Is owned by a named row in the README domain table
- Cross-references rather than restates (its content lives here, not also
  somewhere else)
- Passes `check-skills.py` including `invokes:` validation

## When to promote

A staging skill is ready to promote when all of the following are true:

1. `python3 scripts/check-skills.py` passes for this skill
2. Its `invokes:` frontmatter and INVOKE body markers are in sync (check 7)
3. It cross-references shared content in `references/` rather than restating it
   inline — any block that could apply to more than one skill belongs in
   `plugins/nucleus/references/`, not in the SKILL.md body
4. Jon has reviewed the skill via the staging workflow
   (`plugins/nucleus/skills/staging/SKILL.md`)
5. The skill's `## Provenance` section says what it supersedes and why

## How to promote

1. Remove "This is a staging-namespace (devstudio-) skill — see 'Provenance'
   below before treating it as canonical." from `description:`
2. Update `## Provenance` to describe what the canonical form superseded and
   when, rather than marking it as staging
3. Add a domain row to the README ownership table
4. If a canonical skill already covers the same domain (e.g. `verify-dna-constructs`
   and `devstudio-verify-dna-constructs` overlap), decide: merge into one, or
   keep two with explicitly different scopes and descriptions. Both are valid;
   silent overlap is not.
5. After review and merge, strip the source copy from the origin repo (or update
   it to cross-reference here) — Phase 5 work in REFACTOR-PLAN.md

## Coexistence of staging and canonical

A staging skill and its canonical counterpart may coexist under different names
temporarily (e.g. `devstudio-verify-dna-constructs` alongside `verify-dna-constructs`).
This is intentional: the staging version is narrowly scoped and may have different
behavior. The condition for coexistence is that the two skills must have explicitly
different descriptions and different `invokes:` graphs — if they are functionally
identical, one should be deleted or redirected to the other.

## What is NOT a promotion blocker

- Outstanding REVIEW flags in the skill's outputs (those are runtime artifacts,
  not skill-authoring issues)
- Missing keyword vocabulary (`devnote-keywords.md` not yet built)
- `devstudio-docs-g-to-m` not yet built (downstream pipeline skill, independent)
