"""Modelo ORM de clientes, conservando saldo e historial comercial."""
from datetime import datetime
from decimal import Decimal
from enum import Enum
from sqlalchemy import CheckConstraint, DateTime, Enum as SQLEnum, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class ClientStatus(str, Enum):
    ACTIVO = "activo"
    INACTIVO = "inactivo"
    MOROSO = "moroso"
    SUSPENDIDO = "suspendido"


class Client(Base):
    __tablename__ = "clientes"
    __table_args__ = (CheckConstraint("saldo >= 0", name="ck_clientes_saldo_no_negativo"),)

    documento: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(60), nullable=False)
    apellido: Mapped[str] = mapped_column(String(60), nullable=False)
    direccion: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str | None] = mapped_column(String(254), unique=True, nullable=True, index=True)
    saldo: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"), nullable=False)
    estado: Mapped[ClientStatus] = mapped_column(
        SQLEnum(ClientStatus, name="estado_cliente", values_callable=lambda enum: [item.value for item in enum]),
        default=ClientStatus.ACTIVO,
        nullable=False,
    )
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    fecha_actualizacion: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    sales: Mapped[list["Sale"]] = relationship(back_populates="client")
