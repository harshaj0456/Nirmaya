"""
Real authentication (replaces the earlier prototype's "role as a UI
toggle"). This is deliberately simple - a demo-scale token store, not a
production auth system - but it enforces two real things: a password
check on login, and a server-side check on every subsequent request, so
the frontend can no longer just claim a role without credentials.

Production upgrade path: replace the in-memory TOKENS dict with signed,
expiring JWTs (or session rows in Postgres), and swap the shared demo
password for per-user credentials or institutional SSO.
"""
import secrets
from werkzeug.security import check_password_hash
from mock_data import USERS

TOKENS = {}  # token -> username (role_key)


def login(username, password):
    user = USERS.get(username)
    if not user or not check_password_hash(user["password_hash"], password):
        return None
    token = secrets.token_hex(20)
    TOKENS[token] = username
    return token


def role_for_token(token):
    return TOKENS.get(token)


def logout(token):
    TOKENS.pop(token, None)
