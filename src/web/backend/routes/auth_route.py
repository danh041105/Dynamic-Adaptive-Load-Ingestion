from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.config.database import get_db
from backend.schemas.auth_schemas import UserRole, LoginRequest, TokenResponse, SignUpRequest, SignUpResponse
from backend.controllers.auth_controller import AuthController
from backend.models.user import User
from backend.dependencies.auth_dependencies import require_roles

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/signup", response_model=SignUpResponse)
def register(payload: SignUpRequest, db: Session = Depends(get_db)):
    # Router chỉ nhận request và chuyển ngay cho Controller xử lý
    return AuthController.register_controller(payload=payload, db=db)

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    # Router chỉ nhận request và chuyển ngay cho Controller xử lý
    return AuthController.login_controller(payload=payload, db=db)

@router.post("/data-engineer")
def create_de(current_user: User = Depends(require_roles(UserRole.DATA_ENGINEER))):
    return {"message": "Data Engineer created"}

@router.post("/rf-egineer")
def create_rf_analysis(current_user: User = Depends(require_roles(UserRole.RADIO_FREQUENCY_ENGINEER))):
    return {"message": "RF Engineer created"}

@router.get("/shared-resource")
def get_shared_resource(current_user: User = Depends(
        require_roles(
            UserRole.DATA_ENGINEER,
            UserRole.RADIO_FREQUENCY_ENGINEER,
        )
    ),
):
    return {"message": "Allowed"}