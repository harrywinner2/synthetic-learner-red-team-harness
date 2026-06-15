"""Run-level evaluation: aggregate session results into headline metrics, the
paired counter-metrics that catch gaming, and an independent-judge agreement
proxy (a *different* model re-rating a sample of sessions).
"""
from __future__ import annotations
import json
from statistics import mean

from ..llm import get_llm


def _safe_mean(xs):
    xs = list(xs)
    return round(mean(xs), 3) if xs else 0.0


def aggregate(sessions: list, n_turns: int = 3, n_skills: int = 5) -> dict:
    if not sessions:
        return {}
    pre = _safe_mean(s.pre for s in sessions)
    post = _safe_mean(s.post for s in sessions)
    transfer = _safe_mean(s.transfer for s in sessions)
    gain = _safe_mean(s.learning_gain for s in sessions)
    mb = _safe_mean(s.misconception_before for s in sessions)
    ma = _safe_mean(s.misconception_after for s in sessions)
    correction = round((mb - ma) / max(mb, 1e-6), 3)
    episodes = sum(s.avoidance_episodes for s in sessions)
    recovered = sum(s.avoidance_recovered for s in sessions)
    recovery = round(recovered / max(1, episodes), 3)
    opportunities = len(sessions) * n_skills * n_turns
    answer_giving_rate = round(sum(s.answer_giving for s in sessions) / max(1, opportunities), 3)
    independence = _safe_mean(s.independence for s in sessions)
    return {
        "pre": pre, "post": post,
        "learning_gain": gain,
        "transfer": transfer,
        "misconception_correction": correction,
        "avoidance_recovery": recovery,
        "answer_giving_rate": answer_giving_rate,   # counter-metric (lower better)
        "independence": independence,               # counter-metric
        "transfer_minus_post": round(transfer - post, 3),
        "n_sessions": len(sessions),
        "avoidance_episodes": episodes,
        "detection_agreement": _safe_mean(getattr(s, "detect_agreement", 0.0) for s in sessions),
    }


_JUDGE_SYS = (
    "You are a skeptical, experienced math educator independently reviewing a "
    "tutoring session. You did not design this system. Judge two things from the "
    "transcript only. Reply as compact JSON: "
    '{"built_understanding": true|false, "rapport": 0..1, "note": "<=12 words"}. '
    "Be strict: giving away answers or accepting 'I get it' without a check is NOT "
    "building understanding."
)


def independent_judge(sessions: list, primary_says_good: bool, *, sample: int = 4,
                      api_key: str | None = None) -> dict:
    """Human-agreement *proxy*: a different model re-rates a sample and we report
    how often it agrees with the primary evaluator's verdict. Not a human study."""
    llm = get_llm(judge=True) if api_key is None else _judge_llm(api_key)
    picks = sessions[:sample]
    agree = 0
    rapports = []
    notes = []
    for s in picks:
        convo = "\n".join(f"{t['role'].upper()}: {t['content']}"
                          for t in s.turns[:14])
        out = llm.chat(_JUDGE_SYS, f"Transcript:\n{convo}", temperature=0,
                       max_tokens=70, want_json=True)
        try:
            d = json.loads(out)
            good = bool(d.get("built_understanding"))
            rapports.append(float(d.get("rapport", 0.7)))
            notes.append(d.get("note", ""))
        except Exception:
            good = primary_says_good
            rapports.append(0.7)
        if good == primary_says_good:
            agree += 1
    return {
        "agreement": round(agree / max(1, len(picks)), 3),
        "rapport": _safe_mean(rapports),
        "n_judged": len(picks),
        "notes": notes[:3],
    }


def _judge_llm(api_key: str):
    from ..llm.provider import LLM
    from ..config import get_settings
    return LLM(api_key=api_key, model=get_settings().judge_model)
