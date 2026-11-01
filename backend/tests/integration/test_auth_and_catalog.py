def test_health_endpoints_are_available(client):
    assert client.get("/health").status_code == 200
    assert client.get("/").json()["version"] == "1.0.0"
    assert client.get("/health/db").json()["database"] == "connected"


def test_login_and_current_user(client):
    login = client.post(
        "/api/v1/auth/login",
        data={"username": "admin-test@example.com", "password": "TestAdminPass123!"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "admin-test@example.com"
    assert "password_hash" not in me.json()


def test_invalid_login_is_rejected(client):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin-test@example.com", "password": "wrong-password"},
    )
    assert response.status_code == 401
    assert "incorrectos" in response.json()["detail"]


def test_business_routes_require_authentication(client):
    assert client.get("/api/v1/clientes/").status_code == 401
    assert client.get("/api/v1/productos/").status_code == 401
    assert client.get("/api/v1/ventas/").status_code == 401


def test_create_client_and_duplicate_document_conflicts(client, auth_headers):
    payload = {"documento": 101, "nombre": "Ana", "apellido": "Pérez", "direccion": "Calle 1", "email": "ana@example.com"}
    first = client.post("/api/v1/clientes/", json=payload, headers=auth_headers)
    assert first.status_code == 201, first.text
    assert first.json()["estado"] == "activo"
    assert first.json()["saldo"] in ("0.00", 0, "0")
    duplicate = client.post("/api/v1/clientes/", json=payload, headers=auth_headers)
    assert duplicate.status_code == 409


def test_client_patch_and_soft_deactivation_preserve_record(client, auth_headers):
    payload = {"documento": 202, "nombre": "Carlos", "apellido": "Díaz", "direccion": "Carrera 2"}
    assert client.post("/api/v1/clientes/", json=payload, headers=auth_headers).status_code == 201
    patched = client.patch("/api/v1/clientes/202", json={"direccion": "Calle 10"}, headers=auth_headers)
    assert patched.status_code == 200 and patched.json()["direccion"] == "Calle 10"
    deactivated = client.delete("/api/v1/clientes/202", headers=auth_headers)
    assert deactivated.status_code == 200 and deactivated.json()["estado"] == "inactivo"
    # El cliente sigue consultable: no hubo borrado físico.
    assert client.get("/api/v1/clientes/202", headers=auth_headers).status_code == 200


def test_client_update_requires_at_least_one_field(client, auth_headers):
    response = client.patch("/api/v1/clientes/202", json={}, headers=auth_headers)
    assert response.status_code == 422


def test_create_product_and_stock_zero_sets_out_of_stock(client, auth_headers):
    payload = {"nombre": "Teclado", "descripcion": "Teclado mecánico para oficina", "precio": "85000.00", "stock": 0}
    response = client.post("/api/v1/productos/", json=payload, headers=auth_headers)
    assert response.status_code == 201, response.text
    assert response.json()["estado"] == "agotado"


def test_product_rejects_non_positive_price(client, auth_headers):
    response = client.post(
        "/api/v1/productos/",
        json={"nombre": "Mouse", "descripcion": "Mouse de prueba", "precio": "0", "stock": 5},
        headers=auth_headers,
    )
    assert response.status_code == 422


def test_product_pagination_is_bounded(client, auth_headers):
    response = client.get("/api/v1/productos/?limit=201", headers=auth_headers)
    assert response.status_code == 422


def test_product_rejects_null_description_patch(client, auth_headers):
    created = client.post(
        "/api/v1/productos/",
        json={"nombre": "Teclado", "descripcion": "Accesorio", "precio": "100.00", "stock": 5},
        headers=auth_headers,
    )
    assert created.status_code == 201, created.text
    response = client.patch(
        f"/api/v1/productos/{created.json()['id']}",
        json={"descripcion": None},
        headers=auth_headers,
    )
    assert response.status_code == 422
