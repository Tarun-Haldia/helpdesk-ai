# api/retriever.py
# Lazy loads sentence transformer on first query, not at startup
# This keeps startup RAM under 512MB for Render free tier

import os
import numpy as np
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

DATABASE_URL = os.getenv("SUPABASE_DB_URL")
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping = True,
    pool_size     = 3,
    max_overflow  = 5
)

# Module-level cache — None until first query
_embedder = None


def load_embedder():
    """
    Called at startup — returns None placeholder.
    Actual model loads on first query via get_embedder().
    This keeps startup RAM under 512MB on Render free tier.
    """
    print("  Embedder        : deferred (loads on first query)")
    return "deferred"


def get_embedder():
    """
    Returns cached embedder, loading it on first call.
    Thread-safe enough for single-worker Render free tier.
    """
    global _embedder
    if _embedder is None or _embedder == "deferred":
        print("Loading sentence transformer (first query)...")
        from sentence_transformers import SentenceTransformer
        import torch
        device   = "cpu"
        _embedder = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2",
            device = device
        )
        print("Sentence transformer loaded.")
    return _embedder


def encode_query(user_query: str) -> np.ndarray:
    """Encode a single query string into a 384-dim vector."""
    embedder = get_embedder()
    vec = embedder.encode(
        [user_query],
        normalize_embeddings = True,
        convert_to_numpy     = True
    )[0]
    return vec


def retrieve_similar(
    user_query : str,
    embedder   : any = None,   # kept for API compatibility, ignored
    top_k      : int = 3
) -> list:
    """
    Semantic search — encodes query then finds top_k
    similar tickets via pgvector cosine similarity.
    """
    query_vec = encode_query(user_query)
    vec_str   = str(query_vec.tolist())

    search_sql = text("""
        SELECT
            t.id,
            t.intent,
            t.user_query,
            t.solution,
            ROUND(CAST(1 - (e.embedding <=> :vec) AS NUMERIC), 4) AS similarity
        FROM embeddings e
        JOIN tickets t ON t.id = e.ticket_id
        ORDER BY e.embedding <=> :vec
        LIMIT :top_k;
    """)

    with engine.connect() as conn:
        result = conn.execute(search_sql, {
            "vec"   : vec_str,
            "top_k" : top_k
        })
        rows = result.fetchall()

    return [
        {
            "ticket_id"  : row[0],
            "intent"     : row[1],
            "user_query" : row[2],
            "solution"   : row[3],
            "similarity" : float(row[4])
        }
        for row in rows
    ]


def format_context_for_gemini(similar_tickets: list) -> str:
    """Formats retrieved tickets into Gemini prompt context."""
    if not similar_tickets:
        return "No similar historical tickets found."

    lines = ["SIMILAR HISTORICAL SUPPORT TICKETS:\n"]
    for i, ticket in enumerate(similar_tickets, 1):
        lines.append(
            f"--- Ticket {i} ---\n"
            f"Issue    : {ticket['user_query']}\n"
            f"Category : {ticket['intent']}\n"
            f"Solution : {ticket['solution']}\n"
            f"Match    : {ticket['similarity'] * 100:.1f}%\n"
        )
    return "\n".join(lines)