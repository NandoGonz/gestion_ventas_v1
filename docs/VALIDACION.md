# Registro de validación de la V1

## Backend

La suite se ejecutó con `pytest` en un entorno de verificación aislado usando SQLite en memoria. Resultado: **22 pruebas aprobadas**. La cobertura incluye seguridad de contraseña y JWT, autenticación, protección de rutas, validación de clientes y productos, creación de ventas, crédito, stock insuficiente y rollback al fallar una línea de venta.

Comando para reproducir localmente desde `backend/` con el entorno virtual activo:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -v
```

## Frontend

Se incluye una prueba de componente para el formulario de login con Vitest y Testing Library. Debe ejecutarse en un entorno con Node.js y dependencias instaladas:

```powershell
cd frontend
npm install
npm test
npm run build
```

La instalación y compilación del frontend no se verificaron en este entorno de generación porque no había acceso al registro de paquetes.

## Docker y PostgreSQL

La configuración Docker Compose está incluida. La ejecución de contenedores y la validación de concurrencia en una instancia PostgreSQL real deben comprobarse en el equipo local con Docker Desktop y PostgreSQL disponible. Las pruebas SQLite no sustituyen esas comprobaciones.

## Alcance

La verificación no implica que el MVP esté listo para producción. Antes de un despliegue externo se necesita rotar credenciales, configurar secretos del entorno, validar migraciones de esquema, ejecutar pruebas de integración PostgreSQL y revisar la política de seguridad y operación.

## Configuración de PostgreSQL local

La configuración del backend sigue el patrón del proyecto de referencia: `app/core/config.py` carga `backend/.env` mediante una ruta absoluta, usa `DATABASE_URL` y no tiene una URL de PostgreSQL predeterminada dentro del código. Para ejecutar el backend localmente, asegúrate de que esa variable apunte a una base de datos existente, con credenciales y puerto válidos. Docker Compose usa sus propias variables para conectarse al servicio `postgres` dentro de la red de contenedores.
