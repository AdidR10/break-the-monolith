from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, or_
from typing import Optional, List, Dict, Any
from uuid import UUID
import bcrypt
import logging
import sys
import os
from datetime import datetime, timedelta

# Add the shared directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../'))

from . import models, schemas

logger = logging.getLogger(__name__)

# Import auth module for cache invalidation
try:
    from . import auth
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    logger.warning("Auth module not available for cache invalidation")

class UserCRUD:
    @staticmethod
    def create_user(db: Session, user: schemas.UserCreate) -> models.User:
        """Create a new user with hashed password"""
        try:
            # Hash password
            password_hash = bcrypt.hashpw(
                user.password.encode('utf-8'), 
                bcrypt.gensalt()
            ).decode('utf-8')
            
            # Create user
            db_user = models.User(
                email=user.email.lower(),
                phone=user.phone,
                password_hash=password_hash,
                first_name=user.first_name.strip(),
                last_name=user.last_name.strip(),
                user_type=user.user_type
            )
            
            db.add(db_user)
            db.flush()  # Flush to get the user ID
            
            # Create appropriate profile
            if user.user_type == schemas.UserType.RICKSHAW_PULLER:
                # Note: Rickshaw profile will be created separately with additional info
                pass
            elif user.user_type == schemas.UserType.STUDENT:
                # Note: Student profile will be created separately with additional info
                pass
            
            db.commit()
            db.refresh(db_user)
            logger.info(f"User created successfully: {db_user.email}")
            return db_user
            
        except IntegrityError as e:
            db.rollback()
            if "email" in str(e.orig):
                raise ValueError("User with this email already exists")
            elif "phone" in str(e.orig):
                raise ValueError("User with this phone number already exists")
            else:
                raise ValueError("User creation failed due to constraint violation")
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating user: {e}")
            raise

    @staticmethod
    def get_user_by_id(db: Session, user_id: UUID) -> Optional[models.User]:
        """Get user by ID with profiles"""
        return db.query(models.User).options(
            joinedload(models.User.rickshaw_profile),
            joinedload(models.User.student_profile)
        ).filter(models.User.id == user_id).first()

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
        """Get user by email"""
        return db.query(models.User).options(
            joinedload(models.User.rickshaw_profile),
            joinedload(models.User.student_profile)
        ).filter(models.User.email == email.lower()).first()

    @staticmethod
    def get_user_by_phone(db: Session, phone: str) -> Optional[models.User]:
        """Get user by phone"""
        return db.query(models.User).options(
            joinedload(models.User.rickshaw_profile),
            joinedload(models.User.student_profile)
        ).filter(models.User.phone == phone).first()

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[models.User]:
        """Authenticate user with email and password"""
        user = UserCRUD.get_user_by_email(db, email)
        if user and bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            # Update last login
            user.last_login = datetime.utcnow()
            db.commit()
            return user
        return None

    @staticmethod
    def update_user(db: Session, user_id: UUID, user_update: schemas.UserUpdate) -> Optional[models.User]:
        """Update user information"""
        try:
            user = db.query(models.User).filter(models.User.id == user_id).first()
            if not user:
                return None
            
            update_data = user_update.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                if field == "phone" and value:
                    # Check if phone is already taken by another user
                    existing = db.query(models.User).filter(
                        and_(models.User.phone == value, models.User.id != user_id)
                    ).first()
                    if existing:
                        raise ValueError("Phone number already exists")
                
                setattr(user, field, value)
            
            user.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(user)
            
            # Invalidate Redis cache for updated user
            if CACHE_AVAILABLE:
                auth.invalidate_user_cache(str(user_id))
            
            logger.info(f"User updated successfully: {user.email}")
            return user
            
        except IntegrityError:
            db.rollback()
            raise ValueError("Update failed due to constraint violation")
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating user: {e}")
            raise

    @staticmethod
    def update_last_login(db: Session, user_id: UUID) -> bool:
        """Update user's last login time"""
        try:
            user = db.query(models.User).filter(models.User.id == user_id).first()
            if user:
                user.last_login = datetime.utcnow()
                db.commit()
                
                # Update cache with new last_login time
                if CACHE_AVAILABLE:
                    # Get fresh user data and update cache
                    fresh_user = UserCRUD.get_user_by_id(db, user_id)
                    if fresh_user:
                        user_data = auth.serialize_user_for_cache(fresh_user)
                        auth.cache_user_data(str(user_id), user_data)
                
                return True
            return False
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating last login for user {user_id}: {e}")
            return False

    @staticmethod
    def deactivate_user(db: Session, user_id: UUID) -> bool:
        """Deactivate user account"""
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if user:
            user.is_active = False
            user.updated_at = datetime.utcnow()
            db.commit()
            
            # Invalidate cache and blacklist all user tokens
            if CACHE_AVAILABLE:
                auth.TokenBlacklist.blacklist_user_tokens(str(user_id))
                auth.invalidate_user_cache(str(user_id))
            return True
        return False

    @staticmethod
    def get_users_with_filters(
        db: Session, 
        filters: schemas.UserSearchFilters,
        pagination: schemas.PaginationParams
    ) -> Dict[str, Any]:
        """Get users with filters and pagination"""
        query = db.query(models.User).options(
            joinedload(models.User.rickshaw_profile),
            joinedload(models.User.student_profile)
        )
        
        # Apply filters
        if filters.user_type:
            query = query.filter(models.User.user_type == filters.user_type)
        if filters.is_active is not None:
            query = query.filter(models.User.is_active == filters.is_active)
        if filters.is_verified is not None:
            query = query.filter(models.User.is_verified == filters.is_verified)
        
        # Join filters for profiles
        if filters.department and filters.user_type == schemas.UserType.STUDENT:
            query = query.join(models.StudentProfile).filter(
                models.StudentProfile.department.ilike(f"%{filters.department}%")
            )
        
        if filters.is_available is not None and filters.user_type == schemas.UserType.RICKSHAW_PULLER:
            query = query.join(models.RickshawProfile).filter(
                models.RickshawProfile.is_available == filters.is_available
            )
        
        # Count total
        total = query.count()
        
        # Apply pagination
        offset = (pagination.page - 1) * pagination.size
        users = query.offset(offset).limit(pagination.size).all()
        
        return {
            "items": users,
            "total": total,
            "page": pagination.page,
            "size": pagination.size,
            "pages": (total + pagination.size - 1) // pagination.size
        }

class RickshawProfileCRUD:
    @staticmethod
    def create_profile(db: Session, user_id: UUID, profile: schemas.RickshawProfileCreate) -> models.RickshawProfile:
        """Create rickshaw profile for user"""
        try:
            db_profile = models.RickshawProfile(
                user_id=user_id,
                rickshaw_number=profile.rickshaw_number.upper(),
                license_number=profile.license_number
            )
            
            db.add(db_profile)
            db.commit()
            db.refresh(db_profile)
            logger.info(f"Rickshaw profile created: {profile.rickshaw_number}")
            return db_profile
            
        except IntegrityError:
            db.rollback()
            raise ValueError("Rickshaw number or license number already exists")

    @staticmethod
    def update_profile(
        db: Session, 
        user_id: UUID, 
        profile_update: schemas.RickshawProfileUpdate
    ) -> Optional[models.RickshawProfile]:
        """Update rickshaw profile"""
        profile = db.query(models.RickshawProfile).filter(
            models.RickshawProfile.user_id == user_id
        ).first()
        
        if not profile:
            return None
        
        update_data = profile_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(profile, field, value)
        
        profile.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def update_location(
        db: Session, 
        user_id: UUID, 
        location: schemas.LocationUpdate
    ) -> Optional[models.RickshawProfile]:
        """Update rickshaw location"""
        profile = db.query(models.RickshawProfile).filter(
            models.RickshawProfile.user_id == user_id
        ).first()
        
        if not profile:
            return None
        
        profile.current_location = location.current_location
        profile.current_latitude = location.current_latitude
        profile.current_longitude = location.current_longitude
        profile.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def update_availability(
        db: Session, 
        user_id: UUID, 
        availability: schemas.AvailabilityUpdate
    ) -> Optional[models.RickshawProfile]:
        """Update rickshaw availability"""
        profile = db.query(models.RickshawProfile).filter(
            models.RickshawProfile.user_id == user_id
        ).first()
        
        if not profile:
            return None
        
        profile.is_available = availability.is_available
        profile.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def get_available_rickshaws(db: Session, limit: int = 10) -> List[models.RickshawProfile]:
        """Get available rickshaws"""
        return db.query(models.RickshawProfile).filter(
            models.RickshawProfile.is_available == True
        ).limit(limit).all()

class StudentProfileCRUD:
    @staticmethod
    def create_profile(db: Session, user_id: UUID, profile: schemas.StudentProfileCreate) -> models.StudentProfile:
        """Create student profile for user"""
        try:
            db_profile = models.StudentProfile(
                user_id=user_id,
                student_id=profile.student_id.upper(),
                department=profile.department,
                batch=profile.batch,
                year=profile.year,
                emergency_contact=profile.emergency_contact
            )
            
            db.add(db_profile)
            db.commit()
            db.refresh(db_profile)
            logger.info(f"Student profile created: {profile.student_id}")
            return db_profile
            
        except IntegrityError:
            db.rollback()
            raise ValueError("Student ID already exists")

    @staticmethod
    def update_profile(
        db: Session, 
        user_id: UUID, 
        profile_update: schemas.StudentProfileUpdate
    ) -> Optional[models.StudentProfile]:
        """Update student profile"""
        profile = db.query(models.StudentProfile).filter(
            models.StudentProfile.user_id == user_id
        ).first()
        
        if not profile:
            return None
        
        update_data = profile_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(profile, field, value)
        
        profile.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(profile)
        return profile 