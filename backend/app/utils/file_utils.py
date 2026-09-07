from pathlib import Path
import shutil
import uuid

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings


class FileUtils:
    ALLOWED_EXTENSIONS = {".csv", ".xlsx"}
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

    @staticmethod
    def generate_filename(filename: str) -> str:
        """
        Generate a unique filename using UUID.
        """

        return f"{uuid.uuid4()}_{filename}"

    @staticmethod
    def validate_extension(filename: str) -> None:
        """
        Validate the uploaded file extension.
        """

        extension = Path(filename).suffix.lower()

        if extension not in FileUtils.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only CSV and Excel files are allowed.",
            )

    @staticmethod
    async def validate_file_size(file: UploadFile) -> None:
        """
        Validate uploaded file size.
        """

        contents = await file.read()

        if len(contents) > FileUtils.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File size exceeds 50 MB.",
            )

        await file.seek(0)

    @staticmethod
    def save_file(
        file: UploadFile,
        stored_filename: str,
    ) -> Path:
        """
        Save the uploaded file to disk.
        """

        upload_dir = Path(settings.UPLOAD_DIR)

        upload_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        file_path = upload_dir / stored_filename

        with file_path.open("wb") as buffer:
            shutil.copyfileobj(
                file.file,
                buffer,
            )

        return file_path

    @staticmethod
    def delete_file(file_path: str | Path) -> None:
        """
        Delete a file if it exists.
        """

        path = Path(file_path)

        if path.exists():
            path.unlink()