
import hashlib
import hmac

import streamlit as st
from sqlalchemy import select

from database import SessionLocal
from models import User


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password against its PBKDF2 hash."""

    try:
        algorithm, iterations, salt, expected_hash = stored_hash.split("$")

        if algorithm != "pbkdf2_sha256":
            return False

        actual_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            int(iterations),
        ).hex()

        return hmac.compare_digest(actual_hash, expected_hash)

    except (ValueError, TypeError):
        return False


def authenticate_user(username: str, password: str):
    """Return an active user if the credentials are valid."""

    db = SessionLocal()

    try:
        user = db.scalar(
            select(User).where(
                User.username == username.strip(),
                User.is_active.is_(True),
            )
        )

        if user and verify_password(password, user.password_hash):
            return {
                "id": user.id,
                "username": user.username,
                "full_name": user.full_name,
                "role": user.role,
            }

        return None

    finally:
        db.close()


def logout():
    """Clear the current login session."""

    for key in ("authenticated", "user_id", "username", "full_name", "role"):
        st.session_state.pop(key, None)

    st.rerun()
