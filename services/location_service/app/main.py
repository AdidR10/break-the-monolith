from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '../../../'))
from shared.database_config import get_db, create_tables

from . import models

# Pydantic schemas
class LocationCreate(BaseModel):
    location_name: str = Field(..., min_length=1, max_length=255)
    zone: str = Field(..., min_length=1, max_length=50)
    latitude: Decimal = Field(..., ge=-90, le=90)
    longitude: Decimal = Field(..., ge=-180, le=180)
    description: Optional[str] = None
    is_pickup_point: bool = True
    is_drop_point: bool = True

class LocationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    location_name: str
    zone: str
    latitude: Decimal
    longitude: Decimal
    description: Optional[str]
    is_pickup_point: bool
    is_drop_point: bool
    is_active: bool
    popularity_score: int

app = FastAPI(title="RickshawX Location Service", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    create_tables()

@app.get("/api/v1/locations", response_model=List[LocationResponse])
async def get_locations(
    zone: Optional[str] = Query(None),
    pickup_only: bool = Query(False),
    drop_only: bool = Query(False),
    db: Session = Depends(get_db)
):
    """Get campus locations with filters"""
    query = db.query(models.CampusLocation).filter(models.CampusLocation.is_active == True)
    
    if zone:
        query = query.filter(models.CampusLocation.zone.ilike(f"%{zone}%"))
    if pickup_only:
        query = query.filter(models.CampusLocation.is_pickup_point == True)
    if drop_only:
        query = query.filter(models.CampusLocation.is_drop_point == True)
    
    return query.order_by(models.CampusLocation.popularity_score.desc()).all()

@app.get("/api/v1/locations/{location_id}", response_model=LocationResponse)
async def get_location_by_id(location_id: UUID, db: Session = Depends(get_db)):
    """Get a specific location by its ID"""
    location = db.query(models.CampusLocation).filter(
        models.CampusLocation.id == location_id,
        models.CampusLocation.is_active == True
    ).first()
    
    if not location:
        raise HTTPException(
            status_code=404, 
            detail=f"Location with ID {location_id} not found or inactive"
        )
    
    return location

@app.get("/api/v1/locations/by-name/{location_name}", response_model=LocationResponse)
async def get_location_by_name(location_name: str, db: Session = Depends(get_db)):
    """Get a specific location by its name (case-insensitive)"""
    location = db.query(models.CampusLocation).filter(
        models.CampusLocation.location_name.ilike(location_name),
        models.CampusLocation.is_active == True
    ).first()
    
    if not location:
        raise HTTPException(
            status_code=404, 
            detail=f"Location with name '{location_name}' not found or inactive"
        )
    
    return location

@app.post("/api/v1/locations", response_model=LocationResponse)
async def create_location(location: LocationCreate, db: Session = Depends(get_db)):
    """Create new campus location"""
    # Check if location name already exists
    existing = db.query(models.CampusLocation).filter(
        models.CampusLocation.location_name.ilike(location.location_name)
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Location with name '{location.location_name}' already exists"
        )
    
    db_location = models.CampusLocation(**location.model_dump())
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    return db_location

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "location-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002) 