"""Esquemas para crear ventas y presentar su historial."""
from datetime import date, datetime
from decimal import Decimal
from pydantic import AliasPath, BaseModel, ConfigDict, Field, model_validator
from app.sales.models import PaymentMethod


class SaleDetailCreate(BaseModel):
    producto_id: int = Field(gt=0)
    cantidad: int = Field(gt=0, le=1_000_000)


class SaleCreate(BaseModel):
    cliente_documento: int = Field(gt=0)
    forma_pago: PaymentMethod
    detalles: list[SaleDetailCreate] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def unique_products(self) -> "SaleCreate":
        product_ids = [detail.producto_id for detail in self.detalles]
        if len(product_ids) != len(set(product_ids)):
            raise ValueError("Cada producto debe aparecer una sola vez en los detalles.")
        return self


class SaleDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    venta_id: int
    producto_id: int
    producto_nombre: str = Field(validation_alias=AliasPath("product", "nombre"))
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal


class SaleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    fecha: date
    forma_pago: PaymentMethod
    cliente_documento: int
    usuario_id: int
    total: Decimal
    estado: str
    fecha_creacion: datetime
    detalle_ventas: list[SaleDetailResponse]
