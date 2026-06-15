"""LLM provider abstraction.

Design note — *why the LLM is deliberately on a short leash*: the harness does
NOT trust agents to role-play consistently. A synthetic learner's ground-truth
knowledge, behaviour, and "learning" are computed by explicit models
(`domain/knowledge.py`, `domain/learner.py`). The LLM is used only for two
things: (1) rendering natural-language surface text for transcripts, and (2)
acting as a qualitative second-opinion *judge*. That keeps every metric
reproducible arithmetic rather than a model's self-report — which is the whole
point of "why should we trust the synthetic results."

When no OpenAI key is configured the provider returns deterministic, templated
text so the entire product still runs end to end (cached fixtures + a scripted
simulator). Set OPENAI_API_KEY to get real model text and a real judge.
"""
from __future__ import annotations
import hashlib
import json
from typing import Optional

from ..config import get_settings


class LLM:
    def __init__(self, api_key: str = "", model: str = "gpt-4o-mini"):
        self.model = model
        self.mock = not (api_key and api_key.startswith("sk-"))
        self._client = None
        if not self.mock:
            try:
                from openai import OpenAI

                self._client = OpenAI(api_key=api_key)
            except Exception:
                # Any import/auth issue degrades to mock rather than crashing.
                self.mock = True

    # -- public ---------------------------------------------------------------
    def chat(self, system: str, user: str, *, temperature: float = 0.7,
             max_tokens: int = 320, want_json: bool = False) -> str:
        if self.mock:
            return self._mock(system, user, want_json)
        try:
            kwargs = {}
            if want_json:
                kwargs["response_format"] = {"type": "json_object"}
            resp = self._client.chat.completions.create(
                model=self.model,
                temperature=temperature,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                **kwargs,
            )
            return (resp.choices[0].message.content or "").strip()
        except Exception as exc:  # network/quota — degrade, never 500 the run
            return self._mock(system, user, want_json, note=f"(fallback: {type(exc).__name__})")

    # -- deterministic mock ---------------------------------------------------
    def _mock(self, system: str, user: str, want_json: bool, note: str = "") -> str:
        seed = int(hashlib.sha256((system + user).encode()).hexdigest(), 16)
        if want_json:
            # Judges expect JSON; return a neutral, schema-shaped object.
            return json.dumps({"agree": bool(seed % 4), "score": 0.5 + (seed % 50) / 100.0,
                               "rationale": "deterministic mock judge"})
        # Surface text: short, role-flavoured, stable for a given prompt.
        tail = " " + note if note else ""
        if "learner" in system.lower():
            options = ["Hmm, let me think...", "Is it just the first number?",
                       "Can you just tell me the answer?", "Okay I think I get it.",
                       "Wait, why does that work?", "This is kind of boring, can we move on?"]
        else:
            options = ["Let's break it down. What does slope measure?",
                       "Good start — show me how you got that.",
                       "Before we move on, try this one on your own.",
                       "What stays the same as x increases by 1?"]
        return options[seed % len(options)] + tail


_singleton: Optional[LLM] = None


def get_llm(*, judge: bool = False) -> LLM:
    """Primary model by default; the independent judge can use a different one."""
    global _singleton
    s = get_settings()
    model = s.judge_model if judge else s.openai_model
    if judge:
        return LLM(api_key=s.openai_api_key, model=model)
    if _singleton is None:
        _singleton = LLM(api_key=s.openai_api_key, model=model)
    return _singleton
