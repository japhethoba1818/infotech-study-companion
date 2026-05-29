"""
pages/1_👤_Profile.py — InfoTech Study Companion
Profile creation & editing. All data written to SQLite immediately on submit.
"""

import streamlit as st
from database import (
    initialise_database, upsert_student, get_student,
    initialise_chapters, get_all_chapter_progress, DB_PATH
)

st.set_page_config(page_title="Student Profile", page_icon="👤", layout="centered")

# ── Guard: DB must be ready ───────────────────────────────────────────────────
if "db_ready" not in st.session_state:
    try:
        initialise_database()
        st.session_state["db_ready"] = True
    except RuntimeError as e:
        st.error(f"🚨 Database error: {e}")
        st.stop()

# ── Sync from DB so edits pre-populate the form ───────────────────────────────
try:
    db_profile = get_student()
except RuntimeError as e:
    st.error(f"🚨 Could not load profile: {e}")
    st.stop()

existing = db_profile or {}

# ── Success redirect state ────────────────────────────────────────────────────
if st.session_state.get("profile_saved_successfully"):
    st.balloons()
    st.success("🎉 Profile saved permanently to your device's local storage!")
    st.caption(f"📁 Location: `{DB_PATH}`")
    if st.button("🏠 Go to Homepage", use_container_width=True):
        st.session_state["profile_saved_successfully"] = False
        st.switch_page("app.py")
    st.stop()

# ── Full CAPS subject list ────────────────────────────────────────────────────
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

# ── Page header ───────────────────────────────────────────────────────────────
st.markdown("<h1 style='color: #00FF87;'>👤 Student Profile Setup</h1>", unsafe_allow_html=True)
action_label = "Edit" if existing.get("name") else "Create"
st.write(f"{'Update your' if existing.get('name') else 'Configure your'} academic settings. "
         "Every change is saved permanently to your device.")
st.write("---")

# ── Profile form ──────────────────────────────────────────────────────────────
with st.form("profile_form"):
    st.markdown("### 📝 General Parameters")

    name = st.text_input("Full Name", value=existing.get("name", ""))

    grade_options = ["Grade 10", "Grade 11", "Grade 12"]
    grade_default = grade_options.index(existing["grade"]) if existing.get("grade") in grade_options else 2
    grade = st.selectbox("Current Grade", grade_options, index=grade_default)

    dream_job = st.text_input(
        "Dream Profession (e.g., Engineer, Accountant, Doctor)",
        value=existing.get("dream_job", "")
    )

    col_a, col_b = st.columns(2)
    with col_a:
        return_time = st.text_input(
            "School Return Time (24h format)",
            value=existing.get("return_time", "16:00")
        )
    with col_b:
        sleep_time = st.text_input(
            "Target Sleep Time (24h format)",
            value=existing.get("sleep_time", "21:00")
        )

    st.write("---")
    st.markdown("### 📚 Subject Allocation")

    subjects = st.multiselect(
        "Select all subjects you are taking this term:",
        options=caps_subjects,
        default=existing.get("subjects", []),
    )

    weak_subjects = st.multiselect(
        "Select your weak subjects (prioritised on your timetable):",
        options=caps_subjects,
        default=existing.get("weak_subjects", []),
    )

    study_hours = st.slider(
        "Target Daily Study Hours",
        min_value=1, max_value=8,
        value=int(existing.get("study_hours", 3))
    )

    submit = st.form_submit_button(f"💾 {action_label} Profile", use_container_width=True)

# ── Handle submission ─────────────────────────────────────────────────────────
if submit:
    if not name.strip():
        st.error("⚠️ Full Name is required.")
    elif not subjects:
        st.error("⚠️ Please select at least one subject.")
    else:
        sanitized_weak = [s for s in weak_subjects if s in subjects]
        try:
            student_id = upsert_student(
                name         = name.strip(),
                grade        = grade,
                dream_job    = dream_job.strip(),
                return_time  = return_time.strip(),
                sleep_time   = sleep_time.strip(),
                study_hours  = study_hours,
                subjects     = subjects,
                weak_subjects= sanitized_weak,
            )
            # Seed chapter progress rows for every subject (INSERT OR IGNORE keeps existing progress)
            initialise_chapters(student_id, subjects)

            # Refresh session_state cache from DB
            fresh = get_student()
            st.session_state["student_profile"]   = fresh
            st.session_state["active_student_id"] = fresh["id"]
            st.session_state["completed_chapters"] = get_all_chapter_progress(fresh["id"])
            st.session_state["profile_saved_successfully"] = True
            st.rerun()

        except RuntimeError as e:
            st.error(f"🚨 Could not save profile: {e}")