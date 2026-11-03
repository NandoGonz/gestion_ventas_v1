"""Esquemas de validación y respuesta para inventario."""
from datetime import datetime

from pydantic import AliasPath, BaseModel, ConfigDict, Field

from app.inventory.models import InventoryMovementType


class InventoryMovementCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    producto_id: int = Field(gt=0)
    cantidad: int = Field(gt=0, le=1_000_000)
    motivo: str = Field(min_length=1, max_length=500)


class InventoryMovementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    producto_id: int
    producto_nombre: str = Field(validation_alias=AliasPath("product", "nombre"))
    tipo_movimiento: InventoryMovementType
    cantidad: int
    motivo: str
    venta_id: int | None
    fecha_creacion: datetime
