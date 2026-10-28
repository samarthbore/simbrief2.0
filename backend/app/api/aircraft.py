from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.models import AircraftProfile
from backend.app.schemas.schemas import AircraftProfileResponse, AircraftProfileCreate

router = APIRouter()


@router.get("/aircraft", response_model=List[AircraftProfileResponse])
def list_aircraft_profiles(db: Session = Depends(get_db)):
    """List all available aircraft performance profiles."""
    return db.query(AircraftProfile).order_by(AircraftProfile.name.asc()).all()


@router.post("/aircraft", response_model=AircraftProfileResponse, status_code=201)
def create_aircraft_profile(profile: AircraftProfileCreate, db: Session = Depends(get_db)):
    """Create a new configurable aircraft profile."""
    ident = profile.identifier.strip().upper()
    existing = db.query(AircraftProfile).filter(AircraftProfile.identifier == ident).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Aircraft profile '{ident}' already exists.")

    new_profile = AircraftProfile(
        identifier=ident,
        name=profile.name,
        category=profile.category,
        cruise_speed_kts=profile.cruise_speed_kts,
        fuel_flow_kg_hr=profile.fuel_flow_kg_hr,
        climb_rate_fpm=profile.climb_rate_fpm,
        descent_rate_fpm=profile.descent_rate_fpm,
        service_ceiling_ft=profile.service_ceiling_ft,
        max_range_nm=profile.max_range_nm,
        description=profile.description,
        model_source=profile.model_source,
    )
    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)
    return new_profile


@router.get("/aircraft/{id_or_ident}", response_model=AircraftProfileResponse)
def get_aircraft_profile(id_or_ident: str, db: Session = Depends(get_db)):
    """Retrieve aircraft profile by ID or identifier (e.g., A320)."""
    key = id_or_ident.strip()
    profile = (
        db.query(AircraftProfile)
        .filter(
            (AircraftProfile.id == key) | (AircraftProfile.identifier == key.upper())
        )
        .first()
    )
    if not profile:
        raise HTTPException(status_code=404, detail=f"Aircraft profile '{id_or_ident}' not found.")
    return profile
