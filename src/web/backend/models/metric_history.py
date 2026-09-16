from sqlalchemy import Column, Integer, BigInteger, DOUBLE, DateTime, ForeignKey

from sqlalchemy.orm import relationship

from backend.config.database import Base


class MetricHistory(Base):
    __tablename__ = "metric_history"

    source_id = Column(BigInteger, ForeignKey("nifi_source.id"), primary_key=True, nullable=False)
    recorded_at = Column(DateTime(timezone=True), primary_key=True, nullable=False)
    queued_count = Column(BigInteger, nullable=True)
    queue_bytes = Column(BigInteger, nullable=True)
    input_files = Column(DOUBLE, nullable=True)
    avg_input_bytes = Column(DOUBLE, nullable=True)
    processed_files = Column(DOUBLE, nullable=True)
    processed_bytes = Column(DOUBLE, nullable=True)
    concurrent_tasks = Column(Integer, nullable=True)

    source = relationship(
        "NifiSource",
        back_populates="metric_history"
    )