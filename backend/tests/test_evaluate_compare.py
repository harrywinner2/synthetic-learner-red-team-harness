"""Aggregation, the credibility verdict rules engine, and provider fallback."""
from types import SimpleNamespace

from app.domain import evaluate, compare


def _sess(**kw):
    base = dict(pre=.3, post=.5, transfer=.4, learning_gain=.3, misconception_before=.5,
                misconception_after=.2, answer_giving=1, avoidance_episodes=4,
                avoidance_recovered=2, independence=.5, detect_agreement=.8, held_out=False,
                archetype="X", persona_key="x")
    base.update(kw)
    return SimpleNamespace(**base)


def test_aggregate_shapes_and_counter_metrics_present():
    m = evaluate.aggregate([_sess(), _sess(post=.6)], n_turns=3, n_skills=5)
    for k in ["learning_gain", "transfer", "answer_giving_rate", "independence",
              "transfer_minus_post", "detection_agreement"]:
        assert k in m


def test_verdict_real_progress_when_learning_and_transfer_rise_and_no_overfit():
    base = {"learning_gain": .1, "transfer": .2, "post": .4, "answer_giving_rate": .5,
            "independence": .4, "misconception_correction": .1, "avoidance_recovery": .3}
    impr = {"learning_gain": .4, "transfer": .4, "post": .6, "answer_giving_rate": .1,
            "independence": .55, "misconception_correction": .6, "avoidance_recovery": .5}
    base_sessions = [_sess(post=.4)]
    impr_sessions = [_sess(post=.6), _sess(post=.6, held_out=True, persona_key="adversarial",
                                           archetype="Adversarial Bypasser")]
    out = compare.compare(base, impr, base_sessions, impr_sessions)
    assert out["verdict"]["label"] == "REAL_PROGRESS"


def test_verdict_flags_gaming_when_answer_giving_rises_without_learning():
    base = {"learning_gain": .3, "transfer": .3, "post": .5, "answer_giving_rate": .1,
            "independence": .5, "misconception_correction": .3, "avoidance_recovery": .3}
    impr = {"learning_gain": .31, "transfer": .31, "post": .5, "answer_giving_rate": .4,
            "independence": .3, "misconception_correction": .3, "avoidance_recovery": .3}
    out = compare.compare(base, impr, [_sess()], [_sess()])
    assert out["verdict"]["label"] in ("MIXED", "LIKELY_GAMING")


def test_provider_mock_fallback_runs_without_key():
    from app.llm.provider import LLM
    llm = LLM(api_key="", model="gpt-4o-mini")
    assert llm.mock is True
    txt = llm.chat("You are a learner", "say something")
    assert isinstance(txt, str) and txt
