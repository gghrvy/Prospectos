import base64
import hashlib
import hmac
import json
import secrets
import time
from email.mime.text import MIMEText
from urllib.parse import urlencode

import httpx
from cryptography.fernet import Fernet
from fastapi import HTTPException

from app.database.config import Settings

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GMAIL_SCOPE = "https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/gmail.readonly"


def _require_settings(settings: Settings) -> None:
    if not settings.google_client_id or not settings.google_client_secret or not settings.gmail_token_encryption_key:
        raise HTTPException(503, "Gmail is not configured. Add the Google OAuth values to backend/.env and restart the backend.")


def _fernet(settings: Settings) -> Fernet:
    _require_settings(settings)
    try:
        return Fernet(settings.gmail_token_encryption_key.encode())
    except Exception as exc:
        raise HTTPException(503, "GMAIL_TOKEN_ENCRYPTION_KEY is invalid.") from exc


def authorization_url(settings: Settings) -> str:
    _require_settings(settings)
    issued = str(int(time.time()))
    nonce = secrets.token_urlsafe(16)
    payload = f"{issued}.{nonce}"
    signature = hmac.new(settings.google_client_secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    state = base64.urlsafe_b64encode(f"{payload}.{signature}".encode()).decode()
    return GOOGLE_AUTH_URL + "?" + urlencode({
        "client_id": settings.google_client_id, "redirect_uri": settings.google_oauth_redirect_uri,
        "response_type": "code", "scope": GMAIL_SCOPE, "access_type": "offline",
        "prompt": "consent", "state": state,
    })


def validate_state(state: str | None, settings: Settings) -> None:
    try:
        issued, nonce, signature = base64.urlsafe_b64decode((state or "").encode()).decode().split(".", 2)
        payload = f"{issued}.{nonce}"
        expected = hmac.new(settings.google_client_secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected) or time.time() - int(issued) > 600:
            raise ValueError
    except Exception as exc:
        raise HTTPException(400, "Gmail authorization request expired or was invalid. Try connecting again.") from exc


def exchange_code(code: str, settings: Settings) -> tuple[str, str]:
    response = httpx.post(GOOGLE_TOKEN_URL, data={
        "code": code, "client_id": settings.google_client_id, "client_secret": settings.google_client_secret,
        "redirect_uri": settings.google_oauth_redirect_uri, "grant_type": "authorization_code",
    }, timeout=20)
    if response.is_error:
        # Google returns useful, non-sensitive OAuth error identifiers such as
        # ``invalid_client`` or ``invalid_grant``. Surface that identifier so
        # a local configuration problem can be fixed without exposing either
        # the authorization code or client secret.
        try:
            reason = response.json().get("error", "authorization_exchange_failed")
        except ValueError:
            reason = "authorization_exchange_failed"
        raise HTTPException(400, f"Google could not complete the Gmail connection ({reason}).")
    data = response.json()
    if not data.get("refresh_token") or not data.get("access_token"):
        raise HTTPException(400, "Google did not return a refresh token. Disconnect the app in Google Account settings, then connect again.")
    profile = httpx.get("https://gmail.googleapis.com/gmail/v1/users/me/profile",
                       headers={"Authorization": f"Bearer {data['access_token']}"}, timeout=20)
    if profile.is_error:
        raise HTTPException(400, "Gmail authorization succeeded but the account could not be verified.")
    return profile.json()["emailAddress"], data["refresh_token"]


def send_message(to: str, subject: str, body: str, encrypted_refresh_token: str, settings: Settings) -> dict[str, str]:
    refresh_token = _fernet(settings).decrypt(encrypted_refresh_token.encode()).decode()
    token = httpx.post(GOOGLE_TOKEN_URL, data={
        "client_id": settings.google_client_id, "client_secret": settings.google_client_secret,
        "refresh_token": refresh_token, "grant_type": "refresh_token",
    }, timeout=20)
    if token.is_error:
        raise HTTPException(401, "The Gmail connection has expired or was revoked. Connect Gmail again.")
    message = MIMEText(body, "plain", "utf-8")
    message["To"], message["Subject"] = to, subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    sent = httpx.post("https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
                      headers={"Authorization": f"Bearer {token.json()['access_token']}"},
                      json={"raw": raw}, timeout=20)
    if sent.is_error:
        raise HTTPException(502, "Gmail could not send this draft. No send was recorded.")
    return {"id": sent.json()["id"], "threadId": sent.json().get("threadId", "")}


def access_token(encrypted_refresh_token: str, settings: Settings) -> str:
    refresh_token = _fernet(settings).decrypt(encrypted_refresh_token.encode()).decode()
    response = httpx.post(GOOGLE_TOKEN_URL, data={"client_id": settings.google_client_id, "client_secret": settings.google_client_secret, "refresh_token": refresh_token, "grant_type": "refresh_token"}, timeout=20)
    if response.is_error:
        raise HTTPException(401, "The Gmail connection has expired or was revoked. Connect Gmail again.")
    return response.json()["access_token"]
