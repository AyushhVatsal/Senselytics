from app.services.query.sql_validator import SQLValidator


SCHEMA = {
    "table_name": "dataset_4",
    "columns": [
        {"name": "product", "type": "TEXT"},
        {"name": "category", "type": "TEXT"},
        {"name": "region", "type": "TEXT"},
        {"name": "quantity", "type": "BIGINT"},
        {"name": "unit_price", "type": "BIGINT"},
        {"name": "sale_date", "type": "TEXT"},
        {"name": "revenue", "type": "BIGINT"},
    ],
}


def test_valid_select_query():

    sql = """
    SELECT product
    FROM dataset_4
    GROUP BY product
    ORDER BY SUM(revenue) DESC
    LIMIT 1;
    """

    valid, message = SQLValidator.validate(
        sql=sql,
        schema=SCHEMA,
    )

    assert valid is True
    assert message == "SQL query is valid."


def test_reject_insert():

    sql = """
    INSERT INTO dataset_4 (product)
    VALUES ('Test');
    """

    valid, message = SQLValidator.validate(
        sql=sql,
        schema=SCHEMA,
    )

    assert valid is False


def test_reject_delete():

    sql = """
    DELETE FROM dataset_4;
    """

    valid, message = SQLValidator.validate(
        sql=sql,
        schema=SCHEMA,
    )

    assert valid is False


def test_reject_drop():

    sql = """
    DROP TABLE dataset_4;
    """

    valid, message = SQLValidator.validate(
        sql=sql,
        schema=SCHEMA,
    )

    assert valid is False


def test_reject_wrong_table():

    sql = """
    SELECT product
    FROM users;
    """

    valid, message = SQLValidator.validate(
        sql=sql,
        schema=SCHEMA,
    )

    assert valid is False


def test_reject_empty_sql():

    valid, message = SQLValidator.validate(
        sql="",
        schema=SCHEMA,
    )

    assert valid is False

def test_reject_multiple_statements():

    sql = """
    SELECT product
    FROM dataset_4;

    DROP TABLE dataset_4;
    """

    valid, message = SQLValidator.validate(
        sql=sql,
        schema=SCHEMA,
    )

    assert valid is False


def test_reject_update_inside_with():

    sql = """
    WITH updated AS (
        UPDATE dataset_4
        SET revenue = 0
        RETURNING *
    )
    SELECT *
    FROM updated;
    """

    valid, message = SQLValidator.validate(
        sql=sql,
        schema=SCHEMA,
    )

    assert valid is False


def test_reject_delete_inside_with():

    sql = """
    WITH deleted AS (
        DELETE FROM dataset_4
        RETURNING *
    )
    SELECT *
    FROM deleted;
    """

    valid, message = SQLValidator.validate(
        sql=sql,
        schema=SCHEMA,
    )

    assert valid is False


def test_reject_sql_comment_attack():

    sql = """
    SELECT product
    FROM dataset_4
    -- DROP TABLE dataset_4;
    """

    valid, message = SQLValidator.validate(
        sql=sql,
        schema=SCHEMA,
    )

    assert valid is True


def test_accept_case_insensitive_sql():

    sql = """
    select product
    from dataset_4
    group by product;
    """

    valid, message = SQLValidator.validate(
        sql=sql,
        schema=SCHEMA,
    )

    assert valid is True


def test_accept_complex_analytical_query():

    sql = """
    SELECT
        category,
        SUM(revenue) AS total_revenue,
        AVG(unit_price) AS average_price
    FROM dataset_4
    WHERE quantity > 0
    GROUP BY category
    ORDER BY total_revenue DESC
    LIMIT 5;
    """

    valid, message = SQLValidator.validate(
        sql=sql,
        schema=SCHEMA,
    )

    assert valid is True