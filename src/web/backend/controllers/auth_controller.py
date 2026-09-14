from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from backend.schemas.auth_schemas import LoginRequest, SignUpRequest
from backend.services.auth_service import AuthService

class AuthController:

    @staticmethod
    def login_controller(payload: LoginRequest, db: Session):
        # Gọi tầng Service để xử lý logic kiểm tra tài khoản & tạo token
        result = AuthService.authenticate_user(
            db=db,
            username=payload.username,
            password=payload.password
        )
        return result

    # Gọi service để xử lý logic tạo tài khoản
    @staticmethod
    def register_controller(payload: SignUpRequest, db: Session):
        result = AuthService.register_user(
            db=db,
            username=payload.username,
            password=payload.password,
            role=payload.role
        )
        return result