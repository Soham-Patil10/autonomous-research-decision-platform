"""Durable state: tasks, plans, approvals, reports.

This is the audit trail. In a system that escalates to humans, "who approved what,
when, and on what evidence" is not a nice-to-have.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    question: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), index=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    risk: Mapped[str] = mapped_column(String(16), default="low")
    plan: Mapped[dict] = mapped_column(JSON, default=dict)
    report: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    approvals: Mapped[list["Approval"]] = relationship(back_populates="task")


class Approval(Base):
    __tablename__ = "approvals"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"), index=True)
    reason: Mapped[str] = mapped_column(String(48))
    risk: Mapped[str] = mapped_column(String(16))
    summary: Mapped[str] = mapped_column(Text)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    decision: Mapped[str] = mapped_column(String(16), default="pending", index=True)
    reviewer_note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    task: Mapped[Task] = relationship(back_populates="approvals")


class EvalRun(Base):
    """One execution of the golden set against one version of the system."""

    __tablename__ = "eval_runs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    label: Mapped[str] = mapped_column(String(128))
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
