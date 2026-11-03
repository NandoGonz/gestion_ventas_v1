"""Modelos ORM para el historial inmutable de inventario."""
from datetime import datetime
from enum import Enum

from sqlalchemy import CheckConstraint, DateTime, Enum as SQLEnum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class InventoryMovementType(str, Enum):
    ENTRADA = "entrada"
    SALIDA = "salida"
    VENTA = "venta"


class InventoryMovement(Base):
    __tablename__ = "movimientos_inventario"
    __table_args__ = (
        CheckConstraint("cantidad > 0", name="ck_movimientos_inventario_cantidad_positiva"),
        CheckConstraint(
            "(tipo_movimiento = 'venta' AND venta_id IS NOT NULL) "
            "OR (tipo_movimiento IN ('entrada', 'salida') AND venta_id IS NULL)",
            name="ck_movimientos_inventario_referencia_venta",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    producto_id: Mapped[int] = mapped_column(
        ForeignKey("productos.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    tipo_movimiento: Mapped[InventoryMovementType] = mapped_column(
        SQLEnum(
            InventoryMovementType,
            name="tipo_movimiento_inventario",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
    )
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    motivo: Mapped[str] = mapped_column(String(500), nullable=False)
    venta_id: Mapped[int | None] = mapped_column(
        ForeignKey("ventas.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    product: Mapped["Product"] = relationship(back_populates="inventory_movements")
    sale: Mapped["Sale | None"] = relationship(back_populates="inventory_movements")
