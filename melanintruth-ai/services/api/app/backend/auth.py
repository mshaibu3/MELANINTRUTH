from __future__ import annotations

from .audit import AuditService
from .entities import Device, Session, User, new_id, now
from .errors import AuthenticationError, ConflictError, NotFoundError, ValidationError
from .repository import InMemoryRepository
from .security import hash_password, hash_token, issue_access_token, new_refresh_token, verify_password


class LoginRateLimitHook:
    def __init__(self, threshold: int = 5):
        self.threshold = threshold
        self.failures: dict[str, int] = {}

    def check(self, key: str) -> None:
        if self.failures.get(key, 0) >= self.threshold:
            raise AuthenticationError("too many failed login attempts")

    def failed(self, key: str) -> None:
        self.failures[key] = self.failures.get(key, 0) + 1

    def succeeded(self, key: str) -> None:
        self.failures.pop(key, None)


class AuthService:
    def __init__(self, repo: InMemoryRepository, audit: AuditService, limiter: LoginRateLimitHook | None = None):
        self.repo = repo
        self.audit = audit
        self.limiter = limiter or LoginRateLimitHook()

    def register(self, email: str, password: str, tenant_id: str | None = None, roles: set[str] | None = None) -> User:
        normalized = email.strip().lower()
        if normalized in self.repo.users_by_email:
            raise ConflictError("email already registered")
        if len(password) < 12:
            raise ValidationError("password must be at least 12 characters")
        user = User(email=normalized, password_hash=hash_password(password), tenant_id=tenant_id or new_id(), roles=roles or {"user"})
        self.repo.users[user.id] = user
        self.repo.users_by_email[normalized] = user.id
        self.audit.record("auth.registered", "user", user.id, user.id, user.tenant_id, {"email_domain": normalized.split("@")[-1]})
        return user

    def login(self, email: str, password: str, device_label: str) -> dict[str, str]:
        normalized = email.strip().lower()
        self.limiter.check(normalized)
        user_id = self.repo.users_by_email.get(normalized)
        user = self.repo.users.get(user_id or "")
        if not user or user.deleted_at or not verify_password(password, user.password_hash):
            self.limiter.failed(normalized)
            self.audit.record("auth.failed_login", "user", user_id, user_id, user.tenant_id if user else None, {"email_domain": normalized.split("@")[-1]})
            raise AuthenticationError("invalid credentials")
        self.limiter.succeeded(normalized)
        device = Device(user_id=user.id, tenant_id=user.tenant_id, label=device_label)
        refresh = new_refresh_token()
        session = Session(user_id=user.id, tenant_id=user.tenant_id, device_id=device.id, refresh_token_hash=hash_token(refresh))
        self.repo.devices[device.id] = device
        self.repo.sessions[session.id] = session
        self.audit.record("auth.login", "session", session.id, user.id, user.tenant_id, {"device_id": device.id})
        return {"access_token": issue_access_token(user.id, user.tenant_id, user.roles), "refresh_token": refresh, "session_id": session.id}

    def refresh(self, session_id: str, refresh_token: str) -> dict[str, str]:
        session = self.repo.sessions.get(session_id)
        if not session or session.revoked_at or session.refresh_token_hash != hash_token(refresh_token):
            raise AuthenticationError("invalid refresh token")
        user = self.repo.users[session.user_id]
        new_token = new_refresh_token()
        session.refresh_token_hash = hash_token(new_token)
        self.audit.record("auth.token_refreshed", "session", session.id, user.id, user.tenant_id, {})
        return {"access_token": issue_access_token(user.id, user.tenant_id, user.roles), "refresh_token": new_token, "session_id": session.id}

    def logout(self, user_id: str, session_id: str) -> None:
        session = self.repo.sessions.get(session_id)
        if not session or session.user_id != user_id:
            raise NotFoundError("session not found")
        session.revoked_at = now()
        self.audit.record("auth.logout", "session", session.id, user_id, session.tenant_id, {})

    def request_account_deletion(self, user_id: str) -> None:
        user = self.repo.users[user_id]
        self.audit.record("privacy.account_deletion_requested", "user", user.id, user.id, user.tenant_id, {})
