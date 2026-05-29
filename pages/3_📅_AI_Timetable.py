"""
pages/3_📅_AI_Timetable.py — InfoTech Study Companion
Renders a personalised study timetable based on the persisted profile.
"""

import streamlit as st
from database import initialise_database, get_student, get_all_chapter_progress

st.set_page_config(page_title="AI Timetable Generator", page_icon="📅", layout="centered")

# ── DB boot guard ─────────────────────────────────────────────────────────────
if "db_ready" not in st.session_state:
    try:
        initialise_database()
        st.session_state["db_ready"] = True
    except RuntimeError as e:
        st.error(f"🚨 Database error: {e}")
        st.stop()

# ── Sync from DB ──────────────────────────────────────────────────────────────
try:
    db_profile = get_student()
except RuntimeError as e:
    st.error(f"🚨 Could not load profile: {e}")
    st.stop()

if not db_profile or not db_profile.get("name"):
    st.warning("⚠️ No active profile session detected! Go to the home page to log in.")
    if st.button("🏠 Go to Homepage"):
        st.switch_page("app.py")
    st.stop()

# Push fresh data into session_state cache
st.session_state["student_profile"]    = db_profile
st.session_state["active_student_id"]  = db_profile["id"]
st.session_state["completed_chapters"] = get_all_chapter_progress(db_profile["id"])

profile = db_profile

# ── Page content ──────────────────────────────────────────────────────────────
st.markdown("<h1 style='color: #00FF87;'>📅 Smart Study Timetable</h1>", unsafe_allow_html=True)
st.write("---")

st.markdown(f"### 👋 Ready, {profile['name']}!")

ret_hour        = int(profile.get("return_time", "16:00").split(":")[0])
total_hours     = int(profile["study_hours"])
selected_subs   = profile["subjects"]
weak_subs       = profile["weak_subjects"]

if not selected_subs:
    st.warning("No subjects found in your profile. Please update your profile first.")
    if st.button("✏️ Edit Profile"):
        st.switch_page("pages/1_👤_Profile.py")
    st.stop()

# Weak subjects first, then the rest
ordered_subs = [s for s in selected_subs if s in weak_subs] + \
               [s for s in selected_subs if s not in weak_subs]

st.write(
    f"Based on your school return time of **{profile['return_time']}** "
    f"and your goal of **{total_hours} study hour(s)**, here is your custom focus sequence:"
)

current_hour = ret_hour + 1  # 1-hour buffer to unpack after school

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
    st.switch_page("pages/4_📊_Progress_Tracker.py")