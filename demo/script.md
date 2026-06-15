<!-- Demo narration for the Synthetic Learner Red Team Harness.
     One paragraph = one spoken beat (tts.py splits on blank lines and ignores
     these HTML comments and # headings). ~7 minutes, architecture-deep. -->

# Synthetic Learner Red Team Harness — demo script (~7 min)

<!-- BEAT 1 — Overview top: problem & what this is -->
AI tutors look brilliant in a scripted demo and then fall apart on real students — the ones who guess, stall, ask for the answer, overuse hints, and say "I get it" just to move on. This is the Synthetic Learner Red Team Harness, built for Nerdy and Varsity Tutors. It builds a population of synthetic learners who behave that badly on purpose, runs them through an Algebra tutor, finds where the tutor fails real learners, fixes it, and then proves the improvement is genuine learning rather than a prettier benchmark.

<!-- BEAT 2 — Overview metric row + verdict -->
Here's the result up front. Between the baseline tutor and the improved one, learning gain climbs from near zero to about a third, transfer to brand-new problems more than quadruples, misconception repair jumps from under ten percent to over seventy, and answer-giving nearly disappears. The verdict in green reads "real progress" — but that label is earned by a rules engine, not asserted, and every headline number is deliberately paired with a counter-metric meant to catch us fooling ourselves.

<!-- BEAT 3 — Learner Lab: the core architecture, LLM + hidden oracle -->
The architecture is the important part, so let me be precise. Each synthetic learner is a real language-model agent, but kept on a short leash. A trait vector deterministically decides the learner's move each turn — attempt, ask for the answer, fake understanding, change the subject — and the model only renders that move in character. Underneath sits a hidden Bayesian-Knowledge-Tracing oracle that tracks the learner's true mastery and misconceptions, and the tutor never sees it. That separation is the entire credibility argument: behaviour looks human, but whether learning actually happened is reproducible arithmetic, not the model grading its own homework.

<!-- BEAT 4 — Learner Lab: the personas -->
These are the critics. Eight personas, each a distinct failure risk — the Confident Guesser who mistakes fluency for mastery, the Shortcut Seeker, the Memorizer who aces practiced items and fails novel ones, the one who says "I get it" to escape. The cyan bar is hidden true mastery; the pale tick is what they claim, and the gap between them is exactly what a correctness-only tutor can never see. Two of these personas are held out, so an improvement can't simply overfit to the learners we tuned against.

<!-- BEAT 5 — Transcript Theater: the engine + the interaction log -->
This is the simulation engine in action — a real recorded session. The learner takes a pre-test, works through a multi-turn dialogue with the tutor, then a post-test and a transfer test on novel framings. Here the Confident Guesser insists the slope is "the number in front of x" — a textbook misconception — and the baseline tutor replies "absolutely, you got it," and hands over the answer. Every avoidance move and every leaked answer is flagged inline by a real language-model judge and stored as a structured interaction log. The panel on the right is the hidden mastery the tutor could not see.

<!-- BEAT 6 — Evidence & Metrics: evaluation design + counter-metrics -->
Evaluation is where most red-teams fool themselves, so this screen is built to resist it. Every headline metric sits beside the counter-metric designed to expose gaming it. Transfer rose together with the post-test, so this isn't teaching to the test. Answer-giving collapsed while learning rose, so the tutor didn't just go silent. Independence held, so the new hint ladder didn't breed dependence. We even measure whether avoidance is detectable from text at all, rather than assuming it.

<!-- BEAT 7 — Evidence & Metrics: held-out + independent judge -->
Two further guards against self-deception. First, the held-out personas: we measure the learning-gain gap between the learners we tuned on and the ones we didn't — a small gap means the fix generalises instead of overfitting. Second, an independent judge — a different model running a skeptical-educator prompt — re-rates a sample of sessions, and we report how often it agrees with the primary evaluator. It's a proxy for human review, clearly labelled as such, and never dressed up as a human study.

<!-- BEAT 8 — Failure Report: clustering + diagnostician -->
Aggregate every session and you get this failure map — persona by skill, green for healthy, magenta for failing. The baseline tutor clusters its failures on reading slope from an equation, the reversal error in word problems, and surrendering answers under pressure. A diagnostician then reads the worst clusters and proposes targeted, minimal fixes: never give the answer, gate "I get it" behind an unaided solve, probe the reasoning behind a correct answer, and add a transfer check to every skill.

<!-- BEAT 9 — Improvement Loop: the recursive loop + verdict -->
Apply those and you get version one of the tutor — and this is the recursive loop the brief asks for. Baseline, cluster, propose, re-test including the held-out learners, and a regression check that flags anything that got worse for any subgroup. The credibility verdict isn't a single score; it's a rules engine weighing each gain against the counter-metric that would expose it. And it stays honest: the Adversarial Bypasser, who digs in harder when pushed, is reported as an open robustness gap, not swept under the rug.

<!-- BEAT 10 — Run Arena: usability + cached vs live + BYO key -->
Now usability. The default view is a cached recording of a real experiment, clearly badged, so the demo loads instantly and costs nothing to view. But it is not something you have to take on faith. The Run Arena launches a real run against the model — pick your cohort, your number of skills and turns, and either use the server's key or paste your own, which is used for that one request and never stored. Every learner turn, every tutor turn, and every judge is a live call.

<!-- BEAT 11 — Run Arena: scaling + engineering -->
On scaling and engineering. Sessions run concurrently behind a thread pool, and live runs are deliberately bounded — fewer personas, capped turns — to keep latency and token cost predictable, while the cached full run carries the complete story. The model is a single environment variable, so swapping or upgrading is trivial, and the independent judge can even run on a different model for genuine independence. Persistence is SQLite by default and Postgres in production through one variable, and the whole thing — API plus frontend — ships as a single Docker service.

<!-- BEAT 12 — GitHub repo: code quality + modularity + tests + docs -->
Under the hood it is a clean, modular codebase. A domain layer holds the personas, the oracle, the tutor policies, the engine, the classifiers, the evaluator, and the diagnostician; a thin FastAPI layer serves the API and the single-file frontend; and the credibility-critical logic is pinned by a deterministic test suite that needs no API calls. The documentation is part of the deliverable too — an expanded product spec, a decision log, research notes, a failure-mode report, and a limitations memo.

<!-- BEAT 13 — Methodology & Limits: honesty layer -->
Which brings us to the honesty layer. The methodology screen states plainly what this harness exposes and what it misses — no non-textual signals like hesitation or affect, no long-horizon retention, synthetic learners that may be too coherent or share the base model's blind spots, and judges that could in principle be gamed. Synthetic results are evidence, not proof. The strongest claim we make is comparative and counter-metric-guarded, and the honest next step is a small human pilot.

<!-- BEAT 14 — Overview: close -->
So that is the Synthetic Learner Red Team Harness: a population of synthetic learners who are genuinely useful critics of a tutor — especially when they behave inconveniently, evasively, or irrationally — wrapped in an instrument designed, at every step, to keep us from fooling ourselves with synthetic evidence. Thanks for watching.
