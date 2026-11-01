"""Esquemas públicos de cuentas de usuario."""
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    full_name: str
    email: EmailStr
    is_active: bool
    is_admin: bool
    created_at: datetime
