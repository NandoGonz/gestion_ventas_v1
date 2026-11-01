"""Endpoints protegidos para catálogo e inventario."""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import ResourceNotFoundError
from app.core.dependencies import get_current_admin
from app.products.schemas import ProductCreate, ProductResponse, ProductUpdate
from app.products.services import ProductService
from app.users.models import User

router = APIRouter()


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)):
    return ProductService(db).create(payload)


@router.get("/", response_model=list[ProductResponse])
def list_products(
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    return ProductService(db).list(limit, offset)


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)):
    product = ProductService(db).get(product_id)
    if product is None:
        raise ResourceNotFoundError(f"No existe el producto {product_id}.")
    return product


@router.patch("/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)):
    product = ProductService(db).update(product_id, payload)
    if product is None:
        raise ResourceNotFoundError(f"No existe el producto {product_id}.")
    return product
