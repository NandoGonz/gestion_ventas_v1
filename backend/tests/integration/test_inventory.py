from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session


def create_product(client, headers, name="Producto inventariable", stock=10, status_code=201):
    response = client.post(
        "/api/v1/productos/",
        headers=headers,
        json={
            "nombre": name,
            "descripcion": "Producto para pruebas de inventario",
            "precio": "100.00",
            "stock": stock,
        },
    )
    assert response.status_code == status_code, response.text
    return response.json()


def movements_for_product(client, headers, product_id):
    response = client.get("/api/v1/inventario/movimientos", headers=headers)
    assert response.status_code == 200, response.text
    return [movement for movement in response.json() if movement["producto_id"] == product_id]


def test_new_product_with_stock_creates_initial_inventory_movement(client, auth_headers):
    product = create_product(client, auth_headers, stock=7)

    movements = movements_for_product(client, auth_headers, product["id"])

    assert len(movements) == 1
    assert movements[0]["tipo_movimiento"] == "entrada"
    assert movements[0]["cantidad"] == 7
    assert movements[0]["motivo"] == "Stock inicial del producto"
    assert movements[0]["venta_id"] is None


def test_register_inventory_entry_updates_stock_and_history(client, auth_headers):
    product = create_product(client, auth_headers, stock=5)

    response = client.post(
        "/api/v1/inventario/entradas",
        headers=auth_headers,
        json={"producto_id": product["id"], "cantidad": 4, "motivo": "Recepción de mercancía"},
    )

    assert response.status_code == 201, response.text
    movement = response.json()
    assert movement["tipo_movimiento"] == "entrada"
    assert movement["cantidad"] == 4
    assert movement["motivo"] == "Recepción de mercancía"
    assert movement["producto_nombre"] == product["nombre"]
    assert client.get(f"/api/v1/productos/{product['id']}", headers=auth_headers).json()["stock"] == 9


def test_register_inventory_exit_updates_stock_and_history(client, auth_headers):
    product = create_product(client, auth_headers, stock=5)

    response = client.post(
        "/api/v1/inventario/salidas",
        headers=auth_headers,
        json={"producto_id": product["id"], "cantidad": 2, "motivo": "Producto dañado"},
    )

    assert response.status_code == 201, response.text
    assert response.json()["tipo_movimiento"] == "salida"
    assert response.json()["cantidad"] == 2
    remaining = client.get(f"/api/v1/productos/{product['id']}", headers=auth_headers).json()
    assert remaining["stock"] == 3
    assert remaining["estado"] == "disponible"


def test_inventory_rejects_invalid_quantities_and_missing_reason(client, auth_headers):
    product = create_product(client, auth_headers)

    for payload in (
        {"producto_id": product["id"], "cantidad": 0, "motivo": "Ajuste"},
        {"producto_id": product["id"], "cantidad": -1, "motivo": "Ajuste"},
        {"producto_id": product["id"], "cantidad": 1, "motivo": "   "},
    ):
        response = client.post("/api/v1/inventario/entradas", headers=auth_headers, json=payload)
        assert response.status_code == 422


def test_inventory_rejects_nonexistent_product_without_creating_movement(client, auth_headers):
    response = client.post(
        "/api/v1/inventario/entradas",
        headers=auth_headers,
        json={"producto_id": 999_999, "cantidad": 1, "motivo": "Recepción"},
    )

    assert response.status_code == 404
    assert client.get("/api/v1/inventario/movimientos", headers=auth_headers).json() == []


def test_inventory_rejects_exit_above_stock_without_partial_change(client, auth_headers):
    product = create_product(client, auth_headers, stock=2)

    response = client.post(
        "/api/v1/inventario/salidas",
        headers=auth_headers,
        json={"producto_id": product["id"], "cantidad": 3, "motivo": "Pérdida"},
    )

    assert response.status_code == 409
    assert client.get(f"/api/v1/productos/{product['id']}", headers=auth_headers).json()["stock"] == 2
    assert len(movements_for_product(client, auth_headers, product["id"])) == 1


def test_inventory_rolls_back_stock_when_movement_cannot_be_saved(client, auth_headers, monkeypatch):
    product = create_product(client, auth_headers, stock=5)

    def fail_flush(_session, *args, **kwargs):
        raise SQLAlchemyError("No se pudo guardar el movimiento.")

    monkeypatch.setattr(Session, "flush", fail_flush)
    response = client.post(
        "/api/v1/inventario/entradas",
        headers=auth_headers,
        json={"producto_id": product["id"], "cantidad": 3, "motivo": "Recepción"},
    )

    assert response.status_code == 500
    assert client.get(f"/api/v1/productos/{product['id']}", headers=auth_headers).json()["stock"] == 5
    assert len(movements_for_product(client, auth_headers, product["id"])) == 1


def test_product_patch_rejects_stock_instead_of_ignoring_it(client, auth_headers):
    product = create_product(client, auth_headers, stock=5)

    response = client.patch(
        f"/api/v1/productos/{product['id']}",
        headers=auth_headers,
        json={"stock": 10},
    )

    assert response.status_code == 422
    assert any(item["loc"][-1] == "stock" for item in response.json()["detail"])
    assert client.get(f"/api/v1/productos/{product['id']}", headers=auth_headers).json()["stock"] == 5


def test_sale_creates_one_inventory_movement_per_detail_without_double_decrement(client, auth_headers):
    client_response = client.post(
        "/api/v1/clientes/",
        headers=auth_headers,
        json={
            "documento": 501,
            "nombre": "Cliente",
            "apellido": "Inventario",
            "direccion": "Calle 1",
        },
    )
    assert client_response.status_code == 201, client_response.text
    product = create_product(client, auth_headers, stock=5)

    sale = client.post(
        "/api/v1/ventas/",
        headers=auth_headers,
        json={
            "cliente_documento": 501,
            "forma_pago": "decontado",
            "detalles": [{"producto_id": product["id"], "cantidad": 2}],
        },
    )

    assert sale.status_code == 201, sale.text
    movements = movements_for_product(client, auth_headers, product["id"])
    sale_movements = [movement for movement in movements if movement["tipo_movimiento"] == "venta"]
    assert len(sale_movements) == 1
    assert sale_movements[0]["cantidad"] == 2
    assert sale_movements[0]["venta_id"] == sale.json()["id"]
    assert client.get(f"/api/v1/productos/{product['id']}", headers=auth_headers).json()["stock"] == 3


def test_inventory_history_has_no_ordinary_mutation_endpoints(client, auth_headers):
    product = create_product(client, auth_headers)
    movement = movements_for_product(client, auth_headers, product["id"])[0]

    assert client.patch(
        f"/api/v1/inventario/movimientos/{movement['id']}",
        headers=auth_headers,
        json={"motivo": "Cambio"},
    ).status_code == 404
    assert client.delete(
        f"/api/v1/inventario/movimientos/{movement['id']}",
        headers=auth_headers,
    ).status_code == 404
