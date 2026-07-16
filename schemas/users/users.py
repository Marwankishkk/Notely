from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class UserLogin(BaseModel):
    email: EmailStr
    password: str
class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str