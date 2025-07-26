from sqlalchemy import Column, String, ForeignKey, DECIMAL, Integer, DateTime, Text, Enum as SQLEnum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
import sys
import os

# Add the shared directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../'))
from shared.database_config import Base

class RideStatus(str, enum.Enum):
    REQUESTED = "REQUESTED"
    ACCEPTED = "ACCEPTED"
    DRIVER_ARRIVED = "DRIVER_ARRIVED"
    STARTED = "STARTED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    PAYMENT_PENDING = "PAYMENT_PENDING"

class CancellationReason(str, enum.Enum):
    RIDER_CANCELLED = "RIDER_CANCELLED"
    DRIVER_CANCELLED = "DRIVER_CANCELLED"
    NO_DRIVER_AVAILABLE = "NO_DRIVER_AVAILABLE"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    SYSTEM_CANCELLED = "SYSTEM_CANCELLED"

class Ride(Base):
    __tablename__ = "rides"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rider_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    driver_id = Column(UUID(as_uuid=True), index=True)
    pickup_location = Column(String(255), nullable=False)
    pickup_latitude = Column(DECIMAL(10, 8))
    pickup_longitude = Column(DECIMAL(11, 8))
    drop_location = Column(String(255), nullable=False)
    drop_latitude = Column(DECIMAL(10, 8))
    drop_longitude = Column(DECIMAL(11, 8))
    status = Column(SQLEnum(RideStatus), nullable=False, default=RideStatus.REQUESTED, index=True)
    fare_amount = Column(DECIMAL(10, 2))
    base_fare = Column(DECIMAL(10, 2))
    distance_km = Column(DECIMAL(10, 2))
    duration_minutes = Column(Integer)
    estimated_fare = Column(DECIMAL(10, 2))
    requested_at = Column(DateTime, default=datetime.utcnow, index=True)
    accepted_at = Column(DateTime)
    driver_arrived_at = Column(DateTime)
    started_at = Column(DateTime)
    ended_at = Column(DateTime)
    cancelled_at = Column(DateTime)
    cancellation_reason = Column(SQLEnum(CancellationReason))
    cancellation_details = Column(Text)
    rider_rating = Column(Integer)  # 1-5
    driver_rating = Column(Integer)  # 1-5
    rider_feedback = Column(Text)
    driver_feedback = Column(Text)
    is_emergency = Column(Boolean, default=False)
    special_instructions = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    status_history = relationship("RideStatusHistory", back_populates="ride", cascade="all, delete-orphan")
    ride_tracking = relationship("RideTracking", back_populates="ride", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Ride(id={self.id}, status='{self.status}', rider={self.rider_id})>"

class RideStatusHistory(Base):
    __tablename__ = "ride_status_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ride_id = Column(UUID(as_uuid=True), ForeignKey("rides.id", ondelete="CASCADE"), nullable=False)
    previous_status = Column(String(50))
    new_status = Column(String(50), nullable=False)
    changed_by = Column(UUID(as_uuid=True))  # User who triggered the change
    changed_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text)
    location_at_change = Column(String(255))
    latitude_at_change = Column(DECIMAL(10, 8))
    longitude_at_change = Column(DECIMAL(11, 8))
    
    # Relationships
    ride = relationship("Ride", back_populates="status_history")
    
    def __repr__(self):
        return f"<RideStatusHistory(ride={self.ride_id}, {self.previous_status}->{self.new_status})>"

class RideTracking(Base):
    __tablename__ = "ride_tracking"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ride_id = Column(UUID(as_uuid=True), ForeignKey("rides.id", ondelete="CASCADE"), nullable=False)
    driver_id = Column(UUID(as_uuid=True), nullable=False)
    latitude = Column(DECIMAL(10, 8), nullable=False)
    longitude = Column(DECIMAL(11, 8), nullable=False)
    speed_kmh = Column(DECIMAL(5, 2))
    heading = Column(DECIMAL(5, 2))  # Compass direction
    accuracy_meters = Column(Integer)
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    ride = relationship("Ride", back_populates="ride_tracking")
    
    def __repr__(self):
        return f"<RideTracking(ride={self.ride_id}, lat={self.latitude}, lng={self.longitude})>"

class RideRequest(Base):
    __tablename__ = "ride_requests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rider_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    pickup_location = Column(String(255), nullable=False)
    pickup_latitude = Column(DECIMAL(10, 8), nullable=False)
    pickup_longitude = Column(DECIMAL(11, 8), nullable=False)
    drop_location = Column(String(255), nullable=False)
    drop_latitude = Column(DECIMAL(10, 8), nullable=False)
    drop_longitude = Column(DECIMAL(11, 8), nullable=False)
    estimated_fare = Column(DECIMAL(10, 2))
    estimated_distance = Column(DECIMAL(10, 2))
    estimated_duration = Column(Integer)
    max_wait_time = Column(Integer, default=10)  # minutes
    special_requirements = Column(Text)
    expires_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<RideRequest(id={self.id}, rider={self.rider_id}, active={self.is_active})>"

class DriverRideOffer(Base):
    __tablename__ = "driver_ride_offers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ride_request_id = Column(UUID(as_uuid=True), ForeignKey("ride_requests.id", ondelete="CASCADE"), nullable=False)
    driver_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    offered_fare = Column(DECIMAL(10, 2))
    estimated_arrival_time = Column(Integer)  # minutes
    message = Column(Text)
    expires_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    is_accepted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<DriverRideOffer(request={self.ride_request_id}, driver={self.driver_id})>" 