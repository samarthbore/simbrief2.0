from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.app.core.database import get_db
from backend.app.models.models import Airport
from backend.app.schemas.schemas import AirportSummary, AirportDetail, AirportListResponse

router = APIRouter()


@router.get("/airports", response_model=AirportListResponse)
def list_airports(
    query: Optional[str] = Query(None, description="Search term for ICAO, IATA, ident, name, or city"),
    airport_type: Optional[str] = Query(None, description="Filter by airport type (e.g. large_airport, medium_airport)"),
    scheduled_only: bool = Query(False, description="Filter only airports with scheduled commercial service"),
    min_lat: Optional[float] = Query(None, ge=-90, le=90),
    max_lat: Optional[float] = Query(None, ge=-90, le=90),
    min_lon: Optional[float] = Query(None, ge=-180, le=180),
    max_lon: Optional[float] = Query(None, ge=-180, le=180),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    Search and retrieve airports with pagination and spatial bounding box filtering for LOD viewport loading.
    """
    q = db.query(Airport)

    if query:
        search_pattern = f"%{query.strip().upper()}%"
        name_pattern = f"%{query.strip()}%"
        q = q.filter(
            or_(
                Airport.ident.ilike(search_pattern),
                Airport.icao.ilike(search_pattern),
                Airport.iata.ilike(search_pattern),
                Airport.name.ilike(name_pattern),
                Airport.municipality.ilike(name_pattern),
            )
        )

    if airport_type:
        q = q.filter(Airport.airport_type == airport_type)

    if scheduled_only:
        q = q.filter(Airport.scheduled_service.is_(True))

    # Bounding box spatial filter for map viewport
    if min_lat is not None and max_lat is not None:
        q = q.filter(Airport.latitude >= min_lat, Airport.latitude <= max_lat)
    if min_lon is not None and max_lon is not None:
        if min_lon <= max_lon:
            q = q.filter(Airport.longitude >= min_lon, Airport.longitude <= max_lon)
        else:
            # Handles meridian wrap (e.g., across international dateline)
            q = q.filter(or_(Airport.longitude >= min_lon, Airport.longitude <= max_lon))

    total = q.count()
    items = q.order_by(
        # Prioritize large airports and matching ICAO/IATA
        Airport.scheduled_service.desc(),
        Airport.ident.asc(),
    ).offset(offset).limit(limit).all()

    return AirportListResponse(total=total, items=items)


@router.get("/airports/{id_or_ident}", response_model=AirportDetail)
def get_airport(id_or_ident: str, db: Session = Depends(get_db)):
    """
    Retrieve single airport details by internal ID, ICAO code, IATA code, or OurAirports ident.
    """
    key = id_or_ident.strip()
    airport = (
        db.query(Airport)
        .filter(
            or_(
                Airport.id == key,
                Airport.ident == key.upper(),
                Airport.icao == key.upper(),
                Airport.iata == key.upper(),
            )
        )
        .first()
    )

    if not airport:
        raise HTTPException(status_code=404, detail=f"Airport '{id_or_ident}' not found.")

    return airport
