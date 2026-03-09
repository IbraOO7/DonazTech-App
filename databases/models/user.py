from sqlalchemy import Integer, String, Column, Boolean, Enum, DateTime
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from databases.config import Base

class UserStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVATE = "INACTIVATE"

class UserLevel(enum.Enum):
    STAFF= "STAFF"
    SUPERUSER= "SUPERUSER"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(80), nullable=False)
    email = Column(String, nullable=False)
    password = Column(String(100), nullable=False)
    is_staff = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE)
    level = Column(Enum(UserLevel), default=UserLevel.STAFF)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    update_at = Column(DateTime, onupdate=datetime.utcnow)
    donations = relationship("Donation", backref="admin_user", lazy="dynamic")
    consultations = relationship("ZakatConsultation", backref="admin_user", lazy="dynamic")