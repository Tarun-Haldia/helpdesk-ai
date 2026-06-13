# api/retriever.py
# Uses fastembed instead of sentence-transformers + torch
# RAM usage: ~150MB vs ~800MB — fits Render free tier 512MB limit

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

# Module-level cache
_embedder = None


def load_embedder():
    """
    Loads fastembed model at startup.
    all-MiniLM-L6-v2 via ONNX — same vectors as before,
    fraction of the RAM.
    """
    global _embedder
    from fastembed import TextEmbedding

    print("  Loading fastembed (all-MiniLM-L6-v2 ONNX)...")
    _embedder = TextEmbedding(
        model_name = "sentence-transformers/all-MiniLM-L6-v2"
    )
    print("  Embedder        : loaded (fastembed ONNX)")
    return _embedder


def get_embedder():
    """Returns cached embedder, loads if not yet initialised."""
    global _embedder
    if _embedder is None:
        load_embedder()
    return _embedder


def encode_query(user_query: str) -> np.ndarray:
    """
    Encode a single query string into a 384-dim unit vector.
    fastembed returns a generator — we take the first item.
    """
    embedder = get_embedder()
    vectors  = list(embedder.embed([user_query]))
    vec      = np.array(vectors[0], dtype=np.float32)

    # Normalise to unit vector (cosine similarity)
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec


def retrieve_similar(
    user_query : str,
    embedder   : any = None,   # kept for API compatibility
    top_k      : int = 3
) -> list:
    """
    Encode query → pgvector cosine similarity search → top_k results.
    """
    query_vec = encode_query(user_query)
    vec_str   = str(query_vec.tolist())

    search_sql = text("""
        SELECT
            t.id,
            t.intent,
            t.user_query,
            t.solution,
            ROUND(CAST(1 - (e.embedding <=> :vec) AS NUMERIC), 4)
                AS similarity
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
    """Format retrieved tickets as Gemini prompt context block."""
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