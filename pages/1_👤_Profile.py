import streamlit as st

st.set_page_config(page_title="Student Profile", page_icon="👤", layout="centered")

st.markdown("<h1 style='color: #00FF87;'>👤 Student Profile Setup</h1>", unsafe_allow_html=True)
st.write("Configure your academic metrics below to generate your custom timetable and trackers.")
st.write("---")

if "profile_saved_successfully" not in st.session_state:
    st.session_state.profile_saved_successfully = False

# Exhaustive Official South African CAPS Subject Core Matrix
caps_subjects = [
    "Accounting", "Agricultural Sciences", "Afrikaans Eerste Addisionele Taal", "Afrikaans Huistaal",
    "Business Studies", "Civil Technology", "Computer Applications Technology (CAT)", "Consumer Studies",
    "Design", "Dramatic Arts", "Economics", "Electrical Technology", "Engineering Graphics and Design (EGD)",
    "English First Additional Language", "English Home Language", "Geography", "History", "Hospitality Studies",
    "Information Technology (IT)", "IsiNdebele First Additional Language", "IsiNdebele Home Language",
    "IsiXhosa First Additional Language", "IsiXhosa Home Language", "IsiZulu First Additional Language",
    "IsiZulu Home Language", "Life Orientation", "Life Sciences", "Mathematical Literacy", "Mathematics",
    "Mechanical Technology", "Music", "Physical Sciences", "Religion Studies", "Sepedi First Additional Language",
    "Sepedi Home Language", "Sesotho First Additional Language", "Sesotho Home Language", "Setswana First Additional Language",
    "Setswana Home Language", "SiSwati First Additional Language", "SiSwati Home Language", "Technical Mathematics",
    "Technical Sciences", "Tourism", "Tshivenda First Additional Language", "Tshivenda Home Language",
    "Visual Arts", "Xitsonga First Additional Language", "Xitsonga Home Language"
]

if st.session_state.profile_saved_successfully:
    st.balloons()
    st.success("🎉 Profile created successfully inside secure temporary cache memory!")
    if st.button("🏠 Go back to Homepage to Log In", use_container_width=True):
        st.session_state.profile_saved_successfully = False
        st.switch_page("app.py")
else:
    with st.form("profile_form"):
        st.markdown("### 📝 General Parameters")
        name = st.text_input("Full Name")
        grade = st.selectbox("Current Grade", ["Grade 10", "Grade 11", "Grade 12"])
        dream_job = st.text_input("Dream Profession (e.g., Engineer, Accountant, Doctor)")
        
        col_a, col_b = st.columns(2)
        with col_a:
            return_time = st.text_input("School Return Time (24h format)", value="16:00")
        with col_b:
            sleep_time = st.text_input("Target Sleep Time (24h format)", value="21:00")
        
        st.write("---")
        st.markdown("### 📚 Subject Allocation")
        
        # We pass the full master list to both fields so they are 100% unlocked and responsive
        subjects = st.multiselect("Select all the subjects you are taking this term:", options=caps_subjects)
        weak_subjects = st.multiselect("Select your weak subjects (These will be prioritized on your timetable):", options=caps_subjects)
        
        study_hours = st.slider("Target Daily Study Hours", min_value=1, max_value=8, value=3)

        submit = st.form_submit_button("💾 Lock in Profile Session")

    if submit:
        if not name.strip() or not subjects:
            st.error("⚠️ Form incomplete! Please provide both your full name and choose your subjects.")
        else:
            # Filter weak subjects to make sure they match selected subjects
            sanitized_weak = [sub for sub in weak_subjects if sub in subjects]
            
            # Save right into Streamlit session memory
            st.session_state.student_profile = {
                "name": name.strip(), "grade": grade, "dream_job": dream_job,
                "subjects": subjects, "weak_subjects": sanitized_weak, "study_hours": study_hours,
                "return_time": return_time, "sleep_time": sleep_time
            }
            
            # Create standard base 10-chapter tracking limits
            st.session_state.completed_chapters = {sub: {"total": 10, "done": 0} for sub in subjects}
            st.session_state.profile_saved_successfully = True
            st.rerun()