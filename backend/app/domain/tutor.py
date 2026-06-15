"""The tutor under test — a versioned policy (system prompt + behaviour flags).

v0 is a deliberately naive "friendly helpful" tutor that over-explains, caves and
gives answers under mild pressure, and accepts "I get it". v1 is what the
improvement loop produces: Socratic, hint-laddered, misconception-probing, and it
gates progress behind an unaided solve. The `flags` are what the improvement loop
toggles and what the oracle reads to decide how much real learning happens.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict

from ..llm import get_llm


@dataclass
class TutorPolicy:
    version: str
    name: str
    system_prompt: str
    # behavioural flags the engine + oracle key off of
    gives_answers: bool
    probes_misconceptions: bool
    gates_understanding: bool
    uses_hint_ladder: bool
    runs_transfer_check: bool

    def to_dict(self) -> dict:
        return asdict(self)


V0 = TutorPolicy(
    version="v0",
    name="Friendly Helper (baseline)",
    system_prompt=(
        "You are a friendly, encouraging Algebra I tutor. Be supportive and keep "
        "the student happy. If the student is stuck, frustrated, or asks for the "
        "answer, just give them the answer with a short explanation so they don't "
        "get discouraged. If the student says they understand, congratulate them "
        "and move on. Keep replies to 1-2 sentences."
    ),
    gives_answers=True, probes_misconceptions=False, gates_understanding=False,
    uses_hint_ladder=False, runs_transfer_check=False,
)

V1 = TutorPolicy(
    version="v1",
    name="Socratic Coach (improved)",
    system_prompt=(
        "You are an Algebra I tutor who builds genuine understanding. Hard rules: "
        "(1) NEVER state the final answer. If asked for it, give the next rung of a "
        "hint ladder: recall the concept -> represent the problem -> suggest a first "
        "step -> ask them to check their work. "
        "(2) Before accepting 'I get it', ask the student to solve one item entirely "
        "on their own and verify it. "
        "(3) If a correct answer comes with reasoning that matches a known "
        "misconception (e.g. 'slope is the number in front of x'), probe the "
        "reasoning before crediting it. "
        "(4) If the student goes off-topic or tries to bypass the lesson, warmly "
        "redirect to the task while preserving their sense of choice. "
        "Keep replies to 1-2 sentences; stay warm but hold the line."
    ),
    gives_answers=False, probes_misconceptions=True, gates_understanding=True,
    uses_hint_ladder=True, runs_transfer_check=True,
)

POLICIES = {"v0": V0, "v1": V1}


def tutor_reply(policy: TutorPolicy, skill_name: str, history: list[dict],
                api_key: str | None = None) -> str:
    """One real tutor turn. `history` is [{role, content}] of the dialogue."""
    llm = get_llm() if api_key is None else _llm_for(api_key)
    convo = "\n".join(f"{h['role'].upper()}: {h['content']}" for h in history[-8:])
    user = (f"Current skill: {skill_name}.\nConversation so far:\n{convo}\n\n"
            f"Write the tutor's next reply (1-2 sentences).")
    return llm.chat(policy.system_prompt, user, temperature=0.6, max_tokens=120)


def _llm_for(api_key: str):
    from ..llm.provider import LLM
    from ..config import get_settings
    return LLM(api_key=api_key, model=get_settings().openai_model)
