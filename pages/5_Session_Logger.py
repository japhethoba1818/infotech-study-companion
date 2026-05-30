"""
pages/5_Session_Logger.py — InfoTech Study Companion  (v3)
Study session logger. Requires authenticated session.
"""

import streamlit as st
import pandas as pd
from datetime import date
from auth import require_login, logout_user
from database import (
    get_student, log_session, get_sessions, delete_session
)

st.set_page_config(page_title="Session Logger", page_icon="⏱️", layout="centered")

# ── Auth guard ─────────────────────────────────────────────────────────────────
user_id = require_login()

# ── Load profile for THIS user ─────────────────────────────────────────────────
try:
    db_profile = get_student(user_id)
except RuntimeError as e:
    st.error(f"🚨 Could not load profile: {e}")
    st.stop()

if not db_profile:
    st.warning("⚠️ No student profile found. Please create your profile first.")
    if st.button("👤 Create Profile"):
        st.switch_page("pages/1_Profile.py")
    st.stop()

student_id = db_profile["id"]
subjects   = db_profile["subjects"]

st.session_state["student_profile"]   = db_profile
st.session_state["active_student_id"] = student_id

# ── Page header ────────────────────────────────────────────────────────────────
col_h, col_out = st.columns([5, 1])
with col_h:
    st.markdown("<h1 style='color:#00FF87;'>⏱️ Study Session Logger</h1>", unsafe_allow_html=True)
with col_out:
    st.write("")
    st.write("")
    if st.button("🚪 Logout", use_container_width=True):
        logout_user()
        st.switch_page("pages/0_Login.py")

st.write(f"Track your study sessions, **{db_profile['name']}**. Every minute counts.")
st.write("---")

# ── Log new session ────────────────────────────────────────────────────────────
st.markdown("### ➕ Log a New Study Session")

if not subjects:
    st.warning("⚠️ No subjects in your profile. Add subjects first.")
    if st.button("✏️ Edit Profile"):
        st.switch_page("pages/1_Profile.py")
    st.stop()

with st.form("log_session_form", clear_on_submit=True):
    s1, s2 = st.columns(2)
    with s1:
        subject = st.selectbox("Subject", subjects)
    with s2:
        session_date = st.date_input("Date", value=date.today(), max_value=date.today())

    s3, s4 = st.columns(2)
    with s3:
        hours   = st.number_input("Hours", min_value=0, max_value=12, value=1, step=1)
    with s4:
        minutes = st.number_input("Minutes", min_value=0, max_value=59, value=0, step=5)

    notes   = st.text_area("Notes (optional)", placeholder="What did you cover today?", height=80)
    log_btn = st.form_submit_button("✅ Log Session", use_container_width=True, type="primary")

if log_btn:
    total_mins = hours * 60 + minutes
    if total_mins <= 0:
        st.error("⚠️ Session duration must be greater than 0 minutes.")
    else:
        try:
            log_session(student_id, subject, session_date.isoformat(), total_mins, notes)
            st.success(f"✅ Logged {hours}h {minutes}m of **{subject}** on {session_date.strftime('%d %b %Y')}!")
            st.rerun()
        except RuntimeError as e:
            st.error(str(e))

st.write("---")

# ── Recent sessions ────────────────────────────────────────────────────────────
st.markdown("### 📋 Recent Sessions")
try:
    sessions = get_sessions(student_id, limit=50)
except RuntimeError as e:
    st.error(str(e))
    sessions = []

if not sessions:
    st.info("No sessions logged yet. Use the form above to record your first session!")
else:
    for sesh in sessions:
        hrs  = sesh["duration_mins"] // 60
        mins = sesh["duration_mins"] % 60
        duration_str = f"{hrs}h {mins}m" if hrs > 0 else f"{mins}m"

        col_info, col_del = st.columns([5, 1])
        with col_info:
            st.markdown(
                f"<div style='background:#1F2635;padding:12px 16px;border-radius:8px;"
                f"border-left:4px solid #00FF87;margin-bottom:8px;'>"
                f"<span style='color:#00FF87;font-weight:700;font-size:13px;'>{sesh['subject']}</span>"
                f"<span style='color:#A0AABF;font-size:12px;'> &nbsp;•&nbsp; {sesh['session_date']} "
                f"&nbsp;•&nbsp; {duration_str}</span>"
                f"{'<p style=\"color:#ccc;font-size:13px;margin:4px 0 0;\">' + sesh['notes'] + '</p>' if sesh['notes'] else ''}"
                f"</div>",
                unsafe_allow_html=True,
            )
        with col_del:
            if st.button("🗑️", key=f"del_sess_{sesh['id']}", use_container_width=True):
                try:
                    # Ownership-safe delete: passes student_id so only this user's sessions can be deleted
                    delete_session(sesh["id"], student_id)
                    st.rerun()
                except RuntimeError as e:
                    st.error(str(e))