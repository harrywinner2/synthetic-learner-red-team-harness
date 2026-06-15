# Synthetic Learner Red Team Harness

Built for **Nerdy / Varsity Tutors** · contact harrison.glenn@varsitytutors.com

AI tutors look great in demos and fall apart on real students — the ones who guess, stall,
ask for the answer, fake understanding, and quietly avoid the actual work of learning. This
project builds a population of **synthetic learners** who behave that badly on purpose, runs
them against an Algebra I tutor, finds where the tutor fails, fixes it, and then proves the
fix is *real learning* and not a prettier benchmark.

The thing that makes it trustworthy is one design decision, repeated everywhere: **we never
let the system grade its own homework.** Every learner has a hidden knowledge state the tutor
can't see, "learning" is measured as transfer to problems the learner never practiced, and
every flattering number ships next to a counter-metric designed to catch us fooling ourselves.

> Live demo: see the deploy URL in `BUILD_LOG.md`. The Overview shows a **cached recorded
> run** by default (so it loads instantly and costs nothing to view); the **Run Arena** and
> the **Force live run** button execute a real, smaller experiment against the model.

## What's in the box

A FastAPI backend and a single-page frontend that together give you eight screens:

- **Overview** — baseline vs improved tutor, the four headline metrics, and a credibility verdict.
- **Learner Lab** — the eight personas, their trait radars, and the gap between what they *know* and what they *claim*.
- **Run Arena** — assemble a cohort and run it live (your key or the server's).
- **Transcript Theater** — watch one real session turn by turn, with avoidance and answer-leakage flagged inline.
- **Failure Report** — the persona × skill failure heatmap and the Diagnostician's proposed fixes.
- **Improvement Loop** — the v0→v1 policy diff, before/after by subgroup, the regression check, and the verdict.
- **Evidence & Metrics** — every metric beside its counter-metric, plus held-out and judge-agreement analysis.
- **Methodology & Limits** — the product position, research notes, and an honest list of what this harness misses.

## How it actually works

There are three moving parts, and the separation between them is the whole point.

**1. The synthetic learners are real LLM agents on a short leash.** Each persona (Confident
Guesser, Shortcut Seeker, Anxious Quitter, Memorizer, …) is a vector of behavioural traits.
Those traits deterministically decide *what move* the learner makes each turn — attempt, ask
for the answer, fake understanding, change the subject, try to bypass the lesson — and the LLM
renders that move in character, applying the misconception we seeded. So the transcripts read
like real students, but the behaviour is reproducible rather than left to the model's whim.

**2. A hidden knowledge oracle decides whether anyone actually learned.** Every learner carries
a per-skill *true mastery* and a set of misconceptions, updated by a Bayesian-Knowledge-Tracing-style
model. Crucially the tutor never sees it. A bare explanation nudges mastery a little; a
scaffolded, gated, misconception-probing lesson moves it a lot; giving away the answer moves it
almost not at all. Test scores are the *expected accuracy* this latent state predicts — which is
how we measure "beyond the answer was correct," and why the numbers are reproducible arithmetic
instead of an agent's self-report.

**3. LLM judges do the qualitative work.** A classifier labels avoidance from the transcript
text; an answer-leakage detector flags when the tutor gives the game away; a *different*
model acts as an independent skeptical-educator judge so we can report agreement as a proxy
for human review. The improvement loop is closed by a Diagnostician that reads the failure
clusters and proposes targeted policy edits.

The improvement loop runs baseline (v0) → cluster the failures → propose a fix → build v1 →
re-test on the same learners **plus two held-out personas and held-out problems** → compare →
regression-check → emit a verdict of `REAL_PROGRESS`, `MIXED`, or `LIKELY_GAMING` with the
evidence that drove it.

## Why you can trust the result (and where it breaks)

The harness is built to argue *against* its own good news:

- If the post-test rises, did **transfer** rise with it? (If not → teaching-to-the-test.)
- If answer-giving drops, did **learning** still rise? (If not → the tutor just went silent.)
- If the trained learners improved, did the **held-out** learners improve too? (If not → overfit.)
- If the primary evaluator is happy, does an **independent judge** agree?

It will still miss things, and the Methodology screen says so plainly: no affect or latency
signals, no long-horizon retention, learners that may be *too* coherent or share the base
model's blind spots, and judges that can in principle be gamed. Synthetic results are evidence,
not proof — the honest next step is a human-subjects pilot.

## Running it locally

You need Python 3.11+ and an OpenAI API key.

```bash
cp .env.example .env          # then paste your key into OPENAI_API_KEY
python -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt

# (optional) regenerate the cached run from a real experiment — takes ~3 minutes
python scripts/generate_fixture.py

cd backend && uvicorn app.main:app --reload --port 8000
# open http://localhost:8000
```

The key is read **server-side only**. It lives in `.env` (gitignored) and nowhere else on
disk — never in the frontend, never in the committed fixture, never in a log. In the Run
Arena a user can paste their *own* key; it's used for that one request and never stored.
Rotate the key after the client review.

Run the tests (no API calls — they pin the credibility-critical logic deterministically):

```bash
cd backend && pytest
```

## Deploying

The repo ships a `Dockerfile` and `railway.json`. On Railway: create a project from the repo,
add `OPENAI_API_KEY` (and optionally `OPENAI_MODEL`) as service variables, and deploy. The one
service serves both the API and the frontend. SQLite is the default store; add a Postgres
plugin and Railway's `DATABASE_URL` is picked up automatically.

## Layout

```
backend/app/
  domain/      personas, skills, the BKT oracle, learner & tutor agents,
               the simulation engine, classifiers, evaluator, diagnostician, compare
  llm/         OpenAI provider abstraction (+ a labelled fallback if the API is down)
  harness.py   orchestrates a full baseline→improve→compare experiment
  api/         FastAPI routes;  models.py + store.py  persist runs and the interaction log
  fixtures/    cached_run.json — a recording of a real experiment, shown by default
frontend/      index.html — the single-file SPA (extends ui/mockup.html)
docs/          expanded PRD, decision log, research notes, failure-mode report, limitations
scripts/       fixture generation, secret guard, demo TTS + video assembly
```

See `docs/` for the deliverables called out in the brief, and `BUILD_LOG.md` for the decision
trail.
