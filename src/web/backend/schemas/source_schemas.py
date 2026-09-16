from datetime import datetime
from pydantic import BaseModel
from backend.constants.enums import SourceAvailability, SourceLoadLevel

class SourceListItem(BaseModel):
    id: int
    source_name: str
    vendor: str | None = None
    location: str # Ví dụ Celltrace HNI
    availability: SourceAvailability
    load_level: SourceLoadLevel
    accepting_requests: bool
    last_metric_at: datetime | None = None
    
class SourceDetailResponse(SourceListItem):
    pass

class SourceAvailabilityResponse(BaseModel):
    id: int
    source_name: str
    availability: SourceAvailability
    load_level: SourceLoadLevel
    accepting_requests: bool
    last_metric_at: datetime | None