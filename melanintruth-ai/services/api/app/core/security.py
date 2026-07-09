import hashlib, secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID
import jwt
from passlib.context import CryptContext
from .config import settings
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
def hash_password(password: str) -> str: return pwd_context.hash(password)
def verify_password(password: str, hashed: str) -> bool: return pwd_context.verify(password, hashed)
def hash_token(token: str) -> str: return hashlib.sha256(token.encode()).hexdigest()
def new_refresh_token() -> str: return secrets.token_urlsafe(48)
def create_access_token(user_id: UUID, tenant_id: UUID, roles: list[str]) -> str:
    now=datetime.now(timezone.utc)
    payload={"sub":str(user_id),"tenant_id":str(tenant_id),"roles":roles,"iss":settings.jwt_issuer,"aud":settings.jwt_audience,"iat":now,"exp":now+timedelta(minutes=settings.jwt_access_ttl_minutes)}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")
