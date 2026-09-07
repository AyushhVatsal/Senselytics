from sqlalchemy import inspect
from sqlalchemy.orm import Session


class SchemaService:

    @staticmethod
    def get_dataset_schema(
        db: Session,
        table_name: str,
    ) -> dict:
        """
        Retrieve the schema of a dataset table
        from PostgreSQL.
        """

        inspector = inspect(db.get_bind())

        columns = inspector.get_columns(table_name)

        if not columns:
            raise ValueError(
                f"Table '{table_name}' does not exist or has no columns."
            )

        schema = []

        for column in columns:
            schema.append(
                {
                    "name": column["name"],
                    "type": str(column["type"]),
                    "nullable": column["nullable"],
                }
            )

        return {
            "table_name": table_name,
            "columns": schema,
        }