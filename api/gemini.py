# api/gemini.py
# Calls Gemini API to convert technical solutions
# into friendly step-by-step instructions.

import os
import time
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv

# ──────────────────────────────────────────────
# Load Environment Variables
# ──────────────────────────────────────────────
from pathlib import Path
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)
# On Render .env doesn't exist — env vars are set in dashboard
# load_dotenv silently skips if file not found, which is correct

# ──────────────────────────────────────────────
# Configure Gemini
# ──────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file")

genai.configure(api_key=GEMINI_API_KEY)

# ──────────────────────────────────────────────
# Model Configuration
# ──────────────────────────────────────────────
generation_config = genai.GenerationConfig(
    temperature=0.3,
    top_p=0.85,
    top_k=40,
    max_output_tokens=1024,
)

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
)

# ──────────────────────────────────────────────
# System Prompt
# ──────────────────────────────────────────────
SYSTEM_PROMPT = """
You are a friendly and helpful IT support assistant.

Your job is to help non-technical users solve their
computer and software problems.

RULES:
1. Always respond in clear, simple English
2. Break solutions into numbered steps
3. Each step must be a single action
4. Avoid technical jargon
5. If a command is needed, show it in a code block
6. End by asking if the issue is resolved
7. Keep responses under 300 words
8. Only use information provided in the context

TONE:
Friendly, patient, encouraging.
"""

# ──────────────────────────────────────────────
# Generate Solution
# ──────────────────────────────────────────────
def generate_solution(
    user_query: str,
    predicted_intent: str,
    context: str,
) -> str:
    """
    Generate a friendly step-by-step solution.
    """

    prompt = f"""
{SYSTEM_PROMPT}

USER PROBLEM:
{user_query}

DETECTED ISSUE CATEGORY:
{predicted_intent.replace('_', ' ').title()}

{context}

TASK:
Based on the similar tickets above, provide a clear
step-by-step solution for the user's problem.
Make it easy for a non-technical person to follow.
"""

    for attempt in range(3):
        try:
            response = model.generate_content(prompt)

            if response.parts:
                return response.text.strip()

            return _fallback_solution(predicted_intent)

        except Exception as e:
            error_msg = str(e)

            if "429" in error_msg:
                wait_time = 40 * (attempt + 1)

                print(
                    f"Gemini rate limit hit. "
                    f"Waiting {wait_time}s "
                    f"(attempt {attempt + 1}/3)..."
                )

                time.sleep(wait_time)
            else:
                print(f"Gemini API error: {e}")
                return _fallback_solution(predicted_intent)

    return _fallback_solution(predicted_intent)


# ──────────────────────────────────────────────
# Generate Escalation Message
# ──────────────────────────────────────────────
def generate_escalation_message(
    user_query: str,
    predicted_intent: str,
    confidence: float,
) -> str:
    """
    Generate a polite escalation message when
    confidence is below threshold.
    """

    prompt = f"""
You are a friendly IT support assistant.

A user has submitted a support request that
our AI could not resolve confidently.

Confidence Score: {confidence:.1f}%

USER PROBLEM:
{user_query}

BEST GUESS CATEGORY:
{predicted_intent.replace('_', ' ').title()}

TASK:
Write a short message (max 80 words) that:

1. Acknowledges the issue
2. Explains a support engineer will help
3. Mentions response within 24 hours
4. Encourages additional details

Keep it warm and reassuring.
"""

    for attempt in range(3):
        try:
            response = model.generate_content(prompt)

            if response.parts:
                return response.text.strip()

            return _default_escalation_message()

        except Exception as e:
            error_msg = str(e)

            if "429" in error_msg:
                wait_time = 40 * (attempt + 1)

                print(
                    f"Gemini rate limit hit. "
                    f"Waiting {wait_time}s "
                    f"(attempt {attempt + 1}/3)..."
                )

                time.sleep(wait_time)
            else:
                print(f"Gemini escalation error: {e}")
                return _default_escalation_message()

    return _default_escalation_message()


# ──────────────────────────────────────────────
# Fallback Solution
# ──────────────────────────────────────────────
def _fallback_solution(intent: str) -> str:
    """
    Used when Gemini is unavailable.
    """

    fallbacks = {
        "internet_issue": (
            "1. Restart your router and modem.\n"
            "2. Disconnect and reconnect to Wi-Fi.\n"
            "3. Try opening another website.\n"
            "4. Restart your browser.\n"
            "5. Contact IT support if the issue continues."
        ),

        "vpn_setup": (
            "1. Verify your internet connection works.\n"
            "2. Close and reopen the VPN application.\n"
            "3. Disconnect and reconnect the VPN.\n"
            "4. Restart your computer.\n"
            "5. Contact IT support if needed."
        ),

        "reset_password": (
            "1. Open the login page.\n"
            "2. Click 'Forgot Password'.\n"
            "3. Enter your registered email address.\n"
            "4. Check your email inbox.\n"
            "5. Follow the password reset link."
        ),

        "hardware_issue": (
            "1. Restart your computer.\n"
            "2. Check all cable connections.\n"
            "3. Run hardware diagnostics if available.\n"
            "4. Contact IT support with details."
        ),

        "software_install": (
            "1. Run the installer as Administrator.\n"
            "2. Temporarily disable antivirus software.\n"
            "3. Ensure sufficient disk space.\n"
            "4. Restart your computer.\n"
            "5. Try the installation again."
        ),
    }

    return fallbacks.get(
        intent,
        (
            "1. Restart your device.\n"
            "2. Try the action again.\n"
            "3. If the issue continues, contact IT support."
        ),
    )


# ──────────────────────────────────────────────
# Default Escalation Message
# ──────────────────────────────────────────────
def _default_escalation_message() -> str:
    """
    Returned when Gemini cannot generate
    an escalation message.
    """

    return (
        "We understand you're experiencing a technical issue. "
        "Our AI assistant was unable to resolve it with high confidence. "
        "A support engineer will review your request and respond within "
        "24 hours. Please provide as much detail as possible in your "
        "ticket to help us assist you more quickly."
    )

