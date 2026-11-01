from decimal import Decimal


def create_client(client, headers, document=300):
    response = client.post(
        "/api/v1/clientes/",
        json={"documento": document, "nombre": "Emilia", "apellido": "Gómez", "direccion": "Calle 45", "email": f"emilia{document}@example.com"},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_product(client, headers, name, price, stock):
    response = client.post(
        "/api/v1/productos/",
        json={"nombre": name, "descripcion": f"Producto de prueba {name}", "precio": str(price), "stock": stock},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_sale_decreases_inventory_and_returns_computed_totals(client, auth_headers):
    create_client(client, auth_headers, 301)
    product = create_product(client, auth_headers, "Monitor", "125000.00", 5)
    sale = client.post(
        "/api/v1/ventas/",
        headers=auth_headers,
        json={"cliente_documento": 301, "forma_pago": "decontado", "detalles": [{"producto_id": product["id"], "cantidad": 2}]},
    )
    assert sale.status_code == 201, sale.text
    body = sale.json()
    assert Decimal(str(body["total"])) == Decimal("250000.00")
    assert Decimal(str(body["detalle_ventas"][0]["subtotal"])) == Decimal("250000.00")
    assert body["detalle_ventas"][0]["producto_nombre"] == "Monitor"
    remaining = client.get(f"/api/v1/productos/{product['id']}", headers=auth_headers)
    assert remaining.json()["stock"] == 3


def test_credit_sale_increases_client_balance(client, auth_headers):
    create_client(client, auth_headers, 302)
    product = create_product(client, auth_headers, "Impresora", "200000.00", 2)
    sale = client.post(
        "/api/v1/ventas/", headers=auth_headers,
        json={"cliente_documento": 302, "forma_pago": "credito", "detalles": [{"producto_id": product["id"], "cantidad": 1}]},
    )
    assert sale.status_code == 201, sale.text
    customer = client.get("/api/v1/clientes/302", headers=auth_headers).json()
    assert Decimal(str(customer["saldo"])) == Decimal("200000.00")


def test_insufficient_stock_rejects_sale_without_decrement(client, auth_headers):
    create_client(client, auth_headers, 303)
    product = create_product(client, auth_headers, "Audífonos", "50000.00", 2)
    response = client.post(
        "/api/v1/ventas/", headers=auth_headers,
        json={"cliente_documento": 303, "forma_pago": "decontado", "detalles": [{"producto_id": product["id"], "cantidad": 3}]},
    )
    assert response.status_code == 409
    current = client.get(f"/api/v1/productos/{product['id']}", headers=auth_headers).json()
    assert current["stock"] == 2
    assert client.get("/api/v1/ventas/", headers=auth_headers).json() == []


def test_failed_second_line_rolls_back_first_stock_change(client, auth_headers):
    create_client(client, auth_headers, 304)
    first = create_product(client, auth_headers, "Artículo A", "10000.00", 5)
    second = create_product(client, auth_headers, "Artículo B", "20000.00", 1)
    response = client.post(
        "/api/v1/ventas/", headers=auth_headers,
        json={"cliente_documento": 304, "forma_pago": "decontado", "detalles": [
            {"producto_id": first["id"], "cantidad": 2},
            {"producto_id": second["id"], "cantidad": 2},
        ]},
    )
    assert response.status_code == 409
    stock_first = client.get(f"/api/v1/productos/{first['id']}", headers=auth_headers).json()["stock"]
    stock_second = client.get(f"/api/v1/productos/{second['id']}", headers=auth_headers).json()["stock"]
    assert stock_first == 5
    assert stock_second == 1
    assert client.get("/api/v1/ventas/", headers=auth_headers).json() == []


def test_duplicate_product_lines_are_rejected_by_schema(client, auth_headers):
    create_client(client, auth_headers, 305)
    product = create_product(client, auth_headers, "Lámpara", "25000.00", 10)
    response = client.post(
        "/api/v1/ventas/", headers=auth_headers,
        json={"cliente_documento": 305, "forma_pago": "decontado", "detalles": [
            {"producto_id": product["id"], "cantidad": 1},
            {"producto_id": product["id"], "cantidad": 2},
        ]},
    )
    assert response.status_code == 422


def test_inactive_client_cannot_create_sale(client, auth_headers):
    create_client(client, auth_headers, 306)
    product = create_product(client, auth_headers, "Webcam", "80000.00", 5)
    assert client.delete("/api/v1/clientes/306", headers=auth_headers).status_code == 200
    response = client.post(
        "/api/v1/ventas/", headers=auth_headers,
        json={"cliente_documento": 306, "forma_pago": "decontado", "detalles": [{"producto_id": product["id"], "cantidad": 1}]},
    )
    assert response.status_code == 409
    assert client.get(f"/api/v1/productos/{product['id']}", headers=auth_headers).json()["stock"] == 5
