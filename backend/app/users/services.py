"""Operaciones de aprovisionamiento de usuarios internos."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.users.models import User


def seed_bootstrap_admin(session: Session, *, full_name: str, email: str, password: str) -> User:
    """Crea el administrador inicial si no existe; nunca sobrescribe una cuenta existente."""
    normalized_email = email.strip().lower()
    user = session.scalar(select(User).where(User.email == normalized_email))
    if user:
        return user
    user = User(
        full_name=full_name.strip(),
        email=normalized_email,
        password_hash=hash_password(password),
        is_active=True,
        is_admin=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user
