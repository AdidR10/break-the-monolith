from sqlalchemy import Column, String, Boolean, DateTime, DECIMAL, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import sys
import os

# Add the shared directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../'))
from shared.database_config import Base

class CampusLocation(Base):
    __tablename__ = "campus_locations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_name = Column(String(255), unique=True, nullable=False, index=True)
    zone = Column(String(50), nullable=False)
    latitude = Column(DECIMAL(10, 8), nullable=False)
    longitude = Column(DECIMAL(11, 8), nullable=False)
    description = Column(Text)
    is_pickup_point = Column(Boolean, default=True)
    is_drop_point = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    popularity_score = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<CampusLocation(name='{self.location_name}', zone='{self.zone}')>" 