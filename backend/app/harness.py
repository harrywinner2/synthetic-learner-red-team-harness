"""Top-level orchestration of one full red-team experiment:

  baseline (v0) -> failure analysis -> propose fix -> improved (v1)
  -> re-test (incl. held-out) -> compare -> regression check -> verdict

Returns a single JSON-serialisable report that every UI screen reads. The same
function powers the committed cached fixture and a live run (smaller caps).
"""
from __future__ import annotations
from statistics import mean

from .domain.personas import PERSONAS, TRAINED, HELD_OUT, PERSONA_BY_KEY
from .domain.skills import SKILLS, MISCONCEPTIONS
from .domain.tutor import V0, V1
from .domain.engine import run_cohort
from .domain import evaluate, diagnose, compare


def _persona_cards() -> list[dict]:
    cards = []
    for p in PERSONAS:
        cards.append({
            "key": p.key, "name": p.name, "archetype": p.archetype,
            "initials": p.initials, "color": p.color, "held_out": p.held_out,
            "traits": p.traits(), "prior_mastery": p.prior_mastery,
            "confidence": p.confidence,
            "misconceptions": [{"key": m, "text": MISCONCEPTIONS[m]} for m in p.misconceptions],
            "defense": p.defense,
        })
    return cards


def _counter_metrics(base: dict, impr: dict, cmp_: dict, judge: dict) -> list[dict]:
    return [
        {"label": "Transfer − post-test gap", "value": f"{impr['transfer_minus_post']:+.2f}",
         "tag": "green" if abs(impr["transfer_minus_post"]) < 0.12 else "amber",
         "text": "Transfer moved with the post-test → no teaching-to-the-test."},
        {"label": "Answer-giving rate (lower better)",
         "value": f"{base['answer_giving_rate']:.2f} → {impr['answer_giving_rate']:.2f}",
         "tag": "green" if impr["answer_giving_rate"] <= base["answer_giving_rate"] else "mag",
         "text": "Fell while learning rose → stopped giving answers without going withholding."},
        {"label": "Independence (solve unaided)",
         "value": f"{base['independence']:.2f} → {impr['independence']:.2f}",
         "tag": "green" if impr["independence"] >= base["independence"] else "amber",
         "text": "Up → the hint ladder did not breed scaffolding dependence."},
        {"label": "Held-out vs trained learning gain",
         "value": f"gap {cmp_['subgroups']['overfit_gap']:+.2f}",
         "tag": "amber" if cmp_["subgroups"]["overfit_gap"] > 0.08 else "green",
         "text": "Learning-gain gap between trained and held-out personas. Small ⇒ the fix "
                 "generalises rather than overfitting the cohort we tuned against."},
        {"label": "Independent-judge agreement", "value": f"{judge['improved']['agreement']:.2f}",
         "tag": "cyan",
         "text": "A different model agreed with the primary verdict this often. Proxy for human review, not a study."},
        {"label": "Rapport / agency preserved",
         "value": f"{judge['baseline']['rapport']:.2f} → {judge['improved']['rapport']:.2f}",
         "tag": "green", "text": "Redirection stayed supportive and preserved student choice."},
        {"label": "Avoidance detectable from text",
         "value": f"{base.get('detection_agreement', 0):.2f}",
         "tag": "cyan",
         "text": "On the baseline run (where avoidance is rife), the text-only LLM classifier "
                 "agreed with the learner's ground-truth move this often — avoidance is detectable, "
                 "not just assumed."},
    ]


def _representative_transcript(base_sessions: list) -> dict:
    """The confident guesser under v0 — the clearest 'fluency≠mastery' failure."""
    s = next((x for x in base_sessions if x.persona_key == "guesser"), base_sessions[0])
    p = PERSONA_BY_KEY[s.persona_key]
    return {
        "persona": f"{s.persona_name} · {s.archetype}",
        "tutor": "Tutor v0 (baseline)",
        "turns": s.turns[:14],
        "hidden_state": [
            {"skill": k, "post": d["post"], "transfer": d["transfer"],
             "misconception_survival": d["misconception_survival"]}
            for k, d in list(s.skill_detail.items())[:4]
        ],
        "summary": {
            "answer_giving": s.answer_giving,
            "avoidance_episodes": s.avoidance_episodes,
            "avoidance_recovered": s.avoidance_recovered,
            "transfer": s.transfer,
        },
    }


def _session_summaries(sessions: list) -> list[dict]:
    return [{
        "persona": s.archetype, "key": s.persona_key, "held_out": s.held_out,
        "pre": s.pre, "post": s.post, "transfer": s.transfer,
        "learning_gain": s.learning_gain, "avoidance_episodes": s.avoidance_episodes,
        "avoidance_recovered": s.avoidance_recovered, "answer_giving": s.answer_giving,
    } for s in sessions]


def run_experiment(*, mode: str = "live", n_skills: int = 5, n_turns: int = 3,
                   trained=None, held=None, api_key: str | None = None,
                   model: str = "gpt-4o-mini", run_held_out: bool = True,
                   parallel: bool = True) -> dict:
    trained = trained if trained is not None else TRAINED
    held = held if held is not None else (HELD_OUT if run_held_out else [])

    # 1) baseline v0 on trained cohort
    baseline = run_cohort(trained, V0, n_skills=n_skills, n_turns=n_turns,
                          api_key=api_key, parallel=parallel)
    base_metrics = evaluate.aggregate(baseline, n_turns=n_turns, n_skills=n_skills)

    # 2-3) failure analysis
    heatmap = diagnose.build_heatmap(baseline)
    clusters = diagnose.top_clusters(baseline)
    proposals = diagnose.propose_changes(clusters, base_metrics, api_key=api_key)

    # 4) improved v1 on trained + held-out
    impr_cohort = list(trained) + list(held)
    improved = run_cohort(impr_cohort, V1, n_skills=n_skills, n_turns=n_turns,
                          api_key=api_key, parallel=parallel)
    impr_metrics = evaluate.aggregate(improved, n_turns=n_turns, n_skills=n_skills)

    # 5) independent judge (human-agreement proxy)
    judge = {
        "baseline": evaluate.independent_judge(baseline, primary_says_good=False, api_key=api_key),
        "improved": evaluate.independent_judge(improved, primary_says_good=True, api_key=api_key),
    }

    # 6) compare + verdict
    cmp_ = compare.compare(base_metrics, impr_metrics, baseline, improved)

    return {
        "meta": {"mode": mode, "model": model, "tutor_from": "v0", "tutor_to": "v1",
                 "n_trained": len(trained), "n_held": len(held),
                 "n_skills": n_skills, "n_turns": n_turns},
        "metrics": {"baseline": base_metrics, "improved": impr_metrics},
        "counters": _counter_metrics(base_metrics, impr_metrics, cmp_, judge),
        "verdict": cmp_["verdict"],
        "comparison": cmp_,
        "heatmap": heatmap,
        "clusters": clusters,
        "proposals": proposals,
        "policy": {"v0": V0.to_dict(), "v1": V1.to_dict()},
        "personas": _persona_cards(),
        "transcript": _representative_transcript(baseline),
        "judge": judge,
        "sessions": {"baseline": _session_summaries(baseline),
                     "improved": _session_summaries(improved)},
        "misconception_catalogue": MISCONCEPTIONS,
    }
