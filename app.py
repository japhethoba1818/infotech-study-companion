"""
app.py — InfoTech Study Companion  (v2)
Home dashboard. Shows live stats once a profile exists.
"""

import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from database import (
    initialise_database, get_student, delete_student, backup_database,
    get_study_streak, get_overall_completion, get_upcoming_exams,
    get_hours_per_subject, get_daily_study_trend, DB_PATH
)

st.set_page_config(page_title="InfoTech Study Companion", page_icon="🎓", layout="centered")

# ── DB boot ────────────────────────────────────────────────────────────────────
if "db_ready" not in st.session_state:
    try:
        initialise_database()
        st.session_state["db_ready"] = True
    except RuntimeError as e:
        st.error(f"🚨 Could not initialise database: {e}")
        st.stop()

# ── Sync from DB ───────────────────────────────────────────────────────────────
try:
    db_profile = get_student()
except RuntimeError as e:
    st.error(f"🚨 Database read error: {e}")
    st.stop()

if db_profile:
    st.session_state["student_profile"]   = db_profile
    st.session_state["active_student_id"] = db_profile["id"]
else:
    st.session_state["student_profile"]   = None
    st.session_state["active_student_id"] = None

# ── Hero header ────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;margin-bottom:20px;">
    <h1 style='color:#00FF87;font-size:36px;font-weight:800;margin-bottom:5px;'>
        🎓 InfoTech Study Companion
    </h1>
    <p style='color:#A0AABF;font-size:16px;font-weight:300;'>
        Your Digital AI Study Mentor • Built for South African High School Excellence
    </p>
</div>
""", unsafe_allow_html=True)

profile = st.session_state.get("student_profile")

# ══════════════════════════════════════════════════════
# NO PROFILE — first-time visitor
# ══════════════════════════════════════════════════════
if not profile or not profile.get("name"):
    st.image(
        "https://images.unsplash.com/photo-1577896851231-70ef18881754?auto=format&fit=crop&q=80&w=800",
        caption="Dumela! Map out your subjects, manage your focus hours, and achieve your matric dreams.",
        use_container_width=True,
    )
    st.write("---")
    st.info("👋 Welcome! No profile found. Create yours to get started.")
    if st.button("✨ Create Student Profile", use_container_width=True):
        st.switch_page("pages/1_👤_Profile.py")
    st.stop()

# ══════════════════════════════════════════════════════
# ACTIVE PROFILE — live dashboard
# ══════════════════════════════════════════════════════
sid = db_profile["id"]

st.success(f"👋 Welcome back, **{profile['name']}**!  |  {profile['grade']}  |  Dream: *{profile.get('dream_job','—')}*")

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
        exam_dt = datetime.strptime(ex["exam_date"], "%Y-%m-%d").date()
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
            unsafe_allow_html=True
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
n1, n2, n3, n4 = st.columns(4)
with n1:
    if st.button("🧘 Pre-Study", use_container_width=True):
        st.switch_page("pages/2_🧘_Pre-Study_Routine.py")
with n2:
    if st.button("⏱️ Log Session", use_container_width=True):
        st.switch_page("pages/5_⏱️_Session_Logger.py")
with n3:
    if st.button("📅 Exam Countdown", use_container_width=True):
        st.switch_page("pages/6_📅_Exam_Countdown.py")
with n4:
    if st.button("🤖 AI Study Plan", use_container_width=True):
        st.switch_page("pages/7_🤖_AI_Study_Plan.py")

st.write("---")

# ── Account management ──────────────────────────────────────────────────────────
with st.expander("⚙️ Account & Data Management"):
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("✏️ Edit Profile", use_container_width=True):
            st.switch_page("pages/1_👤_Profile.py")
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
        st.warning("⚠️ This permanently erases ALL your data. Are you sure?")
        y, n = st.columns(2)
        with y:
            if st.button("✅ Yes, delete everything", use_container_width=True):
                try:
                    delete_student()
                    st.session_state.clear()
                    st.rerun()
                except RuntimeError as e:
                    st.error(str(e))
        with n:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state["confirm_delete"] = False
                st.rerun()

    st.caption(f"🗄️ DB location: `{DB_PATH}`")