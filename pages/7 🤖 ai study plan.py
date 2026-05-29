"""
pages/7_🤖_AI_Study_Plan.py — InfoTech Study Companion
Uses the Anthropic Claude API to generate a personalised weekly study plan
based on the student's live chapter progress, exam dates, and weak subjects.
"""

import streamlit as st
from datetime import date, datetime
import anthropic

from database import (
    initialise_database, get_student, get_all_chapter_progress,
    get_upcoming_exams, get_hours_per_subject
)

st.set_page_config(page_title="AI Study Plan", page_icon="🤖", layout="centered")

if "db_ready" not in st.session_state:
    try:
        initialise_database()
        st.session_state["db_ready"] = True
    except RuntimeError as e:
        st.error(f"🚨 {e}")
        st.stop()

try:
    db_profile = get_student()
except RuntimeError as e:
    st.error(f"🚨 {e}")
    st.stop()

if not db_profile:
    st.warning("⚠️ No active profile detected. Please log in first.")
    if st.button("🏠 Go to Homepage"):
        st.switch_page("app.py")
    st.stop()

sid = db_profile["id"]
st.session_state["student_profile"]    = db_profile
st.session_state["active_student_id"]  = sid

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("<h1 style='color:#00FF87;'>🤖 AI Study Plan Generator</h1>", unsafe_allow_html=True)
st.write("Claude reads your actual progress data and writes a personalised weekly plan just for you.")
st.write("---")

# ── API key gate ───────────────────────────────────────────────────────────────
api_key = db_profile.get("api_key", "").strip()

if not api_key:
    st.warning("🔑 No Anthropic API key found in your profile.")
    st.markdown("""
    ### 📋 How to get your free API key — step by step

    **Step 1 — Create your Anthropic account**
    - Open your browser and go to **https://console.anthropic.com**
    - Click **"Sign up"** and register with your email address.
    - Verify your email when the confirmation link arrives.

    **Step 2 — Generate your API key**
    - Once logged in, click your profile icon (top right) → **"API Keys"**
    - Click the **"Create Key"** button.
    - Give it a name like `InfoTech Study Companion`.
    - Copy the key that appears — it starts with `sk-ant-`
    - ⚠️ This key is only shown **once**. Save it somewhere safe before closing.

    **Step 3 — Check your free credits**
    - New accounts receive free API credits automatically.
    - Your usage and remaining credits are visible at **https://console.anthropic.com/settings/billing**
    - Generating a study plan costs less than $0.01 each time.

    **Step 4 — Add the key to your profile**
    - Click the button below to go to your profile.
    - Paste the key into the **"Anthropic API Key"** field.
    - Click **Save Profile**.
    - Come back here and generate your plan!
    """)
    if st.button("✏️ Go to Profile to Add API Key", use_container_width=True):
        st.switch_page("pages/1_👤_Profile.py")
    st.stop()

# ── Load data for the prompt ───────────────────────────────────────────────────
try:
    chapters  = get_all_chapter_progress(sid)
    upcoming  = get_upcoming_exams(sid)
    hours_log = get_hours_per_subject(sid)
except RuntimeError as e:
    st.error(str(e))
    st.stop()

# ── Data preview ───────────────────────────────────────────────────────────────
st.markdown("### 📊 Data Claude will use to build your plan")

with st.expander("View your current progress snapshot", expanded=False):
    if chapters:
        rows = []
        hours_map = {r["subject"]: r["total_hours"] for r in hours_log}
        for sub, data in chapters.items():
            pct = round(data["done"] / data["total"] * 100, 1) if data["total"] > 0 else 0
            rows.append({
                "Subject":       sub,
                "Chapters Done": f"{data['done']}/{data['total']}",
                "Completion %":  pct,
                "Hours Studied": hours_map.get(sub, 0),
            })
        st.dataframe(rows, use_container_width=True, hide_index=True)

    if upcoming:
        st.markdown("**Upcoming exams:**")
        for ex in upcoming:
            exam_dt   = datetime.strptime(ex["exam_date"], "%Y-%m-%d").date()
            days_left = (exam_dt - date.today()).days
            st.write(f"- **{ex['exam_label']}** ({ex['subject']}) — {days_left} days away on {ex['exam_date']}")

st.write("---")

# ── Customisation ──────────────────────────────────────────────────────────────
st.markdown("### ⚙️ Customise Your Plan")
c1, c2 = st.columns(2)
with c1:
    focus_mode = st.selectbox("Plan focus", [
        "Balanced — all subjects",
        "Prioritise weak subjects only",
        "Exam-driven — focus on upcoming exams",
        "Catch up — lowest completion first",
    ])
with c2:
    plan_days = st.selectbox("Plan length", ["5 days (Mon–Fri)", "7 days (full week)"])

extra_notes = st.text_area(
    "Anything else Claude should know?",
    placeholder="e.g. I have extra Maths lessons on Wednesday, I'm writing a test on Friday, I prefer studying in 45-min blocks.",
    height=80
)

st.write("---")

# ── Generate button ────────────────────────────────────────────────────────────
if st.button("🚀 Generate My Personalised Study Plan", use_container_width=True, type="primary"):

    # Build a data-rich prompt
    today_str = date.today().strftime("%A, %d %B %Y")
    days_str  = "5 school days (Monday to Friday)" if "5" in plan_days else "7 days (Monday to Sunday)"

    chapter_block = ""
    if chapters:
        hours_map = {r["subject"]: r["total_hours"] for r in hours_log}
        for sub, data in chapters.items():
            pct   = round(data["done"] / data["total"] * 100, 1) if data["total"] > 0 else 0
            hrs   = hours_map.get(sub, 0)
            label = "⚠️ WEAK" if sub in db_profile.get("weak_subjects", []) else ""
            chapter_block += f"  - {sub}: {data['done']}/{data['total']} chapters ({pct}% complete), {hrs}h studied {label}\n"
    else:
        chapter_block = "  No chapter data recorded yet.\n"

    exam_block = ""
    if upcoming:
        for ex in upcoming:
            exam_dt   = datetime.strptime(ex["exam_date"], "%Y-%m-%d").date()
            days_left = (exam_dt - date.today()).days
            exam_block += f"  - {ex['exam_label']} ({ex['subject']}): {days_left} days away ({ex['exam_date']})\n"
    else:
        exam_block = "  No upcoming exams scheduled.\n"

    prompt = f"""You are a dedicated academic coach helping a South African high school student succeed.

Today is {today_str}.

STUDENT PROFILE:
- Name: {db_profile['name']}
- Grade: {db_profile['grade']}
- Dream career: {db_profile.get('dream_job', 'Not specified')}
- Daily study target: {db_profile['study_hours']} hour(s) after school
- School return time: {db_profile.get('return_time', '16:00')}
- Target sleep time: {db_profile.get('sleep_time', '21:00')}

CHAPTER PROGRESS (live from their study companion):
{chapter_block}
UPCOMING EXAMS:
{exam_block}
PLAN FOCUS: {focus_mode}
PLAN LENGTH: {days_str}
EXTRA NOTES FROM STUDENT: {extra_notes if extra_notes.strip() else 'None'}

YOUR TASK:
Write a detailed, day-by-day study plan for the next {days_str}.

For each day include:
1. A motivating daily theme or goal (one punchy sentence)
2. Specific study blocks with: subject, exact topic/chapters to cover, duration
3. A short reason WHY that subject is prioritised today (link it to their data)
4. One practical tip specific to that subject for South African CAPS curriculum

After the day-by-day plan, add:
- A "Watch Out" section flagging the 1-2 most at-risk subjects or exams
- A personal motivational message that references {db_profile['name']}'s dream of becoming a {db_profile.get('dream_job', 'professional')}

Format the plan clearly with headings for each day. Be specific, encouraging, and direct.
Do not use vague advice. Reference actual subjects, actual chapter numbers, actual exam dates.
"""

    with st.spinner("🤖 Claude is analysing your progress and building your plan..."):
        try:
            client   = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model      = "claude-sonnet-4-20250514",
                max_tokens = 2000,
                messages   = [{"role": "user", "content": prompt}]
            )
            plan_text = response.content[0].text

            st.success("✅ Your personalised study plan is ready!")
            st.write("---")
            st.markdown("## 📋 Your Personalised Study Plan")
            st.markdown(
                f"<div style='background:#1F2635;padding:24px;border-radius:12px;"
                f"border-left:5px solid #00FF87;line-height:1.8;'>{plan_text}</div>",
                unsafe_allow_html=True
            )
            st.write("---")

            # Download button
            st.download_button(
                label    = "⬇️ Download Plan as .txt",
                data     = plan_text,
                file_name= f"study_plan_{date.today().isoformat()}.txt",
                mime     = "text/plain",
                use_container_width=True
            )

        except anthropic.AuthenticationError:
            st.error("🔑 Invalid API key. Please check the key in your profile and try again.")
        except anthropic.RateLimitError:
            st.error("⏳ Rate limit reached. Please wait a moment and try again.")
        except anthropic.APIConnectionError:
            st.error("🌐 Connection failed. Please check your internet connection and try again.")
        except Exception as e:
            st.error(f"🚨 Unexpected error: {e}")