"""Modelo ORM de catálogo e inventario de productos."""
from datetime import datetime
from decimal import Decimal
from enum import Enum
from sqlalchemy import CheckConstraint, DateTime, Enum as SQLEnum, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class ProductStatus(str, Enum):
    DISPONIBLE = "disponible"
    AGOTADO = "agotado"
    DESCONTINUADO = "descontinuado"
    PREVENTA = "preventa"


class Product(Base):
    __tablename__ = "productos"
    __table_args__ = (
        CheckConstraint("precio > 0", name="ck_productos_precio_positivo"),
        CheckConstraint("stock >= 0", name="ck_productos_stock_no_negativo"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    descripcion: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    precio: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    estado: Mapped[ProductStatus] = mapped_column(
        SQLEnum(ProductStatus, name="estado_producto", values_callable=lambda enum: [item.value for item in enum]),
        default=ProductStatus.DISPONIBLE,
        nullable=False,
    )
    fecha_registro: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    fecha_actualizacion: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    sale_details: Mapped[list["SaleDetail"]] = relationship(back_populates="product")
    inventory_movements: Mapped[list["InventoryMovement"]] = relationship(back_populates="product")
