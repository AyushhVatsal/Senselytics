from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.dataset import DatasetResponse
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
):
    """
    Upload a CSV or Excel dataset.
    """

    # TODO:
    # Replace this with authenticated user
    # current_user: User = Depends(get_current_user)

    user_id = 1

    return await DatasetService.upload_dataset(
        db=db,
        user_id=user_id,
        name=name,
        file=file,
    )