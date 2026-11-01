"""Esquemas para la respuesta del inicio de sesión."""
from pydantic import BaseModel


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
