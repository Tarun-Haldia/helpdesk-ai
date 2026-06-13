# frontend/ticket_form.py
# Escalation ticket form.
# Shown when: confidence < threshold OR user clicks Not Solved.

import streamlit as st
from api_client import create_ticket


def render_ticket_form(
    user_query       : str = "",
    predicted_intent : str = "",
    ai_suggestions   : str = ""
):
    """
    Renders escalation form pre-filled with AI context.
    Submits to POST /ticket on confirmation.
    """
    st.markdown("### 🎫 Create Support Ticket")
    st.markdown("Fill in the details below and a support engineer will help you shortly.")

    with st.container():
        # Pre-filled fields
        query_display = st.text_area(
            "Your Issue",
            value    = user_query,
            height   = 100,
            disabled = True,
            help     = "Your original query — cannot be edited here"
        )

        intent_display = st.text_input(
            "Detected Category",
            value    = predicted_intent.replace("_", " ").title() if predicted_intent else "Unknown",
            disabled = True
        )

        # User can add more details
        user_details = st.text_area(
            "Additional Details (optional)",
            placeholder = (
                "Please describe:\n"
                "• When did this start?\n"
                "• What have you already tried?\n"
                "• Any error messages you see?"
            ),
            height = 150
        )

        # Show AI suggestions that will be attached
        if ai_suggestions:
            with st.expander("📋 AI suggestions attached to ticket", expanded=False):
                st.markdown(ai_suggestions)

        st.markdown("")
        col1, col2 = st.columns([1, 3])

        with col1:
            submit = st.button(
                "📨 Submit Ticket",
                type             = "primary",
                use_container_width = True
            )

        if submit:
            with st.spinner("Creating your ticket..."):
                result = create_ticket(
                    user_query       = user_query,
                    predicted_intent = predicted_intent,
                    ai_suggestions   = ai_suggestions,
                    user_details     = user_details
                )

            if result["success"]:
                data = result["data"]
                st.success(f"""
                    ✅ **{data['message']}**

                    Your ticket ID is **#{data['ticket_id']}**.
                    Keep this number for reference.
                    Expected response time: within 24 hours.
                """)
                # Store ticket ID in session
                st.session_state["last_ticket_id"] = data["ticket_id"]
                return True
            else:
                st.error(f"Failed to create ticket: {result['error']}")
                return False

    return False