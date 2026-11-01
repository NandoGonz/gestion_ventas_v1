# Sistema de Gestión de Ventas — V1

MVP local para administrar clientes, productos, existencias y ventas. Se construye con una arquitectura modular inspirada en el proyecto `universidad_digital`: un backend FastAPI por dominios (`core`, `auth`, `users`, `clients`, `products`, `sales`), un frontend React independiente y pruebas agrupadas por nivel.

## Funcionalidades incluidas

- Inicio de sesión con formulario OAuth2 y JWT firmado con `python-jose`.
- Contraseñas almacenadas como hash Argon2 mediante `pwdlib`; no se devuelve el hash por la API.
- Aprovisionamiento idempotente de un administrador a partir de variables locales.
- CRUD de clientes, actualización parcial y desactivación lógica para preservar el historial.
- Catálogo de productos con precio, estado e inventario.
- Creación y consulta de ventas con detalles, total calculado por el backend y snapshot del precio vigente.
- Descuento condicional de stock dentro de la transacción de venta; ante un fallo se revierte el conjunto de cambios.
- Aumento del saldo del cliente en las ventas a crédito.
- Pruebas de unidad, integración y flujo end-to-end.
- React/Vite, Docker Compose y documentación técnica.

## Arquitectura

```text
pruebapostgres/
├── backend/
│   ├── app/
│   │   ├── core/       # config.py, database.py, security.py, dependencies.py y errores
│   │   ├── auth/       # login y /me
│   │   ├── users/      # modelo y bootstrap del administrador
│   │   ├── clients/    # clientes
│   │   ├── products/   # productos e inventario
│   │   ├── sales/      # ventas y detalles
│   │   └── main.py
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── e2e/
│   ├── .env            # configuración LOCAL, ignorada por Git
│   ├── .env.example
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── README.md
├── frontend/
│   ├── src/api/        # cliente HTTP y tipos
│   ├── src/auth/       # rutas protegidas
│   ├── src/context/    # sesión de usuario
│   ├── src/layouts/
│   ├── src/pages/
│   └── README.md
├── docs/               # arquitectura, API y diagrama ER
├── docker-compose.yml
└── README.md
```

## Inicio recomendado con Docker

Requisitos: Docker Desktop con Docker Compose habilitado.

1. Revisa `backend/.env`. Se incluye un archivo local de desarrollo con el administrador inicial indicado por el propietario del proyecto. **No lo publiques ni lo subas a Git.**
2. Desde esta carpeta ejecuta:

   ```powershell
   docker compose up --build
   ```

3. Abre:
   - Frontend: <http://localhost:5173>
   - Swagger: <http://localhost:8000/docs>
   - Healthcheck: <http://localhost:8000/health>

Compose inicia PostgreSQL, espera a que esté saludable, inicia el backend y luego el frontend. La base usa el volumen `ventas_postgres_data` para conservar los datos entre reinicios.

Para detener el sistema: `Ctrl+C` y luego `docker compose down`. Para borrar también la base local del volumen, usa `docker compose down -v` **solo si deseas eliminar los datos de prueba**.

## Ejecución local sin Docker

1. Instala Python 3.13 y PostgreSQL.
2. Confirma que existe la base indicada por `DATABASE_URL` en `backend/.env`. El ejemplo de ejecución local utiliza `proyecto-dev`; puedes cambiar la URL si tu base tiene otro nombre.
3. Desde `backend/` crea y activa el entorno virtual:

   ```powershell
   py -3.13 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements-dev.txt
   python -m uvicorn app.main:app --reload
   ```

La configuración de `backend/.env` se carga mediante una ruta absoluta calculada desde `app/core/config.py`, siguiendo el patrón de configuración centralizada del proyecto de referencia; por eso la carga no depende de la carpeta desde la que ejecutes Uvicorn. `DATABASE_URL` no tiene una conexión predeterminada embebida en el código: si falta, la aplicación falla con un mensaje claro en vez de intentar conectarse silenciosamente a otra base de datos. Esta versión usa una sola variable `DATABASE_URL` con la URL completa de SQLAlchemy (no `DB_HOST`, `DB_PORT` o `DB_NAME` por separado). En ejecución local, confirma que el usuario, contraseña, puerto y nombre de la base sean correctos. En Docker Compose, Compose sustituye `DATABASE_URL` para usar el servicio `postgres` y la base `gestion_ventas` del contenedor. En desarrollo, `AUTO_CREATE_TABLES=true` crea las tablas faltantes; `create_all()` no altera tablas que ya existían con un esquema anterior. Para un esquema antiguo, usa una base de datos nueva o prepara una migración revisada antes de actualizar.

## Pruebas

Desde `backend/`, con `.venv` activo:

```powershell
python -m pytest -v
```

Las pruebas usan SQLite en memoria para no tocar datos locales reales. Consulta `backend/tests/README.md` para entender el alcance. Antes de publicar o desplegar, también se recomienda ejecutar una prueba de integración sobre PostgreSQL.

## Cuenta administrativa inicial (desarrollo local)

- Nombre: **Emiro José González Rivera**.
- Correo de acceso: **adminemiro@version1.com**.
- La contraseña inicial se configura mediante `BOOTSTRAP_ADMIN_PASSWORD` en `backend/.env`; no se copia al código fuente ni a los README.
- Al iniciar, la aplicación crea esta cuenta solo si el correo aún no existe. Si la cuenta ya existe, el bootstrap no reemplaza su contraseña.
- La contraseña se almacena en la base de datos como hash Argon2. El `.env` incluido está destinado únicamente al entorno local de desarrollo.

## Seguridad y credenciales

- La cuenta inicial se crea al inicio si `BOOTSTRAP_ADMIN_PASSWORD` está configurada y aún no existe ese correo.
- El proceso no sobrescribe la contraseña de una cuenta ya creada.
- La clave JWT se genera para desarrollo y se lee desde `.env`.
- `.env` y `.venv` están excluidos de Git por `.gitignore`.
- Esta configuración es solo para desarrollo local; sustituye los secretos y credenciales de desarrollo antes de compartir o desplegar el sistema.
- El token se guarda en memoria en el frontend; recargar el navegador requiere iniciar sesión otra vez.

## Documentación

- [Documento técnico y diagrama de tablas](docs/README.md)
- [Backend](backend/README.md)
- [Frontend](frontend/README.md)
- [Pruebas](backend/tests/README.md)
- [Especificación de la API](docs/API.md)
- [Registro de validación](docs/VALIDACION.md)

## Despliegue siguiendo la arquitectura de referencia

El repositorio incluye GitHub Actions para el flujo `test → build → deploy → verificación`, Railway para el backend y PostgreSQL, y Vercel para el frontend. La lógica de clientes, productos, ventas y autenticación se conserva.

### Railway (backend)

1. Crea un proyecto con PostgreSQL y un servicio vacío para el backend. Conecta GitHub Actions mediante las variables y el secreto indicados abajo; no actives un segundo despliegue automático desde la conexión GitHub del servicio.
2. Configura el servicio backend para desplegar desde `backend/` (el workflow utiliza `railway up ./backend --path-as-root`).
3. Configura estas variables en el servicio backend:
   - `APP_ENV=production`
   - `DATABASE_URL=${{Postgres.DATABASE_URL}}` (usa el nombre real del servicio PostgreSQL si no es `Postgres`).
   - `APP_JWT_SECRET`: secreto aleatorio propio de al menos 32 caracteres.
   - `JWT_ALGORITHM=HS256`
   - `JWT_EXPIRATION_MINUTES=60`
   - `JWT_ISSUER=gestion-ventas`
   - `JWT_AUDIENCE=gestion-ventas-api`
   - `CORS_ORIGINS`: origen HTTPS exacto del frontend Vercel.
   - `AUTO_CREATE_TABLES=true` para crear las tablas faltantes al iniciar. Esta versión no incorpora Alembic; no configures un comando de migración Alembic ni un bootstrap separado.
   - `BOOTSTRAP_ADMIN_NAME`, `BOOTSTRAP_ADMIN_EMAIL` y `BOOTSTRAP_ADMIN_PASSWORD`: credenciales iniciales propias; la contraseña debe tener al menos 12 caracteres.
4. En Railway configura el **Healthcheck Path** como `/health`. No configures Pre-deploy Command de Alembic. El proceso escucha en el puerto `PORT` que Railway proporciona.
5. El endpoint `/health/db` verifica la conexión con PostgreSQL.

### GitHub Actions

En Settings → Secrets and variables → Actions configura:

- Secret `RAILWAY_TOKEN`.
- Variables `RAILWAY_PROJECT_ID`, `RAILWAY_SERVICE_ID` y `RAILWAY_API_URL` (origen HTTPS público del backend, sin ruta).

El workflow ejecuta pruebas y build Docker en pull requests y pushes a `main`; el despliegue ocurre en un push a `main` que cambie `backend/`, o manualmente desde `workflow_dispatch` activando `deploy`.

### Vercel (frontend)

Importa el mismo repositorio y configura **Root Directory** como `frontend`, Framework **Vite**, Install Command `npm install`, Build Command `npm run build` y Output Directory `dist`. En Environment Variables define `VITE_API_BASE_URL` con el origen HTTPS público de Railway, sin `/api/v1` ni barra final. `frontend/vercel.json` conserva el enrutamiento de la SPA. Añade el dominio de Vercel a `CORS_ORIGINS` en Railway.

`VITE_API_BASE_URL` es pública porque queda incorporada al JavaScript del navegador; no coloques secretos en variables `VITE_`.
