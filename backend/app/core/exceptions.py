"""Excepciones de dominio desacopladas del protocolo HTTP."""


class ResourceNotFoundError(Exception):
    """El recurso solicitado no existe."""


class BusinessRuleError(Exception):
    """Una operación infringe una regla de negocio."""


class ConflictError(BusinessRuleError):
    """La operación entra en conflicto con el estado actual del sistema."""
