import re
from pydantic import BaseModel, Field, field_validator
from backend.constants.enums import UserRole

class SignUpRequest(BaseModel):
    username: str = Field(
        ..., 
        min_length=4,
        description="Tên đăng nhập từ 4-50 ký tự, chỉ chứa chữ cái, số và dấu gạch dưới"
    )
    password: str = Field(
        ..., 
        min_length=8,
        description="Mật khẩu ít nhất 8 ký tự, bao gồm chữ hoa, chữ thường, số và ký tự đặc biệt"
    )
    role: UserRole

# Validation username: Không chứa khoảng trắng hoặc ký tự đặc biệt lạ
    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str)-> str:
        # Chỉ cho phép chữ cái, số, dấu gạch dưới (_) và dấu chấm (.)
        if not re.match(r"^[a-zA-Z0-9_.]+$", value):
            raise ValueError("Username chỉ được phép chứa chữ cái, số, dấu gạch dưới _ và dấu chấm .") 
        return value.lower() # Trả về dạng in thường

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not len(value) >= 8:
            raise ValueError("Mật khẩu không đủ 8 kí tự")
        if not re.search(r"[A-Z]", value):
            raise ValueError("Mật khẩu phải chứa ít nhất một chữ cái viết hoa")
        if not re.search(r"[a-z]", value):
            raise ValueError("Mật khẩu phải chứa ít nhất một chữ cái viết thường")
        if not re.search(r"[0-9]", value):
            raise ValueError("Mật khẩu phải chứa ít nhất một chữ số từ 0-9")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
            raise ValueError("Mật khẩu phải chứa ít nhất một ký tự đặc biệt")
        return value

class SignUpResponse(BaseModel):
    user_id: int = Field(validation_alias="id")
    username: str
    role: UserRole
    model_config = {
        "from_attributes": True,
        "populate_by_name": True
    }

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=4) # Dấu ...: Bắt buộc phải điền đầy đủ thông tin
    password: str = Field(..., min_length=8)

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        return value.strip().lower()

class TokenResponse(BaseModel): # Trả về 1 token để đăng nhập
    access_token: str
    token_type: str = "bearer"

class CurrentUserResponse(BaseModel):
    user_id: int = Field(validation_alias="id")
    username: str
    role: UserRole

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }