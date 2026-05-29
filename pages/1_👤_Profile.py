"""
pages/1_👤_Profile.py — InfoTech Study Companion  (v2)
Profile creation & editing — now includes API key field.
"""

import streamlit as st
from database import (
    initialise_database, upsert_student, get_student,
    initialise_chapters, get_all_chapter_progress, backup_database
)

st.set_page_config(page_title="Student Profile", page_icon="👤", layout="centered")

if "db_ready" not in st.session_state:
    try:
        initialise_database()
        st.session_state["db_ready"] = True
    except RuntimeError as e:
        st.error(f"🚨 Database error: {e}")
        st.stop()

try:
    db_profile = get_student()
except RuntimeError as e:
    st.error(f"🚨 Could not load profile: {e}")
    st.stop()

existing = db_profile or {}

if st.session_state.get("profile_saved_successfully"):
    st.balloons()
    st.success("🎉 Profile saved permanently to your device!")
    if st.button("🏠 Go to Dashboard", use_container_width=True):
        st.session_state["profile_saved_successfully"] = False
        st.switch_page("app.py")
    st.stop()

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

st.markdown("<h1 style='color:#00FF87;'>👤 Student Profile Setup</h1>", unsafe_allow_html=True)
st.write("Your profile is saved permanently on your device. Come back and edit any time.")
st.write("---")

with st.form("profile_form"):
    st.markdown("### 📝 General Parameters")
    name      = st.text_input("Full Name", value=existing.get("name", ""))
    grade_opt = ["Grade 10", "Grade 11", "Grade 12"]
    grade     = st.selectbox("Current Grade", grade_opt,
                             index=grade_opt.index(existing["grade"]) if existing.get("grade") in grade_opt else 2)
    dream_job = st.text_input("Dream Profession", value=existing.get("dream_job", ""))

    col_a, col_b = st.columns(2)
    with col_a:
        return_time = st.text_input("School Return Time (24h)", value=existing.get("return_time","16:00"))
    with col_b:
        sleep_time  = st.text_input("Target Sleep Time (24h)",  value=existing.get("sleep_time","21:00"))

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
                name=name.strip(), grade=grade, dream_job=dream_job.strip(),
                return_time=return_time.strip(), sleep_time=sleep_time.strip(),
                study_hours=study_hours, subjects=subjects,
                weak_subjects=sanitized_weak,
            )
            initialise_chapters(student_id, subjects)
            fresh = get_student()
            st.session_state["student_profile"]    = fresh
            st.session_state["active_student_id"]  = fresh["id"]
            st.session_state["completed_chapters"] = get_all_chapter_progress(fresh["id"])
            # Auto-backup on every profile save
            try:
                backup_database()
            except Exception:
                pass
            st.session_state["profile_saved_successfully"] = True
            st.rerun()
        except RuntimeError as e:
            st.error(f"🚨 Could not save profile: {e}")