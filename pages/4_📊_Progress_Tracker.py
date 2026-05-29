"""
pages/4_📊_Progress_Tracker.py — InfoTech Study Companion
Chapter progress tracker. Reads from and writes to SQLite on every change.
"""

import streamlit as st
from database import (
    initialise_database, get_student,
    get_all_chapter_progress, update_chapter_progress
)

st.set_page_config(page_title="Progress Tracker", page_icon="📊", layout="centered")

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

if not db_profile:
    st.warning("⚠️ No active profile session detected. Please return to the homepage to log in or create one.")
    if st.button("🏠 Go to Homepage"):
        st.switch_page("app.py")
    st.stop()

student_id = db_profile["id"]

# Load the latest chapter progress from DB into session_state cache
try:
    db_chapters = get_all_chapter_progress(student_id)
except RuntimeError as e:
    st.error(f"🚨 Could not load chapter progress: {e}")
    st.stop()

st.session_state["student_profile"]    = db_profile
st.session_state["active_student_id"]  = student_id
st.session_state["completed_chapters"] = db_chapters

profile  = db_profile
chapters = db_chapters

# ── Page header ───────────────────────────────────────────────────────────────
st.markdown("<h1 style='color: #00FF87;'>📊 Flexible Chapter Tracker</h1>", unsafe_allow_html=True)
st.write("Customize your textbook scopes and log completed targets smoothly.")
st.write("---")

st.markdown(f"### 📈 {profile['name']}'s Curriculum Board")

# ── AI Smart Focus Recommendation ────────────────────────────────────────────
completion_rates = []
for sub in profile["subjects"]:
    sub_data = chapters.get(sub, {"total": 10, "done": 0})
    total = sub_data["total"]
    done  = sub_data["done"]
    pct   = (done / total * 100) if total > 0 else 100.0
    completion_rates.append((sub, pct))

completion_rates.sort(key=lambda x: x[1])  # ascending — lowest first

st.markdown("### 💡 AI Smart Focus Recommendation")
if completion_rates:
    lowest_sub, lowest_pct = completion_rates[0]
    if lowest_pct < 100:
        st.warning(
            f"👉 **Action Plan:** Spend extra time on **{lowest_sub}** this week! "
            f"Your progress is lowest here at **{int(lowest_pct)}%** completion."
        )
    else:
        st.success("🏆 **Action Plan:** Phenomenal effort! All syllabus chapters are completely mastered.")
else:
    st.info("No subject data yet.")

st.write("---")

# ── Per-subject progress inputs ───────────────────────────────────────────────
for subject in profile["subjects"]:
    sub_data    = chapters.get(subject, {"total": 10, "done": 0})
    saved_total = int(sub_data["total"])
    saved_done  = int(sub_data["done"])

    with st.container():
        st.markdown(f"### 📘 {subject}")
        col_l, col_r = st.columns(2)

        with col_l:
            total_chaps = st.number_input(
                "Total chapters:", 1, 50, saved_total,
                key=f"t_{subject}"
            )
        with col_r:
            done_chaps = st.number_input(
                "Completed chapters:", 0, total_chaps, min(saved_done, total_chaps),
                key=f"d_{subject}"
            )

        # ── Write to DB only when the value has actually changed ─────────────
        if total_chaps != saved_total or done_chaps != saved_done:
            try:
                update_chapter_progress(student_id, subject, total_chaps, done_chaps)
                # Refresh cache from DB after every write
                st.session_state["completed_chapters"] = get_all_chapter_progress(student_id)
                st.rerun()
            except RuntimeError as e:
                st.error(f"🚨 Could not save progress for {subject}: {e}")

        pct_done = int((done_chaps / total_chaps) * 100) if total_chaps > 0 else 0
        st.progress(done_chaps / total_chaps if total_chaps > 0 else 0)
        st.write(f"Syllabus Mastered: **{pct_done}%**")

    st.write("---")