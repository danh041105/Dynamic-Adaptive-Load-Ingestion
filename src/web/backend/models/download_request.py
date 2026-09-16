from sqlalchemy import Column, BigInteger, String, DateTime, ForeignKey, text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from backend.config.database import Base
from backend.constants.enums import DownloadRequestStatus

class DownloadRequest(Base):
    __tablename__ = "download_request"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    source_id = Column(BigInteger, ForeignKey("nifi_source.id"), nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    status = Column(
        String,
        nullable=False,
        default=DownloadRequestStatus.PENDING.value,
        server_default=DownloadRequestStatus.PENDING.value
    )
    failure_reason = Column(String(1000), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    user = relationship(
        "User",
        back_populates="download_requests"
    )

    source = relationship(
        "NifiSource",
        back_populates="download_requests"
    )
    
    allocation_history = relationship(
    "AllocationHistory",
    back_populates="request"
    )