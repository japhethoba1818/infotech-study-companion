import streamlit as st

st.set_page_config(page_title="AI Timetable Generator", page_icon="📅", layout="centered")

st.markdown("<h1 style='color: #00FF87;'>📅 Smart Study Timetable</h1>", unsafe_allow_html=True)
st.write("---")

profile = st.session_state.get("student_profile")

if not profile or not profile.get("name"):
    st.warning("⚠️ No active profile session detected! Go to the home page to log in.")
else:
    st.markdown(f"### 👋 Ready, {profile['name']}!")
    
    # Extract structural time entries
    ret_hour = int(profile.get("return_time", "15:00").split(":")[0])
    total_hours = int(profile["study_hours"])
    
    selected_subjects = profile["subjects"]
    weak_subjects = profile["weak_subjects"]
    
    ordered_subjects = [s for s in selected_subjects if s in weak_subjects] + [s for s in selected_subjects if s not in weak_subjects]

    st.write(f"Based on your school return time of **{profile['return_time']}** and goal of **{total_hours} study hours**, here is your custom focus sequence:")
    
    current_hour = ret_hour + 1 # Allow 1 hour gap to unpack after school
    
    for i in range(total_hours):
        subject_assigned = ordered_subjects[i % len(ordered_subjects)]
        priority_tag = "🔥 CAPS Priority (Weak Subject)" if subject_assigned in weak_subjects else "✅ Curriculum Tracking"
        
        st.markdown(
            f"""
            <div style="background-color: #1F2635; padding: 15px; border-radius: 8px; border-left: 5px solid #00FF87; margin-bottom: 12px;">
                <span style="font-size: 12px; color: #00FF87; font-weight: bold;">BLOCK {i+1} • {current_hour}:00 - {current_hour}:45</span>
                <h4 style="margin: 5px 0 2px 0; color: #FFFFFF;">{subject_assigned}</h4>
                <p style="font-size: 13px; color: #A0AABF; margin: 0;">{priority_tag}</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        current_hour += 1

    st.write("---")
    
    # ADDED REQUESTED NAVIGATION CONTROL
    st.info("💡 Session complete? Click below to record your chapter coverage milestones and check your exam readiness index!")
    if st.button("📊 Go to Progress & Exam Tracker ➡️", use_container_width=True):
        st.switch_page("pages/4_📊_Progress_Tracker.py")