# Failure Mode Report

What the synthetic learners exposed in the baseline Algebra I tutor (v0), what we changed, and
what survived the change. The live, exact numbers are on the **Evidence & Metrics** and
**Improvement Loop** screens; the figures here are the stable headline findings from the
recorded run (`backend/app/fixtures/cached_run.json`).

## The baseline tutor's failures (v0)

v0 is a friendly, encouraging tutor — and that is precisely the problem. Across the cohort it
exhibited four failures that a correctness-only dashboard would never surface:

1. **It gives away answers under mild pressure.** Answer-giving rate ≈ **0.53** — in roughly
   half of stuck-moments the tutor simply stated or confirmed the answer. The Shortcut Seeker
   and the Over-hinter trigger this almost every turn. (See Transcript Theater: the tutor
   replies "Absolutely, you got it!" to a wrong answer.)
2. **It accepts confident wrong answers without probing.** The Confident Guesser asserts
   "slope is the number in front of x" (misconception M1) and v0 validates it. Misconception
   correction is near-zero (**≈0.08**): the misconceptions walk out the way they walked in.
3. **It mistakes "I get it" for understanding.** The False-"I-get-it" persona advances past
   every skill without ever solving one unaided.
4. **It produces brittle, non-transferable performance.** Transfer accuracy sits at **≈0.09**
   and the transfer-minus-post gap is sharply negative — learners can echo a practiced item
   and fail its re-framing. The Memorizer makes this unmistakable.

The persona × skill heatmap (Failure Report screen) clusters the damage on `slope_from_equation`
(M1 unprobed), `translate` (M2 reversal error), and multi-step solving (answer surrendered).

## The change (v1)

The Diagnostician read those clusters and proposed four targeted, minimal edits, which we
applied as the v1 policy:

- **Never state the final answer** — replace the answer-fallback with a recall → represent →
  first-step → self-check hint ladder.
- **Gate "I get it"** behind one independently-solved item.
- **Probe reasoning** when a correct answer matches a known misconception (M1, M2).
- **Run a transfer check** at the end of every skill.

## What improved — and the evidence it's real

| Signal | v0 | v1 | Why it's credible |
|---|---|---|---|
| Learning gain | ≈0.02 | ≈0.32 | normalized pre→post on hidden mastery |
| Transfer | ≈0.09 | ≈0.40 | measured on novel framings, rose *with* the post-test |
| Misconception correction | ≈0.08 | ≈0.75 | only repaired because v1 probes reasoning |
| Answer-giving (↓ better) | ≈0.53 | ≈0.03 | and learning still rose → not just withholding |
| Independence | up | up | hint ladder didn't breed dependence |

The counter-metrics are the point: transfer rose alongside the post-test (not teaching-to-the-test),
answer-giving collapsed *while* learning climbed (not a withholding tutor), and an independent
skeptical-educator judge agreed with the primary verdict on most sessions.

## What survived / what's still open

- **The Adversarial Bypasser remains the weak case.** When pushed, this held-out persona digs
  into bypass attempts; v1's redirection holds the line only inconsistently. This is reported
  as a robustness regression, *separately* from overfit — it is the clearest "still broken."
- **Misconception M5 ("bigger number = steeper") resists repair** more than the others, by
  design, so the report always shows at least one misconception that instruction doesn't fix.
- **Held-out generalisation is good but not perfect** — the learning-gain gap between trained
  and held-out personas is small and disclosed on the Improvement screen; it is the honest
  measure of how much the fix is tuned to the cohort we optimised against.

## The verdict

The rules engine weighs the headline metrics against their counter-metrics and emits
`REAL_PROGRESS`, `MIXED`, or `LIKELY_GAMING` with the specific reasons. Because the LLM
dialogue is stochastic, the verdict can sit at `REAL_PROGRESS` or `MIXED` across runs — and
that honesty is intentional: a single run is evidence, not proof. The strong, repeatable
finding is the **pattern** — large gains on learning, transfer, misconception repair, and
answer-discipline, with the counter-metrics holding — not any single decimal.
