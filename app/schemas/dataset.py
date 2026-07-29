from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DatasetBase(BaseModel):
    name: str

class DatasetCreate(DatasetBase):
    pass

class DatasetUpdate(BaseModel):
    name: str

class DatasetListResponse(BaseModel):
    id: int
    name: str
    file_type: str
    row_count: int
    column_count: int
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
    
class DatasetResponse(DatasetBase):
    id: int

    user_id: int

    original_filename: str

    stored_filename: str

    table_name: str

    file_path: str

    file_type: str

    file_size: int

    row_count: int

    column_count: int

    status: str

    created_at: datetime

    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )