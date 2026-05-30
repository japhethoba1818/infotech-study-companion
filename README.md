# 🎓 InfoTech Study Companion

A personal AI-powered study mentor built for South African high school (matric) students.

## Features

- 🔐 Secure multi-user account system with 4-digit PIN login
- 📚 CAPS-aligned subject tracking
- 📅 Smart AI timetable generator
- 📊 Chapter progress tracker
- ⏱️ Study session logger with streaks
- 📅 Exam countdown with colour-coded urgency
- 🧘 Pre-study routine and mindfulness guide

## Tech Stack

- [Streamlit](https://streamlit.io) — UI framework
- SQLite — local persistent database
- Python 3.12

## Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy

Deployed on [Streamlit Community Cloud](https://share.streamlit.io).

> ⚠️ **Note:** Streamlit Community Cloud has an ephemeral filesystem.
> User data persists between app restarts but will be reset if the app
> is redeployed from scratch. For permanent production storage, connect
> a cloud database (e.g. Supabase, PlanetScale, or Streamlit's built-in secrets).

## Project Structure

```
app.py                        # Home dashboard
auth.py                       # Session management
database.py                   # SQLite persistence layer
requirements.txt
.streamlit/config.toml        # Theme config
pages/
  0_Login.py                  # Login & Create Account
  1_Profile.py                # Student profile setup
  2_Pre_Study_Routine.py      # Pre-study checklist
  3_AI_Timetable.py           # Smart timetable
  4_Progress_Tracker.py       # Chapter progress
  5_Session_Logger.py         # Study session logger
  6_Exam_Countdown.py         # Exam scheduler & countdown
```