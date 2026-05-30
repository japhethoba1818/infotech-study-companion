"""
pages/0_Login.py — InfoTech Study Companion  (v3)
Authentication page: Create Account + Login with 4-digit PIN.
This is the FIRST page a visitor sees.
"""

import streamlit as st
from database import initialise_database, create_user, verify_user
from auth import boot_auth, login_user, is_logged_in

st.set_page_config(
    page_title="Login — InfoTech Study Companion",
    page_icon="🔐",
    layout="centered",
)

# ── Boot DB (no auth required on this page) ────────────────────────────────────
if "db_ready" not in st.session_state:
    try:
        initialise_database()
        st.session_state["db_ready"] = True
    except RuntimeError as e:
        st.error(f"🚨 Could not initialise database: {e}")
        st.stop()

boot_auth()

# ── Already logged in — send to dashboard ─────────────────────────────────────
if is_logged_in():
    st.switch_page("app.py")
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE STYLES
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
    /* Card container */
    .auth-card {
        background: #1F2635;
        border-radius: 16px;
        padding: 32px 28px;
        margin-bottom: 20px;
        border: 1px solid #2D3650;
    }
    /* PIN input — make it look like a PIN pad */
    input[type="password"] {
        letter-spacing: 0.5em;
        font-size: 22px !important;
        text-align: center;
    }
    /* Accent heading */
    .accent { color: #00FF87; }
    /* Sub text */
    .subtext { color: #A0AABF; font-size: 14px; }
    div[data-testid="stTabs"] button {
        font-size: 16px;
        font-weight: 600;
        padding: 10px 20px;
    }
</style>
""", unsafe_allow_html=True)

# ── Hero ───────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding: 20px 0 10px;">
    <h1 style="color:#00FF87; font-size:40px; font-weight:900; margin:0;">🎓</h1>
    <h2 style="color:#00FF87; font-weight:800; margin:6px 0 4px;">InfoTech Study Companion</h2>
    <p style="color:#A0AABF; font-size:15px; margin:0;">
        Your personal AI study mentor • Built for South African matric excellence
    </p>
</div>
""", unsafe_allow_html=True)

st.write("")

# ── Tabs: Login | Create Account ───────────────────────────────────────────────
tab_login, tab_create = st.tabs(["🔑  Login", "✨  Create Account"])

# ════════════════════════════════════════
# TAB 1 — LOGIN
# ════════════════════════════════════════
with tab_login:
    st.markdown("<h3 style='color:#fff;margin-bottom:4px;'>Welcome back 👋</h3>", unsafe_allow_html=True)
    st.markdown("<p class='subtext'>Enter your username and 4-digit PIN to access your account.</p>",
                unsafe_allow_html=True)
    st.write("")

    with st.form("login_form", clear_on_submit=False):
        login_username = st.text_input(
            "Username",
            placeholder="e.g. thabo_2026",
            max_chars=50,
        )
        login_pin = st.text_input(
            "4-Digit PIN",
            type="password",
            placeholder="••••",
            max_chars=4,
            help="Enter your 4-digit numeric PIN",
        )
        login_btn = st.form_submit_button("🔑 Login", use_container_width=True, type="primary")

    if login_btn:
        username_clean = login_username.strip()
        pin_clean      = login_pin.strip()

        # Client-side validation
        if not username_clean:
            st.error("⚠️ Please enter your username.")
        elif not pin_clean:
            st.error("⚠️ Please enter your 4-digit PIN.")
        elif len(pin_clean) != 4 or not pin_clean.isdigit():
            st.error("⚠️ PIN must be exactly 4 numeric digits (e.g. 1234).")
        else:
            with st.spinner("Verifying credentials…"):
                user = verify_user(username_clean, pin_clean)

            if user:
                login_user(user["id"], user["username"])
                st.success(f"✅ Welcome back, **{user['username']}**!")
                st.balloons()
                st.switch_page("app.py")
            else:
                st.error("❌ Incorrect username or PIN. Please try again.")
                st.caption("Tip: usernames are not case-sensitive.")

# ════════════════════════════════════════
# TAB 2 — CREATE ACCOUNT
# ════════════════════════════════════════
with tab_create:
    st.markdown("<h3 style='color:#fff;margin-bottom:4px;'>Create your account 🚀</h3>",
                unsafe_allow_html=True)
    st.markdown(
        "<p class='subtext'>Choose a username and a 4-digit PIN. "
        "Your progress, timetables, and exam countdowns are saved privately to your account.</p>",
        unsafe_allow_html=True,
    )
    st.write("")

    with st.form("create_form", clear_on_submit=True):
        new_username = st.text_input(
            "Choose a Username",
            placeholder="e.g. thabo_2026",
            max_chars=50,
            help="Only letters, numbers, underscores, and hyphens. 3–50 characters.",
        )

        col_pin1, col_pin2 = st.columns(2)
        with col_pin1:
            new_pin = st.text_input(
                "Choose a 4-Digit PIN",
                type="password",
                placeholder="••••",
                max_chars=4,
                help="Exactly 4 numbers, e.g. 7823",
            )
        with col_pin2:
            confirm_pin = st.text_input(
                "Confirm PIN",
                type="password",
                placeholder="••••",
                max_chars=4,
            )

        st.markdown(
            "<p class='subtext'>⚠️ Remember your PIN — it cannot be recovered if lost.</p>",
            unsafe_allow_html=True,
        )

        create_btn = st.form_submit_button("✨ Create Account", use_container_width=True, type="primary")

    if create_btn:
        username_clean  = new_username.strip()
        pin_clean       = new_pin.strip()
        confirm_clean   = confirm_pin.strip()

        # Validation
        error = None
        if not username_clean:
            error = "Username cannot be empty."
        elif len(username_clean) < 3:
            error = "Username must be at least 3 characters."
        elif not all(c.isalnum() or c in ("_", "-") for c in username_clean):
            error = "Username may only contain letters, numbers, underscores, and hyphens."
        elif not pin_clean:
            error = "PIN cannot be empty."
        elif len(pin_clean) != 4 or not pin_clean.isdigit():
            error = "PIN must be exactly 4 numeric digits (e.g. 4821)."
        elif pin_clean != confirm_clean:
            error = "PINs do not match. Please re-enter."

        if error:
            st.error(f"⚠️ {error}")
        else:
            try:
                with st.spinner("Creating your account…"):
                    user_id = create_user(username_clean, pin_clean)
                login_user(user_id, username_clean)
                st.success(f"🎉 Account created! Welcome, **{username_clean}**!")
                st.balloons()
                st.switch_page("pages/1_Profile.py")
            except RuntimeError as e:
                st.error(f"❌ {e}")

# ── Footer ─────────────────────────────────────────────────────────────────────
st.write("---")
st.markdown(
    "<p style='text-align:center;color:#A0AABF;font-size:12px;'>"
    "🔒 Your PIN is hashed and never stored in plain text. "
    "Your data is private and linked only to your account."
    "</p>",
    unsafe_allow_html=True,
)