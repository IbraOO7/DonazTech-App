from sqlalchemy import Column, Integer, String, Text, Float, Index
from databases.config import Base

class Charity(Base):
    __tablename__ = "charities"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    location_name = Column(String(255), nullable=True) 
    lat = Column(Float, nullable=False)                
    lng = Column(Float, nullable=False)                
    category = Column(String(50), index=True)          
    mayar_payment_link = Column(String(255), nullable=True)
    __table_args__ = (
        Index('idx_charity_location', 'lat', 'lng'),
    )

    def __repr__(self):
        return f"<Charity(name='{self.name}', lat={self.lat}, lng={self.lng})>"