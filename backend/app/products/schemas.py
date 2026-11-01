"""Esquemas de validación y respuesta para productos."""
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.products.models import ProductStatus


class ProductCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    nombre: str = Field(min_length=2, max_length=80)
    descripcion: str = Field(default="", max_length=500)
    precio: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    stock: int = Field(ge=0, le=1_000_000)


class ProductUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    nombre: str | None = Field(default=None, min_length=2, max_length=80)
    descripcion: str | None = Field(default=None, max_length=500)
    precio: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    stock: int | None = Field(default=None, ge=0, le=1_000_000)
    estado: ProductStatus | None = None

    @model_validator(mode="after")
    def validate_update(self) -> "ProductUpdate":
        if not self.model_fields_set:
            raise ValueError("Indica al menos un campo para actualizar.")
        if "nombre" in self.model_fields_set and self.nombre is None:
            raise ValueError("El nombre no puede ser nulo.")
        if "descripcion" in self.model_fields_set and self.descripcion is None:
            raise ValueError("La descripción no puede ser nula.")
        if "precio" in self.model_fields_set and self.precio is None:
            raise ValueError("El precio no puede ser nulo.")
        if "stock" in self.model_fields_set and self.stock is None:
            raise ValueError("El stock no puede ser nulo.")
        return self


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str
    descripcion: str
    precio: Decimal
    stock: int
    estado: ProductStatus
    fecha_registro: datetime
    fecha_actualizacion: datetime
