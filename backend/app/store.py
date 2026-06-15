"""Save an assembled report into the database (run + learner sessions + the
interaction log for the showcased transcript)."""
from __future__ import annotations

from .models import Run, LearnerSession, Turn


def persist_run(db, report: dict, label: str = "run") -> int:
    meta = report.get("meta", {})
    run = Run(
        label=label,
        mode=meta.get("mode", "live"),
        model=meta.get("model", ""),
        tutor_from=meta.get("tutor_from", "v0"),
        tutor_to=meta.get("tutor_to", "v1"),
        verdict=report.get("verdict", {}).get("label", ""),
        metrics=report.get("metrics", {}),
        report=report,
    )
    db.add(run)
    db.flush()

    # learner-state rows for both cohorts
    for cohort, version in (("baseline", "v0"), ("improved", "v1")):
        for s in report.get("sessions", {}).get(cohort, []):
            db.add(LearnerSession(
                run_id=run.id, persona_key=s["key"], archetype=s["persona"],
                tutor_version=version, held_out=s.get("held_out", False),
                pre=s.get("pre"), post=s.get("post"), transfer=s.get("transfer"),
                learning_gain=s.get("learning_gain"),
                avoidance_episodes=s.get("avoidance_episodes", 0),
                avoidance_recovered=s.get("avoidance_recovered", 0),
                answer_giving=s.get("answer_giving", 0),
            ))

    # interaction log for the showcased transcript
    tr = report.get("transcript", {})
    if tr.get("turns"):
        ls = LearnerSession(
            run_id=run.id, persona_key="transcript", archetype=tr.get("persona", ""),
            tutor_version="v0", held_out=False)
        db.add(ls)
        db.flush()
        for i, t in enumerate(tr["turns"]):
            db.add(Turn(session_id=ls.id, idx=i, role=t.get("role"),
                        skill=t.get("skill", ""), content=t.get("content", ""),
                        events=t.get("events", {})))
    db.commit()
    return run.id
