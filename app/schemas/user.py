from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=100,
    )
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


# class UserLogin(BaseModel):
#     email: EmailStr
#     password: str = Field(
#         min_length=8,
#         max_length=128,
#     )


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr

    model_config = {
        "from_attributes": True
    }


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    password: str | None = Field(
        default=None,
        min_length=8,
        max_length=128,
    )