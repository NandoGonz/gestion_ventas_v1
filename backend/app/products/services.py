"""Reglas de negocio y persistencia de productos e inventario."""
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError
from app.inventory.models import InventoryMovement, InventoryMovementType
from app.products.models import Product, ProductStatus
from app.products.schemas import ProductCreate, ProductUpdate


class ProductService:
    def __init__(self, session: Session):
        self.session = session

    def create(self, data: ProductCreate) -> Product:
        try:
            values = data.model_dump()
            status = ProductStatus.AGOTADO if values["stock"] == 0 else ProductStatus.DISPONIBLE
            product = Product(**values, estado=status)
            self.session.add(product)
            self.session.flush()
            if product.stock > 0:
                self.session.add(
                    InventoryMovement(
                        producto_id=product.id,
                        tipo_movimiento=InventoryMovementType.ENTRADA,
                        cantidad=product.stock,
                        motivo="Stock inicial del producto",
                    )
                )
            self.session.commit()
            self.session.refresh(product)
            return product
        except SQLAlchemyError:
            self.session.rollback()
            raise

    def get(self, product_id: int) -> Product | None:
        return self.session.scalar(select(Product).where(Product.id == product_id))

    def list(self, limit: int = 100, offset: int = 0) -> list[Product]:
        statement = select(Product).order_by(Product.id).limit(limit).offset(offset)
        return list(self.session.scalars(statement).all())

    def update(self, product_id: int, data: ProductUpdate) -> Product | None:
        product = self.get(product_id)
        if product is None:
            return None
        values = data.model_dump(exclude_unset=True)
        requested_status = values.pop("estado", None)
        if requested_status is not None and requested_status not in {
            ProductStatus.PREVENTA,
            ProductStatus.DESCONTINUADO,
        }:
            raise BusinessRuleError("El estado solo puede cambiarse manualmente a preventa o descontinuado.")
        try:
            for key, value in values.items():
                setattr(product, key, value)
            if requested_status is not None:
                product.estado = requested_status
            self.session.commit()
            self.session.refresh(product)
            return product
        except SQLAlchemyError:
            self.session.rollback()
            raise
