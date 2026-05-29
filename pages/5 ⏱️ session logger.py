"""
pages/5_⏱️_Session_Logger.py — InfoTech Study Companion
Log daily study sessions with subject, duration, and notes.
Every save writes to SQLite immediately.
"""

import streamlit as st
import pandas as pd
from datetime import date, datetime
from database import (
    initialise_database, get_student, get_all_chapter_progress,
    log_session, get_sessions, get_hours_per_subject, delete_session
)

st.set_page_config(page_title="Session Logger", page_icon="⏱️", layout="centered")

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
st.session_state["student_profile"]   = db_profile
st.session_state["active_student_id"] = sid
st.session_state["completed_chapters"] = get_all_chapter_progress(sid)

# ── Page header ────────────────────────────────────────────────────────────────
st.markdown("<h1 style='color:#00FF87;'>⏱️ Session Logger</h1>", unsafe_allow_html=True)
st.write(f"Record every study block, **{db_profile['name']}**. Your hours are saved permanently.")
st.write("---")

# ── Quick stats row ────────────────────────────────────────────────────────────
try:
    hours_data  = get_hours_per_subject(sid)
    total_hours = sum(r["total_hours"] for r in hours_data)
    sessions    = get_sessions(sid, limit=200)
    total_sess  = len(sessions)
except RuntimeError as e:
    st.error(str(e))
    hours_data, total_hours, sessions, total_sess = [], 0, [], 0

k1, k2 = st.columns(2)
k1.metric("⏱️ Total Hours Studied", f"{total_hours:.1f} h")
k2.metric("📝 Total Sessions",       total_sess)

st.write("---")

# ── Log new session form ───────────────────────────────────────────────────────
st.markdown("### ➕ Log a New Session")

if not subjects:
    st.warning("No subjects in your profile. Please update your profile first.")
    if st.button("✏️ Edit Profile"):
        st.switch_page("pages/1_👤_Profile.py")
    st.stop()

with st.form("session_form", clear_on_submit=True):
    f1, f2 = st.columns(2)
    with f1:
        selected_subject = st.selectbox("Subject", subjects)
    with f2:
        session_date = st.date_input("Date", value=date.today(), max_value=date.today())

    f3, f4 = st.columns(2)
    with f3:
        hours_input = st.number_input("Hours",   min_value=0, max_value=12, value=1, step=1)
    with f4:
        mins_input  = st.number_input("Minutes", min_value=0, max_value=59, value=0, step=5)

    notes = st.text_area("Notes / Topics Covered", placeholder="e.g. Completed Chapter 3 — Quadratic Equations. Struggled with discriminant section.", height=80)
    save  = st.form_submit_button("💾 Save Session", use_container_width=True)

if save:
    total_mins = hours_input * 60 + mins_input
    if total_mins < 1:
        st.warning("Duration must be at least 1 minute.")
    else:
        try:
            log_session(
                student_id   = sid,
                subject      = selected_subject,
                session_date = session_date.isoformat(),
                duration_mins= total_mins,
                notes        = notes,
            )
            st.success(f"✅ {hours_input}h {mins_input}m on **{selected_subject}** saved!")
            st.rerun()
        except RuntimeError as e:
            st.error(f"🚨 {e}")

st.write("---")

# ── Hours per subject bar chart ────────────────────────────────────────────────
if hours_data:
    st.markdown("### 📊 Hours Per Subject")
    df_hrs = pd.DataFrame(hours_data)[["subject","total_hours"]].rename(
        columns={"subject":"Subject","total_hours":"Hours"}
    )
    st.bar_chart(df_hrs.set_index("Subject"), color="#00FF87")
    st.write("---")

# ── Recent sessions table ──────────────────────────────────────────────────────
st.markdown("### 📋 Recent Sessions")
if not sessions:
    st.info("No sessions logged yet. Use the form above to start tracking.")
else:
    df = pd.DataFrame(sessions)[["session_date","subject","duration_mins","notes"]]
    df["Hours"] = (df["duration_mins"] / 60).round(2)
    df = df.rename(columns={
        "session_date":"Date","subject":"Subject",
        "duration_mins":"Mins","notes":"Notes"
    })[["Date","Subject","Hours","Mins","Notes"]]
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Delete a session
    with st.expander("🗑️ Delete a session"):
        del_options = {
            f"{s['session_date']} | {s['subject']} | {s['duration_mins']} min": s["id"]
            for s in sessions
        }
        chosen = st.selectbox("Select session to delete", list(del_options.keys()))
        if st.button("Delete Selected Session"):
            try:
                delete_session(del_options[chosen])
                st.success("Session deleted.")
                st.rerun()
            except RuntimeError as e:
                st.error(str(e))