from sqlalchemy import text
from sqlalchemy.orm import Session


class SQLExecutor:

    @staticmethod
    def execute(
        db: Session,
        sql: str,
        max_rows: int = 100,
    ) -> list[dict]:

        # Enforce a maximum result size.
        sql = sql.strip().rstrip(";")
        
        limited_sql = f"""
        SELECT *
        FROM (
            {sql}
        ) AS query_result
        LIMIT {max_rows}
        """

        result = db.execute(text(limited_sql))

        rows = result.mappings().all()

        return [dict(row) for row in rows]