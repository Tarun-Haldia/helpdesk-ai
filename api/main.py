# api/main.py
# FastAPI application entry point
# Handles: app creation, startup/shutdown, CORS, router registration

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from pathlib import Path
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

# ── Startup / shutdown lifecycle ──
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs once at startup — checks DB, loads ML models into memory.
    Runs once at shutdown — cleanup if needed.
    """
    print("Starting up Helpdesk AI API...")

    # 1. Check database connection
    from database import check_db_connection
    check_db_connection()
    print("  Database        : connected")

    # 2. Load ML classifier + vectorizer + label encoder into app state
    from classifier import load_classifier
    app.state.classifier = load_classifier()
    print("  Classifier      : loaded")

    # 3. Load sentence transformer for semantic search
    from retriever import load_embedder
    app.state.embedder = load_embedder()
    print("  Embedder        : loaded")

    print("Startup complete. API is ready.")
    yield

    # Shutdown
    print("Shutting down Helpdesk AI API...")


# ── App creation ──
app = FastAPI(
    title       = "Helpdesk AI — Self-Service Support API",
    description = (
        "AI-powered support assistant that classifies issues, "
        "retrieves similar tickets via semantic search, "
        "and generates step-by-step solutions using Gemini."
    ),
    version     = "1.0.0",
    lifespan    = lifespan,
    docs_url    = "/docs",      # Swagger UI at /docs
    redoc_url   = "/redoc"      # ReDoc UI at /redoc
)


# ── CORS middleware ──
# Allows Streamlit frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["*"],   # tighten this after deployment
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)


# ── Register routes ──
from routes import router
app.include_router(router, prefix="/api/v1")


# ── Root endpoint ──
@app.get("/", tags=["root"])
def root():
    return {
        "message" : "Helpdesk AI API is running",
        "docs"    : "/docs",
        "version" : "1.0.0"
    }