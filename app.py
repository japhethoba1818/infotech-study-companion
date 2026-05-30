"""
app.py — InfoTech Study Companion  (v3)
Home dashboard. Requires authenticated session.
"""

import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from auth import boot_auth, require_login, logout_user, current_username
from database import (
    initialise_database, get_student, delete_student, delete_user_account,
    backup_database, get_study_streak, get_overall_completion,
    get_upcoming_exams, get_hours_per_subject, get_daily_study_trend, DB_PATH
)

st.set_page_config(
    page_title="InfoTech Study Companion",
    page_icon="🎓",
    layout="centered",
)

# ── Auth guard — redirects to login page if not authenticated ──────────────────
user_id = require_login()

# ── Load student profile (scoped to THIS user) ─────────────────────────────────
try:
    db_profile = get_student(user_id)
except RuntimeError as e:
    st.error(f"🚨 Database read error: {e}")
    st.stop()

st.session_state["student_profile"]   = db_profile
st.session_state["active_student_id"] = db_profile["id"] if db_profile else None

# ── Hero header ────────────────────────────────────────────────────────────────
col_title, col_logout = st.columns([5, 1])
with col_title:
    st.markdown("""
    <div style="margin-bottom:10px;">
        <h1 style='color:#00FF87;font-size:34px;font-weight:800;margin-bottom:4px;'>
            🎓 InfoTech Study Companion
        </h1>
        <p style='color:#A0AABF;font-size:14px;font-weight:300;margin:0;'>
            Your Digital AI Study Mentor • Built for South African High School Excellence
        </p>
    </div>
    """, unsafe_allow_html=True)
with col_logout:
    st.write("")
    st.write("")
    if st.button("🚪 Logout", use_container_width=True):
        logout_user()
        st.switch_page("pages/0_Login.py")

profile = st.session_state.get("student_profile")

# ══════════════════════════════════════════════════════
# NO STUDENT PROFILE YET — first-time after account creation
# ══════════════════════════════════════════════════════
if not profile or not profile.get("name"):
    username = current_username()
    st.info(f"👋 Hey **{username}**! You're logged in. Now let's set up your student profile.")
    if st.button("✨ Create Student Profile", use_container_width=True):
        st.switch_page("pages/1_Profile.py")
    st.stop()

# ══════════════════════════════════════════════════════
# ACTIVE PROFILE — live dashboard
# ══════════════════════════════════════════════════════
sid = db_profile["id"]

st.success(
    f"👋 Welcome back, **{profile['name']}**!  |  {profile['grade']}  |  "
    f"Dream: *{profile.get('dream_job', '—')}*"
)

st.write("---")

# ── KPI row ────────────────────────────────────────────────────────────────────
try:
    streak      = get_study_streak(sid)
    overall_pct = get_overall_completion(sid)
    upcoming    = get_upcoming_exams(sid)
    hours_data  = get_hours_per_subject(sid)
    total_hours = sum(r["total_hours"] for r in hours_data)
except RuntimeError as e:
    st.error(str(e))
    st.stop()

k1, k2, k3, k4 = st.columns(4)
k1.metric("🔥 Study Streak",      f"{streak} day{'s' if streak != 1 else ''}")
k2.metric("📚 Syllabus Complete",  f"{overall_pct:.1f}%")
k3.metric("⏱️ Total Hours Logged", f"{total_hours:.1f} h")
k4.metric("📅 Upcoming Exams",     len(upcoming))

st.write("---")

# ── Upcoming exam countdowns ───────────────────────────────────────────────────
st.markdown("### 📅 Exam Countdown")
if not upcoming:
    st.info("No upcoming exams scheduled. Add them in the **Exam Countdown** page.")
else:
    today = date.today()
    for ex in upcoming[:5]:
        exam_dt   = datetime.strptime(ex["exam_date"], "%Y-%m-%d").date()
        days_left = (exam_dt - today).days
        if days_left <= 3:
            colour, icon = "#FF4B4B", "🔴"
        elif days_left <= 7:
            colour, icon = "#FFA500", "🟡"
        else:
            colour, icon = "#00FF87", "🟢"
        st.markdown(
            f"<div style='background:#1F2635;padding:12px 16px;border-radius:8px;"
            f"border-left:5px solid {colour};margin-bottom:10px;display:flex;"
            f"justify-content:space-between;align-items:center;'>"
            f"<div><span style='font-size:13px;color:{colour};font-weight:700;'>"
            f"{icon} {ex['subject']}</span>"
            f"<p style='margin:2px 0 0;color:#fff;font-size:15px;font-weight:600;'>"
            f"{ex['exam_label']}</p></div>"
            f"<div style='text-align:right;'>"
            f"<span style='font-size:28px;font-weight:800;color:{colour};'>{days_left}</span>"
            f"<span style='color:#A0AABF;font-size:12px;'> days</span></div></div>",
            unsafe_allow_html=True,
        )

st.write("---")

# ── Study trend chart ──────────────────────────────────────────────────────────
st.markdown("### 📈 Study Activity — Last 14 Days")
try:
    trend = get_daily_study_trend(sid, days=14)
except RuntimeError as e:
    st.error(str(e))
    trend = []

if trend:
    df_trend = pd.DataFrame(trend)
    df_trend["hours"] = (df_trend["total_mins"] / 60).round(2)
    df_trend = df_trend.rename(columns={"session_date": "Date", "hours": "Hours"})
    st.bar_chart(df_trend.set_index("Date")[["Hours"]], color="#00FF87")
else:
    st.info("No study sessions logged yet. Head to **Session Logger** to start tracking.")

st.write("---")

# ── Hours per subject breakdown ────────────────────────────────────────────────
if hours_data:
    st.markdown("### 📊 Hours Per Subject")
    df_hrs = pd.DataFrame(hours_data)[["subject", "total_hours"]].rename(
        columns={"subject": "Subject", "total_hours": "Hours"}
    )
    st.bar_chart(df_hrs.set_index("Subject"), color="#00FF87")

st.write("---")

# ── Navigation row ─────────────────────────────────────────────────────────────
st.markdown("### 🚀 Quick Navigation")
n1, n2, n3 = st.columns(3)
with n1:
    if st.button("🧘 Pre-Study", use_container_width=True):
        st.switch_page("pages/2_Pre_Study_Routine.py")
with n2:
    if st.button("⏱️ Log Session", use_container_width=True):
        st.switch_page("pages/5_Session_Logger.py")
with n3:
    if st.button("📅 Exam Countdown", use_container_width=True):
        st.switch_page("pages/6_Exam_Countdown.py")

st.write("---")

# ── Account management ──────────────────────────────────────────────────────────
with st.expander("⚙️ Account & Data Management"):
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("✏️ Edit Profile", use_container_width=True):
            st.switch_page("pages/1_Profile.py")
    with c2:
        if st.button("💾 Backup Data", use_container_width=True):
            try:
                path = backup_database()
                st.success(f"Backup saved: `{path}`")
            except Exception as e:
                st.error(str(e))
    with c3:
        if st.button("🗑️ Delete Profile", use_container_width=True, type="secondary"):
            st.session_state["confirm_delete"] = True

    if st.session_state.get("confirm_delete"):
        st.warning("⚠️ This permanently erases your student profile and ALL study data.")
        y, n = st.columns(2)
        with y:
            if st.button("✅ Yes, delete my profile data", use_container_width=True):
                try:
                    delete_student(user_id)
                    st.session_state.pop("student_profile", None)
                    st.session_state.pop("active_student_id", None)
                    st.session_state.pop("completed_chapters", None)
                    st.session_state["confirm_delete"] = False
                    st.success("Profile data deleted. Your login account still exists.")
                    st.rerun()
                except RuntimeError as e:
                    st.error(str(e))
        with n:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state["confirm_delete"] = False
                st.rerun()

    st.write("---")
    # Full account deletion
    if st.button("💀 Delete ENTIRE account (unrecoverable)", type="secondary", use_container_width=True):
        st.session_state["confirm_delete_account"] = True

    if st.session_state.get("confirm_delete_account"):
        st.error("⚠️ This will permanently delete your account, login credentials, and ALL data. There is NO undo.")
        ya, na = st.columns(2)
        with ya:
            if st.button("☠️ Yes, delete everything permanently", use_container_width=True):
                try:
                    delete_user_account(user_id)
                    logout_user()
                    st.switch_page("pages/0_Login.py")
                except RuntimeError as e:
                    st.error(str(e))
        with na:
            if st.button("❌ Cancel account deletion", use_container_width=True):
                st.session_state["confirm_delete_account"] = False
                st.rerun()

    st.caption(f"🗄️ DB location: `{DB_PATH}`")
    st.caption(f"👤 Logged in as: `{current_username()}` (user_id: {user_id})")