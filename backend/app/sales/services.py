"""Reglas de negocio transaccionales para ventas e inventario."""
from decimal import Decimal

from sqlalchemy import case, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload, selectinload

from app.clients.models import Client, ClientStatus
from app.core.exceptions import ConflictError, ResourceNotFoundError
from app.inventory.models import InventoryMovement, InventoryMovementType
from app.products.models import Product, ProductStatus
from app.sales.models import PaymentMethod, Sale, SaleDetail
from app.sales.schemas import SaleCreate


class SaleService:
    def __init__(self, session: Session):
        self.session = session

    def create(self, data: SaleCreate, user_id: int) -> Sale:
        """Descuenta stock, crea venta/detalles y actualiza crédito en una transacción."""
        try:
            client = self.session.scalar(select(Client).where(Client.documento == data.cliente_documento))
            if client is None:
                raise ResourceNotFoundError(f"No existe el cliente {data.cliente_documento}.")
            if client.estado != ClientStatus.ACTIVO:
                raise ConflictError("Solo los clientes activos pueden generar ventas.")

            price_by_product: dict[int, Decimal] = {}
            for line in sorted(data.detalles, key=lambda item: item.producto_id):
                price_by_product[line.producto_id] = self._decrement_stock(line.producto_id, line.cantidad)

            detail_rows: list[SaleDetail] = []
            total = Decimal("0.00")
            for line in data.detalles:
                unit_price = Decimal(price_by_product[line.producto_id])
                total += unit_price * line.cantidad
                detail_rows.append(SaleDetail(
                    producto_id=line.producto_id,
                    cantidad=line.cantidad,
                    precio_unitario=unit_price,
                ))
            total = total.quantize(Decimal("0.01"))
            if total <= 0:
                raise ConflictError("El total de la venta debe ser mayor que cero.")

            if data.forma_pago == PaymentMethod.CREDITO:
                self.session.execute(
                    update(Client)
                    .where(Client.documento == data.cliente_documento)
                    .values(saldo=Client.saldo + total)
                    .execution_options(synchronize_session="fetch")
                )

            sale = Sale(
                cliente_documento=data.cliente_documento,
                usuario_id=user_id,
                forma_pago=data.forma_pago,
                total=total,
                estado="registrada",
            )
            sale.detalle_ventas = detail_rows
            self.session.add(sale)
            self.session.flush()
            sale_id = sale.id
            self.session.add_all(
                [
                    InventoryMovement(
                        producto_id=detail.producto_id,
                        tipo_movimiento=InventoryMovementType.VENTA,
                        cantidad=detail.cantidad,
                        motivo=f"Venta #{sale_id}",
                        venta_id=sale_id,
                    )
                    for detail in detail_rows
                ]
            )
            self.session.commit()
            return self.session.scalar(
                select(Sale)
                .where(Sale.id == sale_id)
                .options(selectinload(Sale.detalle_ventas).joinedload(SaleDetail.product))
            )
        except Exception:
            self.session.rollback()
            raise

    def _decrement_stock(self, product_id: int, quantity: int) -> Decimal:
        statement = (
            update(Product)
            .where(
                Product.id == product_id,
                Product.stock >= quantity,
                Product.estado == ProductStatus.DISPONIBLE,
            )
            .values(
                stock=Product.stock - quantity,
                estado=case(
                    (Product.stock == quantity, ProductStatus.AGOTADO),
                    else_=Product.estado,
                ),
            )
            .returning(Product.precio)
            .execution_options(synchronize_session=False)
        )
        price = self.session.execute(statement).scalar_one_or_none()
        if price is not None:
            return Decimal(price)
        product = self.session.scalar(select(Product).where(Product.id == product_id))
        if product is None:
            raise ResourceNotFoundError(f"No existe el producto {product_id}.")
        if product.estado != ProductStatus.DISPONIBLE:
            raise ConflictError(f"El producto '{product.nombre}' no está disponible.")
        raise ConflictError(
            f"Stock insuficiente para '{product.nombre}'. Disponible: {product.stock}; solicitado: {quantity}."
        )

    def get(self, sale_id: int) -> Sale | None:
        return self.session.scalar(
            select(Sale)
            .where(Sale.id == sale_id)
            .options(selectinload(Sale.detalle_ventas).joinedload(SaleDetail.product))
        )

    def list(self, limit: int = 100, offset: int = 0) -> list[Sale]:
        statement = (
            select(Sale)
            .options(selectinload(Sale.detalle_ventas).joinedload(SaleDetail.product))
            .order_by(Sale.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.session.scalars(statement).all())
