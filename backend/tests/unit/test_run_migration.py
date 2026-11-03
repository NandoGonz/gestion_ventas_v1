from scripts.run_migration import MIGRATION_PATH, split_sql_statements


def test_split_sql_statements_preserves_postgresql_escape_string_quotes():
    sql = r"INSERT INTO ejemplo VALUES (E'valor con \; y \'comillas\''); SELECT 1;"

    statements = split_sql_statements(sql)

    assert statements == [
        r"INSERT INTO ejemplo VALUES (E'valor con \; y \'comillas\'')",
        "SELECT 1",
    ]


def test_split_sql_statements_preserves_dollar_quoted_blocks():
    sql = "DO $$ BEGIN RAISE NOTICE 'una; dos'; END $$; SELECT 1;"

    statements = split_sql_statements(sql)

    assert statements == [
        "DO $$ BEGIN RAISE NOTICE 'una; dos'; END $$",
        "SELECT 1",
    ]


def test_inventory_migration_avoids_psycopg_percent_placeholders():
    sql = MIGRATION_PATH.read_text(encoding="utf-8")

    assert "%" not in sql
    assert "pg_catalog.quote_ident(current_schema())" in sql
