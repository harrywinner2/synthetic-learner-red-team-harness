"""Failure analysis: build the persona x skill failure heatmap from a baseline
run, rank the worst clusters, and ask an LLM Diagnostician to propose targeted,
minimal tutor-policy changes. The proposals are advisory — a human approves them
(the loop is human-in-the-loop by default).
"""
from __future__ import annotations
import json

from ..llm import get_llm
from .skills import SKILLS


def build_heatmap(sessions: list) -> dict:
    """{persona_key: {skill_key: intensity}} plus skill/persona labels."""
    grid = {}
    for s in sessions:
        grid[s.persona_key] = {sk: d["intensity"] for sk, d in s.skill_detail.items()}
    return {
        "skills": [{"key": sk.key, "name": sk.name} for sk in SKILLS],
        "personas": [{"key": s.persona_key, "name": s.archetype,
                      "held_out": s.held_out} for s in sessions],
        "grid": grid,
    }


def top_clusters(sessions: list, k: int = 5) -> list[dict]:
    """Aggregate intensity by skill across personas; surface the worst."""
    agg: dict[str, list[float]] = {}
    for s in sessions:
        for sk, d in s.skill_detail.items():
            agg.setdefault(sk, []).append(d["intensity"])
    skill_name = {sk.key: sk.name for sk in SKILLS}
    rows = []
    for sk, vals in agg.items():
        hit = sum(1 for v in vals if v >= 0.5)
        rows.append({"skill": skill_name.get(sk, sk),
                     "intensity": round(sum(vals) / len(vals), 3),
                     "affected": hit, "total": len(vals)})
    rows.sort(key=lambda r: (r["intensity"], r["affected"]), reverse=True)
    return rows[:k]


_DIAG_SYS = (
    "You are an instructional designer improving an AI tutor. You are given the "
    "tutor's current weaknesses from a red-team run. Propose 3-4 SPECIFIC, minimal "
    "changes to the tutor's policy (system prompt / hint strategy / assessment). "
    "Reply as compact JSON: {\"proposals\":[{\"priority\":\"P0|P1\",\"title\":\"...\","
    "\"rationale\":\"<=30 words\"}]}. Favour: never giving the answer, probing "
    "misconceptions, gating 'I get it' behind an unaided solve, transfer checks."
)


def propose_changes(clusters: list[dict], agg_metrics: dict,
                    api_key: str | None = None) -> list[dict]:
    llm = get_llm() if api_key is None else _llm(api_key)
    summary = (f"Answer-giving rate {agg_metrics.get('answer_giving_rate')}, "
               f"transfer {agg_metrics.get('transfer')}, misconception correction "
               f"{agg_metrics.get('misconception_correction')}, avoidance recovery "
               f"{agg_metrics.get('avoidance_recovery')}. Worst skills: "
               + ", ".join(f"{c['skill']} ({c['affected']}/{c['total']})" for c in clusters[:3]))
    out = llm.chat(_DIAG_SYS, summary, temperature=0.4, max_tokens=320, want_json=True)
    try:
        d = json.loads(out)
        props = d.get("proposals", [])
        if props:
            return props[:4]
    except Exception:
        pass
    # deterministic fallback proposals (still real, just not model-authored)
    return [
        {"priority": "P0", "title": "Replace answer-fallback with a hint ladder",
         "rationale": "Stop surrendering the answer under pressure; give graded hints instead."},
        {"priority": "P0", "title": "Gate 'I get it' behind an unaided solve",
         "rationale": "Require one independently solved item before advancing past a skill."},
        {"priority": "P1", "title": "Add misconception probes (M1, M2)",
         "rationale": "Probe reasoning when a right answer matches a known misconception."},
        {"priority": "P1", "title": "Mandatory transfer item per skill",
         "rationale": "End each skill with a novel-framing check that counts toward mastery."},
    ]


def _llm(api_key: str):
    from ..llm.provider import LLM
    from ..config import get_settings
    return LLM(api_key=api_key, model=get_settings().openai_model)
