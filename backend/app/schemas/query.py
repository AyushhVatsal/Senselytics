from typing import Any

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    dataset_id: int = Field(gt=0)
    question: str = Field(min_length=1)


class QueryResumeRequest(BaseModel):
    answer: str = Field(min_length=1)


class ColumnSchema(BaseModel):
    name: str
    type: str
    nullable: bool


class QueryResponse(BaseModel):
    dataset_id: int
    question: str

    status: str

    sql: str | None = None
    results: list[dict[str, Any]] | None = None
    answer: str | None = None

    thread_id: str | None = None
    clarification_question: str | None = None