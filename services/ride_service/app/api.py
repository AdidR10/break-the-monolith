from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
import httpx
import logging
import sys
import os

# Add the shared directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../'))
from shared.database_config import get_db
from shared.rabbitmq_config import rabbitmq

from . import schemas, crud, models

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()
security = HTTPBearer()

# User service client
user_service_client = crud.UserServiceClient()

# Dependencies
async def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Get current user from token by calling user service"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://user-service:8000/api/v1/users/me",
                headers={"Authorization": f"Bearer {credentials.credentials}"}
            )
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )
    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="User service unavailable"
        )

def require_student_user(current_user: dict = Depends(get_current_user_from_token)):
    """Require student user"""
    if current_user.get("user_type") != "STUDENT":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student access required"
        )
    return current_user

def require_driver_user(current_user: dict = Depends(get_current_user_from_token)):
    """Require rickshaw puller user"""
    if current_user.get("user_type") != "RICKSHAW_PULLER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Rickshaw puller access required"
        )
    return current_user

# Background tasks
async def notify_ride_status_change(ride_id: str, status: str, rider_id: str, driver_id: str = None):
    """Send notification about ride status change"""
    try:
        message = {
            "ride_id": ride_id,
            "status": status,
            "rider_id": rider_id,
            "driver_id": driver_id,
            "timestamp": str(models.datetime.utcnow())
        }
        rabbitmq.publish_message("rides", f"ride.{status.lower()}", message)
    except Exception as e:
        logger.error(f"Failed to send ride notification: {e}")

# Fare calculation endpoint
@router.post("/fare/calculate", response_model=schemas.FareCalculationResponse)
async def calculate_fare(request: schemas.FareCalculationRequest):
    """Calculate fare for a trip"""
    distance_km = crud.FareCalculator.calculate_distance(
        float(request.pickup_latitude), float(request.pickup_longitude),
        float(request.drop_latitude), float(request.drop_longitude)
    )
    
    duration_minutes = crud.FareCalculator.estimate_duration(distance_km)
    fare_calculation = crud.FareCalculator.calculate_fare(
        distance_km, duration_minutes, request.time_of_day
    )
    
    return {
        "estimated_fare": fare_calculation["total_fare"],
        "base_fare": fare_calculation["base_fare"],
        "distance_km": distance_km,
        "estimated_duration": duration_minutes,
        "surge_multiplier": fare_calculation["surge_multiplier"],
        "breakdown": fare_calculation["breakdown"]
    }

# Nearby drivers endpoint
@router.post("/drivers/nearby", response_model=List[schemas.DriverLocationResponse])
async def get_nearby_drivers(request: schemas.NearbyDriversRequest):
    """Get nearby available drivers"""
    drivers = await user_service_client.get_nearby_drivers(
        float(request.latitude), float(request.longitude), float(request.radius_km)
    )
    
    return [
        {
            "driver_id": driver["user_id"],
            "current_latitude": driver["current_latitude"],
            "current_longitude": driver["current_longitude"],
            "distance_km": driver["distance_km"],
            "is_available": driver["is_available"],
            "rating": driver["rating"],
            "total_rides": driver["total_rides"]
        }
        for driver in drivers
    ]

# Ride request endpoints (Student only)
@router.post("/requests", response_model=schemas.RideRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_ride_request(
    request: schemas.RideRequestCreate,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_student_user),
    db: Session = Depends(get_db)
):
    """Create a new ride request"""
    try:
        db_request = crud.RideRequestCRUD.create_ride_request(
            db, request, UUID(current_user["id"])
        )
        
        # Notify nearby drivers
        background_tasks.add_task(
            notify_ride_status_change, 
            str(db_request.id), 
            "REQUESTED", 
            str(current_user["id"])
        )
        
        return db_request
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/requests/active", response_model=List[schemas.RideRequestResponse])
async def get_active_ride_requests(
    limit: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(require_driver_user),
    db: Session = Depends(get_db)
):
    """Get active ride requests (Driver only)"""
    requests = crud.RideRequestCRUD.get_active_ride_requests(db, limit)
    return requests

@router.get("/requests/{request_id}", response_model=schemas.RideRequestResponse)
async def get_ride_request(
    request_id: UUID,
    current_user: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Get ride request by ID"""
    request = crud.RideRequestCRUD.get_ride_request_by_id(db, request_id)
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ride request not found"
        )
    
    # Check authorization
    if (current_user["user_type"] == "STUDENT" and 
        str(request.rider_id) != current_user["id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return request

# Driver offer endpoints (Driver only)
@router.post("/offers", response_model=schemas.DriverOfferResponse, status_code=status.HTTP_201_CREATED)
async def create_driver_offer(
    offer: schemas.DriverOfferCreate,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_driver_user),
    db: Session = Depends(get_db)
):
    """Create driver offer for ride request"""
    try:
        db_offer = crud.DriverOfferCRUD.create_driver_offer(
            db, offer, UUID(current_user["id"])
        )
        
        # Get ride request to notify rider
        ride_request = crud.RideRequestCRUD.get_ride_request_by_id(db, offer.ride_request_id)
        if ride_request:
            background_tasks.add_task(
                notify_ride_status_change,
                str(offer.ride_request_id),
                "OFFER_RECEIVED",
                str(ride_request.rider_id),
                current_user["id"]
            )
        
        return db_offer
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/requests/{request_id}/offers", response_model=List[schemas.DriverOfferResponse])
async def get_offers_for_request(
    request_id: UUID,
    current_user: dict = Depends(require_student_user),
    db: Session = Depends(get_db)
):
    """Get all offers for a ride request (Student only)"""
    # Verify student owns the request
    request = crud.RideRequestCRUD.get_ride_request_by_id(db, request_id)
    if not request or str(request.rider_id) != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ride request not found"
        )
    
    offers = crud.DriverOfferCRUD.get_offers_for_request(db, request_id)
    return offers

@router.post("/offers/{offer_id}/accept", response_model=schemas.RideResponse)
async def accept_driver_offer(
    offer_id: UUID,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_student_user),
    db: Session = Depends(get_db)
):
    """Accept driver offer and create ride"""
    try:
        accepted_offer = crud.DriverOfferCRUD.accept_offer(
            db, offer_id, UUID(current_user["id"])
        )
        
        # Create ride from accepted offer
        ride = crud.RideCRUD.create_ride_from_accepted_offer(db, accepted_offer)
        
        # Notify driver
        background_tasks.add_task(
            notify_ride_status_change,
            str(ride.id),
            "ACCEPTED",
            current_user["id"],
            str(accepted_offer.driver_id)
        )
        
        return ride
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# Ride management endpoints
@router.get("/rides/my", response_model=schemas.PaginatedRidesResponse)
async def get_my_rides(
    status: Optional[schemas.RideStatus] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Get current user's rides"""
    filters = schemas.RideSearchFilters(
        status=status,
        date_from=models.datetime.fromisoformat(date_from) if date_from else None,
        date_to=models.datetime.fromisoformat(date_to) if date_to else None
    )
    pagination = schemas.PaginationParams(page=page, size=size)
    
    result = crud.RideCRUD.get_user_rides(
        db, UUID(current_user["id"]), current_user["user_type"], filters, pagination
    )
    return result

@router.get("/rides/{ride_id}", response_model=schemas.RideResponse)
async def get_ride(
    ride_id: UUID,
    current_user: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Get ride by ID"""
    ride = crud.RideCRUD.get_ride_by_id(db, ride_id)
    if not ride:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ride not found"
        )
    
    # Check authorization
    user_id = UUID(current_user["id"])
    if ride.rider_id != user_id and ride.driver_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return ride

@router.put("/rides/{ride_id}/status", response_model=schemas.RideResponse)
async def update_ride_status(
    ride_id: UUID,
    status_update: schemas.RideUpdate,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Update ride status"""
    ride = crud.RideCRUD.get_ride_by_id(db, ride_id)
    if not ride:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ride not found"
        )
    
    # Check authorization
    user_id = UUID(current_user["id"])
    if ride.rider_id != user_id and ride.driver_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    if status_update.status:
        try:
            updated_ride = crud.RideCRUD.update_ride_status(
                db, ride_id, status_update.status, user_id
            )
            
            # Notify about status change
            background_tasks.add_task(
                notify_ride_status_change,
                str(ride_id),
                status_update.status.value,
                str(ride.rider_id),
                str(ride.driver_id) if ride.driver_id else None
            )
            
            return updated_ride
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    
    return ride

@router.post("/rides/{ride_id}/cancel", response_model=schemas.RideResponse)
async def cancel_ride(
    ride_id: UUID,
    cancel_request: schemas.RideCancel,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Cancel a ride"""
    ride = crud.RideCRUD.get_ride_by_id(db, ride_id)
    if not ride:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ride not found"
        )
    
    # Check authorization
    user_id = UUID(current_user["id"])
    if ride.rider_id != user_id and ride.driver_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    if ride.status in [models.RideStatus.COMPLETED, models.RideStatus.CANCELLED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel completed or already cancelled ride"
        )
    
    try:
        # Update ride with cancellation details
        ride.cancellation_reason = cancel_request.cancellation_reason
        ride.cancellation_details = cancel_request.cancellation_details
        
        updated_ride = crud.RideCRUD.update_ride_status(
            db, ride_id, models.RideStatus.CANCELLED, user_id, 
            cancel_request.cancellation_details
        )
        
        # Notify about cancellation
        background_tasks.add_task(
            notify_ride_status_change,
            str(ride_id),
            "CANCELLED",
            str(ride.rider_id),
            str(ride.driver_id) if ride.driver_id else None
        )
        
        return updated_ride
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# Ride tracking endpoints (Driver only)
@router.post("/rides/{ride_id}/tracking", response_model=schemas.RideTrackingResponse)
async def add_ride_tracking(
    ride_id: UUID,
    tracking: schemas.RideTrackingCreate,
    current_user: dict = Depends(require_driver_user),
    db: Session = Depends(get_db)
):
    """Add tracking point for ride"""
    ride = crud.RideCRUD.get_ride_by_id(db, ride_id)
    if not ride:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ride not found"
        )
    
    if str(ride.driver_id) != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    tracking_point = crud.RideCRUD.add_ride_tracking(
        db, ride_id, tracking, UUID(current_user["id"])
    )
    return tracking_point

@router.get("/rides/{ride_id}/tracking", response_model=List[schemas.RideTrackingResponse])
async def get_ride_tracking(
    ride_id: UUID,
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Get tracking history for ride"""
    ride = crud.RideCRUD.get_ride_by_id(db, ride_id)
    if not ride:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ride not found"
        )
    
    # Check authorization
    user_id = UUID(current_user["id"])
    if ride.rider_id != user_id and ride.driver_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    tracking_points = db.query(models.RideTracking).filter(
        models.RideTracking.ride_id == ride_id
    ).order_by(models.RideTracking.recorded_at.desc()).limit(limit).all()
    
    return tracking_points

# Rating endpoints
@router.post("/rides/{ride_id}/rate", response_model=schemas.MessageResponse)
async def rate_ride(
    ride_id: UUID,
    rating: schemas.RideRating,
    current_user: dict = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """Rate a completed ride"""
    ride = crud.RideCRUD.get_ride_by_id(db, ride_id)
    if not ride:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ride not found"
        )
    
    if ride.status != models.RideStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only rate completed rides"
        )
    
    user_id = UUID(current_user["id"])
    
    if ride.rider_id == user_id:
        if ride.rider_rating is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ride already rated by rider"
            )
        ride.rider_rating = rating.rating
        ride.rider_feedback = rating.feedback
    elif ride.driver_id == user_id:
        if ride.driver_rating is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ride already rated by driver"
            )
        ride.driver_rating = rating.rating
        ride.driver_feedback = rating.feedback
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    db.commit()
    return {"message": "Rating submitted successfully"}

# Health check
@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "ride-service"} 