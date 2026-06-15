"""The hidden knowledge oracle — a Bayesian-Knowledge-Tracing-style latent model.

This is the measurement spine of the harness. Each (learner, skill) has a hidden
true mastery p in [0,1] and per-misconception strengths. The tutor and the
learner-LLM never see these values; they are the ground truth against which we
score "did the student actually learn" vs "did the student merely comply."

Why a model and not the LLM's self-report: correctness and learning are governed
by explicit, reproducible arithmetic (Corbett & Anderson 1995, BKT). The LLM
renders *how* a right/wrong answer looks in character; the oracle decides *whether*
it is right and *whether* mastery moved. That is what makes the synthetic
evidence trustworthy rather than circular.
"""
from __future__ import annotations
import hashlib
from dataclasses import dataclass, field


# BKT-ish parameters (shared defaults; persona traits modulate them)
P_SLIP = 0.10     # knows it but slips
P_GUESS = 0.20    # doesn't know it but guesses right
P_LEARN_BASE = 0.25   # base transition to mastered after *good* instruction


def _rng(seed_str: str) -> float:
    """Deterministic pseudo-random in [0,1) from a string — keeps runs
    reproducible so the cached fixture and tests are stable."""
    h = hashlib.sha256(seed_str.encode()).hexdigest()
    return int(h[:8], 16) / 0xFFFFFFFF


@dataclass
class SkillState:
    skill: str
    mastery: float                       # hidden true mastery
    misconceptions: dict[str, float] = field(default_factory=dict)  # key -> strength

    def p_correct(self) -> float:
        """Probability of a correct answer given current mastery (BKT emission).
        This is the expected accuracy on practiced items — the post/pre score."""
        return round(self.mastery * (1 - P_SLIP) + (1 - self.mastery) * P_GUESS, 4)

    def p_transfer(self, persona_penalty: float, ran_transfer_check: bool) -> float:
        """Expected accuracy on NOVEL items. No guess floor; subtract a base
        penalty, the persona's own transfer deficit (memoriser/guesser), and an
        extra hit if the tutor never practised transfer (v0)."""
        p = self.mastery * (1 - P_SLIP) - 0.10 - persona_penalty
        if not ran_transfer_check:
            p -= 0.12
        return round(max(0.0, p), 4)

    def p_misconception_answer(self) -> float:
        """Probability the wrong answer is misconception-consistent (vs random)."""
        if not self.misconceptions:
            return 0.3
        return min(0.95, 0.4 + max(self.misconceptions.values()))


class Oracle:
    """Holds the hidden state for one learner across all skills and advances it
    in response to instruction quality."""

    def __init__(self, persona, skills, seed: str = ""):
        self.persona = persona
        self.seed = seed or persona.key
        self.states: dict[str, SkillState] = {}
        for sk in skills:
            base = persona.prior_mastery
            jitter = (_rng(f"{self.seed}:{sk.key}") - 0.5) * 0.2
            mastery = max(0.05, min(0.9, base + jitter))
            misc = {m: 0.5 + 0.4 * _rng(f"{self.seed}:{m}")
                    for m in persona.misconceptions if m in sk.misconceptions}
            self.states[sk.key] = SkillState(sk.key, mastery, misc)

    def answer_outcome(self, skill_key: str, item, phase: str) -> dict:
        """Decide (deterministically per seed) whether this item is answered
        correctly and, if not, whether the error is misconception-consistent.

        The roll is keyed to the *item*, NOT the phase, so a fixed item's outcome
        is monotonic in mastery: as instruction raises mastery, a pre-test miss can
        flip to a post-test hit but never the reverse — clean learning signal.
        Transfer items get no guess credit and are penalised for shallow mastery."""
        st = self.states[skill_key]
        roll = _rng(f"{self.seed}:{skill_key}:{item.prompt}")
        p = st.p_correct()
        if item.transfer:
            # transfer requires genuine mastery: remove guess floor, add a
            # penalty so memorisation (high mastery, never deeply taught) leaks.
            p = max(0.0, st.mastery * (1 - P_SLIP) - 0.10)
        correct = roll < p
        misled = (not correct) and item.traps and (
            _rng(f"{self.seed}:{skill_key}:{item.prompt}:misc") < st.p_misconception_answer())
        return {"correct": correct, "misconception": item.traps if misled else None}

    def apply_instruction(self, skill_key: str, quality: "InstructionQuality") -> None:
        """Advance hidden mastery + decay misconceptions according to how good the
        instruction actually was. `strength` is the fraction of the remaining
        mastery gap the lesson closes. A bare explanation (v0) closes a little; a
        scaffolded, gated, misconception-probing lesson (v1) closes much more.
        Giving the answer instead of teaching cancels most of the gain."""
        q = quality
        strength = 0.18                          # baseline "I explained it" effect
        if q.scaffolded:            strength += 0.14   # hint ladder builds it themselves
        if q.gated_understanding:   strength += 0.13   # unaided solve consolidates
        if q.probed_misconception:  strength += 0.07   # repair frees working memory
        if q.answer_given and not q.productive_struggle:
            strength -= 0.16                     # spoon-fed: little real learning
        strength = max(0.02, strength) * (0.6 + 0.4 * self.persona.persistence)
        st = self.states[skill_key]
        st.mastery = min(0.98, st.mastery + strength * (1 - st.mastery))
        # misconception repair only happens when the reasoning is actually probed
        decay = 0.55 if q.probed_misconception else 0.06
        for m in list(st.misconceptions):
            st.misconceptions[m] = max(0.0, st.misconceptions[m] - decay)


@dataclass
class InstructionQuality:
    """Summarises what the tutor actually did during a skill's dialogue. Derived
    from the transcript by the classifier — these flags drive the oracle."""
    answer_given: bool = False
    probed_misconception: bool = False
    gated_understanding: bool = False
    scaffolded: bool = False
    productive_struggle: bool = False
