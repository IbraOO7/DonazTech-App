from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from datetime import datetime
from databases.config import Base

class Donation(Base):
    __tablename__ = 'donations'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True) 
    user_email = Column(String(120), nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String(50))
    status = Column(String(20), default='pending')
    mayar_link_id = Column(String(100))
    mayar_url = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

class ZakatConsultation(Base):
    __tablename__ = 'zakat_consultations'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    query = Column(Text, nullable=False)
    ai_response = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)