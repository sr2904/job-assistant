"""
app.py — AI Job Application Assistant
9-Agent Multi-Agent System
"""

import streamlit as st
import sys
import os
import re

sys.path.insert(0, os.path.dirname(__file__))
from agents.orchestrator import Orchestrator

st.set_page_config(
    page_title="AI Job Application Assistant",
    page_icon="🤝",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono&display=swap');
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

    .agent-card {
        background: #1a1d27; border: 1px solid #2d3148;
        border-radius: 12px; padding: 0.875rem 1.1rem; margin-bottom: 0.6rem;
    }
    .agent-card h4 { margin: 0 0 0.2rem 0; font-size: 0.85rem; font-weight: 600; color: #a5b4fc; }
    .agent-card p  { margin: 0; font-size: 0.75rem; color: #6b7280; line-height: 1.4; }

    .progress-step {
        display: flex; align-items: center; gap: 10px;
        padding: 10px 14px; border-radius: 8px; margin-bottom: 6px;
        font-size: 0.875rem; font-weight: 500;
    }
    .step-done    { background: #14532d22; color: #86efac; border: 1px solid #14532d; }
    .step-active  { background: #1e1b4b; color: #a5b4fc; border: 1px solid #4338ca; }
    .step-pending { background: #1a1d27; color: #4b5563; border: 1px solid #2d3148; }

    .match-card {
        background: #1a1d27; border: 1px solid #2d3148;
        border-radius: 12px; padding: 1rem 1.25rem; margin-bottom: 0.75rem;
    }
    .match-strong  { border-left: 4px solid #22c55e; }
    .match-partial { border-left: 4px solid #f59e0b; }
    .match-weak    { border-left: 4px solid #ef4444; }
    .match-missing { border-left: 4px solid #6b7280; }

    .badge-strong  { background:#14532d; color:#86efac; padding:2px 10px; border-radius:99px; font-size:0.7rem; font-weight:600; }
    .badge-partial { background:#713f12; color:#fde68a; padding:2px 10px; border-radius:99px; font-size:0.7rem; font-weight:600; }
    .badge-weak    { background:#7f1d1d; color:#fca5a5; padding:2px 10px; border-radius:99px; font-size:0.7rem; font-weight:600; }
    .badge-missing { background:#1f2937; color:#9ca3af; padding:2px 10px; border-radius:99px; font-size:0.7rem; font-weight:600; }

    .score-pill { display:inline-block; padding:3px 12px; border-radius:99px; font-size:0.75rem; font-weight:600; margin-right:6px; margin-bottom:4px; }
    .score-good { background:#14532d; color:#86efac; }
    .score-mid  { background:#713f12; color:#fde68a; }
    .score-bad  { background:#7f1d1d; color:#fca5a5; }

    .big-score {
        background: #1a1d27; border: 1px solid #2d3148;
        border-radius: 16px; padding: 1.5rem; text-align: center;
    }
    .big-score .num     { font-size: 3.5rem; font-weight: 700; line-height: 1; }
    .big-score .label   { font-size: 0.85rem; color: #6b7280; margin-top: 6px; }
    .big-score .verdict { font-size: 1rem; font-weight: 600; margin-top: 4px; }

    .sec-safe    { background:#14532d; color:#86efac; padding:2px 10px; border-radius:99px; font-size:0.75rem; font-weight:600; }
    .sec-flagged { background:#7f1d1d; color:#fca5a5; padding:2px 10px; border-radius:99px; font-size:0.75rem; font-weight:600; }
</style>
""", unsafe_allow_html=True)

# ── PDF Extraction ────────────────────────────────────────────────────────────
def extract_pdf_text(uploaded_file) -> tuple:
    """Returns (text, success, message)"""
    try:
        import pypdf
        import io
        pdf_reader = pypdf.PdfReader(io.BytesIO(uploaded_file.read()))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        text = text.strip()
        if len(text) > 100:
            return text[:4000], True, f"✅ Resume extracted ({len(text)} chars)"
        else:
            return "", False, "Could not extract text from this PDF. Please paste your background manually."
    except Exception as e:
        return "", False, f"PDF read error. Please paste your background manually."

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏗️ System Architecture")
    st.markdown("**9-Agent Pipeline**")
    agents_info = [
        ("🔒 Guardrails",      "Input validation & prompt injection protection"),
        ("🗺️ Planner",         "Decomposes task, sets strategy for all agents"),
        ("🔍 Researcher",      "Gathers company info, role context & news"),
        ("🛡️ Security",        "Scans every agent output for PII & violations"),
        ("🧠 Analyst",         "Analyzes fit following the Planner's strategy"),
        ("📊 Match Analyzer",  "Scores candidate against each JD requirement"),
        ("✍️ Writer",          "Drafts cover letter & bullets per plan"),
        ("🔎 Critic",          "Scores draft, negotiates revision with Writer"),
        ("🎯 Interview Prep",  "Generates likely questions & answer frameworks"),
        ("📧 Email Agent",     "Drafts professional follow-up email"),
    ]
    for name, desc in agents_info:
        st.markdown(f'<div class="agent-card"><h4>{name}</h4><p>{desc}</p></div>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("**Pattern:** Hierarchical + Sequential")
    st.markdown("**LLM:** Claude Sonnet (Anthropic)")
    st.markdown("**Framework:** Custom Python")
    st.markdown("**Hosting:** GCP Cloud Run")

# ── Main ──────────────────────────────────────────────────────────────────────
st.title("🤝 AI Job Application Assistant")
st.markdown("*A 9-agent system that plans, researches, analyzes, matches, writes, secures, critiques, and prepares you.*")
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### 📋 Job Description")
    job_description = st.text_area("JD", height=260,
        placeholder="Paste the full job posting here...", label_visibility="collapsed")

with col2:
    st.markdown("#### 👤 Your Background")
    input_method = st.radio("Input method", ["✍️ Type / Paste", "📄 Upload Resume PDF"],
        horizontal=True, label_visibility="collapsed")
    user_background = ""

    if input_method == "✍️ Type / Paste":
        user_background = st.text_area("Background", height=210,
            placeholder="Describe your experience, education, skills, and projects...",
            label_visibility="collapsed")
    else:
        uploaded_file = st.file_uploader("Upload resume PDF", type=["pdf"], label_visibility="collapsed")
        if uploaded_file:
            text, success, message = extract_pdf_text(uploaded_file)
            if success:
                user_background = text
                st.success(message)
                with st.expander("Preview extracted text"):
                    st.text(user_background[:600] + ("..." if len(user_background) > 600 else ""))
            else:
                st.warning(message)
                user_background = st.text_area("Your background (paste here)",
                    height=150, label_visibility="collapsed",
                    placeholder="Paste your background here...")

st.markdown("")
run_button = st.button("🚀 Run Multi-Agent Pipeline", type="primary", use_container_width=True)

# ── Pipeline ──────────────────────────────────────────────────────────────────
if run_button:
    if not job_description.strip() or not user_background.strip():
        st.error("Please fill in both the job description and your background.")
    else:
        # Clear previous results
        if "result" in st.session_state:
            del st.session_state["result"]

        st.markdown("---")
        st.markdown("### ⚙️ Pipeline Progress")

        STEPS = [
            ("🔒", "Guardrails"), ("🗺️", "Planner"), ("🛡️", "Security Check"),
            ("🔍", "Researcher"), ("🛡️", "Security Check"), ("🧠", "Analyst"),
            ("🛡️", "Security Check"), ("📊", "Match Analyzer"), ("✍️", "Writer"),
            ("🛡️", "Security Check"), ("🔎", "Critic"), ("🎯", "Interview Prep"), ("📧", "Email Agent"),
        ]

        progress_placeholder = st.empty()
        current_step = [0]

        def render_progress(current):
            html = ""
            for i, (icon, name) in enumerate(STEPS):
                if i < current:
                    cls, icon_show = "step-done", "✅"
                elif i == current:
                    cls, icon_show = "step-active", icon
                else:
                    cls, icon_show = "step-pending", icon
                html += f'<div class="progress-step {cls}">{icon_show} {name}</div>'
            progress_placeholder.markdown(html, unsafe_allow_html=True)

        render_progress(0)

        def update_status(msg: str):
            step_map = {
                "validating": 0, "planner": 1, "security": 2,
                "researcher": 3, "analyst": 5, "match": 7,
                "writer": 8, "critic": 10, "interview": 11, "email": 12, "complete": 13,
            }
            for keyword, step in step_map.items():
                if keyword.lower() in msg.lower():
                    current_step[0] = step
                    render_progress(step)
                    break

        with st.spinner(""):
            result = Orchestrator().run(
                job_description=job_description,
                user_background=user_background,
                status_callback=update_status
            )

        # Store result in session state so downloads don't trigger rerun
        st.session_state["result"] = result
        render_progress(len(STEPS))

# ── Results (from session state — survives download button clicks) ─────────────
if "result" in st.session_state:
    result = st.session_state["result"]

    if "error" in result:
        st.error(f"Pipeline error: {result['error']}")
    else:
        st.markdown("---")

        # ── Match Dashboard ───────────────────────────────────────────
        match_data = result.get("match_data", {})
        if match_data and "overall_score" in match_data:
            st.markdown("### 📊 Candidate Match Dashboard")

            score = match_data.get("overall_score", 0)
            verdict = match_data.get("overall_verdict", "")
            summary = match_data.get("summary", "")
            score_color = "#22c55e" if score >= 7 else "#f59e0b" if score >= 5 else "#ef4444"

            c1, c2, c3 = st.columns([1, 1, 1])
            with c2:
                st.markdown(f"""
                <div class="big-score">
                    <div class="num" style="color:{score_color}">{score}/10</div>
                    <div class="verdict" style="color:{score_color}">{verdict}</div>
                    <div class="label">{summary}</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("")

            requirements = match_data.get("requirements", [])
            if requirements:
                st.markdown("#### Requirement-by-Requirement Breakdown")
                for req in requirements:
                    level = req.get("match_level", "weak")
                    badge_class = f"badge-{level}"
                    card_class = f"match-{level}"
                    label = {"strong": "✅ Strong Match", "partial": "⚡ Partial Match",
                             "weak": "⚠️ Weak Match", "missing": "❌ Missing"}.get(level, level)
                    dots = "●" * req.get("score", 0) + "○" * (5 - req.get("score", 0))
                    st.markdown(f"""
                    <div class="match-card {card_class}">
                        <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:6px;">
                            <strong style="font-size:0.9rem; color:#e5e7eb">{req.get('requirement', '')}</strong>
                            <span class="{badge_class}">{label}</span>
                        </div>
                        <div style="font-size:0.8rem; color:#9ca3af; margin-bottom:4px;">📌 {req.get('candidate_evidence', 'No evidence found')}</div>
                        <div style="font-size:1rem; color:{score_color}; letter-spacing:2px">{dots}</div>
                    </div>
                    """, unsafe_allow_html=True)

            col_s, col_g = st.columns(2)
            with col_s:
                st.markdown("**🏆 Top Strengths**")
                for s in match_data.get("top_strengths", []):
                    st.markdown(f"✅ {s}")
            with col_g:
                st.markdown("**🎯 Key Gaps to Address**")
                for g in match_data.get("key_gaps", []):
                    st.markdown(f"⚠️ {g}")

            if match_data.get("recommendation"):
                st.info(f"💡 **Recommendation:** {match_data['recommendation']}")

            st.markdown("---")

        # ── Tabs ─────────────────────────────────────────────────────
        st.markdown("### 📋 Full Results")
        tabs = st.tabs(["📝 Application", "🎯 Interview Prep", "📧 Follow-up Email",
                        "🗺️ Plan", "🔍 Research", "🧠 Analysis", "🔎 Critic Log", "🛡️ Security Log"])

        with tabs[0]:
            st.markdown("#### Your Tailored Application")
            final = result.get("final_output", "")
            if "## RESUME BULLETS" in final:
                parts = final.split("## RESUME BULLETS")
                cover = parts[0].replace("## COVER LETTER", "").strip()
                bullets = parts[1].strip()
            else:
                cover, bullets = final, ""

            st.markdown("**Cover Letter**")
            st.markdown(cover)
            c1, c2 = st.columns(2)
            with c1:
                st.download_button("⬇️ Download Cover Letter", data=cover,
                    file_name="cover_letter.txt", mime="text/plain",
                    use_container_width=True, key="dl_cover")
            if bullets:
                st.markdown("---")
                st.markdown("**Resume Bullets**")
                st.markdown(bullets)
                with c2:
                    st.download_button("⬇️ Download Resume Bullets", data=bullets,
                        file_name="resume_bullets.txt", mime="text/plain",
                        use_container_width=True, key="dl_bullets")
            st.download_button("⬇️ Download Full Application", data=final,
                file_name="full_application.txt", mime="text/plain",
                use_container_width=True, key="dl_full")

        with tabs[1]:
            st.markdown("#### 🎯 Interview Preparation")
            st.markdown(result.get("interview_prep", "Not available."))

        with tabs[2]:
            st.markdown("#### 📧 Follow-up Email Draft")
            email_content = result.get("email_draft", "Not available.")
            st.markdown(email_content)
            st.download_button("⬇️ Download Email", data=email_content,
                file_name="followup_email.txt", mime="text/plain",
                use_container_width=True, key="dl_email")

        with tabs[3]:
            st.markdown("#### 🗺️ Planner Agent Strategy")
            st.markdown("*This is the plan all other agents followed*")
            st.markdown(result.get("plan", "Not available."))

        with tabs[4]:
            st.markdown("#### 🔍 Company & Role Research")
            st.markdown(result.get("research", "Not available."))

        with tabs[5]:
            st.markdown("#### 🧠 Fit Analysis")
            st.markdown(result.get("analysis", "Not available."))

        with tabs[6]:
            st.markdown("#### 🔎 Critic Agent Review Log")
            if result.get("critique_history"):
                for i, critique in enumerate(result["critique_history"]):
                    st.markdown(f"**Pass {i+1}**")
                    if critique.get("scores"):
                        scores_html = ""
                        for criterion, score in critique["scores"].items():
                            css = "score-good" if score >= 4 else ("score-mid" if score >= 3 else "score-bad")
                            scores_html += f'<span class="score-pill {css}">{criterion}: {score}/5</span>'
                        st.markdown(scores_html, unsafe_allow_html=True)
                    approved = critique.get("approved", False)
                    st.markdown(f"**Decision:** {'✅ Approved' if approved else '🔁 Revision requested'}")
                    if critique.get("summary"):
                        st.markdown(f"**Summary:** {critique['summary']}")
                    if critique.get("feedback"):
                        st.markdown(f"**Feedback to Writer:** {critique['feedback']}")
                    st.markdown("---")
            else:
                st.info("No critique history available.")

        with tabs[7]:
            st.markdown("#### 🛡️ Security Agent Log")
            if result.get("security_log"):
                for entry in result["security_log"]:
                    agent = entry.get("agent", "Unknown")
                    safe = entry.get("safe", True)
                    action = entry.get("action_taken", "approved")
                    badge = f'<span class="sec-safe">✅ {action}</span>' if safe else f'<span class="sec-flagged">⚠️ {action}</span>'
                    st.markdown(f"**{agent}** — {badge}", unsafe_allow_html=True)
                    for issue in entry.get("issues_found", []):
                        st.markdown(f"&nbsp;&nbsp;&nbsp;• {issue}")
            else:
                st.info("No security log available.")