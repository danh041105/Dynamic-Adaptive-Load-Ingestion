from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from backend.constants.enums import SourceAvailability
from backend.services.source_service import SourceService

class SourceController:
    @staticmethod
    def list_sources_controller(
        db: Session,
        q: str | None = None,
        vendor: str | None = None,
        location: str | None = None,
        availability: SourceAvailability | None = None,
    ):
        service = SourceService(db)

        return service.list_sources(
            q=q,
            vendor=vendor,
            location=location,
            availability=availability
        )

    @staticmethod
    def get_source_controller(source_id: int, db: Session):
        service = SourceService(db)
        source = service.get_source_detail(source_id=source_id)

        if source is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source không tồn tại")
        return source

    @staticmethod
    def get_availability_controller(source_id: int, db: Session):
        service = SourceService(db)
        result = service.get_source_availability(source_id=source_id)

        if result is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source không tồn tại")
        return result