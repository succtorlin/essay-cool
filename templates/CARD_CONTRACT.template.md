# Artifact contract (template)

> Fill the bracketed parts for your project. This is the document you hand to
> whatever writes your artifacts — human or model — and the thing
> `check_contract.py` enforces mechanically.
>
> **Write this before generating anything.** A contract written afterwards
> describes what you got, not what you wanted.

## 1. Structure

Exact section headings, in this order:

```
## [SECTION 1]
## [SECTION 2]
## [SECTION 3]
```

Headings are matched literally. Pick them once and do not let them drift.

## 2. Evidence rules

- **Quote cap: ≤ [N] words per quotation.** Separate quotes into separate blocks; never merge two into one oversized field.
- Every quotation carries a **locatable citation** — source id plus chapter, page, timestamp or chunk id. A citation that names only the work is not locatable.
- **Never reproduce [the protected content class]**. Where you must indicate what it said, paraphrase in ≤ 10 words.

## 3. Attribution rules

- Name every attributed speaker **with their role**, every time.
- **Never aggregate distinct voices into an anonymous consensus** ("experts agree", "reviewers generally think"). If one named person said it, say who.
- **Declare which sources are genuinely independent.** Two works by the same author are one voice reprinted, not two witnesses. State this explicitly wherever it applies — it is the single easiest error to make and the hardest to spot later.
- Second-hand analysis is **post-hoc**. Tag it. A commentator explaining why something worked is not evidence that it did.

## 4. Mandatory clauses

Every artifact's `## [BOUNDARY SECTION]` must carry:

1. **[The honest promise.]** What this method does and does not deliver. If your sources' own authorities limit the claim, quote them — their limits are more credible than yours.
2. **[The sampling limit.]** If the evidence is drawn from successes only, say so, and state plainly which conclusions cannot be drawn from it.
3. **[Currency.]** If the sources have a date and the world has moved, say what changed.
4. **Capability-specific limits.** Single source, single site, undefined dosage, non-converging judgement — enumerate them.

## 5. Additions must be labelled

Any rule your artifact needs that **the source does not supply** gets an inline marker:

```
（ADDED BY PIPELINE — not from the source）
```

This is the clause that keeps a distillation honest. Models fill gaps smoothly and silently; the marker makes the seam visible. Reviewers should be able to grep for it.

## 6. Currency section

When source material is dated, use a physically separate block so your knowledge never blends into the source's voice:

```
### ⚠ [YEAR] → now (NOT from the source)
- The source claims: ...
- What changed since: ...
> Added by the pipeline, not present in the source material.
> Author's knowledge cutoff [DATE]; verify current rules before relying on this.
```

## 7. Executability — the clause most contracts omit

Every artifact with an instruction section must satisfy:

- **Self-sufficiency.** Everything needed to execute is *in this artifact*. If it tells the reader to work through a list, the list is here. Do not rely on a sibling file.
- **Inputs are enumerated**, including the ones only a human can supply. An instruction whose input is never collected is unexecutable, and nothing static will tell you.
- **Completion standard is reachable** from the declared inputs alone.
- **Missing-input behaviour is specified per item** — which items go unjudged, which proceed. "Stop and ask" must not be the answer to a single absent field.
- **Declare every verdict value you actually use.** Promising three and using five is a real defect.

> Verify this clause by **execution**, not inspection. Hand the artifact to a fresh agent, forbid every other file, and ask what was impossible. See `docs/METHODOLOGY.md`.

## 8. Prohibited

- Reproducing [the protected content class] beyond the stated paraphrase limit
- Presenting two same-author works as independent corroboration
- Presenting post-hoc commentary as causal evidence
- Presenting pipeline-added rules as the source's
- Anonymous-consensus phrasing in place of named attribution
- Declaring a taxonomy mutually exclusive without testing it against real input
