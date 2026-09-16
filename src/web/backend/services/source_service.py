from datetime import datetime, timedelta, timezone
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session, joinedload
from backend.config.metric_config import METRIC_STALE_MINUTES
from backend.models.nifi_source import NifiSource
from backend.models.nifi_process_group import NifiProcessGroup
from backend.models.metric_history import MetricHistory
from backend.schemas.source_schemas import (
    SourceAvailability,
    SourceAvailabilityResponse,
    SourceDetailResponse,
    SourceListItem,
    SourceLoadLevel,
)

class SourceService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_sources(
        self,
        q: str | None = None,
        vendor: str | None = None,
        location: str | None = None,
        availability: SourceAvailability | None = None,
    ) -> list[SourceListItem]:

        query = (self.db.query(NifiSource)
                    .options(
                    joinedload(NifiSource.process_group)
                    .joinedload(NifiProcessGroup.parent)
                    .joinedload(NifiProcessGroup.parent)
                    )
                )

        # Search theo tên source: ENM01, ENM02, ...
        if q:
            search = f"%{q.strip()}%"
            query = query.filter(NifiSource.name.ilike(search))

        if vendor:
            query = query.filter(NifiSource.vendor == vendor.strip().lower())

        sources = query.order_by(NifiSource.name).all()

        if not sources:
            return []

        source_ids = [source.id for source in sources]
        latest_metrics = self.get_latest_metric(source_ids=source_ids)

        result = []

        for source in sources:
            metric = latest_metrics.get(source.id)
            item = self._build_list_item(source=source, metric=metric)
            if location is not None and item.location != location.strip(): continue
            if availability is not None and item.availability != availability: continue
            result.append(item)

        return result

    def get_source_by_id(self, source_id: int) -> NifiSource | None:
        return (self.db.query(NifiSource)
                .options(
                joinedload(NifiSource.process_group)
                .joinedload(NifiProcessGroup.parent)
                .joinedload(NifiProcessGroup.parent)
                )
                .filter(NifiSource.id == source_id)
            ).first()

    def get_latest_metric(self, source_ids: list[int] | None = None) -> dict[int, MetricHistory]:
        """
        Lấy metric mới nhất của nhiều source bằng một query.
        Không query metric riêng cho từng source,
        tránh lỗi N+1.
        """
        if source_ids is not None and not source_ids:
            return {}

        latest_subquery = (
            self.db
            .query(
                MetricHistory.source_id.label("source_id"),
                func.max(MetricHistory.recorded_at).label("latest_recorded_at")
            )
        )

        if source_ids is not None:
            latest_subquery = latest_subquery.filter(MetricHistory.source_id.in_(source_ids))

        latest_subquery = latest_subquery.group_by(MetricHistory.source_id).subquery()

        metrics = (
            self.db
            .query(MetricHistory)
            .join(
                latest_subquery,
                and_(
                    MetricHistory.source_id == latest_subquery.c.source_id,
                    MetricHistory.recorded_at == latest_subquery.c.latest_recorded_at
                )
            )
            .all()
        )

        return {
            metric.source_id: metric
            for metric in metrics
        }

    def calculate_availability(self, source: NifiSource, metric: MetricHistory | None) -> SourceAvailability:

        # Chưa có metric
        if metric is None:
            return SourceAvailability.UNAVAILABLE
        
        recorded_at = metric.recorded_at
        if recorded_at is None:
            return SourceAvailability.UNAVAILABLE

        # Phòng trường hợp datetime từ DB là naive
        if recorded_at.tzinfo is None:
            recorded_at = recorded_at.replace(tzinfo=timezone.utc)

        stale_before = datetime.now(timezone.utc) - timedelta(minutes=METRIC_STALE_MINUTES)
        
        if recorded_at < stale_before:
            return SourceAvailability.UNAVAILABLE

        return SourceAvailability.AVAILABLE

    def calculate_load_level(self, metric: MetricHistory | None) -> SourceLoadLevel:
        """
        Giai đoạn 3 chưa tự phân tích LOW/HIGH.

        Load thực tế cần được đánh giá từ chuỗi metric
        và thuộc trách nhiệm của module Optimizer.
        """
        return SourceLoadLevel.UNKNOWN

    def get_source_detail(self, source_id: int) -> SourceDetailResponse | None:
    
            source = self.get_source_by_id(source_id)
            if source is None: return None
            
            metrics = self.get_latest_metric(source_ids=[source.id])
            metric = metrics.get(source.id)
            availability = self.calculate_availability(source=source, metric=metric)
    
            load_level = self.calculate_load_level(metric=metric)
    
            accepting_requests = (availability
                == SourceAvailability.AVAILABLE
                # and load_level
                # == SourceLoadLevel.LOW
            )
    
            return SourceDetailResponse(
                id=source.id,
                source_name=source.name,
                vendor=source.vendor,
                location=self._get_location(source),
                availability=availability,
                load_level=load_level,
                accepting_requests=accepting_requests,
                last_metric_at=(
                    metric.recorded_at
                    if metric
                    else None
                )
            )
    
    def get_source_availability(self, source_id: int) -> SourceAvailabilityResponse | None:

        source = self.get_source_by_id(source_id)
        if source is None:
            return None

        metrics = self.get_latest_metric(source_ids=[source.id])
        metric = metrics.get(source.id)
        availability = self.calculate_availability(source=source, metric=metric)
        load_level = self.calculate_load_level(metric=metric)

        accepting_requests = (
            availability
            == SourceAvailability.AVAILABLE
            # and load_level
            # == SourceLoadLevel.LOW
        )

        return SourceAvailabilityResponse(
            id=source.id,
            source_name=source.name,
            availability=availability,
            load_level=load_level,
            accepting_requests=accepting_requests,
            last_metric_at=(
                metric.recorded_at
                if metric
                else None
            )
        )

    def _build_list_item(self, source: NifiSource, metric: MetricHistory | None) -> SourceListItem:

        availability = self.calculate_availability(source=source, metric=metric)
        load_level = self.calculate_load_level(metric=metric)

        accepting_requests = (
            availability
            == SourceAvailability.AVAILABLE
            # and load_level
            # == SourceLoadLevel.LOW
        )

        return SourceListItem(
            id=source.id,
            source_name=source.name,
            vendor=source.vendor,
            location=self._get_location(source),
            availability=availability,
            load_level=load_level,
            accepting_requests=accepting_requests,
            last_metric_at=(
                metric.recorded_at
                if metric
                else None
            )
        )


    def _get_location(self, source: NifiSource)-> str | None:
        process_group = source.process_group
        # Celltrace 4G HNI/celltrace ENM/ENM01
        # ENM01 không có process group
        if process_group is None:
            return None

        # ENM01 -> celltrace ENM
        parent_group = process_group.parent
        if parent_group is None:
            return None

        # celltrace ENM -> Celltrace 4G HNI
        location_group = parent_group.parent
        if location_group is None:
            return None

        group_name = location_group.group_name.strip().split()
        if not group_name: return None
        
        return group_name[-1]
