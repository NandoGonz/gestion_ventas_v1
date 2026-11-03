"""Modelos ORM de ventas y líneas de venta."""
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from sqlalchemy import CheckConstraint, Computed, Date, DateTime, Enum as SQLEnum, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class PaymentMethod(str, Enum):
    DECONTADO = "decontado"  # Se conserva el valor de la V1 anterior.
    CREDITO = "credito"
    TRANSFERENCIA = "transferencia"


class Sale(Base):
    __tablename__ = "ventas"
    __table_args__ = (CheckConstraint("total > 0", name="ck_ventas_total_positivo"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    fecha: Mapped[date] = mapped_column(Date, server_default=func.current_date(), nullable=False)
    forma_pago: Mapped[PaymentMethod] = mapped_column(
        SQLEnum(PaymentMethod, name="forma_pago", values_callable=lambda enum: [item.value for item in enum]),
        default=PaymentMethod.DECONTADO,
        nullable=False,
    )
    cliente_documento: Mapped[int] = mapped_column(ForeignKey("clientes.documento", ondelete="RESTRICT"), nullable=False, index=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False, index=True)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), default="registrada", nullable=False)
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    client: Mapped["Client"] = relationship(back_populates="sales")
    user: Mapped["User"] = relationship(back_populates="sales")
    detalle_ventas: Mapped[list["SaleDetail"]] = relationship(back_populates="sale", cascade="all, delete-orphan", passive_deletes=True)
    inventory_movements: Mapped[list["InventoryMovement"]] = relationship(back_populates="sale")


class SaleDetail(Base):
    __tablename__ = "detalle_venta"
    __table_args__ = (
        CheckConstraint("cantidad > 0", name="ck_detalle_cantidad_positiva"),
        CheckConstraint("precio_unitario > 0", name="ck_detalle_precio_positivo"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    venta_id: Mapped[int] = mapped_column(ForeignKey("ventas.id", ondelete="CASCADE"), nullable=False, index=True)
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id", ondelete="RESTRICT"), nullable=False, index=True)
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2), Computed("cantidad * precio_unitario", persisted=True), nullable=False)

    sale: Mapped["Sale"] = relationship(back_populates="detalle_ventas")
    product: Mapped["Product"] = relationship(back_populates="sale_details")
