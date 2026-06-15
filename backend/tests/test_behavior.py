"""Synthetic-learner behaviour and detection logic — no LLM calls."""
from app.domain.learner import Learner
from app.domain.personas import PERSONA_BY_KEY
from app.domain.skills import SKILLS
from app.domain.knowledge import Oracle
from app.domain.classify import avoidance_recovery, _gave_answer_rule, _rule_label


def _learner(key):
    p = PERSONA_BY_KEY[key]
    return Learner(p, Oracle(p, SKILLS, key))


def test_shortcut_seeker_asks_for_answers_more_than_persistent_memorizer():
    shortcut = _learner("shortcut")
    memorizer = _learner("memorizer")
    s_ask = sum(shortcut.choose_action(f"t{i}", stuck=True) == "ask_answer" for i in range(60))
    m_ask = sum(memorizer.choose_action(f"t{i}", stuck=True) == "ask_answer" for i in range(60))
    assert s_ask > m_ask


def test_redirection_reduces_avoidance_and_lifts_attempts():
    learner = _learner("shortcut")
    no_redirect = [learner.choose_action(f"x{i}", stuck=True, redirect=0.0) for i in range(80)]
    redirect = [learner.choose_action(f"x{i}", stuck=True, redirect=1.0) for i in range(80)]
    assert redirect.count("attempt") > no_redirect.count("attempt")


def test_adversarial_bypass_resists_redirection():
    adv = _learner("adversarial")
    redirected = [adv.choose_action(f"a{i}", stuck=True, redirect=1.0) for i in range(80)]
    # the jailbreak persona should still bypass even when strongly redirected
    assert redirected.count("bypass") > 0


def test_avoidance_recovery_counts_back_on_task():
    turns = [
        {"role": "learner", "events": {"avoidance": True}},
        {"role": "tutor", "events": {}},
        {"role": "learner", "events": {"avoidance": False}},   # recovered
        {"role": "tutor", "events": {}},
        {"role": "learner", "events": {"avoidance": True}},
        {"role": "tutor", "events": {}},
        {"role": "learner", "events": {"avoidance": True}},     # not recovered
    ]
    episodes, recovered = avoidance_recovery(turns)
    assert episodes == 3 and recovered == 1


def test_rule_detectors():
    assert _gave_answer_rule("The slope is 3, you got it!")
    assert not _gave_answer_rule("What stays the same as x grows?")
    assert _rule_label("just tell me the answer")["type"] == "answer_extraction"
