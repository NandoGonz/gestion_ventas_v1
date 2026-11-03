# Backend — Sistema de Gestión de Ventas

Backend modular basado en FastAPI, SQLAlchemy 2, Pydantic, PostgreSQL, `python-jose` y `pwdlib[argon2]`.

## Estructura

- `app/core/config.py`: settings centralizados desde `backend/.env`, con aliases explícitos como en el proyecto de referencia y sin credenciales de DB predeterminadas.
- `app/core/database.py`: motor SQLAlchemy, base declarativa y sesiones por solicitud.
- `app/core/security.py`: funciones criptográficas de contraseñas y JWT.
- `app/core/dependencies.py`: dependencias de autenticación (`get_current_user`) y autorización de administrador (`get_current_admin`).
- `app/core/error_handlers.py` y `exceptions.py`: tratamiento común de errores.
- `app/auth`: login, JWT y consulta del usuario autenticado.
- `app/users`: modelo `User` y bootstrap seguro e idempotente del administrador inicial.
- `app/clients`: modelo, esquemas, servicios y endpoints de clientes.
- `app/products`: modelo, esquemas, servicios y endpoints del inventario.
- `app/inventory`: movimientos inmutables de entrada, salida, saldo inicial y ventas.
- `app/sales`: venta, detalles y transacción de inventario.
- `tests/unit`, `tests/integration`, `tests/e2e`: pruebas separadas por alcance.

## Setup en Windows / PowerShell

Desde esta carpeta (`pruebapostgres/backend`):

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
```

Copia `.env.example` como `.env` y actualiza `DATABASE_URL`, la clave JWT y la contraseña de bootstrap. La aplicación lee `backend/.env` mediante una ruta absoluta calculada en `app/core/config.py`, siguiendo el patrón del proyecto de referencia; no depende de la carpeta actual de PowerShell. Este proyecto utiliza la variable completa `DATABASE_URL` y no construye la conexión a partir de `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER` y `DB_PASSWORD` separados. Para PostgreSQL local la URL tiene forma `postgresql+psycopg2://USUARIO:CONTRASEÑA@localhost:5432/NOMBRE_BD`. Si la contraseña contiene caracteres reservados de URL, deben codificarse. No subas `.env` a Git.

Levanta la API desde `backend/`:

```powershell
python -m uvicorn app.main:app --reload
```

Swagger: <http://127.0.0.1:8000/docs>.

Antes de arrancar, puedes comprobar de forma segura qué conexión está cargando la aplicación (no imprime la contraseña):

```powershell
python -c "from app.core.config import settings; from sqlalchemy.engine import make_url; u=make_url(settings.database_url); print('Host:', u.host, '| Puerto:', u.port, '| Base:', u.database, '| Usuario:', u.username)"
```

## Cuenta inicial de desarrollo

El archivo local `.env` de esta entrega configura la cuenta administrativa inicial: **Emiro José González Rivera** (`admin@gestionventas.com`). La contraseña se toma de `BOOTSTRAP_ADMIN_PASSWORD`; no se documenta en texto dentro del README. El bootstrap solo crea la cuenta si el correo no existe y nunca reemplaza la contraseña de una cuenta ya creada. Mantén `.env` fuera del control de versiones.

## Variables de configuración

| Variable | Propósito |
|---|---|
| `APP_ENV` | `development`, `test` o `production`. |
| `APP_JWT_SECRET` | Secreto para firmar/verificar JWT. |
| `JWT_ALGORITHM` | Política configurada: `HS256`. |
| `JWT_EXPIRATION_MINUTES` | Duración del token de acceso. |
| `JWT_ISSUER`, `JWT_AUDIENCE` | Validación de emisor y audiencia del token. |
| `DATABASE_URL` | URL de SQLAlchemy/PostgreSQL. |
| `CORS_ORIGINS` | Orígenes HTTP permitidos para el frontend. |
| `AUTO_CREATE_TABLES` | Crea tablas faltantes al iniciar cuando está en `true`; no es una herramienta de migración. |
| `BOOTSTRAP_ADMIN_NAME` | Nombre visible de la cuenta inicial. |
| `BOOTSTRAP_ADMIN_EMAIL` | Correo único de la cuenta inicial. |
| `BOOTSTRAP_ADMIN_PASSWORD` | Contraseña en texto plano leída localmente y almacenada solo como hash Argon2 en la tabla. |

## API principal

Los endpoints de negocio requieren `Authorization: Bearer <token>` y usuario administrador.

- `POST /api/v1/auth/login`: login OAuth2 form (`username=email`, `password=...`).
- `GET /api/v1/auth/me`: perfil de la sesión autenticada.
- `GET|POST /api/v1/clientes/`, `GET|PATCH /api/v1/clientes/{documento}`, `PATCH /api/v1/clientes/{documento}/estado`, `DELETE /api/v1/clientes/{documento}`.
- `GET|POST /api/v1/productos/`, `GET|PATCH /api/v1/productos/{id}`. El `PATCH` no admite `stock`.
- `GET /api/v1/inventario/`, `GET /api/v1/inventario/movimientos`, `POST /api/v1/inventario/entradas`, `POST /api/v1/inventario/salidas`.
- `GET|POST /api/v1/ventas/`, `GET /api/v1/ventas/{id}`.
- `GET /health` y `GET /health/db` para estado del proceso y conectividad.

## Reglas críticas de negocio

1. El documento identifica de forma única a un cliente.
2. El cliente se desactiva lógicamente; no se borra su historial de ventas.
3. Los precios deben ser positivos y el stock nunca puede quedar por debajo de cero.
4. El backend calcula el total usando el precio del producto en base de datos; no confía en totales del frontend.
5. Las entradas y salidas actualizan stock y crean su movimiento en una misma transacción.
6. El descuento de stock, la creación de venta/detalles, los movimientos de venta y el incremento de saldo en ventas a crédito comparten una transacción.
7. Se descuenta stock mediante un `UPDATE` condicional con `stock >= cantidad` y estado disponible. Si cualquier línea falla, se revierte la transacción completa.
8. `detalle_venta.subtotal` es una columna calculada por la base de datos.
9. Los movimientos de inventario no se modifican ni eliminan desde operaciones ordinarias de la API.
10. Los errores de base de datos no exponen SQL ni credenciales al cliente HTTP.

## Migración de inventario en PostgreSQL

`Base.metadata.create_all()` sirve para entornos nuevos, pero no sustituye una migración de producción. Antes de desplegar esta funcionalidad en Railway, crea un respaldo, programa una ventana breve sin escrituras y ejecuta desde `backend/`:

```powershell
python scripts/run_migration.py
```

El ejecutor calcula el SHA-256 de `migrations/001_create_inventory_movements.sql`, adquiere un bloqueo transaccional PostgreSQL, valida el esquema y registra la versión en `gestion_ventas_migraciones`. Una versión con el mismo checksum no se repite; una versión con checksum distinto falla. La transacción crea solo los elementos nuevos y los movimientos de saldo inicial, sin eliminar ni sobrescribir datos existentes. No ejecutes este comando contra Railway sin el respaldo y la ventana de mantenimiento.

### Orden obligatorio en una base existente

No despliegues ni arranques la revisión del backend que contiene el modelo de inventario antes de ejecutar la migración: con `AUTO_CREATE_TABLES=true`, el arranque de FastAPI puede crear `movimientos_inventario` mediante `create_all()` sin registrar la versión ni generar los saldos iniciales. La migración detectará ese estado parcial y fallará para proteger los datos.

El ejecutor no llama a `create_all()`, por lo que puede ejecutarse contra la base existente antes del despliegue. Mantén la configuración de producción sin cambios automáticos; si es imprescindible arrancar un proceso de la nueva revisión antes de migrar, configura temporalmente `AUTO_CREATE_TABLES=false` solo para ese proceso y restáuralo según la política operativa después de validar la migración.

## Pruebas

```powershell
python -m pytest -v
```

Ver [tests/README.md](tests/README.md). Los tests usan SQLite en memoria; una validación real de PostgreSQL sigue siendo recomendable al cambiar esquema o versión del motor.
