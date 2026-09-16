from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.config.database import get_db
from backend.constants.enums import UserRole, SourceAvailability
from backend.controllers.source_controller import SourceController
from backend.dependencies.auth_dependencies import require_roles
from backend.schemas.source_schemas import (
    SourceAvailabilityResponse,
    SourceDetailResponse,
    SourceListItem,
)

router = APIRouter(
    prefix="/radio-frequency-engineer/sources",
    tags=["Radio Frequency Engineer"],
    dependencies=[Depends(require_roles(UserRole.RADIO_FREQUENCY_ENGINEER))]
)

@router.get("", response_model=list[SourceListItem])
def list_sources(
    q: str | None = Query(default=None),
    vendor: str | None = Query(default=None),
    location: str | None = Query(default=None),
    availability: SourceAvailability | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return SourceController.list_sources_controller(
        db=db,
        q=q,
        location=location,
        vendor=vendor,
        availability=availability,
    )

@router.get("/{source_id}", response_model=SourceDetailResponse)
def get_source(source_id: int, db: Session = Depends(get_db)):

    return SourceController.get_source_controller(source_id=source_id, db=db)


@router.get("/{source_id}/availability", response_model=SourceAvailabilityResponse)
def get_source_availability(source_id: int, db: Session = Depends(get_db)):

    return SourceController.get_availability_controller(source_id=source_id, db=db)