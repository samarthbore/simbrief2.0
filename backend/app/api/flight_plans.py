import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.models import (
    FlightPlan,
    FlightPlanRevision,
    Airport,
    AircraftProfile,
)
from backend.app.schemas.schemas import (
    FlightPlanCreate,
    FlightPlanUpdate,
    FlightPlanResponse,
    FlightPlanRevisionResponse,
    AirportSummary,
    AircraftProfileResponse,
    RouteWaypoint,
)
from backend.app.services.routing.geo import (
    haversine_distance_nm,
    initial_bearing,
    generate_great_circle_waypoints,
)
from backend.app.services.performance.models import AircraftPerformanceModel
from backend.app.services.briefing.pdf import generate_flight_briefing_pdf
from backend.app.core.config import settings

router = APIRouter()


def generate_plan_code() -> str:
    """Generate a clean human-readable flight plan code (e.g. FP-261028-AB12)."""
    now = datetime.now(timezone.utc)
    rand_suffix = uuid.uuid4().hex[:4].upper()
    return f"FP-{now.strftime('%y%m%d')}-{rand_suffix}"


def format_plan_response(plan: FlightPlan, db: Session) -> FlightPlanResponse:
    dep = db.query(Airport).filter(Airport.ident == plan.departure_ident).first()
    dest = db.query(Airport).filter(Airport.ident == plan.destination_ident).first()
    ac = db.query(AircraftProfile).filter(AircraftProfile.id == plan.aircraft_profile_id).first()

    waypoints_raw = json.loads(plan.route_waypoints_json) if plan.route_waypoints_json else []
    waypoints = [RouteWaypoint(**w) for w in waypoints_raw]

    revisions = [
        FlightPlanRevisionResponse(
            id=r.id,
            revision_number=r.revision_number,
            changes_summary=r.changes_summary,
            route_summary=r.route_summary,
            total_distance_nm=r.total_distance_nm,
            estimated_flight_time_min=r.estimated_flight_time_min,
            estimated_fuel_burn_kg=r.estimated_fuel_burn_kg,
            created_at=r.created_at,
        )
        for r in plan.revisions
    ]

    return FlightPlanResponse(
        id=plan.id,
        plan_code=plan.plan_code,
        title=plan.title,
        departure_ident=plan.departure_ident,
        destination_ident=plan.destination_ident,
        departure=AirportSummary.model_validate(dep) if dep else None,
        destination=AirportSummary.model_validate(dest) if dest else None,
        aircraft_profile_id=plan.aircraft_profile_id,
        aircraft_profile=AircraftProfileResponse.model_validate(ac) if ac else None,
        routing_objective=plan.routing_objective,
        total_distance_nm=plan.total_distance_nm,
        estimated_flight_time_min=plan.estimated_flight_time_min,
        estimated_fuel_burn_kg=plan.estimated_fuel_burn_kg,
        cruise_altitude_ft=plan.cruise_altitude_ft,
        route_waypoints=waypoints,
        calculation_assumptions=plan.calculation_assumptions,
        status=plan.status,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
        revisions=revisions,
    )


@router.post("/flight-plans", response_model=FlightPlanResponse, status_code=201)
def create_flight_plan(plan_in: FlightPlanCreate, db: Session = Depends(get_db)):
    """
    Save and persist a newly created flight plan.
    """
    dep = db.query(Airport).filter(Airport.ident == plan_in.departure_ident.upper()).first()
    if not dep:
        raise HTTPException(status_code=404, detail=f"Departure airport '{plan_in.departure_ident}' not found.")

    dest = db.query(Airport).filter(Airport.ident == plan_in.destination_ident.upper()).first()
    if not dest:
        raise HTTPException(status_code=404, detail=f"Destination airport '{plan_in.destination_ident}' not found.")

    ac = (
        db.query(AircraftProfile)
        .filter(
            (AircraftProfile.id == plan_in.aircraft_id)
            | (AircraftProfile.identifier == plan_in.aircraft_id.upper())
        )
        .first()
    )
    if not ac:
        raise HTTPException(status_code=404, detail=f"Aircraft profile '{plan_in.aircraft_id}' not found.")

    dist_nm = haversine_distance_nm(dep.latitude, dep.longitude, dest.latitude, dest.longitude)
    bearing = initial_bearing(dep.latitude, dep.longitude, dest.latitude, dest.longitude)

    perf_model = AircraftPerformanceModel(
        identifier=ac.identifier,
        name=ac.name,
        cruise_speed_kts=ac.cruise_speed_kts,
        fuel_flow_kg_hr=ac.fuel_flow_kg_hr,
        category=ac.category,
    )
    perf_est = perf_model.calculate(dist_nm)

    waypoints = [
        {
            "ident": dep.ident,
            "name": dep.name,
            "node_type": "AIRPORT",
            "latitude": dep.latitude,
            "longitude": dep.longitude,
            "leg_distance_nm": 0.0,
            "bearing_deg": bearing,
            "cumulative_distance_nm": 0.0,
        },
        {
            "ident": dest.ident,
            "name": dest.name,
            "node_type": "AIRPORT",
            "latitude": dest.latitude,
            "longitude": dest.longitude,
            "leg_distance_nm": dist_nm,
            "bearing_deg": bearing,
            "cumulative_distance_nm": dist_nm,
        },
    ]

    plan_code = generate_plan_code()
    title = plan_in.title or f"{dep.ident} to {dest.ident} ({ac.identifier})"

    flight_plan = FlightPlan(
        plan_code=plan_code,
        title=title,
        departure_ident=dep.ident,
        destination_ident=dest.ident,
        aircraft_profile_id=ac.id,
        routing_objective=plan_in.routing_objective,
        total_distance_nm=dist_nm,
        estimated_flight_time_min=round(perf_est.flight_time_minutes, 1),
        estimated_fuel_burn_kg=round(perf_est.trip_fuel_kg, 1),
        cruise_altitude_ft=plan_in.cruise_altitude_ft,
        route_waypoints_json=json.dumps(waypoints),
        calculation_assumptions=perf_est.assumptions,
        status="ACTIVE",
    )
    db.add(flight_plan)
    db.flush()

    # Initial revision
    revision = FlightPlanRevision(
        flight_plan_id=flight_plan.id,
        revision_number=1,
        changes_summary="Initial flight plan creation",
        route_summary=f"Direct DCT {dep.ident} -> {dest.ident}",
        waypoints_json=json.dumps(waypoints),
        total_distance_nm=dist_nm,
        estimated_flight_time_min=round(perf_est.flight_time_minutes, 1),
        estimated_fuel_burn_kg=round(perf_est.trip_fuel_kg, 1),
    )
    db.add(revision)
    db.commit()
    db.refresh(flight_plan)

    return format_plan_response(flight_plan, db)


@router.get("/flight-plans", response_model=List[FlightPlanResponse])
def list_flight_plans(db: Session = Depends(get_db)):
    """Retrieve all saved flight plans ordered by recent updates."""
    plans = db.query(FlightPlan).order_by(FlightPlan.updated_at.desc()).all()
    return [format_plan_response(p, db) for p in plans]


@router.get("/flight-plans/{id_or_code}", response_model=FlightPlanResponse)
def get_flight_plan(id_or_code: str, db: Session = Depends(get_db)):
    """Retrieve a single saved flight plan by UUID or plan code."""
    key = id_or_code.strip()
    plan = (
        db.query(FlightPlan)
        .filter((FlightPlan.id == key) | (FlightPlan.plan_code == key.upper()))
        .first()
    )
    if not plan:
        raise HTTPException(status_code=404, detail=f"Flight plan '{id_or_code}' not found.")
    return format_plan_response(plan, db)


@router.patch("/flight-plans/{id_or_code}", response_model=FlightPlanResponse)
def update_flight_plan(id_or_code: str, plan_update: FlightPlanUpdate, db: Session = Depends(get_db)):
    """
    Update flight plan parameters and create an audit revision.
    """
    key = id_or_code.strip()
    plan = (
        db.query(FlightPlan)
        .filter((FlightPlan.id == key) | (FlightPlan.plan_code == key.upper()))
        .first()
    )
    if not plan:
        raise HTTPException(status_code=404, detail=f"Flight plan '{id_or_code}' not found.")

    changes = []
    if plan_update.title is not None and plan_update.title != plan.title:
        changes.append(f"Title changed to '{plan_update.title}'")
        plan.title = plan_update.title

    if plan_update.cruise_altitude_ft is not None and plan_update.cruise_altitude_ft != plan.cruise_altitude_ft:
        changes.append(f"Altitude changed to FL{int(plan_update.cruise_altitude_ft/100)}")
        plan.cruise_altitude_ft = plan_update.cruise_altitude_ft

    if plan_update.aircraft_id:
        ac = (
            db.query(AircraftProfile)
            .filter(
                (AircraftProfile.id == plan_update.aircraft_id)
                | (AircraftProfile.identifier == plan_update.aircraft_id.upper())
            )
            .first()
        )
        if ac and ac.id != plan.aircraft_profile_id:
            changes.append(f"Aircraft changed to {ac.identifier}")
            plan.aircraft_profile_id = ac.id
            # Recalculate performance with new aircraft
            perf_model = AircraftPerformanceModel(
                identifier=ac.identifier,
                name=ac.name,
                cruise_speed_kts=ac.cruise_speed_kts,
                fuel_flow_kg_hr=ac.fuel_flow_kg_hr,
                category=ac.category,
            )
            est = perf_model.calculate(plan.total_distance_nm)
            plan.estimated_flight_time_min = round(est.flight_time_minutes, 1)
            plan.estimated_fuel_burn_kg = round(est.trip_fuel_kg, 1)
            plan.calculation_assumptions = est.assumptions

    if plan_update.routing_objective and plan_update.routing_objective != plan.routing_objective:
        changes.append(f"Objective changed to {plan_update.routing_objective}")
        plan.routing_objective = plan_update.routing_objective

    if changes:
        # Increment revision
        next_rev_num = (max([r.revision_number for r in plan.revisions] or [0])) + 1
        new_rev = FlightPlanRevision(
            flight_plan_id=plan.id,
            revision_number=next_rev_num,
            changes_summary="; ".join(changes),
            route_summary=f"Route revision {next_rev_num}",
            waypoints_json=plan.route_waypoints_json,
            total_distance_nm=plan.total_distance_nm,
            estimated_flight_time_min=plan.estimated_flight_time_min,
            estimated_fuel_burn_kg=plan.estimated_fuel_burn_kg,
        )
        db.add(new_rev)
        plan.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(plan)

    return format_plan_response(plan, db)


@router.get("/flight-plans/{id_or_code}/revisions", response_model=List[FlightPlanRevisionResponse])
def get_flight_plan_revisions(id_or_code: str, db: Session = Depends(get_db)):
    """Retrieve full revision history for a saved plan."""
    key = id_or_code.strip()
    plan = (
        db.query(FlightPlan)
        .filter((FlightPlan.id == key) | (FlightPlan.plan_code == key.upper()))
        .first()
    )
    if not plan:
        raise HTTPException(status_code=404, detail=f"Flight plan '{id_or_code}' not found.")

    return [
        FlightPlanRevisionResponse(
            id=r.id,
            revision_number=r.revision_number,
            changes_summary=r.changes_summary,
            route_summary=r.route_summary,
            total_distance_nm=r.total_distance_nm,
            estimated_flight_time_min=r.estimated_flight_time_min,
            estimated_fuel_burn_kg=r.estimated_fuel_burn_kg,
            created_at=r.created_at,
        )
        for r in plan.revisions
    ]


@router.get("/flight-plans/{id_or_code}/briefing")
def get_flight_plan_briefing_pdf(id_or_code: str, db: Session = Depends(get_db)):
    """
    Generate and download an official-looking OFP PDF briefing document for the flight plan.
    """
    key = id_or_code.strip()
    plan = (
        db.query(FlightPlan)
        .filter((FlightPlan.id == key) | (FlightPlan.plan_code == key.upper()))
        .first()
    )
    if not plan:
        raise HTTPException(status_code=404, detail=f"Flight plan '{id_or_code}' not found.")

    dep = db.query(Airport).filter(Airport.ident == plan.departure_ident).first()
    dest = db.query(Airport).filter(Airport.ident == plan.destination_ident).first()
    ac = db.query(AircraftProfile).filter(AircraftProfile.id == plan.aircraft_profile_id).first()

    perf_model = AircraftPerformanceModel(
        identifier=ac.identifier if ac else "A320",
        name=ac.name if ac else "Airbus A320-200",
        cruise_speed_kts=ac.cruise_speed_kts if ac else 450.0,
        fuel_flow_kg_hr=ac.fuel_flow_kg_hr if ac else 2400.0,
        category=ac.category if ac else "Jet Airliner",
    )
    perf_est = perf_model.calculate(plan.total_distance_nm)

    waypoints_raw = json.loads(plan.route_waypoints_json) if plan.route_waypoints_json else []

    briefing_payload = {
        "plan_code": plan.plan_code,
        "title": plan.title,
        "departure": {
            "ident": dep.ident if dep else plan.departure_ident,
            "icao": dep.icao if dep else None,
            "iata": dep.iata if dep else None,
            "name": dep.name if dep else "Unknown Departure",
            "municipality": dep.municipality if dep else "",
            "iso_country": dep.iso_country if dep else "",
            "elevation_ft": dep.elevation_ft if dep else 0,
        },
        "destination": {
            "ident": dest.ident if dest else plan.destination_ident,
            "icao": dest.icao if dest else None,
            "iata": dest.iata if dest else None,
            "name": dest.name if dest else "Unknown Destination",
            "municipality": dest.municipality if dest else "",
            "iso_country": dest.iso_country if dest else "",
            "elevation_ft": dest.elevation_ft if dest else 0,
        },
        "aircraft": {
            "identifier": ac.identifier if ac else "A320",
            "name": ac.name if ac else "Airbus A320-200",
            "category": ac.category if ac else "Jet Airliner",
            "cruise_speed_kts": ac.cruise_speed_kts if ac else 450.0,
            "fuel_flow_kg_hr": ac.fuel_flow_kg_hr if ac else 2400.0,
        },
        "cruise_altitude_ft": plan.cruise_altitude_ft,
        "routing_objective": plan.routing_objective,
        "total_distance_nm": plan.total_distance_nm,
        "estimated_flight_time_min": plan.estimated_flight_time_min,
        "estimated_fuel_burn_kg": plan.estimated_fuel_burn_kg,
        "performance": perf_est.to_dict(),
        "waypoints": waypoints_raw,
        "calculation_assumptions": plan.calculation_assumptions,
    }

    pdf_bytes = generate_flight_briefing_pdf(briefing_payload, branding_title=settings.APP_NAME)
    filename = f"briefing_{plan.plan_code}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
