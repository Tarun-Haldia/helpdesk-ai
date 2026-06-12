# api/models.py
# Two sections:
#   1. SQLAlchemy ORM models  (table definitions)
#   2. Pydantic schemas       (request/response shapes)

from sqlalchemy import (
    Column, Integer, String, Text,
    Boolean, DateTime, Float
)
from sqlalchemy.sql import func
from pydantic import BaseModel, Field
from typing import Optional, List
from database import Base


# ─────────────────────────────────────────────
# SECTION 1 — SQLAlchemy ORM Models (tables)
# ─────────────────────────────────────────────

class Ticket(Base):
    """
    Historical support tickets — seeded from CSV in Phase A.
    Also used for new tickets created at runtime.
    """
    __tablename__ = "tickets"

    id           = Column(Integer, primary_key=True, index=True)
    user_query   = Column(Text,    nullable=False)
    intent       = Column(String(100))
    solution     = Column(Text)
    source       = Column(String(50),  default="historical")
    created_at   = Column(DateTime,    server_default=func.now())
    is_escalated = Column(Boolean,     default=False)
    resolved     = Column(Boolean,     default=False)


class Embedding(Base):
    """
    Stores pgvector embeddings linked to each ticket.
    The actual vector column is handled via raw SQL
    (SQLAlchemy doesn't support pgvector natively without extra setup).
    """
    __tablename__ = "embeddings"

    id         = Column(Integer, primary_key=True, index=True)
    ticket_id  = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class Feedback(Base):
    """
    Stores user feedback (solved / not solved) after solution delivery.
    Used later to improve retrieval quality.
    """
    __tablename__ = "feedback"

    id               = Column(Integer, primary_key=True, index=True)
    ticket_id        = Column(Integer, nullable=True)
    user_query       = Column(Text)
    predicted_intent = Column(String(100))
    ai_solution      = Column(Text)
    is_solved        = Column(Boolean)
    created_at       = Column(DateTime, server_default=func.now())


class SupportTicket(Base):
    """
    Escalated tickets created when AI confidence is low
    or user marks issue as not solved.
    """
    __tablename__ = "support_tickets"

    id               = Column(Integer, primary_key=True, index=True)
    user_query       = Column(Text,       nullable=False)
    predicted_intent = Column(String(100))
    ai_suggestions   = Column(Text)
    user_details     = Column(Text)
    status           = Column(String(50), default="open")
    created_at       = Column(DateTime,   server_default=func.now())


# ─────────────────────────────────────────────
# SECTION 2 — Pydantic Schemas (API contracts)
# ─────────────────────────────────────────────

# ── Incoming requests ──

class QueryRequest(BaseModel):
    """User submits their issue in natural language."""
    user_query : str = Field(
        ...,
        min_length = 5,
        max_length = 1000,
        example    = "My laptop is connected to WiFi but websites are not opening"
    )


class TicketCreateRequest(BaseModel):
    """User submits an escalation ticket when AI cannot resolve."""
    user_query       : str = Field(..., min_length=5, max_length=1000)
    predicted_intent : Optional[str] = None
    ai_suggestions   : Optional[str] = None
    user_details     : Optional[str] = Field(
        None,
        max_length = 2000,
        example    = "I already tried restarting but the issue persists"
    )


class FeedbackRequest(BaseModel):
    """User marks solution as solved or not solved."""
    ticket_id        : Optional[int] = None
    user_query       : str
    predicted_intent : Optional[str] = None
    ai_solution      : Optional[str] = None
    is_solved        : bool = Field(
        ...,
        example = True
    )


# ── Outgoing responses ──

class SimilarTicket(BaseModel):
    """One retrieved historical ticket from semantic search."""
    ticket_id  : int
    intent     : str
    user_query : str
    solution   : str
    similarity : float


class QueryResponse(BaseModel):
    """
    Full response sent back to Streamlit after /query.
    Contains classification, retrieved tickets, AI solution,
    and escalation decision.
    """
    predicted_intent  : str
    confidence        : float
    similar_tickets   : List[SimilarTicket]
    ai_solution       : str
    should_escalate   : bool
    escalation_reason : Optional[str] = None


class TicketResponse(BaseModel):
    """Confirmation returned after escalation ticket is created."""
    ticket_id  : int
    status     : str
    message    : str


class FeedbackResponse(BaseModel):
    """Confirmation returned after feedback is recorded."""
    message : str
    logged  : bool


class HealthResponse(BaseModel):
    """Health check response for Render uptime monitoring."""
    status   : str
    database : str
    models   : str
    version  : str