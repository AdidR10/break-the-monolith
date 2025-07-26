from pydantic import BaseModel, EmailStr, constr
from enum import Enum
from typing import Optional

class UserType(str, Enum):
    STUDENT = "STUDENT"
    RICKSHAW_PULLER = "RICKSHAW_PULLER"

class RegisterRequest(BaseModel):
    email: EmailStr
    phone: constr(min_length=10, max_length=20)
    password: constr(min_length=6)
    first_name: Optional[str]
    last_name: Optional[str]
    user_type: UserType
    student_id: Optional[str]
    department: Optional[str]
    rickshaw_number: Optional[str]
    license_number: Optional[str]

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
