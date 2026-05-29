"""
app.py — InfoTech Study Companion
Homepage / login gate. Reads profile from SQLite on every load.
"""

import streamlit as st
from database import initialise_database, get_student, delete_student, DB_PATH

st.set_page_config(
    page_title="InfoTech Study Companion",
    page_icon="🎓",
    layout="centered"
)

# ── Boot: initialise DB tables exactly once per process ──────────────────────
if "db_ready" not in st.session_state:
    try:
        initialise_database()
        st.session_state["db_ready"] = True
    except RuntimeError as e:
        st.error(f"🚨 Could not initialise database: {e}")
        st.stop()

# ── Always sync session_state from DB (handles page refreshes & restarts) ────
try:
    db_profile = get_student()
except RuntimeError as e:
    st.error(f"🚨 Database read error: {e}")
    st.stop()

if db_profile:
    st.session_state["student_profile"]    = db_profile
    st.session_state["active_student_id"]  = db_profile["id"]
else:
    st.session_state["student_profile"]   = None
    st.session_state["active_student_id"] = None

# ── Hero section ──────────────────────────────────────────────────────────────
st.markdown(
    """
    <div style="text-align: center; margin-bottom: 20px;">
        <h1 style='color: #00FF87; font-size: 36px; font-weight: 800; margin-bottom: 5px;'>
            🎓 InfoTech Study Companion
        </h1>
        <p style='color: #A0AABF; font-size: 16px; font-weight: 300;'>
            Your Digital AI Study Mentor • Built for South African High School Excellence
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.image(
    "https://images.unsplash.com/photo-1577896851231-70ef18881754?auto=format&fit=crop&q=80&w=800",
    caption="Dumela! Map out your subjects, manage your focus hours, and achieve your matric dreams.",
    use_container_width=True,
)

st.write("---")
st.markdown("### 🔑 Student Access Portal")

profile = st.session_state.get("student_profile")

if profile and profile.get("name"):
    # ── Active session banner ────────────────────────────────────────────────
    st.success(f"👋 Active Session Detected: **{profile['name']}** is currently logged in!")
    st.caption(f"🗄️ Your data is safely stored at: `{DB_PATH}`")

    if st.button("🔓 Enter My Study Dashboard", use_container_width=True):
        st.switch_page("pages/2_🧘_Pre-Study_Routine.py")

    st.write("---")
    st.markdown("#### 🔄 Need to start over or change users?")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✏️ Edit My Profile", use_container_width=True):
            st.switch_page("pages/1_👤_Profile.py")
    with col2:
        if st.button("🗑️ Delete Profile & All Data", use_container_width=True, type="secondary"):
            st.session_state["confirm_delete"] = True

    if st.session_state.get("confirm_delete"):
        st.warning("⚠️ This will permanently erase your profile and all chapter progress from your device. Are you sure?")
        yes_col, no_col = st.columns(2)
        with yes_col:
            if st.button("✅ Yes, delete everything", use_container_width=True):
                try:
                    delete_student()
                    st.session_state.clear()
                    st.rerun()
                except RuntimeError as e:
                    st.error(str(e))
        with no_col:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state["confirm_delete"] = False
                st.rerun()
else:
    # ── No profile yet — first-time visitor ─────────────────────────────────
    st.info("👋 Welcome! No profile found. Create yours to get started.")
    if st.button("✨ Create Student Profile", use_container_width=True):
        st.switch_page("pages/1_👤_Profile.py")