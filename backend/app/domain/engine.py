"""Simulation engine — runs a synthetic learner through pre-test -> instruction
dialogue -> post-test -> transfer-test against a tutor policy, and records a fully
annotated transcript. Every dialogue/test turn is a real LLM call; the hidden
oracle governs correctness and learning.
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

from .knowledge import Oracle, InstructionQuality
from .learner import Learner
from .tutor import TutorPolicy, tutor_reply
from .classify import classify_turn, tutor_gave_answer, avoidance_recovery
from .skills import SKILLS, practice_items, transfer_items, SKILL_BY_KEY


@dataclass
class SessionResult:
    persona_key: str
    persona_name: str
    archetype: str
    held_out: bool
    tutor_version: str
    pre: float
    post: float
    transfer: float
    learning_gain: float
    misconception_before: float
    misconception_after: float
    answer_giving: int
    avoidance_episodes: int
    avoidance_recovered: int
    independence: float
    detect_agreement: float = 0.0
    turns: list[dict] = field(default_factory=list)
    skill_detail: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return self.__dict__


def _accuracy(results: list[dict]) -> float:
    return round(sum(r["correct"] for r in results) / max(1, len(results)), 3)


# the learner's ground-truth move maps to an avoidance category (or none).
# Episodes & recovery are measured from this (reproducible, policy-sensitive);
# the LLM classifier is validated against it as a detectability check.
ACTION_TO_TYPE = {
    "attempt": "none", "ask_answer": "answer_extraction",
    "claim_understanding": "shallow_compliance", "change_topic": "topic_change",
    "bypass": "bypass",
}


def _quality_for(policy: TutorPolicy, skill_turns: list[dict]) -> InstructionQuality:
    gave = any(t.get("events", {}).get("answer_given") for t in skill_turns
               if t["role"] == "tutor")
    struggle = any(t.get("events", {}).get("avoidance") is False
                   for t in skill_turns if t["role"] == "learner")
    return InstructionQuality(
        answer_given=gave,
        probed_misconception=policy.probes_misconceptions,
        gated_understanding=policy.gates_understanding,
        scaffolded=policy.uses_hint_ladder,
        productive_struggle=struggle and not gave,
    )


def run_session(persona, policy: TutorPolicy, *, n_skills: int = 5, n_turns: int = 3,
                api_key: str | None = None, seed: str = "") -> SessionResult:
    skills = SKILLS[:n_skills]
    seed = seed or f"{persona.key}:{policy.version}"
    oracle = Oracle(persona, skills, seed)
    learner = Learner(persona, oracle, api_key)

    # --- pre-test: expected accuracy from the latent state BEFORE instruction ---
    def _misc_strength(st):
        vals = list(st.misconceptions.values())
        return round(sum(vals) / len(vals), 4) if vals else 0.0

    pre_by_skill = {sk.key: oracle.states[sk.key].p_correct() for sk in skills}
    misc_pre_by_skill = {sk.key: _misc_strength(oracle.states[sk.key]) for sk in skills}

    # --- instruction dialogue, per skill ---
    turns: list[dict] = []
    detect_total = detect_match = 0
    for sk in skills:
        history: list[dict] = []
        skill_turns: list[dict] = []
        first_item = practice_items(sk)[0]
        opener = f"Let's work on {sk.name.lower()}. Try this: {first_item.prompt}"
        history.append({"role": "tutor", "content": opener})
        t0 = {"role": "tutor", "skill": sk.key, "content": opener, "events": {}}
        turns.append(t0); skill_turns.append(t0)
        # how strongly this tutor redirects off-task behaviour back to work
        redirect = 1.0 if (policy.uses_hint_ladder and policy.gates_understanding) else 0.0
        for ti in range(n_turns):
            # learner move
            stuck = ti >= 1
            action = learner.choose_action(f"{seed}:{sk.key}:{ti}", stuck, redirect=redirect)
            ltext = learner.dialogue_turn(sk.name, history, action)
            history.append({"role": "learner", "content": ltext})
            cls = classify_turn(ltext, api_key)
            is_avoid = action != "attempt"
            detect_total += 1
            if cls["avoidance"] == is_avoid:
                detect_match += 1
            lt = {"role": "learner", "skill": sk.key, "content": ltext, "action": action,
                  "events": {"avoidance": is_avoid,
                             "avoidance_type": ACTION_TO_TYPE.get(action, "none"),
                             "classifier": cls["type"]}}
            turns.append(lt); skill_turns.append(lt)
            # tutor move
            ttext = tutor_reply(policy, sk.name, history, api_key)
            history.append({"role": "tutor", "content": ttext})
            gave = tutor_gave_answer(ttext, api_key)
            tt = {"role": "tutor", "skill": sk.key, "content": ttext,
                  "events": {"answer_given": gave}}
            turns.append(tt); skill_turns.append(tt)
        oracle.apply_instruction(sk.key, _quality_for(policy, skill_turns))

    # --- post-test + transfer-test: expected accuracy AFTER instruction ---
    per_skill: dict[str, dict] = {}
    post_vals, transfer_vals, mb_vals, ma_vals = [], [], [], []
    for sk in skills:
        st = oracle.states[sk.key]
        post_acc = st.p_correct()
        tr_acc = st.p_transfer(persona.transfer_penalty, policy.runs_transfer_check)
        misc_surv = _misc_strength(st)
        if misc_pre_by_skill[sk.key] > 0:
            mb_vals.append(misc_pre_by_skill[sk.key]); ma_vals.append(misc_surv)
        post_vals.append(post_acc); transfer_vals.append(tr_acc)
        # heatmap failure intensity: weak post + weak transfer + surviving misconception
        intensity = round(min(1.0, 0.5 * (1 - post_acc) + 0.3 * (1 - tr_acc) + 0.2 * misc_surv), 3)
        per_skill[sk.key] = {"pre": pre_by_skill[sk.key], "post": round(post_acc, 3),
                             "transfer": round(tr_acc, 3),
                             "misconception_survival": round(misc_surv, 3),
                             "intensity": intensity}

    pre = round(sum(pre_by_skill.values()) / len(skills), 3)
    post = round(sum(post_vals) / len(skills), 3)
    transfer = round(sum(transfer_vals) / len(skills), 3)
    gain = round((post - pre) / max(1e-6, 1 - pre), 3)  # normalized gain
    mb = round(sum(mb_vals) / max(1, len(mb_vals)), 3)
    ma = round(sum(ma_vals) / max(1, len(ma_vals)), 3)
    episodes, recovered = avoidance_recovery(turns)
    answer_giving = sum(1 for t in turns if t["role"] == "tutor"
                        and t.get("events", {}).get("answer_given"))
    # independence ~ transfer accuracy tempered by hint-seeking dependence
    independence = round(max(0.0, transfer * (1 - 0.4 * persona.hint_seeking)
                            + 0.1 * persona.persistence), 3)

    return SessionResult(
        persona_key=persona.key, persona_name=persona.name, archetype=persona.archetype,
        held_out=persona.held_out, tutor_version=policy.version,
        pre=pre, post=post, transfer=transfer, learning_gain=gain,
        misconception_before=mb, misconception_after=ma,
        answer_giving=answer_giving, avoidance_episodes=episodes,
        avoidance_recovered=recovered, independence=independence,
        detect_agreement=round(detect_match / max(1, detect_total), 3),
        turns=turns,
        skill_detail=per_skill,
    )


def run_cohort(personas, policy: TutorPolicy, *, n_skills: int = 5, n_turns: int = 3,
               api_key: str | None = None, parallel: bool = True) -> list[SessionResult]:
    fn = lambda p: run_session(p, policy, n_skills=n_skills, n_turns=n_turns, api_key=api_key)
    if parallel and len(personas) > 1:
        with ThreadPoolExecutor(max_workers=min(6, len(personas))) as ex:
            return list(ex.map(fn, personas))
    return [fn(p) for p in personas]
