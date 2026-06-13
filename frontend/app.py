# frontend/app.py — GenZ dark UI

import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from api_client import query_api, health_check, get_tickets

st.set_page_config(
    page_title = "HelpDesk AI",
    page_icon  = "🤖",
    layout     = "wide",
    initial_sidebar_state = "expanded"
)

# ── Inject global CSS ──
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
  --bg:      #0A0A0F;
  --surface: #12121A;
  --card:    #1A1A28;
  --border:  #2A2A40;
  --accent:  #7C5CFC;
  --accent2: #FC5C7D;
  --green:   #5CFC8A;
  --yellow:  #FCE05C;
  --text:    #F0F0FF;
  --muted:   #6B6B8A;
}

html, body, [class*="css"] {
  font-family: 'Space Grotesk', sans-serif !important;
  background-color: var(--bg) !important;
  color: var(--text) !important;
}

/* Hide Streamlit default header/footer */
#MainMenu, footer, header { visibility: hidden; }

/* Sidebar */
section[data-testid="stSidebar"] {
  background: var(--surface) !important;
  border-right: 1px solid var(--border) !important;
}

section[data-testid="stSidebar"] * {
  color: var(--text) !important;
}

/* Main background */
.main .block-container {
  background: var(--bg) !important;
  padding-top: 1rem !important;
}

/* Text area */
textarea {
  background: var(--card) !important;
  border: 1px solid var(--border) !important;
  color: var(--text) !important;
  border-radius: 12px !important;
  font-family: 'Space Grotesk', sans-serif !important;
  font-size: 0.9rem !important;
}

textarea:focus {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 3px #7C5CFC18 !important;
}

/* Primary button */
.stButton > button[kind="primary"] {
  background: linear-gradient(135deg, #7C5CFC, #FC5C7D) !important;
  border: none !important;
  border-radius: 10px !important;
  font-family: 'Space Grotesk', sans-serif !important;
  font-weight: 600 !important;
  font-size: 0.88rem !important;
  padding: 0.6rem 1.5rem !important;
  color: white !important;
  transition: opacity 0.15s !important;
}

.stButton > button[kind="primary"]:hover {
  opacity: 0.85 !important;
}

/* Secondary button */
.stButton > button {
  background: var(--card) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
  font-family: 'Space Grotesk', sans-serif !important;
  font-size: 0.83rem !important;
  color: var(--muted) !important;
  transition: all 0.15s !important;
}

.stButton > button:hover {
  border-color: var(--accent) !important;
  color: var(--text) !important;
}

/* Expander */
.streamlit-expanderHeader {
  background: var(--card) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
  font-size: 0.82rem !important;
  color: var(--muted) !important;
}

/* Spinner */
.stSpinner > div { border-top-color: var(--accent) !important; }

/* Divider */
hr { border-color: var(--border) !important; }

/* Success/warning/error */
.stSuccess { background: #5CFC8A11 !important; border-color: #5CFC8A44 !important; }
.stWarning { background: #FCE05C11 !important; border-color: #FCE05C44 !important; }
.stError   { background: #FC5C7D11 !important; border-color: #FC5C7D44 !important; }

/* Code */
code {
  background: #0A0A1A !important;
  color: #5CFC8A !important;
  border: 1px solid var(--border) !important;
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 0.8rem !important;
  padding: 1px 6px !important;
  border-radius: 4px !important;
}

/* Metric */
[data-testid="metric-container"] {
  background: var(--card) !important;
  border: 1px solid var(--border) !important;
  border-radius: 12px !important;
  padding: 0.8rem 1rem !important;
}

/* Radio */
.stRadio > div { gap: 0.3rem !important; }
.stRadio label {
  background: var(--card) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
  padding: 0.4rem 0.8rem !important;
  font-size: 0.82rem !important;
  cursor: pointer !important;
}
</style>
""", unsafe_allow_html=True)


# ── Session state ──
for key, default in {
    "history"        : [],
    "last_result"    : None,
    "show_ticket"    : False,
    "feedback_given" : False,
    "page"           : "💬 Chat"
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ── Sidebar ──
with st.sidebar:
    st.markdown("""
    <div style='display:flex;align-items:center;gap:10px;
                padding:0 0 1rem 0;border-bottom:1px solid #2A2A40;
                margin-bottom:1rem'>
        <div style='width:34px;height:34px;
                    background:linear-gradient(135deg,#7C5CFC,#FC5C7D);
                    border-radius:9px;display:flex;align-items:center;
                    justify-content:center;font-size:17px'>🤖</div>
        <div>
            <div style='font-size:0.95rem;font-weight:600;
                        letter-spacing:-0.02em'>HelpDesk AI</div>
            <div style='font-size:0.65rem;color:#6B6B8A;
                        font-family:monospace'>v1.0 · self-service</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "",
        ["💬 Chat", "📋 History", "🎫 Tickets"],
        label_visibility = "collapsed"
    )

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # Health status
    health = health_check()
    h_data = health.get("data", {})
    if h_data.get("status") == "ok":
        st.markdown("""
        <div style='display:flex;align-items:center;gap:8px;
                    background:#1A1A28;border:1px solid #2A2A40;
                    border-radius:9px;padding:0.5rem 0.8rem;
                    font-size:0.75rem;color:#6B6B8A'>
            <div style='width:7px;height:7px;border-radius:50%;
                        background:#5CFC8A;
                        box-shadow:0 0 6px #5CFC8A'></div>
            All systems normal
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style='display:flex;align-items:center;gap:8px;
                    background:#1A1A28;border:1px solid #FC5C7D44;
                    border-radius:9px;padding:0.5rem 0.8rem;
                    font-size:0.75rem;color:#FC5C7D'>
            <div style='width:7px;height:7px;border-radius:50%;
                        background:#FC5C7D'></div>
            API offline — start FastAPI
        </div>
        """, unsafe_allow_html=True)

    # Recent history
    if st.session_state["history"]:
        st.markdown("""
        <div style='font-size:0.65rem;text-transform:uppercase;
                    letter-spacing:0.08em;color:#6B6B8A;
                    font-family:monospace;
                    margin:1rem 0 0.4rem 0'>Recent</div>
        """, unsafe_allow_html=True)
        for item in st.session_state["history"][-4:][::-1]:
            q     = item["query"]
            short = q[:32] + "..." if len(q) > 32 else q
            st.markdown(f"""
            <div style='font-size:0.75rem;color:#6B6B8A;
                        padding:0.35rem 0.5rem;border-radius:6px;
                        cursor:pointer;white-space:nowrap;
                        overflow:hidden;text-overflow:ellipsis'>
                {short}
            </div>
            """, unsafe_allow_html=True)

    if st.button("🗑 Clear session", use_container_width=True):
        st.session_state.update({
            "history": [], "last_result": None,
            "show_ticket": False, "feedback_given": False
        })
        st.rerun()


# ════════════════════════════════════
# PAGE 1 — Chat
# ════════════════════════════════════
if page == "💬 Chat":

    # Header
    st.markdown("""
    <div style='margin-bottom:1.5rem'>
        <h2 style='font-size:1.6rem;font-weight:700;
                   letter-spacing:-0.03em;margin-bottom:0.2rem'>
            hey, what's broken? 👾
        </h2>
        <p style='color:#6B6B8A;font-size:0.88rem'>
            describe your issue — no hold music, no ticket queues
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Quick chips
    st.markdown("""
    <div style='display:flex;flex-wrap:wrap;gap:8px;margin-bottom:1.2rem'>
        <span style='font-size:0.72rem;font-family:monospace;
                     padding:4px 12px;border-radius:20px;
                     background:#1A1A28;border:1px solid #2A2A40;
                     color:#6B6B8A'>📶 WiFi issues</span>
        <span style='font-size:0.72rem;font-family:monospace;
                     padding:4px 12px;border-radius:20px;
                     background:#1A1A28;border:1px solid #2A2A40;
                     color:#6B6B8A'>🔒 VPN problems</span>
        <span style='font-size:0.72rem;font-family:monospace;
                     padding:4px 12px;border-radius:20px;
                     background:#1A1A28;border:1px solid #2A2A40;
                     color:#6B6B8A'>🔑 Password reset</span>
        <span style='font-size:0.72rem;font-family:monospace;
                     padding:4px 12px;border-radius:20px;
                     background:#1A1A28;border:1px solid #2A2A40;
                     color:#6B6B8A'>💻 Slow computer</span>
        <span style='font-size:0.72rem;font-family:monospace;
                     padding:4px 12px;border-radius:20px;
                     background:#1A1A28;border:1px solid #2A2A40;
                     color:#6B6B8A'>🖨️ Printer offline</span>
    </div>
    """, unsafe_allow_html=True)

    # Input form
    with st.form("chat_form", clear_on_submit=False):
        user_query = st.text_area(
            "",
            placeholder = "what's going on with your machine... (be specific, it helps)",
            height      = 100,
            label_visibility = "collapsed"
        )
        col1, col2 = st.columns([1, 5])
        with col1:
            submitted = st.form_submit_button(
                "⚡ Get Fix",
                type = "primary",
                use_container_width = True
            )

    if submitted and user_query.strip():
        st.session_state["show_ticket"]    = False
        st.session_state["feedback_given"] = False

        with st.spinner("🔍 classifying · retrieving · generating..."):
            result = query_api(user_query.strip())

        if result["success"]:
            st.session_state["last_result"] = {
                "query" : user_query.strip(),
                "data"  : result["data"]
            }
            st.session_state["history"].append({
                "query"  : user_query.strip(),
                "intent" : result["data"]["predicted_intent"]
            })
        else:
            st.error(f"❌ {result['error']}")

    elif submitted:
        st.warning("⚠️ type something first")

    # ── Result display ──
    if st.session_state["last_result"]:
        res  = st.session_state["last_result"]
        data = res["data"]
        q    = res["query"]

        conf    = data["confidence"]
        intent  = data["intent"] if "intent" in data else data["predicted_intent"]
        escalate = data["should_escalate"]

        # User bubble
        st.markdown(f"""
        <div style='display:flex;justify-content:flex-end;
                    margin:1rem 0 0.5rem 0'>
            <div style='max-width:70%;
                        background:linear-gradient(135deg,#7C5CFC,#5C3DFC);
                        border-radius:12px 4px 12px 12px;
                        padding:0.85rem 1.1rem;
                        font-size:0.88rem;line-height:1.6;color:white'>
                {q}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Intent + confidence bar
        if conf >= 75:
            bar_color = "#5CFC8A"
            conf_label = "high confidence"
            badge_style = "background:#5CFC8A22;color:#5CFC8A;border:1px solid #5CFC8A44"
        elif conf >= 60:
            bar_color = "#FCE05C"
            conf_label = "medium confidence"
            badge_style = "background:#FCE05C22;color:#FCE05C;border:1px solid #FCE05C44"
        else:
            bar_color = "#FC5C7D"
            conf_label = "low — escalating"
            badge_style = "background:#FC5C7D22;color:#FC5C7D;border:1px solid #FC5C7D44"

        intent_clean = intent.replace("_", " ").title()
        bar_width    = min(int(conf), 100)

        st.markdown(f"""
        <div style='display:flex;align-items:center;gap:10px;
                    margin-bottom:0.8rem;flex-wrap:wrap'>
            <span style='font-size:0.78rem;font-family:monospace;
                         color:#7C5CFC;
                         background:#7C5CFC18;border:1px solid #7C5CFC44;
                         padding:3px 10px;border-radius:20px'>
                {intent_clean}
            </span>
            <div style='display:flex;align-items:center;gap:8px'>
                <div style='width:100px;height:4px;background:#2A2A40;
                            border-radius:2px;overflow:hidden'>
                    <div style='width:{bar_width}%;height:100%;
                                background:{bar_color};border-radius:2px'></div>
                </div>
                <span style='font-size:0.72rem;font-family:monospace;
                             color:#6B6B8A'>{conf:.1f}%</span>
            </div>
            <span style='font-size:0.72rem;font-family:monospace;
                         padding:3px 10px;border-radius:20px;{badge_style}'>
                {conf_label}
            </span>
        </div>
        """, unsafe_allow_html=True)

        # Solution or escalation
        if escalate:
            st.markdown(f"""
            <div style='background:#FC5C7D11;border:1px solid #FC5C7D33;
                        border-left:3px solid #FC5C7D;
                        border-radius:0 10px 10px 0;
                        padding:1rem 1.2rem;margin-bottom:1rem;
                        font-size:0.85rem;line-height:1.6;color:#F0F0FF'>
                ⚠️ <strong>routing to support engineer</strong><br>
                <span style='color:#6B6B8A'>{data.get('escalation_reason','Confidence too low for automated fix.')}</span>
            </div>
            """, unsafe_allow_html=True)
            st.session_state["show_ticket"] = True

        else:
            # AI solution card
            solution = data["ai_solution"]
            lines    = solution.strip().split("\n")
            steps_html = ""
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                import re
                m = re.match(r'^(\d+)[.)]\s+(.*)', line)
                if m:
                    num, text = m.group(1), m.group(2)
                    steps_html += f"""
                    <div style='display:flex;gap:10px;
                                margin-bottom:0.65rem;align-items:flex-start'>
                        <div style='width:22px;height:22px;border-radius:6px;
                                    background:#7C5CFC22;color:#7C5CFC;
                                    font-size:0.7rem;font-family:monospace;
                                    font-weight:600;flex-shrink:0;
                                    display:flex;align-items:center;
                                    justify-content:center'>{num}</div>
                        <div style='font-size:0.85rem;color:#C8C8E8;
                                    line-height:1.6'>{text}</div>
                    </div>"""
                else:
                    steps_html += f"""
                    <div style='font-size:0.85rem;color:#C8C8E8;
                                line-height:1.6;margin-bottom:0.5rem'>
                        {line}
                    </div>"""

            st.markdown(f"""
            <div style='background:#1A1A28;border:1px solid #2A2A40;
                        border-radius:14px;overflow:hidden;
                        margin-bottom:0.5rem'>
                <div style='background:#1E1E30;border-bottom:1px solid #2A2A40;
                            padding:0.75rem 1rem;display:flex;
                            align-items:center;justify-content:space-between'>
                    <span style='font-size:0.78rem;font-family:monospace;
                                 color:#7C5CFC'>💡 ai solution</span>
                    <span style='font-size:0.7rem;font-family:monospace;
                                 color:#6B6B8A'>gemini-2.0-flash-lite</span>
                </div>
                <div style='padding:1rem'>
                    {steps_html}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Similar tickets
            similar = data.get("similar_tickets", [])
            if similar:
                with st.expander(f"📂 {len(similar)} similar tickets retrieved", expanded=False):
                    for t in similar:
                        score  = t['similarity'] * 100
                        ic     = t['intent'].replace('_',' ').title()
                        st.markdown(f"""
                        <div style='background:#12121A;border:1px solid #2A2A40;
                                    border-radius:8px;padding:0.75rem;
                                    margin-bottom:0.5rem;font-size:0.82rem'>
                            <div style='display:flex;justify-content:space-between;
                                        margin-bottom:0.3rem'>
                                <span style='font-family:monospace;color:#7C5CFC'>
                                    #{t['ticket_id']} · {ic}
                                </span>
                                <span style='font-family:monospace;
                                             color:#5CFC8A;font-size:0.75rem'>
                                    {score:.1f}% match
                                </span>
                            </div>
                            <div style='color:#6B6B8A;margin-bottom:0.2rem'>
                                {t['user_query']}
                            </div>
                            <div style='color:#C8C8E8'>
                                {t['solution'][:160]}...
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

            # Feedback
            if not st.session_state["feedback_given"]:
                st.markdown("""
                <div style='font-size:0.8rem;color:#6B6B8A;
                            margin:0.8rem 0 0.4rem 0'>
                    did this fix it?
                </div>
                """, unsafe_allow_html=True)
                c1, c2, c3 = st.columns([1, 1, 5])
                with c1:
                    if st.button("✅ fixed it", key="solved"):
                        from api_client import submit_feedback
                        submit_feedback(q, True, intent, solution)
                        st.session_state["feedback_given"] = True
                        st.success("nice! glad that worked 🎉")
                        st.rerun()
                with c2:
                    if st.button("❌ still broken", key="not_solved"):
                        from api_client import submit_feedback
                        submit_feedback(q, False, intent, solution)
                        st.session_state["feedback_given"] = True
                        st.session_state["show_ticket"]    = True
                        st.rerun()

        # Ticket form
        if st.session_state["show_ticket"]:
            st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
            st.markdown("""
            <div style='font-size:1rem;font-weight:600;margin-bottom:0.8rem'>
                🎫 create support ticket
            </div>
            """, unsafe_allow_html=True)

            from ticket_form import render_ticket_form
            render_ticket_form(
                user_query       = q,
                predicted_intent = intent,
                ai_suggestions   = data["ai_solution"]
            )


# ════════════════════════════════════
# PAGE 2 — History
# ════════════════════════════════════
elif page == "📋 History":
    st.markdown("""
    <h2 style='font-size:1.4rem;font-weight:700;
               letter-spacing:-0.03em;margin-bottom:1rem'>
        session history 📋
    </h2>
    """, unsafe_allow_html=True)

    if not st.session_state["history"]:
        st.markdown("""
        <div style='background:#1A1A28;border:1px solid #2A2A40;
                    border-radius:12px;padding:2rem;text-align:center;
                    color:#6B6B8A;font-size:0.88rem'>
            nothing here yet — go break something 🤷
        </div>
        """, unsafe_allow_html=True)
    else:
        for i, item in enumerate(reversed(st.session_state["history"]), 1):
            ic = item["intent"].replace("_", " ").title()
            st.markdown(f"""
            <div style='background:#1A1A28;border:1px solid #2A2A40;
                        border-radius:10px;padding:0.8rem 1rem;
                        margin-bottom:0.5rem;
                        display:flex;justify-content:space-between;
                        align-items:center'>
                <span style='font-size:0.85rem'>{i}. {item['query']}</span>
                <span style='font-size:0.72rem;font-family:monospace;
                             color:#7C5CFC;background:#7C5CFC18;
                             border:1px solid #7C5CFC44;
                             padding:2px 9px;border-radius:20px'>
                    {ic}
                </span>
            </div>
            """, unsafe_allow_html=True)


# ════════════════════════════════════
# PAGE 3 — Tickets
# ════════════════════════════════════
elif page == "🎫 Tickets":
    st.markdown("""
    <h2 style='font-size:1.4rem;font-weight:700;
               letter-spacing:-0.03em;margin-bottom:1rem'>
        open tickets 🎫
    </h2>
    """, unsafe_allow_html=True)

    with st.spinner("loading..."):
        result = get_tickets()

    if result["success"]:
        tickets = result["data"].get("tickets", [])
        total   = result["data"].get("total", 0)

        c1, c2, c3 = st.columns(3)
        c1.metric("Total tickets", total)
        c2.metric("Open", total)
        c3.metric("Resolved", 0)

        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

        if not tickets:
            st.markdown("""
            <div style='background:#1A1A28;border:1px solid #2A2A40;
                        border-radius:12px;padding:2rem;text-align:center;
                        color:#6B6B8A;font-size:0.88rem'>
                no open tickets 🎉
            </div>
            """, unsafe_allow_html=True)
        else:
            for t in tickets:
                ic = (t["predicted_intent"] or "unknown").replace("_"," ").title()
                with st.expander(
                    f"#{t['id']} · {ic} · {t['status'].upper()}"
                ):
                    st.markdown(f"""
                    <div style='font-size:0.85rem;line-height:1.8'>
                        <div><span style='color:#6B6B8A'>Issue: </span>{t['user_query']}</div>
                        <div><span style='color:#6B6B8A'>Category: </span>
                             <span style='font-family:monospace;color:#7C5CFC'>{ic}</span>
                        </div>
                        <div><span style='color:#6B6B8A'>Created: </span>
                             <span style='font-family:monospace;font-size:0.78rem'>
                             {t['created_at']}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.error(f"failed to load tickets: {result['error']}")