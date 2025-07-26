from pydantic import BaseModel, Field, validator, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from enum import Enum
from decimal import Decimal

class RideStatus(str, Enum):
    REQUESTED = "REQUESTED"
    ACCEPTED = "ACCEPTED"
    DRIVER_ARRIVED = "DRIVER_ARRIVED"
    STARTED = "STARTED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    PAYMENT_PENDING = "PAYMENT_PENDING"

class CancellationReason(str, Enum):
    RIDER_CANCELLED = "RIDER_CANCELLED"
    DRIVER_CANCELLED = "DRIVER_CANCELLED"
    NO_DRIVER_AVAILABLE = "NO_DRIVER_AVAILABLE"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    SYSTEM_CANCELLED = "SYSTEM_CANCELLED"

# Location schemas
class LocationBase(BaseModel):
    location_name: str = Field(..., min_length=1, max_length=255)
    latitude: Decimal = Field(..., ge=-90, le=90)
    longitude: Decimal = Field(..., ge=-180, le=180)

class LocationCreate(LocationBase):
    pass

class LocationResponse(LocationBase):
    model_config = ConfigDict(from_attributes=True)

# Ride request schemas
class RideRequestCreate(BaseModel):
    pickup_location: str = Field(..., min_length=1, max_length=255)
    pickup_latitude: Decimal = Field(..., ge=-90, le=90)
    pickup_longitude: Decimal = Field(..., ge=-180, le=180)
    drop_location: str = Field(..., min_length=1, max_length=255)
    drop_latitude: Decimal = Field(..., ge=-90, le=90)
    drop_longitude: Decimal = Field(..., ge=-180, le=180)
    max_wait_time: Optional[int] = Field(10, ge=1, le=60, description="Maximum wait time in minutes")
    special_requirements: Optional[str] = Field(None, max_length=500)
    
    @validator('pickup_location', 'drop_location')
    def validate_locations_different(cls, v, values):
        if 'pickup_location' in values and v == values['pickup_location']:
            raise ValueError('Pickup and drop locations cannot be the same')
        return v

class RideRequestResponse(BaseModel):
    id: UUID
    rider_id: UUID
    pickup_location: str
    pickup_latitude: Decimal
    pickup_longitude: Decimal
    drop_location: str
    drop_latitude: Decimal
    drop_longitude: Decimal
    estimated_fare: Optional[Decimal]
    estimated_distance: Optional[Decimal]
    estimated_duration: Optional[int]
    max_wait_time: int
    special_requirements: Optional[str]
    expires_at: datetime
    is_active: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Driver offer schemas
class DriverOfferCreate(BaseModel):
    ride_request_id: UUID
    offered_fare: Optional[Decimal] = Field(None, ge=0)
    estimated_arrival_time: int = Field(..., ge=1, le=60, description="ETA in minutes")
    message: Optional[str] = Field(None, max_length=200)

class DriverOfferResponse(BaseModel):
    id: UUID
    ride_request_id: UUID
    driver_id: UUID
    offered_fare: Optional[Decimal]
    estimated_arrival_time: int
    message: Optional[str]
    expires_at: datetime
    is_active: bool
    is_accepted: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Ride schemas
class RideCreate(BaseModel):
    ride_request_id: UUID
    driver_offer_id: UUID

class RideUpdate(BaseModel):
    status: Optional[RideStatus] = None
    driver_id: Optional[UUID] = None
    fare_amount: Optional[Decimal] = Field(None, ge=0)
    distance_km: Optional[Decimal] = Field(None, ge=0)
    duration_minutes: Optional[int] = Field(None, ge=0)

class RideCancel(BaseModel):
    cancellation_reason: CancellationReason
    cancellation_details: Optional[str] = Field(None, max_length=500)

class RideRating(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    feedback: Optional[str] = Field(None, max_length=500)

class RideResponse(BaseModel):
    id: UUID
    rider_id: UUID
    driver_id: Optional[UUID]
    pickup_location: str
    pickup_latitude: Optional[Decimal]
    pickup_longitude: Optional[Decimal]
    drop_location: str
    drop_latitude: Optional[Decimal]
    drop_longitude: Optional[Decimal]
    status: RideStatus
    fare_amount: Optional[Decimal]
    base_fare: Optional[Decimal]
    distance_km: Optional[Decimal]
    duration_minutes: Optional[int]
    estimated_fare: Optional[Decimal]
    requested_at: datetime
    accepted_at: Optional[datetime]
    driver_arrived_at: Optional[datetime]
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    cancellation_reason: Optional[CancellationReason]
    cancellation_details: Optional[str]
    rider_rating: Optional[int]
    driver_rating: Optional[int]
    rider_feedback: Optional[str]
    driver_feedback: Optional[str]
    is_emergency: bool
    special_instructions: Optional[str]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Ride tracking schemas
class RideTrackingCreate(BaseModel):
    latitude: Decimal = Field(..., ge=-90, le=90)
    longitude: Decimal = Field(..., ge=-180, le=180)
    speed_kmh: Optional[Decimal] = Field(None, ge=0, le=200)
    heading: Optional[Decimal] = Field(None, ge=0, le=360)
    accuracy_meters: Optional[int] = Field(None, ge=1)

class RideTrackingResponse(BaseModel):
    id: UUID
    ride_id: UUID
    driver_id: UUID
    latitude: Decimal
    longitude: Decimal
    speed_kmh: Optional[Decimal]
    heading: Optional[Decimal]
    accuracy_meters: Optional[int]
    recorded_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Status history schemas
class RideStatusHistoryResponse(BaseModel):
    id: UUID
    ride_id: UUID
    previous_status: Optional[str]
    new_status: str
    changed_by: Optional[UUID]
    changed_at: datetime
    notes: Optional[str]
    location_at_change: Optional[str]
    
    model_config = ConfigDict(from_attributes=True)

# Search and filter schemas
class RideSearchFilters(BaseModel):
    rider_id: Optional[UUID] = None
    driver_id: Optional[UUID] = None
    status: Optional[RideStatus] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    min_fare: Optional[Decimal] = None
    max_fare: Optional[Decimal] = None

class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    size: int = Field(10, ge=1, le=100)

class PaginatedRidesResponse(BaseModel):
    items: List[RideResponse]
    total: int
    page: int
    size: int
    pages: int

# Fare calculation schemas
class FareCalculationRequest(BaseModel):
    pickup_latitude: Decimal = Field(..., ge=-90, le=90)
    pickup_longitude: Decimal = Field(..., ge=-180, le=180)
    drop_latitude: Decimal = Field(..., ge=-90, le=90)
    drop_longitude: Decimal = Field(..., ge=-180, le=180)
    time_of_day: Optional[datetime] = None

class FareCalculationResponse(BaseModel):
    estimated_fare: Decimal
    base_fare: Decimal
    distance_km: Decimal
    estimated_duration: int
    surge_multiplier: Decimal
    breakdown: dict

# Nearby drivers schema
class NearbyDriversRequest(BaseModel):
    latitude: Decimal = Field(..., ge=-90, le=90)
    longitude: Decimal = Field(..., ge=-180, le=180)
    radius_km: Decimal = Field(5.0, ge=0.1, le=50)

class DriverLocationResponse(BaseModel):
    driver_id: UUID
    current_latitude: Decimal
    current_longitude: Decimal
    distance_km: Decimal
    is_available: bool
    rating: Decimal
    total_rides: int

# Response schemas
class MessageResponse(BaseModel):
    message: str
    success: bool = True

class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None 