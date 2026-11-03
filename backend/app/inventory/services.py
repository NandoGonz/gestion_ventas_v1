"""Reglas de negocio transaccionales para movimientos de inventario."""
from sqlalchemy import case, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import ConflictError, ResourceNotFoundError
from app.inventory.models import InventoryMovement, InventoryMovementType
from app.inventory.schemas import InventoryMovementCreate
from app.products.models import Product, ProductStatus


class InventoryService:
    def __init__(self, session: Session):
        self.session = session

    def list_stock(self, limit: int = 100, offset: int = 0) -> list[Product]:
        statement = select(Product).order_by(Product.id).limit(limit).offset(offset)
        return list(self.session.scalars(statement).all())

    def list_movements(self, limit: int = 100, offset: int = 0) -> list[InventoryMovement]:
        statement = (
            select(InventoryMovement)
            .options(joinedload(InventoryMovement.product))
            .order_by(InventoryMovement.fecha_creacion.desc(), InventoryMovement.id.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.session.scalars(statement).all())

    def register_entry(self, data: InventoryMovementCreate) -> InventoryMovement:
        statement = (
            update(Product)
            .where(
                Product.id == data.producto_id,
                Product.estado.in_([ProductStatus.DISPONIBLE, ProductStatus.AGOTADO]),
            )
            .values(stock=Product.stock + data.cantidad, estado=ProductStatus.DISPONIBLE)
            .returning(Product.id)
            .execution_options(synchronize_session=False)
        )
        return self._register_movement(statement, data, InventoryMovementType.ENTRADA)

    def register_exit(self, data: InventoryMovementCreate) -> InventoryMovement:
        statement = (
            update(Product)
            .where(
                Product.id == data.producto_id,
                Product.stock >= data.cantidad,
                Product.estado == ProductStatus.DISPONIBLE,
            )
            .values(
                stock=Product.stock - data.cantidad,
                estado=case(
                    (Product.stock == data.cantidad, ProductStatus.AGOTADO),
                    else_=Product.estado,
                ),
            )
            .returning(Product.id)
            .execution_options(synchronize_session=False)
        )
        return self._register_movement(statement, data, InventoryMovementType.SALIDA)

    def _register_movement(
        self,
        stock_statement,
        data: InventoryMovementCreate,
        movement_type: InventoryMovementType,
    ) -> InventoryMovement:
        try:
            product_id = self.session.execute(stock_statement).scalar_one_or_none()
            if product_id is None:
                self._raise_unavailable_product(data.producto_id, movement_type)

            movement = InventoryMovement(
                producto_id=product_id,
                tipo_movimiento=movement_type,
                cantidad=data.cantidad,
                motivo=data.motivo,
            )
            self.session.add(movement)
            self.session.flush()
            movement_id = movement.id
            movement = self._get_movement(movement_id)
            self.session.commit()
            return movement
        except SQLAlchemyError:
            self.session.rollback()
            raise

    def _raise_unavailable_product(self, product_id: int, movement_type: InventoryMovementType) -> None:
        product = self.session.scalar(select(Product).where(Product.id == product_id))
        if product is None:
            raise ResourceNotFoundError(f"No existe el producto {product_id}.")
        if movement_type == InventoryMovementType.SALIDA and product.stock <= 0:
            raise ConflictError(f"Stock insuficiente para '{product.nombre}'. Disponible: {product.stock}.")
        raise ConflictError(f"El producto '{product.nombre}' no está disponible para esta operación.")

    def _get_movement(self, movement_id: int) -> InventoryMovement:
        return self.session.scalar(
            select(InventoryMovement)
            .where(InventoryMovement.id == movement_id)
            .options(joinedload(InventoryMovement.product))
        )
