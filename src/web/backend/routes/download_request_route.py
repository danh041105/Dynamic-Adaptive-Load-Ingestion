from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from backend.config.database import get_db
from backend.constants.enums import UserRole
from backend.controllers.download_request_controller import DownloadRequestController
from backend.dependencies.auth_dependencies import require_roles
from backend.models.user import User
from backend.schemas.download_request_schemas import (
    DownloadRequestCreate,
    DownloadRequestCreateResponse,
    DownloadRequestListItem,
    DownloadRequestDetailResponse,
)


router = APIRouter(
    prefix="/radio-frequency-engineer/requests",
    tags=["RF Download Requests"],
)

@router.post("", response_model=DownloadRequestCreateResponse, status_code=status.HTTP_201_CREATED)
def create_download_request(
    payload: DownloadRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.RADIO_FREQUENCY_ENGINEER))):
    return DownloadRequestController.create_request_controller(
        payload=payload,
        current_user=current_user,
        db=db,
    )

@router.get("", response_model=list[DownloadRequestListItem])
def get_my_requests(db: Session = Depends(get_db), current_user: User = Depends(
        require_roles(UserRole.RADIO_FREQUENCY_ENGINEER)
    )
):
    return DownloadRequestController.get_my_requests_controller(
        current_user=current_user,
        db=db,
    )


@router.get("/{request_id}", response_model=DownloadRequestDetailResponse)
def get_request_detail(request_id: int, db: Session = Depends(get_db), current_user: User = Depends(
        require_roles(UserRole.RADIO_FREQUENCY_ENGINEER)
    )
):
    return DownloadRequestController.get_request_detail_controller(
        request_id=request_id,
        current_user=current_user,
        db=db,
    )
