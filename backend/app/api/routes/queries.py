from uuid import uuid4

from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_user
from app.api.deps.db import get_db

from app.models.user import User

from app.schemas.query import (
    QueryRequest,
    QueryResponse,
    QueryResumeRequest,
)

from app.services.query.query_service import QueryService


router = APIRouter(
    prefix="/queries",
    tags=["Queries"],
)


# ==========================================================
# NORMAL QUERY
# ==========================================================

@router.post(
    "/",
    response_model=QueryResponse,
)
def create_query(
    query: QueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    return QueryService.process_query(
        db=db,
        user_id=current_user.id,
        dataset_id=query.dataset_id,
        question=query.question,
        thread_id=str(uuid4()),
    )


# ==========================================================
# STREAMING QUERY
# ==========================================================

@router.post(
    "/stream",
)
def stream_query(
    query: QueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    return QueryService.stream_query(
        db=db,
        user_id=current_user.id,
        dataset_id=query.dataset_id,
        question=query.question,
        thread_id=str(uuid4()),
    )


# ==========================================================
# RESUME QUERY
# ==========================================================

@router.post(
    "/{thread_id}/resume",
    response_model=QueryResponse,
)
def resume_query(
    thread_id: str,
    request: QueryResumeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    return QueryService.resume_query(
        db=db,
        thread_id=thread_id,
        answer=request.answer,
    )