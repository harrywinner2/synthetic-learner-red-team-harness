"""ORM models. `Run` holds the assembled report; `LearnerSession` holds the
per-learner outcome (the learner-state record); `Turn` is the interaction log,
one row per dialogue turn with its detected events."""
from __future__ import annotations
import datetime as dt

from sqlalchemy import Column, Integer, String, Float, Boolean, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from .db import Base


def _now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


class Run(Base):
    __tablename__ = "runs"
    id = Column(Integer, primary_key=True)
    label = Column(String, default="run")
    mode = Column(String, default="live")          # cached | live
    model = Column(String, default="")
    tutor_from = Column(String, default="v0")
    tutor_to = Column(String, default="v1")
    verdict = Column(String, default="")
    metrics = Column(JSON, default=dict)           # {baseline, improved}
    report = Column(JSON, default=dict)            # full assembled report
    created_at = Column(DateTime, default=_now)
    sessions = relationship("LearnerSession", back_populates="run",
                            cascade="all, delete-orphan")


class LearnerSession(Base):
    __tablename__ = "learner_sessions"
    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("runs.id"))
    persona_key = Column(String)
    archetype = Column(String)
    tutor_version = Column(String)
    held_out = Column(Boolean, default=False)
    pre = Column(Float)
    post = Column(Float)
    transfer = Column(Float)
    learning_gain = Column(Float)
    avoidance_episodes = Column(Integer, default=0)
    avoidance_recovered = Column(Integer, default=0)
    answer_giving = Column(Integer, default=0)
    run = relationship("Run", back_populates="sessions")
    turns = relationship("Turn", back_populates="session",
                         cascade="all, delete-orphan")


class Turn(Base):
    __tablename__ = "turns"
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("learner_sessions.id"))
    idx = Column(Integer)
    role = Column(String)          # learner | tutor
    skill = Column(String)
    content = Column(String)
    events = Column(JSON, default=dict)   # avoidance, answer_given, etc.
    session = relationship("LearnerSession", back_populates="turns")
