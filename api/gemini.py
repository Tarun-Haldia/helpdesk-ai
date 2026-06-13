# api/gemini.py
# Calls Gemini API to convert technical solutions
# into friendly step-by-step instructions.

import os
import google.generativeai as genai
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

# ── Configure Gemini ──
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file")

genai.configure(api_key=GEMINI_API_KEY)

# ── Model config ──
generation_config = genai.GenerationConfig(
    temperature       = 0.3,   # low = more focused, less creative
    top_p             = 0.85,
    top_k             = 40,
    max_output_tokens = 1024,
)

model = genai.GenerativeModel(
    model_name        = "gemini-1.5-flash",   # fast + free tier
    generation_config = generation_config
)


# ── System prompt ──
SYSTEM_PROMPT = """You are a friendly and helpful IT support assistant.
Your job is to help non-technical users solve their computer and software problems.

RULES:
1. Always respond in clear, simple English that anyone can understand
2. Break solutions into numbered steps
3. Each step must be a single, specific action
4. Use plain language — avoid technical jargon
5. If a command is needed, show it in a code block
6. End with a follow-up line asking if the issue is resolved
7. Keep the total response under 300 words
8. Never make up solutions — only use what is provided in the context

TONE: Friendly, patient, encouraging. Like explaining to a friend.
"""


def generate_solution(
    user_query      : str,
    predicted_intent: str,
    context         : str,
) -> str:
    """
    Calls Gemini with user query + retrieved context.
    Returns a friendly step-by-step solution string.

    Args:
        user_query       : original user query (raw text)
        predicted_intent : intent label from classifier
        context          : formatted similar tickets from retriever

    Returns:
        str — human-friendly solution from Gemini
    """

    prompt = f"""
{SYSTEM_PROMPT}

USER PROBLEM:
{user_query}

DETECTED ISSUE CATEGORY:
{predicted_intent.replace('_', ' ').title()}

{context}

TASK:
Based on the similar tickets above, provide a clear step-by-step solution
for the user's problem. Make it easy to follow for a non-technical person.
"""

    try:
        response = model.generate_content(prompt)

        # Extract text from response
        if response.parts:
            return response.text.strip()
        else:
            return _fallback_solution(predicted_intent)

    except Exception as e:
        print(f"Gemini API error: {e}")
        return _fallback_solution(predicted_intent)


def generate_escalation_message(
    user_query       : str,
    predicted_intent : str,
    confidence       : float
) -> str:
    """
    Called when confidence is below threshold.
    Generates a polite message explaining escalation
    and what the user can expect next.

    Args:
        user_query       : original user query
        predicted_intent : best-guess intent from classifier
        confidence       : classifier confidence score (0-100)

    Returns:
        str — friendly escalation message
    """
    prompt = f"""
You are a friendly IT support assistant.
A user has submitted a support request that our AI could not
resolve with high confidence ({confidence:.1f}% confidence).

USER PROBLEM:
{user_query}

BEST GUESS CATEGORY:
{predicted_intent.replace('_', ' ').title()}

TASK:
Write a short, friendly message (max 80 words) that:
1. Acknowledges their problem with empathy
2. Explains that a support engineer will help them
3. Tells them what to expect next (response within 24 hours)
4. Encourages them to provide more details in the ticket form

Keep it warm and reassuring.
"""
    try:
        response = model.generate_content(prompt)
        if response.parts:
            return response.text.strip()
        else:
            return _default_escalation_message()
    except Exception as e:
        print(f"Gemini escalation error: {e}")
        return _default_escalation_message()


def _fallback_solution(intent: str) -> str:
    """
    Hardcoded fallback when Gemini API fails.
    Ensures users always get some guidance.
    """
    fallbacks = {
        "internet_issue"     : "1. Restart your router and modem.\n2. Disconnect and reconnect to WiFi.\n3. Try opening a different website.\n4. Restart your browser.\n5. If still not working, contact IT support.",
        "vpn_setup"          : "1. Check your internet connection is working.\n2. Close and reopen the VPN application.\n3. Try disconnecting then reconnecting.\n4. Restart your computer and try again.\n5. Contact IT support if issue persists.",
        "reset_password"     : "1. Go to the login page.\n2. Click 'Forgot Password'.\n3. Enter your registered email address.\n4. Check your email for reset link.\n5. Follow the link to create a new password.",
        "hardware_issue"     : "1. Restart your computer.\n2. Check all cable connections.\n3. Run hardware diagnostics if available.\n4. Contact IT support with the issue details.",
        "software_install"   : "1. Run the installer as Administrator.\n2. Temporarily disable antivirus.\n3. Ensure you have enough disk space.\n4. Restart and try installation again.",
    }
    return fallbacks.get(
        intent,
        "Please restart your device and try again. "
        "If the issue persists, contact IT support with details of your problem."
    )


def _default_escalation_message() -> str:
    """Default escalation message when Gemini API fails."""
    return (
        "We understand you're experiencing a technical issue. "
        "Our AI assistant wasn't able to resolve this with full confidence, "
        "so we're connecting you with a support engineer who will help you shortly. "
        "Please fill in the ticket form below with as much detail as possible. "
        "You can expect a response within 24 hours."
    )

# api/check_gemini.py — list all available Gemini models
import os
import google.generativeai as genai
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

print("Available Gemini models that support generateContent:\n")
for m in genai.list_models():
    if "generateContent" in m.supported_generation_methods:
        print(f"  {m.name}")