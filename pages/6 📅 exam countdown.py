"""
pages/6_📅_Exam_Countdown.py — InfoTech Study Companion
Schedule exams, see colour-coded countdowns, record achieved marks.
"""

import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from database import (
    initialise_database, get_student, get_all_chapter_progress,
    add_exam, get_exams, get_upcoming_exams,
    mark_exam_done, delete_exam
)

st.set_page_config(page_title="Exam Countdown", page_icon="📅", layout="centered")

if "db_ready" not in st.session_state:
    try:
        initialise_database()
        st.session_state["db_ready"] = True
    except RuntimeError as e:
        st.error(f"🚨 {e}")
        st.stop()

try:
    db_profile = get_student()
except RuntimeError as e:
    st.error(f"🚨 {e}")
    st.stop()

if not db_profile:
    st.warning("⚠️ No active profile detected. Please log in first.")
    if st.button("🏠 Go to Homepage"):
        st.switch_page("app.py")
    st.stop()

sid      = db_profile["id"]
subjects = db_profile["subjects"]
st.session_state["student_profile"]    = db_profile
st.session_state["active_student_id"]  = sid
st.session_state["completed_chapters"] = get_all_chapter_progress(sid)

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("<h1 style='color:#00FF87;'>📅 Exam Countdown</h1>", unsafe_allow_html=True)
st.write(f"Schedule your assessments, **{db_profile['name']}**, and never be caught off guard.")
st.write("---")

# ── Add exam form ──────────────────────────────────────────────────────────────
st.markdown("### ➕ Schedule an Exam or Assessment")
with st.form("add_exam_form", clear_on_submit=True):
    e1, e2 = st.columns(2)
    with e1:
        exam_subject = st.selectbox("Subject", subjects if subjects else ["— add subjects to profile first —"])
    with e2:
        exam_label = st.text_input("Assessment Name", placeholder="e.g. Term 2 Test, Final Exam")

    e3, e4 = st.columns(2)
    with e3:
        exam_date = st.date_input("Exam Date", value=date.today() + timedelta(days=14),
                                  min_value=date.today())
    with e4:
        weight_pct = st.number_input("Weight / Mark (%) — optional", min_value=0.0,
                                     max_value=100.0, value=0.0, step=1.0)

    add_btn = st.form_submit_button("📌 Add to Calendar", use_container_width=True)

if add_btn:
    if not subjects:
        st.error("⚠️ Add subjects to your profile first.")
    elif not exam_label.strip():
        st.error("⚠️ Please give this assessment a name.")
    else:
        try:
            add_exam(sid, exam_subject, exam_label, exam_date.isoformat(), weight_pct)
            st.success(f"✅ '{exam_label}' added for {exam_date.strftime('%d %b %Y')}!")
            st.rerun()
        except RuntimeError as e:
            st.error(str(e))

st.write("---")

# ── Upcoming countdowns ────────────────────────────────────────────────────────
st.markdown("### ⏳ Upcoming Assessments")
try:
    upcoming = get_upcoming_exams(sid)
except RuntimeError as e:
    st.error(str(e))
    upcoming = []

today = date.today()

if not upcoming:
    st.info("No upcoming assessments yet. Schedule one above!")
else:
    for ex in upcoming:
        exam_dt   = datetime.strptime(ex["exam_date"], "%Y-%m-%d").date()
        days_left = (exam_dt - today).days

        if days_left <= 3:
            bar_colour, urgency_label, urgency_icon = "#FF4B4B", "URGENT", "🔴"
        elif days_left <= 7:
            bar_colour, urgency_label, urgency_icon = "#FFA500", "THIS WEEK", "🟡"
        elif days_left <= 14:
            bar_colour, urgency_label, urgency_icon = "#FFD700", "COMING UP", "🟡"
        else:
            bar_colour, urgency_label, urgency_icon = "#00FF87", "SCHEDULED", "🟢"

        weight_str = f" • {ex['weight_pct']:.0f}%" if ex["weight_pct"] > 0 else ""

        st.markdown(
            f"<div style='background:#1F2635;padding:16px;border-radius:10px;"
            f"border-left:6px solid {bar_colour};margin-bottom:14px;'>"
            f"<div style='display:flex;justify-content:space-between;align-items:flex-start;'>"
            f"<div>"
            f"<span style='font-size:11px;color:{bar_colour};font-weight:700;letter-spacing:.08em;'>"
            f"{urgency_icon} {urgency_label}{weight_str}</span>"
            f"<h4 style='margin:4px 0 2px;color:#fff;'>{ex['exam_label']}</h4>"
            f"<p style='margin:0;color:#A0AABF;font-size:13px;'>{ex['subject']} &nbsp;•&nbsp; {exam_dt.strftime('%A, %d %B %Y')}</p>"
            f"</div>"
            f"<div style='text-align:right;min-width:70px;'>"
            f"<span style='font-size:36px;font-weight:900;color:{bar_colour};line-height:1;'>{days_left}</span><br>"
            f"<span style='font-size:11px;color:#A0AABF;'>days left</span>"
            f"</div></div></div>",
            unsafe_allow_html=True
        )

        # Inline mark recording + delete
        mc1, mc2, mc3 = st.columns([3, 2, 1])
        with mc1:
            mark_key = f"mark_{ex['id']}"
            achieved = st.number_input("Record achieved mark (%)", 0.0, 100.0, 0.0,
                                       step=0.5, key=mark_key,
                                       label_visibility="collapsed")
        with mc2:
            if st.button("✅ Mark as Done", key=f"done_{ex['id']}", use_container_width=True):
                try:
                    mark_exam_done(ex["id"], achieved)
                    st.success("Marked complete!")
                    st.rerun()
                except RuntimeError as e:
                    st.error(str(e))
        with mc3:
            if st.button("🗑️", key=f"del_{ex['id']}", use_container_width=True):
                try:
                    delete_exam(ex["id"])
                    st.rerun()
                except RuntimeError as e:
                    st.error(str(e))

st.write("---")

# ── Completed exams table ──────────────────────────────────────────────────────
st.markdown("### 🏆 Completed Assessments")
try:
    all_exams = get_exams(sid)
except RuntimeError as e:
    st.error(str(e))
    all_exams = []

completed = [e for e in all_exams if e["status"] == "Completed"]

if not completed:
    st.info("No completed assessments yet — they'll appear here once you mark them done.")
else:
    rows = []
    for e in completed:
        rows.append({
            "Subject":   e["subject"],
            "Assessment": e["exam_label"],
            "Date":       e["exam_date"],
            "Weight %":   e["weight_pct"],
            "Achieved %": e["achieved_pct"] if e["achieved_pct"] is not None else "—",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)