from sqlalchemy import Column, BigInteger, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.config.database import Base

class NifiProcessGroup(Base):
    __tablename__ = "nifi_process_group"

    id = Column(BigInteger, primary_key=True, index=True)
    group_id = Column(String(100), unique=True, nullable=False)
    group_name = Column(String(255), nullable=False)
    parent_id = Column(BigInteger, ForeignKey("nifi_process_group.id"), nullable=True)
    level = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Process Group cha
    parent = relationship(
        "NifiProcessGroup",
        remote_side=[id],
        back_populates="children"
    )

    # Các Process Group con
    children = relationship(
        "NifiProcessGroup",
        back_populates="parent"
    )

    # Các source thuộc Process Group này
    sources = relationship(
        "NifiSource",
        back_populates="process_group"
    )