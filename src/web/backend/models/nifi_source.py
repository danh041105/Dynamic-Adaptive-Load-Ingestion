from sqlalchemy import Column, BigInteger, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from backend.config.database import Base

class NifiSource(Base):
    __tablename__ = "nifi_source"

    id = Column(BigInteger, primary_key=True, index=True)
    external_source_id = Column("source_id", String(100), unique=True, nullable=False)
    name = Column("source_name", String(255), nullable=False)
    process_group_id = Column(BigInteger, ForeignKey("nifi_process_group.id"), nullable=False)
    vendor = Column(String(100), nullable=True)
    remote_path = Column(String(1000), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    process_group = relationship(
        "NifiProcessGroup",
        back_populates="sources"
    )
    
    components = relationship(
        "NifiComponent",
        back_populates="source"
    )

    download_requests = relationship(
        "DownloadRequest",
        back_populates="source"
    )

    metric_history = relationship(
        "MetricHistory",
        back_populates="source"
    )

    allocation_history = relationship(
        "AllocationHistory",
        back_populates="source"
    )