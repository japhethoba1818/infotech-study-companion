import streamlit as st
import random

st.set_page_config(page_title="Pre-Study Routine", page_icon="🧘", layout="centered")

st.markdown("<h1 style='color: #00FF87;'>🧘 Pre-Study Routine</h1>", unsafe_allow_html=True)
st.write("Clear your physical and mental space before starting your work blocks.")
st.write("---")

quotes = [
    "“Discipline is choosing between what you want now and what you want most.” – Abraham Lincoln",
    "“The secret of getting ahead is getting started.” – Mark Twain",
    "“It always seems impossible until it's done.” – Nelson Mandela",
    "“Success isn't always about greatness. It's about consistency.”",
    "“Ke nako. Your future is built during these quiet study hours.”"
]

st.markdown(f"<div style='background-color: #1F2635; padding: 15px; border-radius: 8px; border-left: 4px solid #00FF87; text-align: center; font-style: italic; margin-bottom: 20px;'>{random.choice(quotes)}</div>", unsafe_allow_html=True)

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
        # FIXED: Removed the broken notifications list append and replaced it with a sleek native toast message!
        st.toast("🔥 Focus session started successfully! Stick to your time allocation slots.")
        
        # Move directly to the timetable page as intended
        st.switch_page("pages/3_📅_AI_Timetable.py")
else:
    st.info("💡 Complete all 3 checklist items above to activate deep study focus mode.")