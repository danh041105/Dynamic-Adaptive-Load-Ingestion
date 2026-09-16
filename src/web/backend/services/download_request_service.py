from datetime import datetime, timezone
from sqlalchemy.orm import Session, joinedload

from backend.constants.enums import DownloadRequestStatus
from backend.models.download_request import DownloadRequest
from backend.models.nifi_source import NifiSource
from backend.models.user import User
from backend.schemas.download_request_schemas import (
    DownloadRequestCreate,
    DownloadRequestCreateResponse,
    DownloadRequestListItem,
    DownloadRequestDetailResponse,
)
from backend.services.source_service import SourceService


class SourceNotFoundError(Exception):
    pass

class SourceNotAvailableError(Exception):
    pass

class InvalidTimeRangeError(Exception):
    pass

class DownloadRequestNotFoundError(Exception):
    pass

class DownloadRequestService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_request(self, payload: DownloadRequestCreate, current_user: User) -> DownloadRequestCreateResponse:

        self._validate_time_range(start_time=payload.start_time, end_time=payload.end_time)
        source = self.db.query(NifiSource).filter(NifiSource.id == payload.source_id).first()
        
        if source is None:
            raise SourceNotFoundError("Source không tồn tại")

        self._validate_source_accepting_requests(source)

        download_request = DownloadRequest(
            user_id=current_user.id,
            source_id=source.id,
            start_time=payload.start_time,
            end_time=payload.end_time,
            status=DownloadRequestStatus.PENDING.value,
            failure_reason=None,
            created_at=datetime.now(timezone.utc),
            started_at=None,
            completed_at=None,
        )
    
        try:
            self.db.add(download_request)
            self.db.commit()
            self.db.refresh(download_request)

        except Exception:
            self.db.rollback()
            raise

        return DownloadRequestCreateResponse(
            id=download_request.id,
            source_id=source.id,
            source_name=source.name,
            start_time=download_request.start_time,
            end_time=download_request.end_time,
            status=DownloadRequestStatus(download_request.status),
            created_at=download_request.created_at,
        )

    def get_my_requests(self, current_user: User) -> list[DownloadRequestListItem]:
        requests = (self.db.query(DownloadRequest)
        .options(joinedload(DownloadRequest.source))
        .filter(DownloadRequest.user_id == current_user.id)
        .order_by(DownloadRequest.created_at.desc())
        .all()
        )
        return [
            DownloadRequestListItem(
                id=request.id,
                source_id=request.source_id,
                source_name=request.source.name,
                start_time=request.start_time,
                end_time=request.end_time,
                status=DownloadRequestStatus(request.status),
                created_at=request.created_at,
            )
            for request in requests
        ]

    def get_request_detail(self, request_id: int, current_user: User) -> DownloadRequestDetailResponse:
        request = (
            self.db.query(DownloadRequest)
            .options(joinedload(DownloadRequest.source))
            .filter(
                DownloadRequest.id == request_id,
                DownloadRequest.user_id == current_user.id
            ).first()
        )

        if request is None:
            raise DownloadRequestNotFoundError(
                "Download request không tồn tại"
            )

        return DownloadRequestDetailResponse(
            id=request.id,
            source_id=request.source_id,
            source_name=request.source.name,
            start_time=request.start_time,
            end_time=request.end_time,
            status=DownloadRequestStatus(request.status),
            failure_reason=request.failure_reason,
            created_at=request.created_at,
            started_at=request.started_at,
            completed_at=request.completed_at,
        )
    
    def _validate_source_accepting_requests(self, source: NifiSource) -> None:
        if not source.external_source_id:
            raise SourceNotAvailableError('Source is not mapped to a NiFi Process Group')
        availability = SourceService(self.db).get_source_availability(source.id)
        if availability is None:
            raise SourceNotFoundError('Source does not exist')
        if not availability.accepting_requests:
            raise SourceNotAvailableError('Source is not accepting download requests')

    # def _validate_source_accepting_requests(self, source_id: int) -> None:
    #     source_service = SourceService(self.db)
    #     availability = source_service.get_source_availability(source_id=source_id)
                        
    #     if availability is None:
    #         raise SourceNotFoundError("Source không tồn tại")
        
    #     if not availability.accepting_requests:
    #         raise SourceNotAvailableError("Source hiện không nhận download request")
        
    @staticmethod
    def _validate_time_range(start_time, end_time) -> None:
        if start_time.tzinfo is None or end_time.tzinfo is None:
            raise InvalidTimeRangeError('datetime values must include timezone')
        if start_time >= end_time:
            raise InvalidTimeRangeError('start_time must be before end_time')
        if end_time <= datetime.now(timezone.utc):
            raise InvalidTimeRangeError('download interval has ended')
            raise InvalidTimeRangeError("start_time phải nhỏ hơn end_time")
