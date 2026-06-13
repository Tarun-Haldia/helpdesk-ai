# api/main.py
import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent))
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up Helpdesk AI API...")

    # Check DB
    from database import check_db_connection
    check_db_connection()
    print("  Database        : connected")

    # Load classifier (small — just pkl files)
    from classifier import load_classifier
    app.state.classifier = load_classifier()
    print("  Classifier      : loaded")

    # Embedder deferred — loads on first query to save RAM
    from retriever import load_embedder
    app.state.embedder = load_embedder()
    # prints "Embedder : deferred"

    print("Startup complete. API is ready.")
    yield
    print("Shutting down...")


app = FastAPI(
    title    = "Helpdesk AI API",
    version  = "1.0.0",
    lifespan = lifespan,
    docs_url = "/docs",
    redoc_url= "/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["*"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

from routes import router
app.include_router(router, prefix="/api/v1")


@app.get("/", tags=["root"])
def root():
    return {
        "message" : "Helpdesk AI API is running",
        "docs"    : "/docs",
        "version" : "1.0.0"
    }