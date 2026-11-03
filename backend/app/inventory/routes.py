"""Endpoints protegidos para consultar y ajustar inventario."""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_admin
from app.inventory.schemas import InventoryMovementCreate, InventoryMovementResponse
from app.inventory.services import InventoryService
from app.products.schemas import ProductResponse
from app.users.models import User

router = APIRouter()


@router.get("/", response_model=list[ProductResponse])
def list_inventory(
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    return InventoryService(db).list_stock(limit, offset)


@router.get("/movimientos", response_model=list[InventoryMovementResponse])
def list_movements(
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    return InventoryService(db).list_movements(limit, offset)


@router.post("/entradas", response_model=InventoryMovementResponse, status_code=status.HTTP_201_CREATED)
def register_entry(
    payload: InventoryMovementCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    return InventoryService(db).register_entry(payload)


@router.post("/salidas", response_model=InventoryMovementResponse, status_code=status.HTTP_201_CREATED)
def register_exit(
    payload: InventoryMovementCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    return InventoryService(db).register_exit(payload)
