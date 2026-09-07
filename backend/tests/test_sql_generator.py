from app.services.query.sql_generator import SQLGenerator


def test_sql_generator():

    schema = {
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

    generator = SQLGenerator()

    sql = generator.generate_sql(
        question="Which product generated the most revenue?",
        schema=schema,
    )

    print("\nGenerated SQL:")
    print(sql)

    assert sql