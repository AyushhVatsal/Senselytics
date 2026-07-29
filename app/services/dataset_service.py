from pathlib import Path

import pandas as pd
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.crud.dataset import DatasetCRUD
from app.models.dataset import Dataset
from app.schemas.dataset import DatasetResponse
from app.utils.file_utils import FileUtils
import traceback


class DatasetService:
    """
    Business logic for Dataset operations.
    """

    @staticmethod
    async def upload_dataset(
        db: Session,
        user_id: int,
        name: str,
        file: UploadFile,
    ) -> DatasetResponse:
        """
        Upload a dataset.

        Workflow:
        1. Validate uploaded file
        2. Save uploaded file
        3. Read dataset using Pandas
        4. Clean dataframe
        5. Extract metadata
        6. Create dataset record
        7. Import dataframe into PostgreSQL
        8. Update dataset status
        9. Commit transaction
        """

        file_path: Path | None = None

        try:
            # -------------------------------------------------------
            # Step 1 : Validate Uploaded File
            # -------------------------------------------------------

            FileUtils.validate_extension(file.filename)
            await FileUtils.validate_file_size(file)

            # -------------------------------------------------------
            # Step 2 : Save Uploaded File
            # -------------------------------------------------------

            stored_filename = FileUtils.generate_filename(
                file.filename
            )

            file_path = FileUtils.save_file(
                file=file,
                stored_filename=stored_filename,
            )

            # -------------------------------------------------------
            # Step 3 : Read Dataset
            # -------------------------------------------------------

            dataframe = DatasetService._read_dataframe(file_path)

            # -------------------------------------------------------
            # Step 4 : Clean Dataset
            # -------------------------------------------------------

            dataframe = DatasetService._clean_dataframe(dataframe)

            # -------------------------------------------------------
            # Step 5 : Extract Metadata
            # -------------------------------------------------------

            metadata = DatasetService._extract_metadata(
                dataframe=dataframe,
                file_path=file_path,
            )

            # -------------------------------------------------------
            # Step 6 : Create Dataset Record
            # -------------------------------------------------------

            dataset = DatasetService._create_dataset_record(
                db=db,
                user_id=user_id,
                name=name,
                original_filename=file.filename,
                stored_filename=stored_filename,
                file_path=file_path,
                metadata=metadata,
            )

            # -------------------------------------------------------
            # Step 7 : Generate SQL Table Name
            # -------------------------------------------------------

            dataset.table_name = f"dataset_{dataset.id}"

            DatasetCRUD.update_dataset(
                db=db,
                dataset=dataset,
            )

            # -------------------------------------------------------
            # Step 8 : Import Dataset into PostgreSQL
            # -------------------------------------------------------

            DatasetService._import_dataframe(
                dataframe=dataframe,
                table_name=dataset.table_name,
                db=db,
            )

            # -------------------------------------------------------
            # Step 9 : Mark Upload Complete
            # -------------------------------------------------------

            dataset.status = "ready"

            DatasetCRUD.update_dataset(
                db=db,
                dataset=dataset,
            )

            db.commit()

            db.refresh(dataset)

            return DatasetResponse.model_validate(dataset)

        except HTTPException:
            db.rollback()

            if file_path:
                FileUtils.delete_file(file_path)

            raise

        except pd.errors.ParserError:
            db.rollback()

            if file_path:
                FileUtils.delete_file(file_path)

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to parse uploaded dataset.",
            )

        except SQLAlchemyError:
            db.rollback()

            if file_path:
                FileUtils.delete_file(file_path)

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred while uploading dataset.",
            )

        except Exception as e:
            traceback.print_exc()   # prints full traceback in terminal

            db.rollback()

            if file_path:
                FileUtils.delete_file(file_path)

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e),
            )

    # ===============================================================
    # Private Helper Methods
    # ===============================================================

    @staticmethod
    def _read_dataframe(file_path: Path) -> pd.DataFrame:
        """
        Read CSV or Excel file into a Pandas DataFrame.
        """

        extension = file_path.suffix.lower()

        if extension == ".csv":
            return pd.read_csv(file_path)

        if extension == ".xlsx":
            return pd.read_excel(file_path)

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format.",
        )

    @staticmethod
    def _clean_dataframe(
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Clean dataframe before importing into PostgreSQL.
        """

        dataframe.columns = (
            dataframe.columns
            .str.strip()
            .str.lower()
            .str.replace(" ", "_", regex=False)
        )

        return dataframe

    @staticmethod
    def _extract_metadata(
        dataframe: pd.DataFrame,
        file_path: Path,
    ) -> dict:
        """
        Extract dataset metadata.
        """

        return {
            "row_count": len(dataframe),
            "column_count": len(dataframe.columns),
            "file_size": file_path.stat().st_size,
            "file_type": file_path.suffix.lstrip("."),
        }

    @staticmethod
    def _create_dataset_record(
        db: Session,
        user_id: int,
        name: str,
        original_filename: str,
        stored_filename: str,
        file_path: Path,
        metadata: dict,
    ) -> Dataset:
        """
        Create Dataset ORM object.
        """

        dataset = Dataset(
            user_id=user_id,
            name=name,
            original_filename=original_filename,
            stored_filename=stored_filename,
            table_name="",
            file_path=str(file_path),
            file_type=metadata["file_type"],
            file_size=metadata["file_size"],
            row_count=metadata["row_count"],
            column_count=metadata["column_count"],
            status="uploading",
        )

        return DatasetCRUD.create_dataset(
            db=db,
            dataset=dataset,
        )

    @staticmethod
    def _import_dataframe(
        dataframe: pd.DataFrame,
        table_name: str,
        db: Session,
    ) -> None:
        """
        Import dataframe into PostgreSQL.

        TODO (Current V1):
        ------------------
        This uses Pandas to_sql().

        Future Improvements:
        - Infer SQL column types manually.
        - Add batch size configuration.
        - Use PostgreSQL COPY for very large datasets.
        - Handle duplicate column names.
        - Handle unsupported dtypes.
        - Add progress tracking.
        """

        dataframe.to_sql(
            name=table_name,
            con=db.get_bind(),
            if_exists="fail",
            index=False,
            method="multi",
        )

    # ===============================================================
    # TODO - Remaining Dataset Operations
    # ===============================================================

    @staticmethod
    def list_datasets(
        db: Session,
        user_id: int,
    ) -> list[Dataset]:
        """
        Retrieve all datasets belonging to the authenticated user.
        """

        return DatasetCRUD.get_user_datasets(
            db=db,
            user_id=user_id,
        )

    @staticmethod
    def get_dataset(
        db: Session,
        user_id: int,
        dataset_id: int,
    ) -> Dataset:
        """
        Retrieve a dataset owned by the authenticated user.
        """

        dataset = DatasetCRUD.get_dataset_by_id(
            db=db,
            dataset_id=dataset_id,
        )

        if dataset is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found.",
            )

        if dataset.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this dataset.",
            )

        return dataset

    @staticmethod
    def rename_dataset(
        db: Session,
        user_id: int,
        dataset_id: int,
        name: str,
    ) -> Dataset:
        """
        Rename a dataset.
        """

        dataset = DatasetService.get_dataset(
            db=db,
            user_id=user_id,
            dataset_id=dataset_id,
        )

        dataset = DatasetCRUD.update_dataset(
            db=db,
            dataset=dataset,
            name=name,
        )

        db.commit()
        db.refresh(dataset)

        return dataset

    @staticmethod
    def delete_dataset(
        db: Session,
        user_id: int,
        dataset_id: int,
    ) -> None:
        """
        Delete a dataset owned by the authenticated user.
        """

        dataset = DatasetService.get_dataset(
            db=db,
            user_id=user_id,
            dataset_id=dataset_id,
        )

        try:
            FileUtils.delete_file(dataset.file_path)

            db.execute(
                text(f'DROP TABLE IF EXISTS "{dataset.table_name}"')
            )

            DatasetCRUD.delete_dataset(
                db=db,
                dataset=dataset,
            )

            db.commit()

        except SQLAlchemyError:
            db.rollback()
            raise

        except Exception:
            db.rollback()
            raise