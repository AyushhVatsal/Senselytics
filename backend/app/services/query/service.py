from sqlalchemy.orm import Session

from app.services.query.graph.workflow import build_query_graph


class QueryService:

    def __init__(self, db: Session):
        self.db = db
        self.graph = build_query_graph(db)

    def execute(
        self,
        question: str,
        schema: dict,
        thread_id: str,
    ):

        config = {
            "configurable": {
                "thread_id": thread_id,
            }
        }

        state = {
            "question": question,
            "schema": schema,
        }

        return self.graph.invoke(
            state,
            config=config,
        )