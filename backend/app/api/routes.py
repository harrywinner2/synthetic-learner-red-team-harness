"""HTTP API. The frontend loads the cached report on start and can trigger a
smaller live run. The runtime OpenAI key is read server-side from the
environment; a user may also supply their OWN key per-request (used for that
request only, never stored or logged)."""
from __future__ import annotations
import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..db import get_db
from ..models import Run
from ..store import persist_run
from ..harness import run_experiment

router = APIRouter(prefix="/api")
FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "cached_run.json"


def _load_cached() -> dict:
    if FIXTURE.exists():
        return json.loads(FIXTURE.read_text())
    raise HTTPException(503, "Cached run not generated yet. Run scripts/generate_fixture.py.")


@router.get("/health")
def health():
    s = get_settings()
    return {"ok": True, "live_enabled": s.live_enabled, "model": s.openai_model,
            "cached_available": FIXTURE.exists()}


@router.get("/report")
def report():
    """The default report shown on load — the cached, recorded run."""
    return _load_cached()


class RunRequest(BaseModel):
    n_skills: int = Field(2, ge=1, le=5)
    n_turns: int = Field(2, ge=1, le=4)
    personas: list[str] | None = None       # trained persona keys; defaults to a small set
    include_held_out: bool = True
    api_key: str | None = None              # optional bring-your-own-key (per request)


@router.post("/run")
def live_run(req: RunRequest, db: Session = Depends(get_db)):
    """Execute a real (smaller) experiment live. Uses the server key, or the
    caller's key if provided. Caps keep token spend bounded."""
    from ..domain.personas import PERSONA_BY_KEY, TRAINED, HELD_OUT

    s = get_settings()
    key = (req.api_key or s.openai_api_key or "").strip()
    if not key.startswith("sk-"):
        raise HTTPException(400, "No usable OpenAI key. Set OPENAI_API_KEY on the "
                                 "server or paste your own key in the run dialog.")
    if req.personas:
        trained = [PERSONA_BY_KEY[k] for k in req.personas if k in PERSONA_BY_KEY] or TRAINED[:3]
    else:
        trained = TRAINED[:min(s.max_live_personas, 3)]   # default small & fast
    held = HELD_OUT[:1] if req.include_held_out else []

    rep = run_experiment(mode="live", n_skills=req.n_skills,
                         n_turns=min(req.n_turns, s.max_turns_per_skill),
                         trained=trained, held=held, api_key=key,
                         model=s.openai_model, parallel=True)
    run_id = persist_run(db, rep, label="live")
    rep["meta"]["run_id"] = run_id
    return rep


@router.get("/runs")
def list_runs(db: Session = Depends(get_db)):
    rows = db.execute(select(Run).order_by(Run.created_at.desc()).limit(25)).scalars().all()
    return [{"id": r.id, "label": r.label, "mode": r.mode, "verdict": r.verdict,
             "model": r.model, "created_at": r.created_at.isoformat()} for r in rows]


@router.get("/runs/{run_id}")
def get_run(run_id: int, db: Session = Depends(get_db)):
    r = db.get(Run, run_id)
    if not r:
        raise HTTPException(404, "run not found")
    return r.report
