"""
auth.py — InfoTech Study Companion  (v3)
Session management helpers.

HOW SESSIONS WORK IN THIS APP
──────────────────────────────
Streamlit's st.session_state is per browser-tab and is reset whenever the
server restarts.  We persist the authenticated user_id in a tiny JSON file
inside the app-data directory so that:

  • Page refreshes keep the correct user logged in.
  • Different browser tabs that share the same Streamlit token (same person)
    stay on the same account.
  • A new visitor who has never logged in always lands on the auth page.
  • Logging out clears both session_state AND the token file so a new visitor
    can log in as a completely different user.

Security note:
  The token file is stored on the server's local filesystem
  (~/.infotech_study_companion/session_token.json).
  This is appropriate for a single-user Codespace / local deployment.
  For a multi-user cloud deployment, replace with a proper server-side
  session store or JWT cookies.
"""

import json
import os
import streamlit as st
from pathlib import Path
from database import get_user_by_id, initialise_database

# ── Paths ──────────────────────────────────────────────────────────────────────
_APP_DIR     = Path(os.path.expanduser("~/.infotech_study_companion"))
_TOKEN_FILE  = _APP_DIR / "session_token.json"

# ── Session state keys ─────────────────────────────────────────────────────────
_KEY_USER_ID   = "auth_user_id"
_KEY_USERNAME  = "auth_username"
_KEY_LOGGED_IN = "auth_logged_in"


# ── Internal helpers ───────────────────────────────────────────────────────────

def _save_token(user_id: int, username: str) -> None:
    """Persist session to disk so page refreshes don't log the user out."""
    _APP_DIR.mkdir(parents=True, exist_ok=True)
    _TOKEN_FILE.write_text(json.dumps({"user_id": user_id, "username": username}))


def _clear_token() -> None:
    """Remove the on-disk session token."""
    if _TOKEN_FILE.exists():
        _TOKEN_FILE.unlink()


def _load_token() -> dict | None:
    """Read the on-disk token and validate that the user still exists in the DB."""
    if not _TOKEN_FILE.exists():
        return None
    try:
        data = json.loads(_TOKEN_FILE.read_text())
        user_id  = int(data["user_id"])
        username = str(data["username"])
        # Validate the user still exists in the DB
        user = get_user_by_id(user_id)
        if user and user["username"].lower() == username.lower():
            return {"user_id": user_id, "username": user["username"]}
    except Exception:
        pass
    # Token corrupt or user deleted — clean up
    _clear_token()
    return None


# ── Public API ─────────────────────────────────────────────────────────────────

def boot_auth() -> None:
    """
    Call once at the top of every page (before any other DB call).
    1. Ensures the database schema exists.
    2. Tries to restore an existing session from the token file.
    """
    if "db_ready" not in st.session_state:
        try:
            initialise_database()
            st.session_state["db_ready"] = True
        except RuntimeError as e:
            st.error(f"🚨 Could not initialise database: {e}")
            st.stop()

    # Already in session_state — nothing to do
    if st.session_state.get(_KEY_LOGGED_IN):
        return

    # Try to restore from disk token
    token = _load_token()
    if token:
        st.session_state[_KEY_USER_ID]   = token["user_id"]
        st.session_state[_KEY_USERNAME]  = token["username"]
        st.session_state[_KEY_LOGGED_IN] = True


def login_user(user_id: int, username: str) -> None:
    """Called by the login page after successful credential verification."""
    st.session_state[_KEY_USER_ID]   = user_id
    st.session_state[_KEY_USERNAME]  = username
    st.session_state[_KEY_LOGGED_IN] = True
    _save_token(user_id, username)


def logout_user() -> None:
    """Clear all auth state and the on-disk token, then redirect to auth page."""
    # Remove auth keys
    for key in [_KEY_USER_ID, _KEY_USERNAME, _KEY_LOGGED_IN,
                "student_profile", "active_student_id", "completed_chapters",
                "db_ready"]:
        st.session_state.pop(key, None)
    _clear_token()


def is_logged_in() -> bool:
    return bool(st.session_state.get(_KEY_LOGGED_IN))


def current_user_id() -> int | None:
    return st.session_state.get(_KEY_USER_ID)


def current_username() -> str | None:
    return st.session_state.get(_KEY_USERNAME)


def require_login() -> int:
    """
    Guard every protected page with this call.
    If the user is not authenticated, redirect to the auth page and stop.
    Returns the current user_id if authenticated.
    """
    boot_auth()
    if not is_logged_in():
        st.switch_page("pages/0_Login.py")
        st.stop()
    uid = current_user_id()
    if uid is None:
        logout_user()
        st.switch_page("pages/0_Login.py")
        st.stop()
    return uid