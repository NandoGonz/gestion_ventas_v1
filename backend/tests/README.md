# Pruebas del backend

## Organización

- `unit/`: funciones de seguridad sin llamadas HTTP.
- `integration/`: rutas, esquema/validación HTTP y persistencia temporal.
- `e2e/`: flujos completos de creación de cliente, producto y venta.
- `conftest.py`: configuración de SQLite en memoria y credenciales de prueba aisladas.

## Ejecutar

Desde `backend/`, activa `.venv` y ejecuta:

```powershell
python -m pytest -v
```

La configuración `pytest.ini` usa `testpaths=tests` y `pythonpath=.` porque los módulos se importan desde el paquete `app`. Los tests sobrescriben variables de entorno antes de importar la aplicación y usan una base SQLite en memoria; no utilizan `backend/.env` para la base de pruebas ni modifican datos PostgreSQL.

## Casos cubiertos

- Hash Argon2, verificación correcta/incorrecta y rechazo de JWT alterado o vencido.
- Login correcto e incorrecto y protección de endpoints.
- Creación/actualización/desactivación lógica de clientes y conflictos por documento/email.
- Validación de precio y estado por stock de productos.
- Venta exitosa, total/subtotal, descuento de existencias y saldo a crédito.
- Rechazo de stock insuficiente, cliente inactivo y líneas duplicadas.
- Rollback completo cuando una línea falla después de descontar otra.

La suite actual se valida en SQLite. Algunas garantías concretas de PostgreSQL (bloqueos, aislamiento, restricciones ya existentes) deben probarse también contra PostgreSQL antes de desplegar.
