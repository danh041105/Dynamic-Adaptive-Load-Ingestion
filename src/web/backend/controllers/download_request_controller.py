from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from backend.models.user import User
from backend.schemas.download_request_schemas import DownloadRequestCreate
from backend.services.download_request_service import (
    DownloadRequestService,
    DownloadRequestNotFoundError,
    InvalidTimeRangeError,
    SourceNotAvailableError,
    SourceNotFoundError,
)

class DownloadRequestController:

    @staticmethod
    def create_request_controller(payload: DownloadRequestCreate, current_user: User, db: Session):
        service = DownloadRequestService(db)

        try:
            return service.create_request(
                payload=payload,
                current_user=current_user,
            )

        except SourceNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc)
            )

        except SourceNotAvailableError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(exc)
            )

        except InvalidTimeRangeError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc)
            )

    @staticmethod
    def get_my_requests_controller(current_user: User,db: Session):
        service = DownloadRequestService(db)
        return service.get_my_requests(current_user=current_user)


    @staticmethod
    def get_request_detail_controller(request_id: int, current_user: User, db: Session):
        service = DownloadRequestService(db)
        try:
            return service.get_request_detail(
                request_id=request_id,
                current_user=current_user,
            )

        except DownloadRequestNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc)
            )