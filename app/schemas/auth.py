from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    identifier: str
    password: str


class LoginResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: str
    is_blocked: int
