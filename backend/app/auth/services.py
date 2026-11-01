"""Autenticación de usuarios y emisión de tokens."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, verify_password
from app.users.models import User


def authenticate_user(session: Session, email: str, password: str) -> tuple[User, str] | None:
    normalized_email = email.strip().lower()
    user = session.scalar(select(User).where(func.lower(User.email) == normalized_email))
    # La comprobación de hash solo se realiza si el usuario existe. La respuesta HTTP
    # no diferencia entre correo inexistente y contraseña incorrecta.
    if user is None or not user.is_active or not verify_password(password, user.password_hash):
        return None
    token = create_access_token(str(user.id))
    return user, token
