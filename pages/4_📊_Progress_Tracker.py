import streamlit as st

st.set_page_config(page_title="Progress Tracker", page_icon="📊", layout="centered")

st.markdown("<h1 style='color: #00FF87;'>📊 Flexible Chapter Tracker</h1>", unsafe_allow_html=True)
st.write("Customize your textbook scopes and log completed targets smoothly.")
st.write("---")

profile = st.session_state.get("student_profile")

if not profile:
    st.warning("⚠️ No active profile session detected. Please return to the homepage to log in or create one.")
else:
    st.markdown(f"### 📈 {profile['name']}'s Curriculum Board")
    
    # --- FIXED AI SMART FOCUS RECOMMENDATION ENGINE ---
    completion_rates = []
    for sub in profile["subjects"]:
        # FIXED: Changed 'subject' to 'sub' to match the loop variable perfectly!
        sub_data = st.session_state.completed_chapters.get(sub, {"total": 10, "done": 0})
        pct = (sub_data["done"] / sub_data["total"]) * 100 if sub_data["total"] > 0 else 100
        completion_rates.append((sub, pct))
        
    completion_rates.sort(key=lambda x: x[1])
    lowest_subject, lowest_pct = completion_rates[0] if completion_rates else (None, 100)

    st.markdown("### 💡 AI Smart Focus Recommendation")
    if lowest_subject and lowest_pct < 100:
        st.warning(f"👉 **Action Plan:** Spend extra time on **{lowest_subject}** this week! Your progress is lowest here at **{int(lowest_pct)}%** completion.")
    else:
        st.success("🏆 **Action Plan:** Phenomenal effort! All syllabus chapters are completely mastered.")
        
    st.write("---")

    # Render inputs per subject
    for subject in profile["subjects"]:
        sub_data = st.session_state.completed_chapters.get(subject, {"total": 10, "done": 0})
        
        with st.container():
            st.markdown(f"### 📘 {subject}")
            col_l, col_r = st.columns(2)
            with col_l:
                total_chaps = st.number_input("Total chapters:", 1, 50, int(sub_data["total"]), key=f"t_{subject}")
            with col_r:
                done_chaps = st.number_input("Completed chapters:", 0, total_chaps, int(sub_data["done"]), key=f"d_{subject}")
            
            # Save changes instantly to session state memory
            if total_chaps != sub_data["total"] or done_chaps != sub_data["done"]:
                st.session_state.completed_chapters[subject] = {"total": total_chaps, "done": done_chaps}
                st.rerun()

            percentage_done = int((done_chaps / total_chaps) * 100) if total_chaps > 0 else 0
            st.progress(done_chaps / total_chaps if total_chaps > 0 else 0)
            st.write(f"Syllabus Mastered: **{percentage_done}%**")
        st.write("---")