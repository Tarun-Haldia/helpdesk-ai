# api/retriever.py
# Loads sentence transformer at startup.
# Encodes user query at runtime and retrieves
# top-K similar tickets from Supabase pgvector.

import os
import numpy as np
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sentence_transformers import SentenceTransformer

from pathlib import Path
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)
# On Render .env doesn't exist — env vars are set in dashboard
# load_dotenv silently skips if file not found, which is correct

# ── Database engine ──
DATABASE_URL = os.getenv("SUPABASE_DB_URL")
engine       = create_engine(
    DATABASE_URL,
    pool_pre_ping = True,
    pool_size     = 5,
    max_overflow  = 10
)

# ── Module-level cache ──
_embedder = None


def load_embedder():
    """
    Called once in main.py lifespan at startup.
    Loads sentence transformer into memory.
    Returns the embedder stored in app.state.embedder.
    """
    global _embedder

    import torch
    device    = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"  Loading sentence transformer on {device} ...")

    _embedder = SentenceTransformer(
        "sentence-transformers/all-MiniLM-L6-v2",
        device = device
    )

    dim = _embedder.get_sentence_embedding_dimension()
    print(f"  Embedder ready  : dim={dim}, device={device}")

    return _embedder


def encode_query(user_query: str, embedder: SentenceTransformer) -> np.ndarray:
    """
    Encode a single user query into a 384-dim unit vector.

    Args:
        user_query : raw text string from user
        embedder   : loaded SentenceTransformer from app.state.embedder

    Returns:
        numpy array of shape (384,)
    """
    vec = embedder.encode(
        [user_query],
        normalize_embeddings = True,
        convert_to_numpy     = True
    )[0]
    return vec


def retrieve_similar(
    user_query : str,
    embedder   : SentenceTransformer,
    top_k      : int = 3
) -> list:
    """
    Full semantic search pipeline.

    Steps:
        1. Encode user query → 384-dim vector
        2. Run pgvector cosine similarity search
        3. Return top_k tickets with similarity scores

    Args:
        user_query : raw text from user
        embedder   : SentenceTransformer from app.state.embedder
        top_k      : number of similar tickets to return (default 3)

    Returns:
        list of dicts with keys:
            ticket_id, intent, user_query, solution, similarity
    """
    # Step 1 — encode query
    query_vec = encode_query(user_query, embedder)
    vec_str   = str(query_vec.tolist())

    # Step 2 — pgvector cosine similarity search
    # <=> is pgvector cosine distance operator
    # similarity = 1 - cosine_distance
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

    # Step 3 — format results
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
    """
    Formats retrieved tickets into a clean context block
    to inject into the Gemini prompt.

    Args:
        similar_tickets : list from retrieve_similar()

    Returns:
        formatted string ready for Gemini prompt injection
    """
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