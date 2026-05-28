import streamlit as st

st.set_page_config(page_title="InfoTech Study Companion", page_icon="🎓", layout="centered")

# --- INITIALIZE INTERNAL MEMORY MAPS ---
if "student_profile" not in st.session_state:
    st.session_state.student_profile = None
if "completed_chapters" not in st.session_state:
    st.session_state.completed_chapters = {}

# --- GORGEOUS SOUTH AFRICAN HERO DESIGN SECTION ---
st.markdown(
    """
    <div style="text-align: center; margin-bottom: 20px;">
        <h1 style='color: #00FF87; font-size: 36px; font-weight: 800; margin-bottom: 5px;'>🎓 InfoTech Study Companion</h1>
        <p style='color: #A0AABF; font-size: 16px; font-weight: 300;'>Your Digital AI Study Mentor • Built for South African High School Excellence</p>
    </div>
    """, 
    unsafe_allow_html=True
)

# FIXED: Changed use_column_width=True to use_container_width=True to clear the deprecation warning box!
st.image(
    "https://images.unsplash.com/photo-1577896851231-70ef18881754?auto=format&fit=crop&q=80&w=800",
    caption="Dumela! Map out your subjects, manage your focus hours, and achieve your matric dreams.",
    use_container_width=True
)

st.write("---")

st.markdown("### 🔑 Student Access Portal")

# Active Session Logic Gate Tracker
if st.session_state.student_profile is not None:
    current_name = st.session_state.student_profile["name"]
    st.success(f"👋 Active Session Detected: **{current_name}** is currently logged in!")
    
    if st.button("🔓 Enter My Study Dashboard", use_container_width=True):
        st.switch_page("pages/2_🧘_Pre-Study_Routine.py")
        
    st.write("---")
    st.markdown("#### 🔄 Need to start over or change users?")

# Main Button Navigation Options
if st.button("✨ Create / Reset Student Profile", use_container_width=True):
    st.session_state.student_profile = {
        "name": "", "grade": "Grade 12", "dream_job": "",
        "subjects": [], "weak_subjects": [], "study_hours": 3,
        "return_time": "16:00", "sleep_time": "21:00"
    }
    st.session_state.completed_chapters = {}
    st.switch_page("pages/1_👤_Profile.py")