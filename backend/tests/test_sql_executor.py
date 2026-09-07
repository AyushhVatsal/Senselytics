from app.services.query.sql_executor import SQLExecutor


def test_sql_executor(db_session):

    sql = """
    SELECT product, revenue
    FROM dataset_4
    ORDER BY revenue DESC
    """

    results = SQLExecutor.execute(
        db=db_session,
        sql=sql,
    )

    assert isinstance(results, list)