# Synthetic Learner Red Team Harness — Expanded PRD

**Client:** Nerdy / Varsity Tutors · **Contact:** harrison.glenn@varsitytutors.com
**Status:** Engineering spec for a demoable prototype · **Last updated:** 2026-06-15

---

## Original brief (preserved)

AI tutors and adaptive curricula look impressive in demos but fail when learners behave
like *real* students — who guess, stall, ask for the answer, change the subject, overuse
hints, pretend to understand, get bored, and creatively avoid the mental workout of
learning. Build a system that uses **synthetic learners** to stress-test and **recursively
improve** an AI tutor / curriculum / learning flow.

> "Do not just simulate students. Convince us your simulations reveal educational failures
> that would matter for real learners, then use those failures to improve the system."

The required loop:

```
synthetic learners → learning attempt → failure analysis → system improvement → re-test → regression check
```

A strong submission shows not only that the system improved, but **why the improvement is
credible and what may have been overfit** to the synthetic learners. (Full brief in `tmp1.pdf`.)

What the client says they are *actually* evaluating:

> "We are not evaluating whether you can make agents talk to each other. We are evaluating
> whether you can reason about learning, design a credible test harness, expose real
> educational risk, and avoid fooling yourself with synthetic evidence."

That sentence is the north star for every decision below.

---

## Product point of view (the position we are required to take)

A synthetic learner is only useful if it can **lose** — if it can fail to learn in ways that a
real student fails, *and* if our instrument can tell the difference between a learner who
*understood* and one who merely *complied*. So we build the harness around three
commitments:

1. **Separate what a learner *says* from what a learner *knows*.** Every synthetic learner
   has a hidden, ground-truth **knowledge state** (per-skill mastery + seeded
   misconceptions) that only the simulator sees. The tutor never sees it. "I get it" is a
   *claim*, scored against the hidden truth. This is what lets us catch a tutor that produces
   confident-sounding learners who can't transfer.

2. **Measure learning as transfer, not as local correctness.** A learner who can redo the
   exact problem they were just walked through has demonstrated mimicry, not learning. The
   instrument is a **pre-test → instruction → post-test → delayed transfer-test** design with
   *novel framings* on the transfer set. "Learning" = gain on the hidden mastery *that shows
   up on items the learner never practiced.*

3. **Instrument ourselves against self-deception.** Every headline metric ships with a
   **counter-metric** designed to catch us gaming it (details below), plus **held-out
   personas** and **held-out problems** to detect overfitting, and an **independent skeptical
   judge** (different prompt, configurable different model) as a human-agreement proxy.

### What counts as "learning" in this system
A statistically meaningful increase in **hidden true mastery** for a skill, demonstrated on
the **transfer test** (novel problem framings), net of any pre-existing mastery. We report
normalized gain `g = (post − pre) / (1 − pre)` for the post-test *and* a separate transfer
score, and we treat them as different things on purpose.

### What counts as "avoidance" in this system
A learner turn (or run of turns) where the learner reduces cognitive effort instead of doing
the work. Detected operational categories: **answer-extraction** ("just tell me"),
**topic-change / stalling**, **shallow compliance** ("ok", "I get it" with no reasoning
shown), **hint-farming** (requesting the next hint before attempting), and **bypass /
adversarial** (trying to derail or jailbreak the lesson). Each learner turn is labeled by an
**avoidance classifier** (LLM judge + deterministic rules). **Avoidance-recovery rate** =
fraction of avoidance episodes the tutor pulls back into productive work within N turns,
*without* surrendering the answer.

### Failure modes the harness is *designed* to expose
- Tutor **gives away answers** instead of teaching (answer-giving rate).
- Tutor accepts **shallow compliance** ("I get it") and moves on.
- Instruction that **raises post-test but not transfer** (teaching to the test).
- **Misconceptions that survive** instruction (and which ones, per skill).
- Tutor **fails to redirect** avoidance; or redirects but **damages rapport/agency**.
- **Hint dependence** — learner can't solve unaided after a hint-heavy session.
- **Robustness gaps** — a change that helps persona A regresses persona B.

### Failure modes the harness probably **misses** (stated up front, see Limitations memo)
- Anything driven by **non-textual** signals (affect, latency, classroom context).
- **Long-horizon** retention (we simulate one session + a short delay, not weeks).
- **Real human variance** — our learners are model-generated and may be *too* coherent, or
  share the base model's blind spots ("monoculture" risk).
- **Reward-hacking the judges** themselves — partially mitigated by the independent judge,
  not eliminated.

---

## Problem & users

- **Primary user:** an AI-tutoring / curriculum team at Nerdy (PM, learning scientist, ML
  eng) who needs to know *where their tutor fails real students before students do.*
- **Job to be done:** run a credible red-team of a tutor, get a ranked, evidence-backed
  failure report, apply a targeted fix, and **prove** the fix is real progress and not
  benchmark gaming.
- **The single most important flow:** open the **Overview**, see baseline-vs-improved with
  counter-metrics and a credibility verdict → drill into **Transcript Theater** to *watch* a
  synthetic learner expose a failure → see that failure drive a tutor change on the
  **Improvement Loop** screen, with the regression check that proves it didn't break other
  learners.

---

## Subject, learners, and tutor under test (the concrete instance)

- **Subject:** Algebra I — **linear relationships**: slope as rate of change, y-intercept as
  starting value, solving multi-step linear equations, translating word problems to
  equations. Chosen for its dense, well-replicated misconception literature and its fit with
  Varsity Tutors' K-12 / test-prep market.
- **Skills (graph nodes):** `slope_from_equation`, `slope_vs_intercept`,
  `rate_in_context`, `solve_linear_multistep`, `translate_word_problem`.
- **Seeded misconceptions (with citations in research notes):**
  - `M1 number-in-front` — "slope is whatever number sits in front of x," even when the
    equation isn't in `y = mx + b` form.
  - `M2 reversal-error` — "6 students per professor" → writes `6S = P` (Clement, 1981).
  - `M3 rate-as-intercept` — swaps the constant rate and the starting value in context.
  - `M4 equals-as-operator` — reads `=` as "compute the answer," mishandles balance in
    multi-step solving.
  - `M5 sign-blind-steepness` — "bigger number = steeper," ignoring sign.
- **Tutor under test (TUT):** an LLM tutor defined by a **versioned policy** (system prompt +
  hint ladder + assessment rules). `v0` is a deliberately naive "friendly helpful tutor"
  that over-explains, gives answers under mild pressure, and accepts "I get it." The
  improvement loop produces `v1` (Socratic redirection, hint laddering, misconception
  probes, mandatory transfer check).

---

## Synthetic learner design

Each learner = **persona archetype** × **trait vector** × **hidden knowledge state**.

- **Trait vector** (0–1 each, drives the learner agent's behavior prompt): `persistence`,
  `hint_seeking`, `honesty` (low = claims false understanding), `distractibility`,
  `reading_comprehension`, `effort_avoidance`, `gaming_tendency`, `confidence_calibration`
  (high = overconfident).
- **Motivation:** `mastery_vs_performance`, `anxiety`.
- **Hidden knowledge state:** per-skill `true_mastery ∈ [0,1]` + active misconceptions with
  strengths. Updated each turn by a lightweight **BKT-style learning model** (Bayesian
  Knowledge Tracing: parameters for prior, learn-rate, slip, guess) — so genuine instruction
  *can* move mastery, and slip/guess inject realistic noise. The tutor never sees this.

**The eight personas we ship (and why each matters):**

| # | Persona | Behavior it approximates | Failure it is designed to provoke |
|---|---------|--------------------------|-----------------------------------|
| 1 | **Shortcut Seeker** | "Just tell me the answer." | Tutor's answer-giving discipline |
| 2 | **Confident Guesser** | Fluent, fast, wrong; mistakes fluency for mastery | Tutor mistaking confidence for understanding |
| 3 | **Anxious Quitter** | Gives up after one struggle | Tutor's encouragement vs rigor balance |
| 4 | **Memorizer** | Aces familiar items, fails novel framings | Transfer failure hidden by local correctness |
| 5 | **Distractible** | Changes topic when effort rises | Tutor's redirection without losing rapport |
| 6 | **False-"I-get-it"** | Says "I understand" to move on | Tutor accepting shallow compliance |
| 7 | **Over-hinter** | Farms hints; can't act unaided | Scaffolding that breeds dependence |
| 8 | **Adversarial Bypasser** | Tries to derail/jailbreak the lesson | Tutor staying on-task under pressure |

Personas 1–6 are the **training set** for the improvement loop; **7–8 are held out** to test
whether a fix generalizes or was overfit to the learners we tuned against.

---

## Evaluation method

Per session we record a transcript with per-turn event labels; per run we aggregate.

**Headline metrics** (higher is better unless noted):
- **Learning gain** — normalized gain on the post-test.
- **Transfer rate** — accuracy on novel-framing transfer items.
- **Misconception correction** — drop in misconception-consistent answers, pre→post.
- **Avoidance-recovery rate** — avoidance episodes successfully redirected.

**Counter-metrics** (each paired to catch gaming of a headline):
- **Transfer-minus-posttest gap** — if post-test ↑ but transfer flat → *teaching-to-the-test* flag.
- **Answer-giving rate** (lower better) — paired with learning: if it drops but learning also
  drops, the tutor just went withholding.
- **Independence score** — can the learner solve unaided after instruction? Catches hint-dependence.
- **Held-out-persona delta** — improvement on personas 7–8 vs 1–6. Large gap → *overfit to synthetic*.
- **Held-out-problem delta** — improvement on unseen items vs seen items.
- **Rapport/agency score** — does redirection stay supportive and preserve student choice?
- **Independent-judge agreement** — a second judge (different prompt, optionally different
  model) re-rates a sample; we report agreement as a **proxy** for human review (clearly
  labeled as a proxy, not a human study).

**Credibility verdict:** a rules engine reads the metric/counter-metric pair set and emits
one of `REAL_PROGRESS`, `MIXED`, or `LIKELY_GAMING`, with the specific evidence that drove
the call.

---

## Recursive improvement loop (the core mechanic)

1. **Baseline run** — cohort (personas 1–6) × TUT `v0` → transcripts, per-turn events, metrics.
2. **Failure analysis** — cluster failures by `persona × skill × failure-mode` (heatmap); a
   **Diagnostician** (LLM) reads the worst clusters and proposes *targeted, minimal* policy
   changes with rationale (e.g., "add a misconception probe for M2 before accepting an
   answer; replace direct-answer fallback with a hint ladder").
3. **Apply** — produce TUT `v1` (new versioned policy; diff stored).
4. **Re-run** — same cohort **and** held-out personas 7–8, on seen **and** held-out problems.
5. **Compare + regression check** — per-persona, per-skill deltas; flag any metric that got
   *worse* for any subgroup.
6. **Verdict** — `REAL_PROGRESS / MIXED / LIKELY_GAMING` with evidence and an explicit
   overfit assessment.

Loop automation level: **human-in-the-loop by default** — the Diagnostician *proposes*, the
UI shows the diff, a click applies and re-runs. (Fully-auto is a config flag; we default to
proposal-and-approve because the brief rewards judgment over autonomy theater.)

---

## Screens / routes (demo inventory — the contract for Phase 3 & 4)

| Route | Screen | Purpose | Key components | Data shown |
|-------|--------|---------|----------------|------------|
| `/` | **Overview** | The headline story | Metric row (gain/transfer/misconception/recovery), baseline↔improved bars, credibility verdict callout, **CACHED-RUN badge + "Force live run"** | Latest baseline vs v1 summary |
| `/learners` | **Learner Lab** | Defend the population | Persona cards w/ trait radar (SVG), knowledge-state bars, seeded misconceptions, "why it matters" | 8 personas, traits, hidden state |
| `/run` | **Run Arena** | Configure & launch | Persona multiselect, tutor-version picker, topic, **cached vs live toggle**, progress stream | Run config + live/cached progress |
| `/transcripts` | **Transcript Theater** | *Make us believe* | Turn-by-turn dialogue, inline event chips (avoidance / answer-given / hint / misconception), hidden-state sidebar | One learner↔tutor session, annotated |
| `/failures` | **Failure Report** | Surface educational risk | `persona × skill × failure-mode` heatmap, ranked failure clusters, Diagnostician proposals | Clustered failures from baseline |
| `/improve` | **Improvement Loop** | Prove the fix | v0→v1 policy diff, loop stepper, before/after per-subgroup, **regression check**, verdict | Improvement record + comparison |
| `/metrics` | **Evidence & Metrics** | Anti-self-deception | Full metric+counter-metric table, held-out analysis, judge agreement, methodology notes | All metrics, both runs |
| `/about` | **Methodology & Limits** | Honesty layer | Product POV, research notes, decision log, **what we miss**, limitations memo | Static narrative + links |

Eight screens, every nav item real and wired. Nothing else is in scope.

---

## Data model (SQLite for the demo; Postgres-compatible via SQLAlchemy)

- **Skill**(id, key, name, description, misconceptions[json])
- **Persona**(id, key, name, archetype, trait_vector[json], motivation[json], defense)
- **KnowledgeState**(id, persona_id, skill_id, true_mastery, misconceptions[json]) — *hidden*
- **TutorVersion**(id, version, name, system_prompt, policy[json], parent_id, rationale)
- **Run**(id, tutor_version_id, label, cohort[json], mode[cached|live], status, created_at, summary[json])
- **Session**(id, run_id, persona_id, pre[json], post[json], transfer[json], scores[json])
- **Turn**(id, session_id, idx, role[learner|tutor|system], content, events[json]) — *the interaction log*
- **Metric**(id, run_id, name, value, counter[json], subgroup)
- **Improvement**(id, from_version_id, to_version_id, rationale, changes[json], regressions[json], verdict)

`Turn` + structured `events` *is* the "interaction logging system"; `KnowledgeState` *is* the
"learner state tracking database."

## AI surface (runtime — powered by the deployed-app OpenAI key)

| # | Call | Input | Output shape | Renders on |
|---|------|-------|--------------|-----------|
| 1 | **Learner turn** | persona + hidden state + history | learner utterance (+ hidden internal action) | Transcript / Run |
| 2 | **Tutor turn** | TUT policy + history | tutor response | Transcript / Run |
| 3 | **Assess answer** | item + learner answer | correct?, mastery update, misconception evidence | Metrics, hidden state |
| 4 | **Avoidance classifier** | learner turn + context | label + confidence | Transcript chips, recovery metric |
| 5 | **Evaluator judges** | session/run | rubric scores (transfer, scaffolding, rapport…) | Metrics |
| 6 | **Diagnostician** | failure clusters | proposed policy changes + rationale | Failure / Improve |
| 7 | **Independent judge** | sample of sessions | re-rating | Metrics (agreement) |

All calls go through one **provider abstraction** (`llm/`); OpenAI `gpt-4o-mini` is the
default model, swappable by env. LangChain is available but used sparingly (we keep prompt
control explicit). Every call is **logged** and the cached run is a recording of calls 1–7 so
the demo is instant and free; "Force live run" re-executes them for real.

## External integrations
- **OpenAI API** (chat completions + TTS for the demo video). Nothing else external at runtime.
- Optional **Postgres** via `DATABASE_URL` (Railway). Defaults to bundled SQLite.

## Acceptance criteria (live-verify ticks these)
- [ ] Overview loads and shows baseline↔improved with the CACHED badge and a credibility verdict.
- [ ] Learner Lab shows all 8 personas with trait radars and seeded misconceptions.
- [ ] Transcript Theater shows a real annotated session with avoidance + answer-giving + misconception chips.
- [ ] Failure Report renders the persona×skill×failure heatmap and Diagnostician proposals.
- [ ] Improvement Loop shows the v0→v1 diff, before/after per subgroup, a **regression check**, and a verdict.
- [ ] Evidence screen shows every metric *with* its counter-metric and the held-out/overfit analysis.
- [ ] "Force live run" triggers real OpenAI calls and produces a fresh run (when the key is set).
- [ ] No API key is present anywhere in the repo, the bundle, or the mockup.

## Open questions
None that block architecture. (Model choice, persona counts, and DB backend are all
config-driven with sensible defaults.)
