from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.dataset import Dataset


class DatasetCRUD:
    @staticmethod
    def create_dataset(
        db: Session,
        dataset: Dataset,
    ) -> Dataset:
        """
        Add a dataset to the current transaction.

        NOTE:
        Does not commit. The service layer is responsible
        for committing or rolling back the transaction.
        """

        db.add(dataset)
        db.flush()          # Generates dataset.id
        db.refresh(dataset)

        return dataset

    @staticmethod
    def get_dataset_by_id(
        db: Session,
        dataset_id: int,
    ) -> Dataset | None:
        """
        Retrieve a dataset by its ID.
        """

        stmt = select(Dataset).where(
            Dataset.id == dataset_id
        )

        return db.scalar(stmt)

    @staticmethod
    def get_user_datasets(
        db: Session,
        user_id: int,
    ) -> list[Dataset]:
        """
        Retrieve all datasets belonging to a user.
        """

        stmt = (
            select(Dataset)
            .where(Dataset.user_id == user_id)
            .order_by(Dataset.created_at.desc())
        )

        return list(db.scalars(stmt))

    @staticmethod
    def delete_dataset(
        db: Session,
        dataset: Dataset,
    ) -> None:
        """
        Delete a dataset record.
        """

        db.delete(dataset)
        db.flush()

    @staticmethod
    def update_dataset(
        db: Session,
        dataset: Dataset,
        name: str,
    ) -> Dataset:
        """
        Update the dataset name.
        """

        dataset.name = name

        db.flush()
        db.refresh(dataset)

        return dataset

    @staticmethod
    def commit(db: Session) -> None:
        """
        Commit the current transaction.
        """
        db.commit()


    @staticmethod
    def rollback(db: Session) -> None:
        """
        Roll back the current transaction.
        """
        db.rollback()