# frontend/api_client.py
# Single source of truth for all FastAPI calls.
# Streamlit pages import from here — never call requests directly.

import os
import requests
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

# During local dev  → points to local uvicorn
# After deployment  → points to Render FastAPI URL
API_BASE = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/api/v1")

TIMEOUT = 60   # seconds — Gemini can be slow on free tier


def query_api(user_query: str) -> dict:
    """
    POST /query
    Sends user issue → gets intent, confidence,
    similar tickets, AI solution, escalation flag.

    Returns dict or error dict.
    """
    try:
        response = requests.post(
            f"{API_BASE}/query",
            json    = {"user_query": user_query},
            timeout = TIMEOUT
        )
        response.raise_for_status()
        return {"success": True, "data": response.json()}

    except requests.exceptions.Timeout:
        return {
            "success" : False,
            "error"   : "Request timed out. Gemini may be slow. Please try again."
        }
    except requests.exceptions.ConnectionError:
        return {
            "success" : False,
            "error"   : "Cannot connect to API server. Make sure FastAPI is running."
        }
    except requests.exceptions.HTTPError as e:
        return {
            "success" : False,
            "error"   : f"API error: {e.response.status_code} — {e.response.text}"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def create_ticket(
    user_query       : str,
    predicted_intent : str = None,
    ai_suggestions   : str = None,
    user_details     : str = None
) -> dict:
    """
    POST /ticket
    Creates an escalation ticket in the database.
    Returns ticket_id and confirmation message.
    """
    try:
        response = requests.post(
            f"{API_BASE}/ticket",
            json = {
                "user_query"       : user_query,
                "predicted_intent" : predicted_intent,
                "ai_suggestions"   : ai_suggestions,
                "user_details"     : user_details
            },
            timeout = TIMEOUT
        )
        response.raise_for_status()
        return {"success": True, "data": response.json()}

    except requests.exceptions.HTTPError as e:
        return {
            "success" : False,
            "error"   : f"Failed to create ticket: {e.response.status_code}"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def submit_feedback(
    user_query       : str,
    is_solved        : bool,
    predicted_intent : str = None,
    ai_solution      : str = None,
    ticket_id        : int = None
) -> dict:
    """
    POST /feedback
    Logs whether user found the solution helpful.
    """
    try:
        response = requests.post(
            f"{API_BASE}/feedback",
            json = {
                "user_query"       : user_query,
                "is_solved"        : is_solved,
                "predicted_intent" : predicted_intent,
                "ai_solution"      : ai_solution,
                "ticket_id"        : ticket_id
            },
            timeout = TIMEOUT
        )
        response.raise_for_status()
        return {"success": True, "data": response.json()}

    except Exception as e:
        return {"success": False, "error": str(e)}


def get_tickets() -> dict:
    """
    GET /tickets
    Fetches all open support tickets for admin view.
    """
    try:
        response = requests.get(
            f"{API_BASE}/tickets",
            timeout = TIMEOUT
        )
        response.raise_for_status()
        return {"success": True, "data": response.json()}

    except Exception as e:
        return {"success": False, "error": str(e)}


def health_check() -> dict:
    """
    GET /health
    Checks if API server is reachable and healthy.
    """
    try:
        response = requests.get(
            f"{API_BASE}/health",
            timeout = 5
        )
        response.raise_for_status()
        return {"success": True, "data": response.json()}

    except Exception:
        return {
            "success" : False,
            "data"    : {"status": "offline", "database": "unknown", "models": "unknown"}
        }