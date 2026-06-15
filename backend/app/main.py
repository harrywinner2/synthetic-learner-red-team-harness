"""FastAPI entrypoint. Serves the JSON API and the static single-page frontend
from one service (one Railway deploy, one URL)."""
from __future__ import annotations
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .api.routes import router as api_router
from .db import init_db

app = FastAPI(title="Synthetic Learner Red Team Harness",
              description="Stress-test and recursively improve an AI tutor with synthetic learners.",
              version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(api_router)

# create tables at import so the DB is ready under any launcher (uvicorn, gunicorn,
# TestClient without a lifespan context). Idempotent.
init_db()

FRONTEND = Path(__file__).resolve().parents[2] / "frontend"


@app.on_event("startup")
def _startup():
    init_db()


@app.get("/")
def index():
    return FileResponse(FRONTEND / "index.html")


# static assets (the SPA is a single index.html, but keep this for any extras)
if FRONTEND.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND)), name="static")
