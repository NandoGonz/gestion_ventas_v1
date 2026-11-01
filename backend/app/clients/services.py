"""Reglas de negocio y persistencia para clientes."""
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.clients.models import Client, ClientStatus
from app.clients.schemas import ClientCreate, ClientUpdate


class ClientService:
    def __init__(self, session: Session):
        self.session = session

    def create(self, data: ClientCreate) -> Client:
        try:
            values = data.model_dump()
            if values.get("email"):
                values["email"] = str(values["email"]).lower()
            client = Client(**values, estado=ClientStatus.ACTIVO)
            self.session.add(client)
            self.session.commit()
            self.session.refresh(client)
            return client
        except SQLAlchemyError:
            self.session.rollback()
            raise

    def get(self, documento: int) -> Client | None:
        return self.session.scalar(select(Client).where(Client.documento == documento))

    def list(self, limit: int = 100, offset: int = 0) -> list[Client]:
        statement = select(Client).order_by(Client.documento).limit(limit).offset(offset)
        return list(self.session.scalars(statement).all())

    def update(self, documento: int, data: ClientUpdate) -> Client | None:
        client = self.get(documento)
        if client is None:
            return None
        values = data.model_dump(exclude_unset=True)
        if "email" in values and values["email"]:
            values["email"] = str(values["email"]).lower()
        try:
            for key, value in values.items():
                setattr(client, key, value)
            self.session.commit()
            self.session.refresh(client)
            return client
        except SQLAlchemyError:
            self.session.rollback()
            raise

    def set_status(self, documento: int, estado: ClientStatus) -> Client | None:
        client = self.get(documento)
        if client is None:
            return None
        try:
            client.estado = estado
            self.session.commit()
            self.session.refresh(client)
            return client
        except SQLAlchemyError:
            self.session.rollback()
            raise

    def deactivate(self, documento: int) -> Client | None:
        """Desactivación lógica: preserva el cliente y todas sus ventas."""
        return self.set_status(documento, ClientStatus.INACTIVO)
