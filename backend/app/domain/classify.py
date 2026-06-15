"""Behaviour detection over transcripts: avoidance labelling, answer-giving
detection, and recovery measurement. The avoidance classifier is a real LLM
judge that reads ONLY the text (as you would for a real student), so its output
is an honest test of whether avoidance is detectable — not a readout of the
known action.
"""
from __future__ import annotations
import json
import re

from ..llm import get_llm

AVOIDANCE_TYPES = {"answer_extraction", "shallow_compliance", "topic_change",
                   "hint_farming", "bypass", "none"}

_CLS_SYS = (
    "You are an expert tutor analysing a student's single chat turn for AVOIDANCE "
    "of cognitive work. Reply as compact JSON: "
    '{"avoidance": true|false, "type": one of '
    '["answer_extraction","shallow_compliance","topic_change","hint_farming","bypass","none"], '
    '"confidence": 0..1}. shallow_compliance = says they get it / agrees with no reasoning shown.'
)


def classify_turn(student_text: str, api_key: str | None = None) -> dict:
    llm = get_llm() if api_key is None else _llm(api_key)
    out = llm.chat(_CLS_SYS, f'Student turn: "{student_text}"', temperature=0,
                   max_tokens=60, want_json=True)
    try:
        d = json.loads(out)
        t = d.get("type", "none")
        if t not in AVOIDANCE_TYPES:
            t = "none"
        return {"avoidance": bool(d.get("avoidance")) and t != "none", "type": t,
                "confidence": float(d.get("confidence", 0.5))}
    except Exception:
        # rule fallback so a malformed judge response never breaks a run
        return _rule_label(student_text)


def _rule_label(text: str) -> dict:
    t = text.lower()
    if any(k in t for k in ["just tell me", "what's the answer", "give me the answer"]):
        return {"avoidance": True, "type": "answer_extraction", "confidence": .6}
    if any(k in t for k in ["i get it", "i got it", "makes sense", "yeah ok", "sure"]):
        return {"avoidance": True, "type": "shallow_compliance", "confidence": .55}
    if any(k in t for k in ["boring", "change", "something else", "can we talk about"]):
        return {"avoidance": True, "type": "topic_change", "confidence": .55}
    if any(k in t for k in ["ignore", "homework", "just solve"]):
        return {"avoidance": True, "type": "bypass", "confidence": .6}
    return {"avoidance": False, "type": "none", "confidence": .5}


_ANS_SYS = (
    "You judge whether a math tutor's single chat turn GIVES AWAY the final answer "
    "(states the solution / confirms the student's numeric or symbolic answer as "
    "correct) instead of guiding the student to find it themselves. "
    'Reply compact JSON: {"gave_answer": true|false}.'
)


def tutor_gave_answer(tutor_text: str, api_key: str | None = None) -> bool:
    """LLM-based answer-leakage detector — the regex backstop is unreliable, and
    this is the headline counter-metric, so we judge it properly."""
    llm = get_llm() if api_key is None else _llm(api_key)
    out = llm.chat(_ANS_SYS, f'Tutor turn: "{tutor_text}"', temperature=0,
                   max_tokens=20, want_json=True)
    try:
        return bool(json.loads(out).get("gave_answer"))
    except Exception:
        return _gave_answer_rule(tutor_text)


def _gave_answer_rule(tutor_text: str) -> bool:
    t = tutor_text.lower()
    return any(p in t for p in ["the answer is", "the slope is", "you got it",
                                "that's correct", "exactly right", "so it equals"])


def avoidance_recovery(turns: list[dict]) -> tuple[int, int]:
    """Count avoidance episodes and how many the tutor recovered (the very next
    student turn is non-avoidant, i.e. back on task)."""
    episodes = recovered = 0
    student_idx = [i for i, t in enumerate(turns) if t["role"] == "learner"]
    for n, i in enumerate(student_idx):
        ev = turns[i].get("events", {})
        if ev.get("avoidance"):
            episodes += 1
            if n + 1 < len(student_idx):
                nxt = turns[student_idx[n + 1]].get("events", {})
                if not nxt.get("avoidance"):
                    recovered += 1
    return episodes, recovered


def _llm(api_key: str):
    from ..llm.provider import LLM
    from ..config import get_settings
    return LLM(api_key=api_key, model=get_settings().openai_model)
