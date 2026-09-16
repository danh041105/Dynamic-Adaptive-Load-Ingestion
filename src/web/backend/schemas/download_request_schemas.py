from datetime import datetime
from pydantic import BaseModel
from backend.constants.enums import DownloadRequestStatus

class DownloadRequestCreate(BaseModel):
    source_id: int
    start_time: datetime
    end_time: datetime


class DownloadRequestCreateResponse(BaseModel):
    id: int
    source_id: int
    source_name: str
    start_time: datetime
    end_time: datetime
    status: DownloadRequestStatus
    created_at: datetime

class DownloadRequestListItem(BaseModel):
    id: int
    source_id: int
    source_name: str
    start_time: datetime
    end_time: datetime
    status: DownloadRequestStatus
    created_at: datetime


class DownloadRequestDetailResponse(BaseModel):
    id: int
    source_id: int
    source_name: str
    start_time: datetime
    end_time: datetime
    status: DownloadRequestStatus
    failure_reason: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None