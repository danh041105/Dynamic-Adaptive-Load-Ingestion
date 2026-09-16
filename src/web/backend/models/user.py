from sqlalchemy import Column, BigInteger, String, DateTime
from sqlalchemy.sql import func
from backend.config.database import Base
from backend.constants.enums import UserRole
from sqlalchemy.orm import relationship
class User(Base):
    __tablename__ = "users"

    id = Column("user_id", BigInteger, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default=UserRole.DATA_ENGINEER.value)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    download_requests = relationship(
        "DownloadRequest",
        back_populates="user"
    )