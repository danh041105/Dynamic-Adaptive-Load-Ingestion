from sqlalchemy import Column, BigInteger, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from backend.config.database import Base

class NifiComponent(Base):
    __tablename__ = "nifi_component"

    id = Column(BigInteger, primary_key=True, index=True)
    source_id = Column(BigInteger, ForeignKey("nifi_source.id"), nullable=False)
    component_id = Column(String(100), unique=True, nullable=False)
    component_name = Column(String(255), nullable=False)
    component_type = Column(String(50), nullable=False)
    destination_component_id = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    source = relationship(
        "NifiSource",
        back_populates="components"
    )