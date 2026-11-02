"""Comprueba los endpoints reales de salud de Gestión de Ventas."""

import json
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import urlopen


def check(base_url: str, deadline_seconds: int = 120) -> None:
    parsed = urlsplit(base_url)
    if (
        parsed.scheme != "https"
        or not parsed.netloc
        or parsed.username
        or parsed.password
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError(
            "RAILWAY_API_URL debe ser un origen HTTPS sin ruta ni credenciales"
        )

    origin = base_url.rstrip("/")
    deadline = time.monotonic() + deadline_seconds
    for path, expected in (
        ("/health", {"status": "ok"}),
        ("/health/db", {"status": "ok", "database": "connected"}),
    ):
        while True:
            try:
                with urlopen(origin + path, timeout=5) as response:
                    payload = json.load(response)
                    if response.status != 200 or payload != expected:
                        raise ValueError(f"Respuesta inesperada en {path}: {payload!r}")
                print(f"{path}: OK")
                break
            except (HTTPError, URLError, TimeoutError, ValueError) as exc:
                if time.monotonic() >= deadline:
                    raise SystemExit(f"Verificación fallida en {path}: {exc}") from exc
                time.sleep(5)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Uso: python check_deployment.py https://api.example.com")
    check(sys.argv[1])
