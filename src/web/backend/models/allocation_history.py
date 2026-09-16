from sqlalchemy import Column, Integer, DOUBLE, BigInteger, ForeignKey, DateTime, String
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from backend.config.database import Base

class AllocationHistory(Base):
    __tablename__ = "allocation_history"

    id = Column(BigInteger, primary_key=True, index=True)
    source_id = Column(BigInteger, ForeignKey("nifi_source.id"), nullable=False)
    request_id = Column(BigInteger,ForeignKey("download_request.id"),nullable=True)
    old_concurrent_tasks = Column(Integer, nullable=False)
    new_concurrent_tasks = Column(Integer, nullable=False)
    reason = Column(String, nullable=True)
    queued_count = Column(BigInteger, nullable=True)
    queue_bytes = Column(BigInteger, nullable=True)
    input_files = Column(DOUBLE, nullable=True)
    avg_input_bytes = Column(DOUBLE, nullable=True)
    processed_files = Column(DOUBLE, nullable=True)
    processed_bytes = Column(DOUBLE, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    source = relationship(
        "NifiSource",
        back_populates="allocation_history"
    )
    request = relationship(
        "DownloadRequest",
        back_populates="allocation_history"
        )