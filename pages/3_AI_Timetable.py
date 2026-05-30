"""
pages/3_AI_Timetable.py — InfoTech Study Companion  (v3)
Renders a personalised study timetable. Requires authenticated session.
"""

import streamlit as st
from auth import require_login, logout_user
from database import get_student, get_all_chapter_progress

st.set_page_config(page_title="AI Timetable Generator", page_icon="📅", layout="centered")

# ── Auth guard ─────────────────────────────────────────────────────────────────
user_id = require_login()

# ── Load profile for THIS user ─────────────────────────────────────────────────
try:
    db_profile = get_student(user_id)
except RuntimeError as e:
    st.error(f"🚨 Could not load profile: {e}")
    st.stop()

if not db_profile or not db_profile.get("name"):
    st.warning("⚠️ No student profile found. Please create your profile first.")
    if st.button("👤 Create Profile"):
        st.switch_page("pages/1_Profile.py")
    st.stop()

st.session_state["student_profile"]    = db_profile
st.session_state["active_student_id"]  = db_profile["id"]
st.session_state["completed_chapters"] = get_all_chapter_progress(db_profile["id"])

profile = db_profile

# ── Page header ────────────────────────────────────────────────────────────────
col_h, col_out = st.columns([5, 1])
with col_h:
    st.markdown("<h1 style='color: #00FF87;'>📅 Smart Study Timetable</h1>", unsafe_allow_html=True)
with col_out:
    st.write("")
    st.write("")
    if st.button("🚪 Logout", use_container_width=True):
        logout_user()
        st.switch_page("pages/0_Login.py")

st.write("---")
st.markdown(f"### 👋 Ready, {profile['name']}!")

ret_hour      = int(profile.get("return_time", "16:00").split(":")[0])
total_hours   = int(profile["study_hours"])
selected_subs = profile["subjects"]
weak_subs     = profile["weak_subjects"]

if not selected_subs:
    st.warning("No subjects found in your profile. Please update your profile first.")
    if st.button("✏️ Edit Profile"):
        st.switch_page("pages/1_Profile.py")
    st.stop()

# Weak subjects first, then the rest
ordered_subs = [s for s in selected_subs if s in weak_subs] + \
               [s for s in selected_subs if s not in weak_subs]

st.write(
    f"Based on your school return time of **{profile['return_time']}** "
    f"and your goal of **{total_hours} study hour(s)**, here is your custom focus sequence:"
)

current_hour = ret_hour + 1  # 1-hour buffer after school

for i in range(total_hours):
    subject_assigned = ordered_subs[i % len(ordered_subs)]
    priority_tag = (
        "🔥 CAPS Priority (Weak Subject)" if subject_assigned in weak_subs
        else "✅ Curriculum Tracking"
    )
    st.markdown(
        f"""
        <div style="background-color:#1F2635;padding:15px;border-radius:8px;
                    border-left:5px solid #00FF87;margin-bottom:12px;">
            <span style="font-size:12px;color:#00FF87;font-weight:bold;">
                BLOCK {i+1} &nbsp;•&nbsp; {current_hour}:00 – {current_hour}:45
            </span>
            <h4 style="margin:5px 0 2px 0;color:#FFFFFF;">{subject_assigned}</h4>
            <p style="font-size:13px;color:#A0AABF;margin:0;">{priority_tag}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    current_hour += 1

st.write("---")
st.info("💡 Session complete? Click below to record your chapter coverage milestones!")
if st.button("📊 Go to Progress & Exam Tracker ➡️", use_container_width=True):
    st.switch_page("pages/4_Progress_Tracker.py")