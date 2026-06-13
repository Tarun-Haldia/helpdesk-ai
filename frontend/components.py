# frontend/components.py
# Reusable UI components for Streamlit pages.
# Each function renders one visual block.

import streamlit as st


def render_header():
    """Top header shown on every page."""
    st.markdown("""
        <div style='text-align:center; padding: 1.5rem 0 0.5rem 0'>
            <h1 style='font-size:2rem; margin-bottom:0.2rem'>
                🤖 Helpdesk AI Assistant
            </h1>
            <p style='color:gray; font-size:1rem'>
                Describe your issue and get instant step-by-step help
            </p>
        </div>
    """, unsafe_allow_html=True)
    st.divider()


def render_api_status(health: dict):
    """
    Small status bar showing API + DB health.
    Green = ok, Red = offline.
    """
    status = health.get("status", "unknown")
    db     = health.get("database", "unknown")
    models = health.get("models",   "unknown")

    if status == "ok":
        st.success(f"✅ API online — Database: {db} — Models: {models}", icon=None)
    else:
        st.error("❌ API offline — Make sure FastAPI server is running")


def render_intent_badge(intent: str, confidence: float):
    """
    Coloured badge showing predicted intent and confidence.
    Green > 75%, Orange 60-75%, Red < 60%.
    """
    if confidence >= 75:
        color = "#2ECC71"
        label = "High confidence"
    elif confidence >= 60:
        color = "#EF9F27"
        label = "Medium confidence"
    else:
        color = "#E24B4A"
        label = "Low confidence — escalating"

    intent_clean = intent.replace("_", " ").title()

    st.markdown(f"""
        <div style='display:flex; gap:10px; align-items:center; margin:0.5rem 0'>
            <span style='background:{color}22; color:{color};
                         border:1px solid {color}55;
                         padding:4px 14px; border-radius:20px;
                         font-size:0.85rem; font-weight:500'>
                {intent_clean}
            </span>
            <span style='color:gray; font-size:0.85rem'>
                {confidence:.1f}% — {label}
            </span>
        </div>
    """, unsafe_allow_html=True)


def render_solution_card(solution: str):
    """
    Displays the AI-generated solution in a clean card.
    """
    st.markdown("### 💡 AI Solution")
    st.markdown(f"""
        <div style='background:#F8F9FA; border-left:4px solid #378ADD;
                    padding:1rem 1.2rem; border-radius:0 8px 8px 0;
                    font-size:0.95rem; line-height:1.7'>
            {solution.replace(chr(10), '<br>')}
        </div>
    """, unsafe_allow_html=True)


def render_similar_tickets(similar_tickets: list):
    """
    Expandable section showing top-K similar historical tickets.
    """
    if not similar_tickets:
        return

    with st.expander(f"📂 View {len(similar_tickets)} similar historical tickets", expanded=False):
        for i, ticket in enumerate(similar_tickets, 1):
            intent_clean = ticket['intent'].replace('_', ' ').title()
            similarity   = ticket['similarity'] * 100

            st.markdown(f"""
                <div style='border:1px solid #E0E0E0; border-radius:8px;
                            padding:0.8rem 1rem; margin-bottom:0.6rem'>
                    <div style='display:flex; justify-content:space-between;
                                align-items:center; margin-bottom:0.4rem'>
                        <span style='font-weight:500; font-size:0.9rem'>
                            Ticket #{ticket['ticket_id']} — {intent_clean}
                        </span>
                        <span style='color:gray; font-size:0.8rem'>
                            {similarity:.1f}% match
                        </span>
                    </div>
                    <div style='color:#555; font-size:0.85rem; margin-bottom:0.3rem'>
                        <b>Issue:</b> {ticket['user_query']}
                    </div>
                    <div style='color:#555; font-size:0.85rem'>
                        <b>Solution:</b> {ticket['solution'][:180]}...
                    </div>
                </div>
            """, unsafe_allow_html=True)


def render_feedback_buttons(
    user_query       : str,
    predicted_intent : str,
    ai_solution      : str
):
    """
    Solved / Not Solved buttons after solution delivery.
    Submits feedback to POST /feedback.
    Returns: 'solved', 'not_solved', or None
    """
    from api_client import submit_feedback

    st.markdown("---")
    st.markdown("**Did this solution help you?**")

    col1, col2, _ = st.columns([1, 1, 4])

    with col1:
        if st.button("✅ Solved", key="btn_solved", use_container_width=True):
            submit_feedback(
                user_query       = user_query,
                is_solved        = True,
                predicted_intent = predicted_intent,
                ai_solution      = ai_solution
            )
            st.success("Great! Glad it helped.")
            return "solved"

    with col2:
        if st.button("❌ Not Solved", key="btn_not_solved", use_container_width=True):
            submit_feedback(
                user_query       = user_query,
                is_solved        = False,
                predicted_intent = predicted_intent,
                ai_solution      = ai_solution
            )
            return "not_solved"

    return None


def render_escalation_banner(reason: str):
    """
    Warning banner shown when confidence is too low
    and issue is being routed to a support engineer.
    """
    st.warning(f"""
        ⚠️ **Routing to Support Engineer**

        {reason}

        Please fill in the ticket form below to describe your issue in more detail.
        A support engineer will respond within 24 hours.
    """)