"""Endpoints protegidos de ventas."""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import ResourceNotFoundError
from app.core.dependencies import get_current_admin
from app.sales.schemas import SaleCreate, SaleResponse
from app.sales.services import SaleService
from app.users.models import User

router = APIRouter()


@router.post("/", response_model=SaleResponse, status_code=status.HTTP_201_CREATED)
def create_sale(payload: SaleCreate, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    return SaleService(db).create(payload, user_id=admin.id)


@router.get("/", response_model=list[SaleResponse])
def list_sales(
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    return SaleService(db).list(limit, offset)


@router.get("/{sale_id}", response_model=SaleResponse)
def get_sale(sale_id: int, db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)):
    sale = SaleService(db).get(sale_id)
    if sale is None:
        raise ResourceNotFoundError(f"No existe la venta {sale_id}.")
    return sale
