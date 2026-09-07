from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(min_length=1)


class QueryResponse(BaseModel):
    question: str
    sql: str | None = None
    results: list[dict] | None = None
    final_answer: str | None = None
    status: str
    execution_error: str | None = None