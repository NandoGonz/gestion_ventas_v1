DO $$
DECLARE
    expected_source_columns integer;
BEGIN
    SELECT count(*)
    INTO expected_source_columns
    FROM information_schema.columns
    WHERE (table_schema = current_schema() AND table_name = 'productos' AND column_name IN ('id', 'stock'))
       OR (table_schema = current_schema() AND table_name = 'ventas' AND column_name = 'id');

    IF expected_source_columns <> 3 THEN
        RAISE EXCEPTION 'El esquema existente no contiene las columnas requeridas de productos y ventas.';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = 'productos'
          AND column_name IN ('id', 'stock')
          AND (data_type <> 'integer' OR is_nullable <> 'NO')
    ) OR EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = 'ventas'
          AND column_name = 'id'
          AND (data_type <> 'integer' OR is_nullable <> 'NO')
    ) THEN
        RAISE EXCEPTION 'Las columnas requeridas no son compatibles con la migración de inventario.';
    END IF;

    IF to_regtype(
        pg_catalog.quote_ident(current_schema())
        || '.'
        || pg_catalog.quote_ident('tipo_movimiento_inventario')
    ) IS NOT NULL
       OR to_regclass(
           pg_catalog.quote_ident(current_schema())
           || '.'
           || pg_catalog.quote_ident('movimientos_inventario')
       ) IS NOT NULL THEN
        RAISE EXCEPTION 'Se detectaron elementos de inventario sin una migración registrada.';
    END IF;
END
$$;

CREATE TYPE tipo_movimiento_inventario AS ENUM ('entrada', 'salida', 'venta');

CREATE TABLE movimientos_inventario (
    id SERIAL PRIMARY KEY,
    producto_id INTEGER NOT NULL,
    tipo_movimiento tipo_movimiento_inventario NOT NULL,
    cantidad INTEGER NOT NULL,
    motivo VARCHAR(500) NOT NULL,
    venta_id INTEGER NULL,
    fecha_creacion TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    CONSTRAINT fk_movimientos_inventario_producto
        FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE RESTRICT,
    CONSTRAINT fk_movimientos_inventario_venta
        FOREIGN KEY (venta_id) REFERENCES ventas(id) ON DELETE RESTRICT,
    CONSTRAINT ck_movimientos_inventario_cantidad_positiva CHECK (cantidad > 0),
    CONSTRAINT ck_movimientos_inventario_referencia_venta CHECK (
        (tipo_movimiento = 'venta' AND venta_id IS NOT NULL)
        OR (tipo_movimiento IN ('entrada', 'salida') AND venta_id IS NULL)
    )
);

CREATE INDEX ix_movimientos_inventario_producto_id ON movimientos_inventario (producto_id);
CREATE INDEX ix_movimientos_inventario_venta_id ON movimientos_inventario (venta_id);
CREATE INDEX ix_movimientos_inventario_fecha_creacion ON movimientos_inventario (fecha_creacion);

INSERT INTO movimientos_inventario (producto_id, tipo_movimiento, cantidad, motivo)
SELECT
    productos.id,
    'entrada'::tipo_movimiento_inventario,
    productos.stock,
    'Saldo inicial al activar el módulo de inventario'
FROM productos
WHERE productos.stock > 0;
