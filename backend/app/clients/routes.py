"""Endpoints protegidos de clientes."""
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.clients.schemas import ClientCreate, ClientResponse, ClientStatusUpdate, ClientUpdate
from app.clients.services import ClientService
from app.core.database import get_db
from app.core.exceptions import ResourceNotFoundError
from app.core.dependencies import get_current_admin
from app.users.models import User

router = APIRouter()


@router.post("/", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
def create_client(payload: ClientCreate, db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)):
    return ClientService(db).create(payload)


@router.get("/", response_model=list[ClientResponse])
def list_clients(
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    return ClientService(db).list(limit, offset)


@router.get("/{documento}", response_model=ClientResponse)
def get_client(documento: int, db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)):
    client = ClientService(db).get(documento)
    if client is None:
        raise ResourceNotFoundError(f"No existe el cliente {documento}.")
    return client


@router.patch("/{documento}", response_model=ClientResponse)
def update_client(documento: int, payload: ClientUpdate, db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)):
    client = ClientService(db).update(documento, payload)
    if client is None:
        raise ResourceNotFoundError(f"No existe el cliente {documento}.")
    return client


@router.patch("/{documento}/estado", response_model=ClientResponse)
def update_client_status(documento: int, payload: ClientStatusUpdate, db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)):
    client = ClientService(db).set_status(documento, payload.estado)
    if client is None:
        raise ResourceNotFoundError(f"No existe el cliente {documento}.")
    return client


@router.delete("/{documento}", response_model=ClientResponse, summary="Desactivar cliente sin borrar el historial")
def deactivate_client(documento: int, db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)):
    client = ClientService(db).deactivate(documento)
    if client is None:
        raise ResourceNotFoundError(f"No existe el cliente {documento}.")
    return client
