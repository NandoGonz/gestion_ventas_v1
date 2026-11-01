"""Funciones criptográficas para hashes de contraseñas y tokens JWT."""
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from jose import JWTError, jwt
from pwdlib import PasswordHash
from pwdlib.exceptions import PwdlibError

from app.core.config import settings

password_hasher = PasswordHash.recommended()

def hash_password(password: str) -> str:
    """Devuelve un hash Argon2; nunca almacena la contraseña en texto plano."""
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verifica una contraseña usando el hash previamente almacenado."""
    try:
        return password_hasher.verify(password, password_hash)
    except (PwdlibError, ValueError, TypeError):
        return False


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    now = datetime.now(timezone.utc)
    lifetime = expires_delta or timedelta(minutes=settings.jwt_expiration_minutes)
    payload = {
        "sub": str(subject),
        "iat": now,
        "exp": now + lifetime,
        "jti": str(uuid4()),
        "iss": settings.jwt_issuer,
        "aud": settings.jwt_audience,
        "type": "access",
    }
    return jwt.encode(payload, settings.app_jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    """Verifica firma, algoritmo, expiración, emisor y audiencia del token."""
    try:
        payload = jwt.decode(
            token,
            settings.app_jwt_secret,
            algorithms=[settings.jwt_algorithm],
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            options={"require_exp": True, "require_sub": True},
        )
    except JWTError as exc:
        raise ValueError("Token inválido o vencido") from exc
    if payload.get("type") != "access" or not isinstance(payload.get("sub"), str):
        raise ValueError("Token de acceso inválido")
    return payload
