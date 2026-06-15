"""Before/after comparison, regression check, and the credibility verdict — the
part that separates real educational progress from a prettier benchmark.
"""
from __future__ import annotations


def _delta(a: float, b: float) -> float:
    return round(b - a, 3)


def subgroup_recovery(sessions: list, held: bool) -> float:
    grp = [s for s in sessions if s.held_out == held]
    ep = sum(s.avoidance_episodes for s in grp)
    rec = sum(s.avoidance_recovered for s in grp)
    return round(rec / max(1, ep), 3)


def subgroup_mean(sessions: list, held: bool, attr: str) -> float:
    grp = [getattr(s, attr) for s in sessions if s.held_out == held]
    return round(sum(grp) / max(1, len(grp)), 3)


def compare(base_metrics: dict, impr_metrics: dict,
            base_sessions: list, impr_sessions: list) -> dict:
    """Headline deltas, per-subgroup before/after, regression flags, verdict."""
    keys = ["learning_gain", "transfer", "misconception_correction",
            "avoidance_recovery", "answer_giving_rate", "independence", "post"]
    deltas = {k: _delta(base_metrics.get(k, 0), impr_metrics.get(k, 0)) for k in keys}

    # OVERFIT is measured on the core LEARNING signal (trained vs held-out under v1),
    # NOT on avoidance recovery — otherwise the by-design Adversarial Bypasser, which
    # is *supposed* to resist, would masquerade as overfitting. Its stubbornness is
    # reported separately below as a robustness regression.
    trained_lg = subgroup_mean(impr_sessions, False, "learning_gain")
    held_lg = subgroup_mean(impr_sessions, True, "learning_gain")
    overfit_gap = round(trained_lg - held_lg, 3)
    trained_rec = subgroup_recovery(impr_sessions, held=False)
    held_rec = subgroup_recovery(impr_sessions, held=True)

    # regression check: any persona whose post-test got worse v0->v1
    base_post = {s.persona_key: s.post for s in base_sessions}
    regressions = []
    for s in impr_sessions:
        if s.persona_key in base_post and s.post < base_post[s.persona_key] - 0.05:
            regressions.append({
                "persona": s.archetype,
                "detail": f"post {base_post[s.persona_key]:.2f} -> {s.post:.2f}",
                "ok": False,
                "note": "Post-test regressed for this learner.",
            })
    # the adversarial held-out persona is the known stress point
    adv = next((s for s in impr_sessions if s.persona_key == "adversarial"), None)
    if adv:
        regressions.append({
            "persona": "Adversarial Bypasser", "ok": adv.avoidance_recovered >= adv.avoidance_episodes * 0.5,
            "detail": f"recovered {adv.avoidance_recovered}/{adv.avoidance_episodes} avoidance episodes",
            "note": "Held-out jailbreak persona — the hardest robustness case.",
        })

    verdict = _verdict(deltas, overfit_gap, impr_metrics)
    return {
        "deltas": deltas,
        "subgroups": {
            "trained_learning": trained_lg,
            "held_out_learning": held_lg,
            "trained_recovery": trained_rec,
            "held_out_recovery": held_rec,
            "overfit_gap": overfit_gap,
        },
        "regressions": regressions,
        "verdict": verdict,
    }


def _verdict(deltas: dict, overfit_gap: float, impr: dict) -> dict:
    """Rules engine: real progress requires that learning AND transfer rose, the
    answer-giving counter-metric did NOT worsen, and overfit is modest."""
    reasons = []
    learning_up = deltas["learning_gain"] > 0.03 and deltas["post"] > 0.03
    transfer_up = deltas["transfer"] > 0.02
    not_just_withholding = deltas["answer_giving_rate"] <= 0 and deltas["learning_gain"] > 0
    independence_ok = deltas["independence"] >= -0.02
    modest_overfit = overfit_gap <= 0.15

    if learning_up and transfer_up:
        reasons.append("Learning and transfer both rose — not teaching-to-the-test.")
    if not_just_withholding:
        reasons.append("Answer-giving fell while learning rose — genuinely stopped giving answers.")
    if independence_ok:
        reasons.append("Independence held or improved — no scaffolding dependence.")
    if not modest_overfit:
        reasons.append(f"WARNING: held-out gain lags trained by {overfit_gap} — overfit risk.")
    elif overfit_gap > 0.05:
        reasons.append(f"Mild overfit: held-out gain lags trained by {overfit_gap} (disclosed).")

    if learning_up and transfer_up and not_just_withholding and modest_overfit:
        label = "REAL_PROGRESS"
    elif learning_up and transfer_up:
        label = "MIXED"
    else:
        label = "LIKELY_GAMING"
    return {"label": label, "reasons": reasons}
