"""Mapeo centralizado de errores de dominio y persistencia a HTTP."""
import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.exceptions import BusinessRuleError, ConflictError, ResourceNotFoundError

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ResourceNotFoundError)
    async def not_found_handler(_request: Request, exc: ResourceNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)})

    @app.exception_handler(ConflictError)
    async def conflict_handler(_request: Request, exc: ConflictError) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": str(exc)})

    @app.exception_handler(BusinessRuleError)
    async def business_rule_handler(_request: Request, exc: BusinessRuleError) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(exc)})

    @app.exception_handler(IntegrityError)
    async def integrity_handler(_request: Request, _exc: IntegrityError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": "La operación entra en conflicto con un registro o una restricción existente."},
        )

    @app.exception_handler(SQLAlchemyError)
    async def database_handler(_request: Request, exc: SQLAlchemyError) -> JSONResponse:
        logger.exception("Error de persistencia no controlado", exc_info=exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "No fue posible completar la operación en la base de datos."},
        )
