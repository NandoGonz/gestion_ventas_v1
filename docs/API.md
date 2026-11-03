# API — V1

Base URL local: `http://localhost:8000/api/v1`. Las operaciones de negocio requieren un JWT con el encabezado `Authorization: Bearer <token>`.

## Autenticación

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| POST | `/auth/login` | No | Formulario OAuth2: `username` contiene el correo y `password` la contraseña. Devuelve `access_token`. |
| GET | `/auth/me` | Sí | Perfil de la cuenta autenticada. |

Ejemplo PowerShell:

```powershell
$body = @{ username = 'adminemiro@version1.com'; password = '<tu-password-local>' }
$tokenResponse = Invoke-RestMethod -Method Post -Uri 'http://localhost:8000/api/v1/auth/login' -Body $body -ContentType 'application/x-www-form-urlencoded'
$headers = @{ Authorization = "Bearer $($tokenResponse.access_token)" }
Invoke-RestMethod -Uri 'http://localhost:8000/api/v1/auth/me' -Headers $headers
```

## Clientes

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/clientes/?limit=100&offset=0` | Lista paginada. |
| POST | `/clientes/` | Crea cliente. |
| GET | `/clientes/{documento}` | Consulta cliente. |
| PATCH | `/clientes/{documento}` | Actualiza nombre, apellido, dirección o correo. |
| PATCH | `/clientes/{documento}/estado` | Cambia estado controlado. |
| DELETE | `/clientes/{documento}` | Desactiva; no borra físicamente. |

Ejemplo de creación:

```json
{
  "documento": 101234567,
  "nombre": "Ana",
  "apellido": "Pérez",
  "direccion": "Calle 1 # 2-03",
  "email": "ana@example.com"
}
```

## Productos

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/productos/?limit=100&offset=0` | Lista paginada. |
| POST | `/productos/` | Crea producto. |
| GET | `/productos/{id}` | Consulta producto. |
| PATCH | `/productos/{id}` | Actualiza datos, precio o estado de preventa/descontinuación. No acepta `stock`. |

Ejemplo de creación:

```json
{"nombre":"Teclado","descripcion":"Teclado para estación de trabajo","precio":"85000.00","stock":10}
```

Después de crear un producto con existencias iniciales, los cambios de stock se realizan exclusivamente desde Inventario o mediante una venta. Enviar `stock` a `PATCH /productos/{id}` se rechaza con `422`.

## Inventario

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/inventario/?limit=100&offset=0` | Lista productos con sus existencias actuales. |
| GET | `/inventario/movimientos?limit=100&offset=0` | Lista el historial inmutable de movimientos, del más reciente al más antiguo. |
| POST | `/inventario/entradas` | Registra una entrada y aumenta el stock. |
| POST | `/inventario/salidas` | Registra una salida manual y disminuye el stock si hay disponibilidad. |

Ejemplo de entrada:

```json
{
  "producto_id": 1,
  "cantidad": 10,
  "motivo": "Recepción de mercancía"
}
```

Ejemplo de salida:

```json
{
  "producto_id": 1,
  "cantidad": 2,
  "motivo": "Producto dañado"
}
```

Los movimientos son de tipo `entrada`, `salida` o `venta`. No disponen de endpoints ordinarios de modificación o eliminación. Las ventas registran automáticamente un movimiento `venta` por cada detalle dentro de la misma transacción que descuenta el stock.

## Ventas

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/ventas/?limit=100&offset=0` | Lista paginada con detalles. |
| POST | `/ventas/` | Crea venta y descuenta inventario transaccionalmente. |
| GET | `/ventas/{id}` | Consulta venta y detalles. |

Ejemplo:

```json
{
  "cliente_documento": 101234567,
  "forma_pago": "decontado",
  "detalles": [
    {"producto_id": 1, "cantidad": 2},
    {"producto_id": 2, "cantidad": 1}
  ]
}
```

Formas de pago aceptadas: `decontado`, `credito`, `transferencia`. El backend obtiene el precio de cada producto, calcula los subtotales y el total, descuenta existencias y en las ventas a crédito suma el total al saldo del cliente.

## Códigos HTTP frecuentes

- `200`: lectura o actualización correcta.
- `201`: recurso creado.
- `401`: falta token válido o credenciales incorrectas.
- `403`: la cuenta no tiene permiso de administrador.
- `404`: el recurso no existe.
- `409`: conflicto de negocio o restricción de integridad.
- `422`: payload inválido.
- `500`: error inesperado de persistencia; los detalles internos no se devuelven.
