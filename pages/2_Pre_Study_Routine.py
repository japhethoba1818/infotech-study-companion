"""
pages/2_Pre_Study_Routine.py — InfoTech Study Companion  (v3)
Pre-study routine page. Requires authenticated session.
"""

import streamlit as st
import random
from auth import require_login, logout_user
from database import get_student, get_all_chapter_progress

st.set_page_config(page_title="Pre-Study Routine", page_icon="🧘", layout="centered")

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

st.session_state["student_profile"]    = db_profile
st.session_state["active_student_id"]  = db_profile["id"]
st.session_state["completed_chapters"] = get_all_chapter_progress(db_profile["id"])

# ── Page header ────────────────────────────────────────────────────────────────
col_h, col_out = st.columns([5, 1])
with col_h:
    st.markdown("<h1 style='color: #00FF87;'>🧘 Pre-Study Routine</h1>", unsafe_allow_html=True)
with col_out:
    st.write("")
    st.write("")
    if st.button("🚪 Logout", use_container_width=True):
        logout_user()
        st.switch_page("pages/0_Login.py")

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
        st.switch_page("pages/3_AI_Timetable.py")
else:
    st.info("💡 Complete all 3 checklist items above to activate deep study focus mode.")