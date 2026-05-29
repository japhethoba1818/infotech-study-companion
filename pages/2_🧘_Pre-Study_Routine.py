"""
pages/2_🧘_Pre-Study_Routine.py — InfoTech Study Companion
Pre-study routine page. Reads session from DB on every load.
No data is written here — this is a pure UX gate.
"""

import streamlit as st
import random
from database import initialise_database, get_student, get_all_chapter_progress

st.set_page_config(page_title="Pre-Study Routine", page_icon="🧘", layout="centered")

# ── DB boot guard ─────────────────────────────────────────────────────────────
if "db_ready" not in st.session_state:
    try:
        initialise_database()
        st.session_state["db_ready"] = True
    except RuntimeError as e:
        st.error(f"🚨 Database error: {e}")
        st.stop()

# ── Sync session_state from DB ────────────────────────────────────────────────
try:
    db_profile = get_student()
except RuntimeError as e:
    st.error(f"🚨 Could not load profile: {e}")
    st.stop()

if db_profile:
    st.session_state["student_profile"]    = db_profile
    st.session_state["active_student_id"]  = db_profile["id"]
    # Refresh chapter progress cache as well
    st.session_state["completed_chapters"] = get_all_chapter_progress(db_profile["id"])
else:
    st.warning("⚠️ No active profile session detected! Go to the home page to log in.")
    if st.button("🏠 Go to Homepage"):
        st.switch_page("app.py")
    st.stop()

# ── Page content ──────────────────────────────────────────────────────────────
st.markdown("<h1 style='color: #00FF87;'>🧘 Pre-Study Routine</h1>", unsafe_allow_html=True)
st.write("Clear your physical and mental space before starting your work blocks.")
st.write("---")

quotes = [
    "\u201cDiscipline is choosing between what you want now and what you want most.\u201d \u2013 Abraham Lincoln",
    "\u201cThe secret of getting ahead is getting started.\u201d \u2013 Mark Twain",
    "\u201cIt always seems impossible until it\u2019s done.\u201d \u2013 Nelson Mandela",
    "\u201cSuccess isn\u2019t always about greatness. It\u2019s about consistency.\u201d",
    "\u201cKe nako. Your future is built during these quiet study hours.\u201d",
]

st.markdown(
    f"<div style='background-color:#1F2635;padding:15px;border-radius:8px;"
    f"border-left:4px solid #00FF87;text-align:center;font-style:italic;"
    f"margin-bottom:20px;'>{random.choice(quotes)}</div>",
    unsafe_allow_html=True,
)

st.markdown("### ⏱️ Quick Setup Checklist")
check1 = st.checkbox("📱 Phone set to Silent/Do Not Disturb mode and placed out of sight.")
check2 = st.checkbox("💧 Water bottle filled up and study materials sitting on desk.")
check3 = st.checkbox("🙏 A quick prayer or silent moment to clarify your intentions.")

st.write("---")
st.markdown("### 🫁 Box Breathing Reset")
with st.container():
    st.markdown("""
    1. **Inhale** slowly through your nose for **4 seconds**.
    2. **Hold** that breath deep in your lungs for **4 seconds**.
    3. **Exhale** completely through your mouth for **4 seconds**.
    4. **Rest** empty without breathing for **4 seconds**.
    """)

st.write("---")

if check1 and check2 and check3:
    st.success("🎯 Environment clean. Mind prepared. You are completely ready to dominate this session!")
    if st.button("🚀 Enter Deep Study Focus Mode", use_container_width=True):
        st.toast("🔥 Focus session started! Stick to your time allocation slots.")
        st.switch_page("pages/3_📅_AI_Timetable.py")
else:
    st.info("💡 Complete all 3 checklist items above to activate deep study focus mode.")