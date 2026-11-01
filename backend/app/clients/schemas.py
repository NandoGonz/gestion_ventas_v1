"""Esquemas de validación y respuesta para clientes."""
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator
from app.clients.models import ClientStatus


class ClientCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    documento: int = Field(gt=0)
    nombre: str = Field(min_length=2, max_length=60)
    apellido: str = Field(min_length=2, max_length=60)
    direccion: str = Field(min_length=3, max_length=120)
    email: EmailStr | None = None
    saldo: Decimal = Field(default=Decimal("0.00"), ge=0, max_digits=12, decimal_places=2)


class ClientUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    nombre: str | None = Field(default=None, min_length=2, max_length=60)
    apellido: str | None = Field(default=None, min_length=2, max_length=60)
    direccion: str | None = Field(default=None, min_length=3, max_length=120)
    email: EmailStr | None = None

    @model_validator(mode="after")
    def require_changes(self) -> "ClientUpdate":
        if not self.model_fields_set:
            raise ValueError("Indica al menos un campo para actualizar.")
        for field in ("nombre", "apellido", "direccion"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"El campo {field} no puede ser nulo.")
        return self


class ClientStatusUpdate(BaseModel):
    estado: ClientStatus


class ClientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    documento: int
    nombre: str
    apellido: str
    direccion: str
    email: EmailStr | None
    saldo: Decimal
    estado: ClientStatus
    fecha_creacion: datetime
    fecha_actualizacion: datetime
