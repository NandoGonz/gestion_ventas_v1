"""Endpoints de inicio de sesión y consulta de identidad."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.auth.schemas import TokenResponse
from app.auth.services import authenticate_user
from app.users.models import User
from app.users.schemas import UserResponse

router = APIRouter()


@router.post("/login", response_model=TokenResponse, summary="Iniciar sesión")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> TokenResponse:
    """Recibe email en el campo OAuth2 username y emite un JWT de acceso."""
    result = authenticate_user(db, form.username, form.password)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    _user, token = result
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse, summary="Usuario autenticado")
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
