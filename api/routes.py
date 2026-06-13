# api/routes.py
# All FastAPI endpoint handlers.
# Wires classifier + retriever + gemini + database together.

import os
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
from pathlib import Path
from dotenv import load_dotenv

from pathlib import Path
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)
# On Render .env doesn't exist — env vars are set in dashboard
# load_dotenv silently skips if file not found, which is correct

from database import get_db
from models import (
    QueryRequest, QueryResponse, SimilarTicket,
    TicketCreateRequest, TicketResponse,
    FeedbackRequest, FeedbackResponse,
    HealthResponse
)
from classifier import predict, should_escalate
from retriever  import retrieve_similar, format_context_for_gemini
from gemini     import generate_solution, generate_escalation_message

router = APIRouter()

CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", 60))


# ─────────────────────────────────────────────
# POST /query — main endpoint
# User submits issue → get solution or escalate
# ─────────────────────────────────────────────
@router.post("/query", response_model=QueryResponse)
async def query_endpoint(request: Request, body: QueryRequest, db: Session = Depends(get_db)):
    """
    Full pipeline:
    1. Classify intent + confidence
    2. Check confidence gate
    3. Retrieve similar tickets
    4. Generate AI solution OR escalation message
    5. Return structured response
    """
    user_query = body.user_query.strip()

    # Step 1 — classify
    classifier     = request.app.state.classifier
    clf_result     = predict(user_query, classifier)
    intent         = clf_result["intent"]
    confidence     = clf_result["confidence"]

    # Step 2 — confidence gate
    escalate, escalation_reason = should_escalate(confidence)


# embedder is loaded lazily inside retrieve_similar
    similar = retrieve_similar(user_query, top_k=3)

    similar_tickets = [
        SimilarTicket(
            ticket_id  = t["ticket_id"],
            intent     = t["intent"],
            user_query = t["user_query"],
            solution   = t["solution"],
            similarity = t["similarity"]
        )
        for t in similar
    ]

    # Step 4 — generate solution or escalation message
    if escalate:
        ai_solution = generate_escalation_message(
            user_query        = user_query,
            predicted_intent  = intent,
            confidence        = confidence
        )
    else:
        context     = format_context_for_gemini(similar)
        ai_solution = generate_solution(
            user_query        = user_query,
            predicted_intent  = intent,
            context           = context
        )

    # Step 5 — return response
    return QueryResponse(
        predicted_intent  = intent,
        confidence        = confidence,
        similar_tickets   = similar_tickets,
        ai_solution       = ai_solution,
        should_escalate   = escalate,
        escalation_reason = escalation_reason if escalate else None
    )


# ─────────────────────────────────────────────
# POST /ticket — create escalation ticket
# ─────────────────────────────────────────────
@router.post("/ticket", response_model=TicketResponse)
async def create_ticket(body: TicketCreateRequest, db: Session = Depends(get_db)):
    """
    Creates a support ticket when:
    - Confidence is below threshold, OR
    - User marks solution as Not Solved
    """
    try:
        result = db.execute(
            text("""
                INSERT INTO support_tickets
                    (user_query, predicted_intent, ai_suggestions, user_details, status)
                VALUES
                    (:user_query, :predicted_intent, :ai_suggestions, :user_details, 'open')
                RETURNING id;
            """),
            {
                "user_query"       : body.user_query,
                "predicted_intent" : body.predicted_intent or "unknown",
                "ai_suggestions"   : body.ai_suggestions   or "",
                "user_details"     : body.user_details      or ""
            }
        )
        db.commit()
        ticket_id = result.fetchone()[0]

        return TicketResponse(
            ticket_id = ticket_id,
            status    = "open",
            message   = f"Ticket #{ticket_id} created. A support engineer will respond within 24 hours."
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create ticket: {str(e)}")


# ─────────────────────────────────────────────
# POST /feedback — store solved / not solved
# ─────────────────────────────────────────────
@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(body: FeedbackRequest, db: Session = Depends(get_db)):
    """
    Stores user feedback after solution is delivered.
    Solved=True improves retrieval quality over time.
    """
    try:
        db.execute(
            text("""
                INSERT INTO feedback
                    (ticket_id, user_query, predicted_intent, ai_solution, is_solved)
                VALUES
                    (:ticket_id, :user_query, :predicted_intent, :ai_solution, :is_solved);
            """),
            {
                "ticket_id"        : body.ticket_id,
                "user_query"       : body.user_query,
                "predicted_intent" : body.predicted_intent or "unknown",
                "ai_solution"      : body.ai_solution      or "",
                "is_solved"        : body.is_solved
            }
        )
        db.commit()

        return FeedbackResponse(
            message = "Thank you for your feedback!" if body.is_solved else "Sorry it didn't help. Creating a ticket for you.",
            logged  = True
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to log feedback: {str(e)}")


# ─────────────────────────────────────────────
# GET /tickets — list all open support tickets
# ─────────────────────────────────────────────
@router.get("/tickets")
async def list_tickets(db: Session = Depends(get_db)):
    """Returns all open escalation tickets — for admin view."""
    try:
        result = db.execute(
            text("""
                SELECT id, user_query, predicted_intent,
                       status, created_at
                FROM support_tickets
                ORDER BY created_at DESC
                LIMIT 50;
            """)
        )
        rows = result.fetchall()

        return {
            "tickets": [
                {
                    "id"               : row[0],
                    "user_query"       : row[1],
                    "predicted_intent" : row[2],
                    "status"           : row[3],
                    "created_at"       : str(row[4])
                }
                for row in rows
            ],
            "total": len(rows)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch tickets: {str(e)}")


# ─────────────────────────────────────────────
# GET /health — liveness check for Render
# ─────────────────────────────────────────────
@router.get("/health", response_model=HealthResponse)
async def health_check(request: Request, db: Session = Depends(get_db)):
    """
    Render uses this to check if the service is alive.
    Checks DB connection and model availability.
    """
    # Check DB
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "error"

    # Check models loaded
    try:
        clf_loaded = request.app.state.classifier is not None
        emb_loaded = request.app.state.embedder   is not None
        model_status = "loaded" if clf_loaded and emb_loaded else "error"
    except Exception:
        model_status = "error"

    return HealthResponse(
        status   = "ok" if db_status == "connected" and model_status == "loaded" else "degraded",
        database = db_status,
        models   = model_status,
        version  = "1.0.0"
    )