# The harness

How the gates fit together, and what each one can and cannot see.

## Four checks, increasing power, increasing cost

| # | Check | Catches | Cost | Can it see the blocker? |
|---|---|---|---|---|
| 1 | Schema / packager validation | malformed output | free | no |
| 2 | `check_contract.py` | missing sections, over-long quotes, banned phrasings, out-of-range references | free | **no** |
| 3 | `verify_quotes.py` + `verify_attribution.py` | invented evidence, wrong speaker | free | **no** |
| 4 | **Execution test** | unexecutable instructions, contradictions, impossible completion standards | one agent run | **yes** |

Checks 1–3 all passed on an artifact that could not be executed. If you only budget for the free ones, you ship that.

## The execution test

Three rules make it work.

### Rule 1 — isolate the executor

> Give the executor the artifact and nothing else.

A capable executor with access to neighbouring files *patches the gap*. It finds the missing material elsewhere, produces a plausible result, and the artifact's insufficiency never surfaces. The first execution run in this project hit exactly that: the executor disclosed it had to read two neighbouring files, "without which the output would have been a 1-row file instead of a 26-row one."

Forbid sibling access and the artifact either stands alone or doesn't.

Enumerate the forbidden paths explicitly. "Only read X" is weaker than "only read X; do not read A, B, C, or anything under D."

### Rule 2 — hide the answer key

If your test fixture documents its own planted defects, the executor must be told where to stop reading — and the instruction must be mechanical:

> Read from `# Prompt` to `# Draft`. **Stop at the line beginning `# Enumerated`.** Use `sed -n '/^# Prompt/,/^# Enumerated/p'` and ignore the last line.

Same for routing tests: strip expected answers from the task packs, and name the files that would leak them.

### Rule 3 — ask what was impossible, not whether it passed

The highest-yield question in the whole harness:

> **Any instruction that was ambiguous, self-contradictory, impossible to follow, or that referenced something not present?** Be blunt. A clean pass that hides a problem is worse than a failure report.

That question produced the blocker, a precise root cause ("three items depend on facts the input list does not collect"), and a dozen smaller defects. The pass/fail verdict produced almost nothing by comparison.

## Routing tests, if your artifacts are agent skills

Run them in rounds, tightening the rule each time.

**Round 1 — generous.** Let the evaluator read whatever a host plausibly sees. Establishes a baseline. Scored 49/49 here.

**Round 2 — strict.** Restrict to the `description` field alone, because that is all a real host sees at routing time. This is where defects appear: a one-sentence router description concealing 12 capabilities, deferral pointers naming targets that were not installed, scope exclusions living in the body where no host reads them.

**Round 3 — verify the fix with new probes.** Do not re-run the old wording. If you added a paraphrase to catch a phrasing, test *that paraphrase*. If you added a refusal clause, test a *fresh* request in the same family.

### Sibling-confusion cases are the valuable ones

For each pair of artifacts that could plausibly compete, write a case that must route to the *other* one. Here, 14 of 51 cases were sibling discriminations, and they all resolved — because **each description named its sibling as the destination for the cases it should not take.**

The structural finding: **negative pointers outperform positive ones.** "Not me → sibling X" did more routing work than any amount of positive self-description.

### One scoring mistake to avoid

The scorer compared every answer against a single `target`, and I set that to the bundle id rather than per-case expectations. It marked every *correct* answer as a false negative. The tool was fine; the suite was the wrong shape for it. **Sanity-check a 0% or 100% result before believing it.**

## Fixture hygiene

Your fixture will have bugs too. Mine claimed 412 words and contained 252 — and the artifact under test had percentage-based gates, so every one of them shifted. The executor caught it and recomputed against the real number.

Plant defects you can enumerate, then assert against the enumeration. If a gate is supposed to flag four mixed metaphors, put exactly four in and know where they are.

## Order of operations

```
generate artifacts
      │
      ├─ schema / packager validation ......... cheap, catches malformed
      ├─ check_contract.py .................... cheap, catches structural drift
      ├─ verify_quotes.py ..................... cheap, catches invented evidence
      ├─ verify_attribution.py ................ cheap, catches wrong speaker
      │
      └─ EXECUTION TEST (isolated) ............ the only one that catches
                │                               unexecutable instructions
                ▼
         fix, then RE-TEST IN ISOLATION
```

Re-testing in isolation matters: the fix for the blocker was inlining the missing 26 items, and the only way to confirm it worked was handing the single file to a fresh executor and getting back *"26/26 judgeable. I never read another file."*
