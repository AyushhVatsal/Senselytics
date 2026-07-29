from sqlalchemy.orm import Session

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
        return (
            db.query(Dataset)
            .filter(Dataset.id == dataset_id)
            .first()
        )

    @staticmethod
    def get_user_datasets(
        db: Session,
        user_id: int,
    ) -> list[Dataset]:
        return (
            db.query(Dataset)
            .filter(Dataset.user_id == user_id)
            .order_by(Dataset.created_at.desc())
            .all()
        )

    @staticmethod
    def delete_dataset(
        db: Session,
        dataset: Dataset,
    ) -> None:
        """
        Mark dataset for deletion.

        Service layer commits.
        """

        db.delete(dataset)

    @staticmethod
    def update_dataset(
        db: Session,
        dataset: Dataset,
    ) -> Dataset:
        """
        Flush pending updates.

        Service layer commits.
        """

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