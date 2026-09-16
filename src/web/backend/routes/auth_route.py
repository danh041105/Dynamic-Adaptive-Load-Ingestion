from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.config.database import get_db
from backend.schemas.auth_schemas import (
        LoginRequest, TokenResponse, SignUpRequest, SignUpResponse,
        CurrentUserResponse
)
from backend.dependencies.auth_dependencies import get_current_user   
from backend.controllers.auth_controller import AuthController
from backend.models.user import User
from backend.constants.enums import UserRole

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/signup", response_model=SignUpResponse)
def register(payload: SignUpRequest, db: Session = Depends(get_db)):
    # Router chỉ nhận request và chuyển ngay cho Controller xử lý
    return AuthController.register_controller(payload=payload, db=db)

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    # Router chỉ nhận request và chuyển ngay cho Controller xử lý
    return AuthController.login_controller(payload=payload, db=db)

@router.get("/me", response_model=CurrentUserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

# @router.post("/data-engineer")
# def create_de(current_user: User = Depends(require_roles(UserRole.DATA_ENGINEER))):
#     return {"message": "Data Engineer created"}

# @router.post("/rf-engineer")
# def create_rf_analysis(current_user: User = Depends(require_roles(UserRole.RADIO_FREQUENCY_ENGINEER))):
#     return {"message": "RF Engineer created"}

# @router.get("/shared-resource")
# def get_shared_resource(current_user: User = Depends(
#         require_roles(
#             UserRole.DATA_ENGINEER,
#             UserRole.RADIO_FREQUENCY_ENGINEER,
#         )
#     ),
# ):
#     return {"message": "Allowed"}