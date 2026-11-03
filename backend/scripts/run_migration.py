"""Ejecuta una migración SQL versionada de forma atómica en PostgreSQL."""

import argparse
import hashlib
import re
import sys
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import SQLAlchemyError

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.database import engine

MIGRATIONS_DIR = BACKEND_DIR / "migrations"
MIGRATION_VERSION = "001_create_inventory_movements"
MIGRATION_PATH = MIGRATIONS_DIR / f"{MIGRATION_VERSION}.sql"
EXPECTED_TRACKING_COLUMNS = {
    "version": ("character varying", "NO", 120),
    "checksum": ("character varying", "NO", 64),
    "applied_at": ("timestamp with time zone", "NO", None),
}
EXPECTED_INVENTORY_COLUMNS = {
    "id": ("integer", "NO", None),
    "producto_id": ("integer", "NO", None),
    "tipo_movimiento": ("USER-DEFINED", "NO", None),
    "cantidad": ("integer", "NO", None),
    "motivo": ("character varying", "NO", 500),
    "venta_id": ("integer", "YES", None),
    "fecha_creacion": ("timestamp with time zone", "NO", None),
}
EXPECTED_CONSTRAINTS = {
    "ck_movimientos_inventario_cantidad_positiva",
    "ck_movimientos_inventario_referencia_venta",
    "fk_movimientos_inventario_producto",
    "fk_movimientos_inventario_venta",
    "movimientos_inventario_pkey",
}
EXPECTED_INDEXES = {
    "ix_movimientos_inventario_producto_id",
    "ix_movimientos_inventario_venta_id",
    "ix_movimientos_inventario_fecha_creacion",
}
_DOLLAR_QUOTE_PATTERN = re.compile(r"\$(?:[A-Za-z_][A-Za-z0-9_]*)?\$")


def migration_checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def split_sql_statements(sql: str) -> list[str]:
    """Separa sentencias sin dividir bloques dólar, cadenas o comentarios PostgreSQL."""
    statements: list[str] = []
    start = 0
    position = 0
    dollar_quote: str | None = None
    in_single_quote = False
    single_quote_uses_backslash_escapes = False
    in_double_quote = False
    in_line_comment = False
    block_comment_depth = 0

    while position < len(sql):
        character = sql[position]
        next_character = sql[position + 1] if position + 1 < len(sql) else ""

        if dollar_quote is not None:
            if sql.startswith(dollar_quote, position):
                position += len(dollar_quote)
                dollar_quote = None
                continue
            position += 1
            continue

        if in_single_quote:
            if single_quote_uses_backslash_escapes and character == "\\":
                position += 2
                continue
            if character == "'" and next_character == "'":
                position += 2
                continue
            if character == "'":
                in_single_quote = False
                single_quote_uses_backslash_escapes = False
            position += 1
            continue

        if in_double_quote:
            if character == '"' and next_character == '"':
                position += 2
                continue
            if character == '"':
                in_double_quote = False
            position += 1
            continue

        if in_line_comment:
            if character == "\n":
                in_line_comment = False
            position += 1
            continue

        if block_comment_depth:
            if character == "/" and next_character == "*":
                block_comment_depth += 1
                position += 2
                continue
            if character == "*" and next_character == "/":
                block_comment_depth -= 1
                position += 2
                continue
            position += 1
            continue

        if character == "-" and next_character == "-":
            in_line_comment = True
            position += 2
            continue
        if character == "/" and next_character == "*":
            block_comment_depth = 1
            position += 2
            continue
        if character == "'":
            in_single_quote = True
            previous_character = sql[position - 1] if position else ""
            prefix_character = sql[position - 2] if position > 1 else ""
            single_quote_uses_backslash_escapes = (
                previous_character in {"E", "e"}
                and (not prefix_character or not (prefix_character.isalnum() or prefix_character == "_"))
            )
            position += 1
            continue
        if character == '"':
            in_double_quote = True
            position += 1
            continue
        if character == "$":
            match = _DOLLAR_QUOTE_PATTERN.match(sql, position)
            if match is not None:
                dollar_quote = match.group()
                position += len(dollar_quote)
                continue
        if character == ";":
            statement = sql[start:position].strip()
            if statement:
                statements.append(statement)
            start = position + 1
        position += 1

    if (
        dollar_quote is not None
        or in_single_quote
        or in_double_quote
        or block_comment_depth
    ):
        raise RuntimeError(
            "El archivo SQL contiene una cadena, comentario o bloque dólar sin cerrar."
        )

    statement = sql[start:].strip()
    if statement:
        statements.append(statement)
    return statements


def execute_sql_script(connection: Connection, sql: str) -> None:
    """Ejecuta cada sentencia PostgreSQL en la transacción SQLAlchemy abierta."""
    for statement in split_sql_statements(sql):
        connection.exec_driver_sql(statement)


def ensure_postgresql() -> None:
    if engine.dialect.name != "postgresql":
        raise RuntimeError(
            "Las migraciones versionadas de producción requieren PostgreSQL."
        )


def ensure_tracking_table(connection: Connection) -> None:
    connection.execute(text("""
            CREATE TABLE IF NOT EXISTS gestion_ventas_migraciones (
                version VARCHAR(120) PRIMARY KEY,
                checksum VARCHAR(64) NOT NULL,
                applied_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
            )
            """))
    rows = connection.execute(text("""
            SELECT column_name, data_type, is_nullable, character_maximum_length
            FROM information_schema.columns
            WHERE table_schema = current_schema()
            AND table_name = 'gestion_ventas_migraciones'
            """)).all()
    actual_columns = {
        row.column_name: (row.data_type, row.is_nullable, row.character_maximum_length)
        for row in rows
    }
    if actual_columns != EXPECTED_TRACKING_COLUMNS:
        raise RuntimeError("La tabla de control de migraciones no es compatible.")
    primary_key = connection.execute(text("""
            SELECT constraint_table.conname
            FROM pg_constraint AS constraint_table
            JOIN pg_class AS source_table
                ON source_table.oid = constraint_table.conrelid
            JOIN pg_namespace AS source_schema
                ON source_schema.oid = source_table.relnamespace
            WHERE source_schema.nspname = current_schema()
            AND source_table.relname = 'gestion_ventas_migraciones'
            AND constraint_table.contype = 'p'
            """)).scalar_one_or_none()
    if primary_key != "gestion_ventas_migraciones_pkey":
        raise RuntimeError(
            "La tabla de control de migraciones no tiene la clave primaria esperada."
        )


def verify_inventory_schema(connection: Connection) -> None:
    enum_values = connection.execute(text("""
            SELECT enumlabel
            FROM pg_enum
            JOIN pg_type ON pg_type.oid = pg_enum.enumtypid
            JOIN pg_namespace ON pg_namespace.oid = pg_type.typnamespace
            WHERE pg_type.typname = 'tipo_movimiento_inventario'
            AND pg_namespace.nspname = current_schema()
            ORDER BY enumsortorder
            """)).scalars().all()
    if enum_values != ["entrada", "salida", "venta"]:
        raise RuntimeError("El enum tipo_movimiento_inventario no es compatible.")

    rows = connection.execute(text("""
            SELECT column_name, data_type, is_nullable, character_maximum_length
            FROM information_schema.columns
            WHERE table_schema = current_schema()
            AND table_name = 'movimientos_inventario'
            """)).all()
    actual_columns = {
        row.column_name: (row.data_type, row.is_nullable, row.character_maximum_length)
        for row in rows
    }
    if actual_columns != EXPECTED_INVENTORY_COLUMNS:
        raise RuntimeError("La tabla movimientos_inventario no es compatible.")

    constraints = {row.conname: row.definition for row in connection.execute(text("""
                SELECT
                    constraint_table.conname,
                    pg_get_constraintdef(constraint_table.oid) AS definition
                FROM pg_constraint AS constraint_table
                JOIN pg_class AS source_table
                    ON source_table.oid = constraint_table.conrelid
                JOIN pg_namespace AS source_schema
                    ON source_schema.oid = source_table.relnamespace
                WHERE source_schema.nspname = current_schema()
                AND source_table.relname = 'movimientos_inventario'
                """))}
    if not EXPECTED_CONSTRAINTS.issubset(constraints):
        raise RuntimeError(
            "Las restricciones de movimientos_inventario no son compatibles."
        )
    if "cantidad > 0" not in constraints["ck_movimientos_inventario_cantidad_positiva"]:
        raise RuntimeError("La restricción de cantidad positiva no es compatible.")
    if (
        "tipo_movimiento = 'venta'::tipo_movimiento_inventario"
        not in constraints["ck_movimientos_inventario_referencia_venta"]
        or "venta_id IS NOT NULL"
        not in constraints["ck_movimientos_inventario_referencia_venta"]
        or "venta_id IS NULL"
        not in constraints["ck_movimientos_inventario_referencia_venta"]
    ):
        raise RuntimeError("La restricción de referencia de venta no es compatible.")

    foreign_key_targets = {
        row.conname: row.target_is_compatible for row in connection.execute(text("""
                SELECT
                    constraint_table.conname,
                    CASE
                        WHEN constraint_table.conname = 'fk_movimientos_inventario_producto'
                            THEN referenced_schema.nspname = current_schema()
                                AND referenced_table.relname = 'productos'
                                AND constraint_table.confdeltype = 'r'
                        WHEN constraint_table.conname = 'fk_movimientos_inventario_venta'
                            THEN referenced_schema.nspname = current_schema()
                                AND referenced_table.relname = 'ventas'
                                AND constraint_table.confdeltype = 'r'
                        ELSE false
                    END AS target_is_compatible
                FROM pg_constraint AS constraint_table
                JOIN pg_class AS source_table
                    ON source_table.oid = constraint_table.conrelid
                JOIN pg_namespace AS source_schema
                    ON source_schema.oid = source_table.relnamespace
                JOIN pg_class AS referenced_table
                    ON referenced_table.oid = constraint_table.confrelid
                JOIN pg_namespace AS referenced_schema
                    ON referenced_schema.oid = referenced_table.relnamespace
                WHERE source_schema.nspname = current_schema()
                AND source_table.relname = 'movimientos_inventario'
                AND constraint_table.contype = 'f'
                """))
    }
    if not foreign_key_targets.get(
        "fk_movimientos_inventario_producto"
    ) or not foreign_key_targets.get("fk_movimientos_inventario_venta"):
        raise RuntimeError(
            "Las claves foráneas o sus acciones ON DELETE de movimientos_inventario no son compatibles."
        )

    indexes = {row.indexname: row.indexdef for row in connection.execute(text("""
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE schemaname = current_schema()
                AND tablename = 'movimientos_inventario'
                """))}
    if not EXPECTED_INDEXES.issubset(indexes):
        raise RuntimeError("Los índices de movimientos_inventario no son compatibles.")
    for index_name, column_name in {
        "ix_movimientos_inventario_producto_id": "producto_id",
        "ix_movimientos_inventario_venta_id": "venta_id",
        "ix_movimientos_inventario_fecha_creacion": "fecha_creacion",
    }.items():
        if f"({column_name})" not in indexes[index_name]:
            raise RuntimeError(f"El índice {index_name} no es compatible.")


def run_migration(path: Path, version: str) -> bool:
    if not path.is_file():
        raise FileNotFoundError(f"No existe la migración: {path}")
    ensure_postgresql()
    checksum = migration_checksum(path)
    sql = path.read_text(encoding="utf-8")

    with engine.begin() as connection:
        connection.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:version))"),
            {"version": version},
        )
        ensure_tracking_table(connection)
        applied_checksum = connection.execute(
            text("""
                SELECT checksum
                FROM gestion_ventas_migraciones
                WHERE version = :version
                FOR UPDATE
                """),
            {"version": version},
        ).scalar_one_or_none()

        if applied_checksum is not None:
            if applied_checksum != checksum:
                raise RuntimeError(
                    f"La migración {version} ya fue aplicada con un checksum diferente."
                )
            verify_inventory_schema(connection)
            return False

        execute_sql_script(connection, sql)
        verify_inventory_schema(connection)
        connection.execute(
            text("""
                INSERT INTO gestion_ventas_migraciones (version, checksum)
                VALUES (:version, :checksum)
                """),
            {"version": version, "checksum": checksum},
        )
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ejecuta una migración PostgreSQL versionada."
    )
    parser.add_argument(
        "--path", type=Path, default=MIGRATION_PATH, help="Ruta del archivo SQL."
    )
    parser.add_argument(
        "--version",
        default=MIGRATION_VERSION,
        help="Identificador de versión de la migración.",
    )
    arguments = parser.parse_args()

    try:
        executed = run_migration(arguments.path, arguments.version)
    except (FileNotFoundError, RuntimeError, SQLAlchemyError) as exc:
        print(f"Error de migración: {exc}", file=sys.stderr)
        return 1

    if executed:
        print(f"Migración {arguments.version} aplicada correctamente.")
    else:
        print(
            f"Migración {arguments.version} ya estaba aplicada con el mismo checksum."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
