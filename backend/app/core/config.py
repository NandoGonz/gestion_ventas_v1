"""Configuración centralizada y dependiente del entorno.

La configuración sigue el patrón del proyecto de referencia: las claves se
leen desde variables de entorno o desde ``backend/.env``. No se incluyen
credenciales de PostgreSQL como valores predeterminados en el código.
"""
from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Configuración de la API de gestión de ventas."""

    app_env: Literal["development", "test", "production"] = Field(
        default="development",
        validation_alias=AliasChoices("APP_ENV", "app_env"),
    )
    app_name: str = Field(
        default="Sistema de Gestión de Ventas",
        validation_alias=AliasChoices("APP_NAME", "app_name"),
    )
    app_jwt_secret: str = Field(
        default="",
        validation_alias=AliasChoices("APP_JWT_SECRET", "app_jwt_secret"),
    )
    jwt_algorithm: Literal["HS256"] = Field(
        default="HS256",
        validation_alias=AliasChoices("JWT_ALGORITHM", "jwt_algorithm"),
    )
    jwt_expiration_minutes: int = Field(
        default=60,
        ge=5,
        le=1440,
        validation_alias=AliasChoices(
            "JWT_EXPIRATION_MINUTES", "jwt_expiration_minutes"
        ),
    )
    jwt_issuer: str = Field(
        default="gestion-ventas",
        validation_alias=AliasChoices("JWT_ISSUER", "jwt_issuer"),
    )
    jwt_audience: str = Field(
        default="gestion-ventas-api",
        validation_alias=AliasChoices("JWT_AUDIENCE", "jwt_audience"),
    )
    database_url: str = Field(
        default="",
        validation_alias=AliasChoices("DATABASE_URL", "database_url"),
    )
    cors_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        validation_alias=AliasChoices("CORS_ORIGINS", "cors_origins"),
    )
    auto_create_tables: bool = Field(
        default=True,
        validation_alias=AliasChoices("AUTO_CREATE_TABLES", "auto_create_tables"),
    )
    bootstrap_admin_name: str = Field(
        default="Emiro José González Rivera",
        validation_alias=AliasChoices("BOOTSTRAP_ADMIN_NAME", "bootstrap_admin_name"),
    )
    bootstrap_admin_email: str = Field(
        default="adminemiro@version1.com",
        validation_alias=AliasChoices(
            "BOOTSTRAP_ADMIN_EMAIL", "bootstrap_admin_email"
        ),
    )
    bootstrap_admin_password: str = Field(
        default="",
        validation_alias=AliasChoices(
            "BOOTSTRAP_ADMIN_PASSWORD", "bootstrap_admin_password"
        ),
    )

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        """Lista de orígenes separados por coma para la configuración CORS."""
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]

    @model_validator(mode="after")
    def validate_settings(self) -> "Settings":
        """Falla pronto si faltan secretos o la URL de la base de datos."""
        if not self.database_url.strip():
            raise ValueError(
                "DATABASE_URL es obligatoria. Configura la URL completa en backend/.env."
            )
        if not self.app_jwt_secret.strip():
            raise ValueError(
                "APP_JWT_SECRET es obligatoria. Define un secreto local en backend/.env."
            )
        if self.jwt_algorithm != "HS256":
            raise ValueError("La política JWT configurada solo admite HS256.")

        if self.app_env == "production":
            if len(self.app_jwt_secret) < 32:
                raise ValueError(
                    "APP_JWT_SECRET debe tener al menos 32 caracteres en producción."
                )
            if any(
                "localhost" in origin or "127.0.0.1" in origin
                for origin in self.cors_origin_list
            ):
                raise ValueError(
                    "CORS_ORIGINS no puede contener direcciones locales en producción."
                )
            if "postgres:postgres@" in self.database_url:
                raise ValueError(
                    "DATABASE_URL no puede usar credenciales PostgreSQL predeterminadas en producción."
                )
            if not self.bootstrap_admin_password:
                raise ValueError(
                    "BOOTSTRAP_ADMIN_PASSWORD es obligatoria para aprovisionar el administrador."
                )
        return self


settings = Settings()
