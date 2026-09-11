import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from fastapi import Cookie, Depends, Header, HTTPException, Request, Response, status
from pwdlib import PasswordHash
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from .database import get_db
from .models import AppSession, User
from .settings import Settings, get_settings

password_hash = PasswordHash.recommended()


def utc(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def verify_password(plain: str, encoded: str) -> bool:
    if encoded.startswith("pbkdf2_sha256$"):
        try:
            _, iterations, salt, expected = encoded.split("$", 3)
            calculated = hashlib.pbkdf2_hmac("sha256", plain.encode(), salt.encode(), int(iterations))
            return hmac.compare_digest(base64.b64encode(calculated).decode(), expected)
        except (ValueError, TypeError):
            return False
    try:
        return password_hash.verify(plain, encoded)
    except Exception:
        return False


def new_session(db: Session, user: User, settings: Settings) -> tuple[str, AppSession]:
    token = secrets.token_urlsafe(48)
    now = datetime.now(timezone.utc)
    session = AppSession(token_hash=hash_token(token), user_id=user.id, csrf_token=secrets.token_urlsafe(32), expires_at=now + timedelta(hours=settings.session_hours), last_seen_at=now)
    db.add(session)
    user.last_login = now
    db.commit()
    db.refresh(session)
    return token, session


def set_session_cookie(response: Response, token: str, settings: Settings) -> None:
    response.set_cookie(settings.session_cookie, token, max_age=settings.session_hours * 3600, httponly=True, secure=settings.app_mode != "local-demo", samesite="lax", path="/")


def current_user(request: Request, db: Session = Depends(get_db), settings: Settings = Depends(get_settings), x_csrftoken: str | None = Header(None)) -> User:
    token = request.cookies.get(settings.session_cookie)
    if not token:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Authentication required.")
    session = db.scalar(select(AppSession).where(AppSession.token_hash == hash_token(token)))
    now = datetime.now(timezone.utc)
    if not session or utc(session.expires_at) <= now:
        if session:
            db.delete(session)
            db.commit()
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Your session has expired.")
    unsafe = request.method not in {"GET", "HEAD", "OPTIONS"}
    if unsafe and (not x_csrftoken or not hmac.compare_digest(x_csrftoken, session.csrf_token)):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "CSRF validation failed.")
    user = db.scalar(select(User).where(User.id == session.user_id, User.is_active.is_(True)))
    if not user or not user.tenant or user.tenant.key != settings.tenant_key:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account is not available in this workspace.")
    session.last_seen_at = now
    session.expires_at = now + timedelta(hours=settings.session_hours)
    db.commit()
    return user


def delete_session(request: Request, response: Response, db: Session, settings: Settings) -> None:
    token = request.cookies.get(settings.session_cookie)
    if token:
        db.execute(delete(AppSession).where(AppSession.token_hash == hash_token(token)))
        db.commit()
    response.delete_cookie(settings.session_cookie, path="/")
