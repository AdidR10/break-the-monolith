from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, or_, func
from typing import Optional, List, Dict, Any
from uuid import UUID
import logging
from datetime import datetime, timedelta
from geopy.distance import geodesic
import httpx

from . import models, schemas

logger = logging.getLogger(__name__)

class FareCalculator:
    """Fare calculation service"""
    BASE_FARE = 30.0  # BDT
    PER_KM_RATE = 15.0  # BDT per km
    PER_MINUTE_RATE = 2.0  # BDT per minute
    SURGE_HOURS = [(7, 9), (17, 19)]  # Morning and evening rush hours
    SURGE_MULTIPLIER = 1.5
    
    @classmethod
    def calculate_distance(cls, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance in kilometers using geopy"""
        return geodesic((lat1, lng1), (lat2, lng2)).kilometers
    
    @classmethod
    def estimate_duration(cls, distance_km: float) -> int:
        """Estimate duration in minutes based on distance"""
        # Assuming average speed of 20 km/h in campus
        return max(5, int(distance_km * 3))  # Minimum 5 minutes
    
    @classmethod
    def calculate_fare(cls, distance_km: float, duration_minutes: int, time_of_day: datetime = None) -> Dict[str, Any]:
        """Calculate fare based on distance, duration, and time"""
        if time_of_day is None:
            time_of_day = datetime.now()
        
        base_fare = cls.BASE_FARE
        distance_fare = distance_km * cls.PER_KM_RATE
        time_fare = duration_minutes * cls.PER_MINUTE_RATE
        
        subtotal = base_fare + distance_fare + time_fare
        
        # Check for surge pricing
        current_hour = time_of_day.hour
        surge_multiplier = 1.0
        
        for start_hour, end_hour in cls.SURGE_HOURS:
            if start_hour <= current_hour < end_hour:
                surge_multiplier = cls.SURGE_MULTIPLIER
                break
        
        total_fare = subtotal * surge_multiplier
        
        return {
            "base_fare": base_fare,
            "distance_fare": distance_fare,
            "time_fare": time_fare,
            "subtotal": subtotal,
            "surge_multiplier": surge_multiplier,
            "total_fare": total_fare,
            "breakdown": {
                "base": f"৳{base_fare:.2f}",
                "distance": f"৳{distance_fare:.2f} ({distance_km:.1f} km × ৳{cls.PER_KM_RATE})",
                "time": f"৳{time_fare:.2f} ({duration_minutes} min × ৳{cls.PER_MINUTE_RATE})",
                "surge": f"{surge_multiplier}x" if surge_multiplier > 1 else "No surge"
            }
        }

class RideRequestCRUD:
    @staticmethod
    def create_ride_request(db: Session, request: schemas.RideRequestCreate, rider_id: UUID) -> models.RideRequest:
        """Create a new ride request"""
        try:
            # Calculate fare and distance
            distance_km = FareCalculator.calculate_distance(
                float(request.pickup_latitude), float(request.pickup_longitude),
                float(request.drop_latitude), float(request.drop_longitude)
            )
            
            duration_minutes = FareCalculator.estimate_duration(distance_km)
            fare_calculation = FareCalculator.calculate_fare(distance_km, duration_minutes)
            
            # Set expiration time
            expires_at = datetime.utcnow() + timedelta(minutes=request.max_wait_time)
            
            db_request = models.RideRequest(
                rider_id=rider_id,
                pickup_location=request.pickup_location,
                pickup_latitude=request.pickup_latitude,
                pickup_longitude=request.pickup_longitude,
                drop_location=request.drop_location,
                drop_latitude=request.drop_latitude,
                drop_longitude=request.drop_longitude,
                estimated_fare=fare_calculation["total_fare"],
                estimated_distance=distance_km,
                estimated_duration=duration_minutes,
                max_wait_time=request.max_wait_time,
                special_requirements=request.special_requirements,
                expires_at=expires_at
            )
            
            db.add(db_request)
            db.commit()
            db.refresh(db_request)
            logger.info(f"Ride request created: {db_request.id}")
            return db_request
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating ride request: {e}")
            raise

    @staticmethod
    def get_active_ride_requests(db: Session, limit: int = 20) -> List[models.RideRequest]:
        """Get active ride requests"""
        return db.query(models.RideRequest).filter(
            and_(
                models.RideRequest.is_active == True,
                models.RideRequest.expires_at > datetime.utcnow()
            )
        ).order_by(models.RideRequest.created_at.desc()).limit(limit).all()

    @staticmethod
    def get_ride_request_by_id(db: Session, request_id: UUID) -> Optional[models.RideRequest]:
        """Get ride request by ID"""
        return db.query(models.RideRequest).filter(models.RideRequest.id == request_id).first()

    @staticmethod
    def deactivate_expired_requests(db: Session) -> int:
        """Deactivate expired ride requests"""
        count = db.query(models.RideRequest).filter(
            and_(
                models.RideRequest.is_active == True,
                models.RideRequest.expires_at <= datetime.utcnow()
            )
        ).update({"is_active": False})
        
        db.commit()
        return count

class DriverOfferCRUD:
    @staticmethod
    def create_driver_offer(db: Session, offer: schemas.DriverOfferCreate, driver_id: UUID) -> models.DriverRideOffer:
        """Create driver offer for ride request"""
        try:
            # Check if ride request is still active
            ride_request = db.query(models.RideRequest).filter(
                and_(
                    models.RideRequest.id == offer.ride_request_id,
                    models.RideRequest.is_active == True,
                    models.RideRequest.expires_at > datetime.utcnow()
                )
            ).first()
            
            if not ride_request:
                raise ValueError("Ride request not found or expired")
            
            # Check if driver already made an offer
            existing_offer = db.query(models.DriverRideOffer).filter(
                and_(
                    models.DriverRideOffer.ride_request_id == offer.ride_request_id,
                    models.DriverRideOffer.driver_id == driver_id,
                    models.DriverRideOffer.is_active == True
                )
            ).first()
            
            if existing_offer:
                raise ValueError("Driver already made an offer for this ride")
            
            expires_at = datetime.utcnow() + timedelta(minutes=5)  # Offer expires in 5 minutes
            
            db_offer = models.DriverRideOffer(
                ride_request_id=offer.ride_request_id,
                driver_id=driver_id,
                offered_fare=offer.offered_fare or ride_request.estimated_fare,
                estimated_arrival_time=offer.estimated_arrival_time,
                message=offer.message,
                expires_at=expires_at
            )
            
            db.add(db_offer)
            db.commit()
            db.refresh(db_offer)
            logger.info(f"Driver offer created: {db_offer.id}")
            return db_offer
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating driver offer: {e}")
            raise

    @staticmethod
    def get_offers_for_request(db: Session, request_id: UUID) -> List[models.DriverRideOffer]:
        """Get all offers for a ride request"""
        return db.query(models.DriverRideOffer).filter(
            and_(
                models.DriverRideOffer.ride_request_id == request_id,
                models.DriverRideOffer.is_active == True,
                models.DriverRideOffer.expires_at > datetime.utcnow()
            )
        ).order_by(models.DriverRideOffer.created_at).all()

    @staticmethod
    def accept_offer(db: Session, offer_id: UUID, rider_id: UUID) -> models.DriverRideOffer:
        """Accept driver offer and create ride"""
        try:
            offer = db.query(models.DriverRideOffer).filter(
                models.DriverRideOffer.id == offer_id
            ).first()
            
            if not offer:
                raise ValueError("Offer not found")
            
            if not offer.is_active or offer.expires_at <= datetime.utcnow():
                raise ValueError("Offer expired or inactive")
            
            # Verify rider owns the request
            ride_request = db.query(models.RideRequest).filter(
                and_(
                    models.RideRequest.id == offer.ride_request_id,
                    models.RideRequest.rider_id == rider_id
                )
            ).first()
            
            if not ride_request:
                raise ValueError("Unauthorized or request not found")
            
            # Accept the offer
            offer.is_accepted = True
            
            # Deactivate all other offers for this request
            db.query(models.DriverRideOffer).filter(
                and_(
                    models.DriverRideOffer.ride_request_id == offer.ride_request_id,
                    models.DriverRideOffer.id != offer_id
                )
            ).update({"is_active": False})
            
            # Deactivate the ride request
            ride_request.is_active = False
            
            db.commit()
            return offer
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error accepting offer: {e}")
            raise

class RideCRUD:
    @staticmethod
    def create_ride_from_accepted_offer(db: Session, offer: models.DriverRideOffer) -> models.Ride:
        """Create ride from accepted offer"""
        try:
            ride_request = db.query(models.RideRequest).filter(
                models.RideRequest.id == offer.ride_request_id
            ).first()
            
            db_ride = models.Ride(
                rider_id=ride_request.rider_id,
                driver_id=offer.driver_id,
                pickup_location=ride_request.pickup_location,
                pickup_latitude=ride_request.pickup_latitude,
                pickup_longitude=ride_request.pickup_longitude,
                drop_location=ride_request.drop_location,
                drop_latitude=ride_request.drop_latitude,
                drop_longitude=ride_request.drop_longitude,
                status=models.RideStatus.ACCEPTED,
                estimated_fare=offer.offered_fare,
                base_fare=30.0,  # Default base fare
                distance_km=ride_request.estimated_distance,
                duration_minutes=ride_request.estimated_duration,
                special_instructions=ride_request.special_requirements,
                accepted_at=datetime.utcnow()
            )
            
            db.add(db_ride)
            db.flush()
            
            # Create status history
            RideCRUD.add_status_history(
                db, db_ride.id, None, models.RideStatus.ACCEPTED.value, offer.driver_id
            )
            
            db.commit()
            db.refresh(db_ride)
            logger.info(f"Ride created: {db_ride.id}")
            return db_ride
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating ride: {e}")
            raise

    @staticmethod
    def update_ride_status(
        db: Session, 
        ride_id: UUID, 
        new_status: models.RideStatus, 
        user_id: UUID,
        notes: Optional[str] = None
    ) -> models.Ride:
        """Update ride status with history tracking"""
        try:
            ride = db.query(models.Ride).filter(models.Ride.id == ride_id).first()
            if not ride:
                raise ValueError("Ride not found")
            
            old_status = ride.status
            ride.status = new_status
            ride.updated_at = datetime.utcnow()
            
            # Update specific timestamps
            if new_status == models.RideStatus.DRIVER_ARRIVED:
                ride.driver_arrived_at = datetime.utcnow()
            elif new_status == models.RideStatus.STARTED:
                ride.started_at = datetime.utcnow()
            elif new_status == models.RideStatus.COMPLETED:
                ride.ended_at = datetime.utcnow()
            elif new_status == models.RideStatus.CANCELLED:
                ride.cancelled_at = datetime.utcnow()
            
            # Add status history
            RideCRUD.add_status_history(db, ride_id, old_status.value, new_status.value, user_id, notes)
            
            db.commit()
            db.refresh(ride)
            return ride
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating ride status: {e}")
            raise

    @staticmethod
    def add_status_history(
        db: Session,
        ride_id: UUID,
        previous_status: Optional[str],
        new_status: str,
        changed_by: UUID,
        notes: Optional[str] = None
    ):
        """Add status change to history"""
        history = models.RideStatusHistory(
            ride_id=ride_id,
            previous_status=previous_status,
            new_status=new_status,
            changed_by=changed_by,
            notes=notes
        )
        db.add(history)

    @staticmethod
    def get_ride_by_id(db: Session, ride_id: UUID) -> Optional[models.Ride]:
        """Get ride by ID with relationships"""
        return db.query(models.Ride).options(
            joinedload(models.Ride.status_history),
            joinedload(models.Ride.ride_tracking)
        ).filter(models.Ride.id == ride_id).first()

    @staticmethod
    def get_user_rides(
        db: Session, 
        user_id: UUID, 
        user_type: str,
        filters: schemas.RideSearchFilters,
        pagination: schemas.PaginationParams
    ) -> Dict[str, Any]:
        """Get rides for user with filters"""
        query = db.query(models.Ride)
        
        # Filter by user type
        if user_type == "STUDENT":
            query = query.filter(models.Ride.rider_id == user_id)
        elif user_type == "RICKSHAW_PULLER":
            query = query.filter(models.Ride.driver_id == user_id)
        
        # Apply filters
        if filters.status:
            query = query.filter(models.Ride.status == filters.status)
        if filters.date_from:
            query = query.filter(models.Ride.created_at >= filters.date_from)
        if filters.date_to:
            query = query.filter(models.Ride.created_at <= filters.date_to)
        
        # Count total
        total = query.count()
        
        # Apply pagination
        offset = (pagination.page - 1) * pagination.size
        rides = query.order_by(models.Ride.created_at.desc()).offset(offset).limit(pagination.size).all()
        
        return {
            "items": rides,
            "total": total,
            "page": pagination.page,
            "size": pagination.size,
            "pages": (total + pagination.size - 1) // pagination.size
        }

    @staticmethod
    def add_ride_tracking(db: Session, ride_id: UUID, tracking: schemas.RideTrackingCreate, driver_id: UUID) -> models.RideTracking:
        """Add tracking point for ride"""
        db_tracking = models.RideTracking(
            ride_id=ride_id,
            driver_id=driver_id,
            latitude=tracking.latitude,
            longitude=tracking.longitude,
            speed_kmh=tracking.speed_kmh,
            heading=tracking.heading,
            accuracy_meters=tracking.accuracy_meters
        )
        
        db.add(db_tracking)
        db.commit()
        db.refresh(db_tracking)
        return db_tracking

class UserServiceClient:
    """Client to communicate with user service"""
    
    def __init__(self, base_url: str = "http://user-service:8000"):
        self.base_url = base_url
    
    async def get_nearby_drivers(self, latitude: float, longitude: float, radius_km: float = 5.0) -> List[Dict]:
        """Get nearby available drivers from user service"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/rickshaw/available",
                    params={"limit": 20}
                )
                if response.status_code == 200:
                    drivers = response.json()
                    # Filter by distance (simplified)
                    nearby_drivers = []
                    for driver in drivers:
                        if driver.get("current_latitude") and driver.get("current_longitude"):
                            distance = FareCalculator.calculate_distance(
                                latitude, longitude,
                                float(driver["current_latitude"]), float(driver["current_longitude"])
                            )
                            if distance <= radius_km:
                                driver["distance_km"] = distance
                                nearby_drivers.append(driver)
                    
                    # Sort by distance
                    nearby_drivers.sort(key=lambda x: x["distance_km"])
                    return nearby_drivers
                return []
        except Exception as e:
            logger.error(f"Error getting nearby drivers: {e}")
            return [] 