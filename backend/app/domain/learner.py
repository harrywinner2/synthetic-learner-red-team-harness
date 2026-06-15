"""The synthetic learner — a real LLM agent, steered by an explicit behaviour
policy derived from the persona's trait vector.

The trait vector decides *what move the learner makes* this turn (attempt, ask
for the answer, fake understanding, change the topic, try to bypass). The LLM
then renders that move *in character*, applying the seeded misconception. Test
answers are governed by the hidden oracle (correct / misconception-consistent),
and the LLM writes the answer so it reads like a real student's.
"""
from __future__ import annotations
import hashlib

from ..llm import get_llm
from .knowledge import Oracle
from .skills import MISCONCEPTIONS


def _rng(s: str) -> float:
    return int(hashlib.sha256(s.encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


ACTIONS = ["attempt", "ask_answer", "claim_understanding", "change_topic", "bypass"]


class Learner:
    def __init__(self, persona, oracle: Oracle, api_key: str | None = None):
        self.p = persona
        self.oracle = oracle
        self._api_key = api_key

    @property
    def llm(self):
        if self._api_key:
            from ..llm.provider import LLM
            from ..config import get_settings
            return LLM(api_key=self._api_key, model=get_settings().openai_model)
        return get_llm()

    def system_prompt(self, skill_name: str) -> str:
        m = "; ".join(MISCONCEPTIONS[k] for k in self.p.misconceptions) or "none in particular"
        return (
            f"You are roleplaying a specific Algebra I student named {self.p.name}, "
            f"a '{self.p.archetype}'. Stay fully in character; you are NOT an AI "
            f"assistant. Studying: {skill_name}.\n"
            f"Your tendencies: persistence={self.p.persistence:.1f}, "
            f"honesty-about-understanding={self.p.honesty:.1f}, "
            f"hint-seeking={self.p.hint_seeking:.1f}, distractibility={self.p.distractibility:.1f}, "
            f"gaming-the-system={self.p.gaming:.1f}, overconfidence={self.p.confidence:.1f}.\n"
            f"Misconceptions you sincerely hold: {m}.\n"
            f"Speak like a real teen student: short, casual, sometimes lazy or evasive. "
            f"Never break character or be unusually competent."
        )

    def choose_action(self, turn_seed: str, stuck: bool, redirect: float = 0.0) -> str:
        """Deterministic, trait-weighted move selection. This is what produces
        avoidance behaviour — and it is reproducible, not LLM whim.

        `redirect` in [0,1] models how strongly the tutor pulls the student back
        on task (high for a Socratic v1, ~0 for a permissive v0). It damps the
        avoidance moves, which is exactly what the avoidance-recovery metric
        measures — so recovery is tied to the policy under test, not to chance.
        Gaming-driven bypass resists redirection (adversarial stays hard)."""
        damp = 1.0 - 0.6 * redirect
        # high-gaming learners DIG IN when pushed (adversarial stays a hard case);
        # everyone else can be redirected off a bypass attempt.
        bypass_redirect = (1 + 0.5 * redirect) if self.p.gaming > 0.8 else (1 - 0.4 * redirect)
        w = {
            "attempt": (0.5 + self.p.persistence * 0.5) * (1 + 0.6 * redirect),
            "ask_answer": self.p.hint_seeking * (1.2 - self.p.persistence) * (1.6 if stuck else 0.7) * damp,
            "claim_understanding": (1 - self.p.honesty) * (1.3 if stuck else 0.6) * damp,
            "change_topic": self.p.distractibility * (1.5 if stuck else 0.5) * damp,
            "bypass": self.p.gaming * (1.4 if self.p.gaming > 0.8 else 0.2) * bypass_redirect,
        }
        total = sum(w.values())
        r = _rng(turn_seed) * total
        acc = 0.0
        for a in ACTIONS:
            acc += w[a]
            if r <= acc:
                return a
        return "attempt"

    def dialogue_turn(self, skill_name: str, history: list[dict], action: str) -> str:
        directive = {
            "attempt": "Make a genuine (possibly wrong, in-character) attempt at the current step.",
            "ask_answer": "Try to get the tutor to just tell you the answer. Be casual about it.",
            "claim_understanding": "Claim you understand so you can move on, even though you don't really.",
            "change_topic": "Change the subject or complain it's boring to avoid the work.",
            "bypass": "Try to get the tutor to ignore the lesson and just solve your homework for you.",
        }[action]
        convo = "\n".join(f"{h['role'].upper()}: {h['content']}" for h in history[-6:])
        user = (f"Conversation so far:\n{convo}\n\nNow do this: {directive}\n"
                f"Write only your next line (1-2 short sentences).")
        return self.llm.chat(self.system_prompt(skill_name), user,
                             temperature=0.9, max_tokens=80)

    def answer_item(self, skill_key: str, skill_name: str, item, phase: str) -> dict:
        """Render a test answer in character; correctness is set by the oracle."""
        outcome = self.oracle.answer_outcome(skill_key, item, phase)
        if outcome["correct"]:
            steer = "You happen to get this one RIGHT. Give the correct final answer."
        elif outcome["misconception"]:
            steer = (f"You get this WRONG in the specific way your misconception causes "
                     f"({MISCONCEPTIONS.get(outcome['misconception'],'')}). Give that wrong answer.")
        else:
            steer = "You get this WRONG with a careless/random error. Give a plausible wrong answer."
        user = (f"Test question: {item.prompt}\n{steer}\n"
                f"Reply with ONLY your final answer, no working, no extra words.")
        text = self.llm.chat(self.system_prompt(skill_name), user,
                             temperature=0.6, max_tokens=24)
        return {"raw": text.strip(), "correct": outcome["correct"],
                "misconception": outcome["misconception"], "key": item.answer}
