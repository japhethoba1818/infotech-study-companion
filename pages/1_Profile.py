"""
pages/1_Profile.py — InfoTech Study Companion  (v3)
Profile creation & editing — scoped to the authenticated user.
"""

import streamlit as st
from auth import require_login, logout_user, current_username
from database import (
    initialise_database, upsert_student, get_student,
    initialise_chapters, get_all_chapter_progress, backup_database
)

st.set_page_config(page_title="Student Profile", page_icon="👤", layout="centered")

# ── Auth guard ─────────────────────────────────────────────────────────────────
user_id = require_login()

# ── Load existing profile for THIS user only ───────────────────────────────────
try:
    db_profile = get_student(user_id)
except RuntimeError as e:
    st.error(f"🚨 Could not load profile: {e}")
    st.stop()

existing = db_profile or {}

# ── Post-save celebration ──────────────────────────────────────────────────────
if st.session_state.get("profile_saved_successfully"):
    st.balloons()
    st.success("🎉 Profile saved permanently to your account!")
    if st.button("🏠 Go to Dashboard", use_container_width=True):
        st.session_state["profile_saved_successfully"] = False
        st.switch_page("app.py")
    st.stop()

# ── Subject list (CAPS) ────────────────────────────────────────────────────────
caps_subjects = [
    "Accounting", "Agricultural Sciences", "Afrikaans Eerste Addisionele Taal", "Afrikaans Huistaal",
    "Business Studies", "Civil Technology", "Computer Applications Technology (CAT)", "Consumer Studies",
    "Design", "Dramatic Arts", "Economics", "Electrical Technology", "Engineering Graphics and Design (EGD)",
    "English First Additional Language", "English Home Language", "Geography", "History", "Hospitality Studies",
    "Information Technology (IT)", "IsiNdebele First Additional Language", "IsiNdebele Home Language",
    "IsiXhosa First Additional Language", "IsiXhosa Home Language", "IsiZulu First Additional Language",
    "IsiZulu Home Language", "Life Orientation", "Life Sciences", "Mathematical Literacy", "Mathematics",
    "Mechanical Technology", "Music", "Physical Sciences", "Religion Studies", "Sepedi First Additional Language",
    "Sepedi Home Language", "Sesotho First Additional Language", "Sesotho Home Language",
    "Setswana First Additional Language", "Setswana Home Language", "SiSwati First Additional Language",
    "SiSwati Home Language", "Technical Mathematics", "Technical Sciences", "Tourism",
    "Tshivenda First Additional Language", "Tshivenda Home Language", "Visual Arts",
    "Xitsonga First Additional Language", "Xitsonga Home Language",
]

# ── Page header ────────────────────────────────────────────────────────────────
col_h, col_out = st.columns([5, 1])
with col_h:
    st.markdown("<h1 style='color:#00FF87;'>👤 Student Profile Setup</h1>", unsafe_allow_html=True)
with col_out:
    st.write("")
    st.write("")
    if st.button("🚪 Logout", use_container_width=True):
        logout_user()
        st.switch_page("pages/0_Login.py")

st.write(f"Logged in as: **{current_username()}** · Profile data is saved only to your account.")
st.write("---")

# ── Profile form ───────────────────────────────────────────────────────────────
with st.form("profile_form"):
    st.markdown("### 📝 General Parameters")
    name      = st.text_input("Full Name", value=existing.get("name", ""))
    grade_opt = ["Grade 10", "Grade 11", "Grade 12"]
    grade     = st.selectbox(
        "Current Grade", grade_opt,
        index=grade_opt.index(existing["grade"]) if existing.get("grade") in grade_opt else 2,
    )
    dream_job = st.text_input("Dream Profession", value=existing.get("dream_job", ""))

    col_a, col_b = st.columns(2)
    with col_a:
        return_time = st.text_input("School Return Time (24h)", value=existing.get("return_time", "16:00"))
    with col_b:
        sleep_time  = st.text_input("Target Sleep Time (24h)",  value=existing.get("sleep_time", "21:00"))

    st.write("---")
    st.markdown("### 📚 Subject Allocation")
    subjects      = st.multiselect("Subjects you are taking:", options=caps_subjects,
                                   default=existing.get("subjects", []))
    weak_subjects = st.multiselect("Your weak subjects:", options=caps_subjects,
                                   default=existing.get("weak_subjects", []))
    study_hours   = st.slider("Target Daily Study Hours", 1, 8, int(existing.get("study_hours", 3)))

    submit = st.form_submit_button("💾 Save Profile", use_container_width=True)

if submit:
    if not name.strip():
        st.error("⚠️ Full Name is required.")
    elif not subjects:
        st.error("⚠️ Please select at least one subject.")
    else:
        sanitized_weak = [s for s in weak_subjects if s in subjects]
        try:
            student_id = upsert_student(
                user_id=user_id,
                name=name.strip(), grade=grade, dream_job=dream_job.strip(),
                return_time=return_time.strip(), sleep_time=sleep_time.strip(),
                study_hours=study_hours, subjects=subjects,
                weak_subjects=sanitized_weak,
            )
            initialise_chapters(student_id, subjects)
            fresh = get_student(user_id)
            st.session_state["student_profile"]    = fresh
            st.session_state["active_student_id"]  = fresh["id"]
            st.session_state["completed_chapters"] = get_all_chapter_progress(fresh["id"])
            try:
                backup_database()
            except Exception:
                pass
            st.session_state["profile_saved_successfully"] = True
            st.rerun()
        except RuntimeError as e:
            st.error(f"🚨 Could not save profile: {e}")