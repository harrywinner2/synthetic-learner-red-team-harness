<!-- Demo narration for the Synthetic Learner Red Team Harness.
     One paragraph = one spoken beat (tts.py splits on blank lines and ignores
     these HTML comments and # headings). Stage directions are in the comments. -->

# Synthetic Learner Red Team Harness — demo script (~4.5 min)

<!-- BEAT 1 — Overview, top of page -->
AI tutors look brilliant in a demo and then fall apart on real students — the ones who guess, stall, ask for the answer, and fake understanding to move on. This is the Synthetic Learner Red Team Harness, built for Nerdy and Varsity Tutors. It runs a population of synthetic learners who behave that badly on purpose against an Algebra tutor, finds where the tutor fails, fixes it, and then proves the fix is real learning and not just a prettier score.

<!-- BEAT 2 — Overview metric row + verdict banner -->
Here's the headline. Between the baseline tutor and the improved one, learning gain went from near zero to about a third, transfer to brand-new problems more than quadrupled, misconception repair jumped, and the credibility verdict reads "real progress." But a rising number proves nothing on its own — so every figure here is paired with a counter-metric designed to catch us fooling ourselves.

<!-- BEAT 3 — Overview counter-metrics column -->
That's this column. Transfer rose together with the post-test, so we're not teaching to the test. Answer-giving collapsed while learning climbed, so the tutor didn't just go quiet. And an independent judge — a different model — agreed with our verdict most of the time. The whole system is built so it can't grade its own homework.

<!-- BEAT 4 — Learner Lab -->
These are the learners doing the stress-testing. Each one is a trait vector, a hidden knowledge state, and a seeded misconception — the Confident Guesser who mistakes fluency for mastery, the Shortcut Seeker, the one who says "I get it" just to escape. The tutor never sees the hidden state, so "I get it" is a claim we score against the truth. Two personas are held out, so a fix can't simply overfit to the learners we tuned against.

<!-- BEAT 5 — Transcript Theater -->
This is where it gets convincing. A real recorded session: the Confident Guesser insists the slope is "the number in front of x" — a textbook misconception — and the baseline tutor says "absolutely, you got it," and hands over the answer. Every avoidance move and every answer the tutor leaks is flagged inline by a real language-model judge. The panel on the right is the hidden mastery the tutor couldn't see.

<!-- BEAT 6 — Failure Report -->
Aggregate every session and you get this failure map — persona by skill, where green is healthy and magenta is failing. A diagnostician reads the worst clusters and proposes targeted fixes: never give the answer, gate "I get it" behind an unaided solve, probe the reasoning behind a right answer, and add a transfer check to every skill.

<!-- BEAT 7 — Improvement Loop -->
Apply those and you get version one of the tutor. This is the loop: baseline, cluster the failures, propose, re-test on the held-out learners too, and check for regressions. The verdict isn't a single score — it's a rules engine weighing each gain against the counter-metric that would expose it, and it tells you plainly where the tutor is still weak. The Adversarial Bypasser, for instance, is reported as an open robustness gap, not swept under the rug.

<!-- BEAT 8 — Run Arena, trigger a live run -->
And it's not a recording you have to take on faith. The Run Arena launches a real run against the model — your cohort, your settings, your key or ours. Every learner turn, every tutor turn, every judge is a live call. The default view is clearly labelled as a cached recording precisely so this button can prove it.

<!-- BEAT 9 — Methodology & Limits, then back to overview -->
Finally, the honesty layer. The methodology screen states what this harness exposes and what it misses — no long-horizon retention, learners that may be too coherent, judges that could in principle be gamed. Synthetic results are evidence, not proof. But the pattern is strong and repeatable, and the next step is a human pilot. That's the harness: synthetic learners that are genuinely useful critics — especially when they behave badly.
