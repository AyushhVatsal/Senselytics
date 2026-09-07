from fastapi import APIRouter, Depends, File, Form, UploadFile, status, Response
from sqlalchemy.orm import Session

from app.api.deps.auth import get_current_user
from app.api.deps.db import get_db
from app.models.user import User
from app.schemas.dataset import (
    DatasetListResponse,
    DatasetResponse,
    DatasetUpdate,
)
from app.services.dataset_service import DatasetService

router = APIRouter(
    prefix="/datasets",
    tags=["Datasets"],
)


@router.post(
    "/upload",
    response_model=DatasetResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_dataset(
    name: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a CSV or Excel dataset.
    """

    return await DatasetService.upload_dataset(
        db=db,
        user_id=current_user.id,
        name=name,
        file=file,
    )


@router.get(
    "",
    response_model=list[DatasetListResponse],
    status_code=status.HTTP_200_OK,
)
def list_datasets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve all datasets belonging to the authenticated user.
    """

    return DatasetService.list_datasets(
        db=db,
        user_id=current_user.id,
    )

@router.get(
    "/{dataset_id}",
    response_model=DatasetResponse,
    status_code=status.HTTP_200_OK,
)
def get_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve a single dataset.
    """

    return DatasetService.get_dataset(
        db=db,
        user_id=current_user.id,
        dataset_id=dataset_id,
    )

@router.patch(
    "/{dataset_id}",
    response_model=DatasetResponse,
    status_code=status.HTTP_200_OK,
)
def rename_dataset(
    dataset_id: int,
    dataset_update: DatasetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Rename a dataset.
    """

    return DatasetService.rename_dataset(
        db=db,
        user_id=current_user.id,
        dataset_id=dataset_id,
        name=dataset_update.name,
    )

@router.delete(
    "/{dataset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a dataset.
    """

    DatasetService.delete_dataset(
        db=db,
        user_id=current_user.id,
        dataset_id=dataset_id,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)