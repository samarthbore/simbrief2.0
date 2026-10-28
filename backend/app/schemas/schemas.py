from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# ---------------- Runway Schemas ----------------
class RunwayBase(BaseModel):
    airport_ident: Optional[str] = None
    length_ft: Optional[float] = None
    width_ft: Optional[float] = None
    surface: Optional[str] = None
    lighted: bool = False
    closed: bool = False
    le_ident: Optional[str] = None
    le_latitude: Optional[float] = None
    le_longitude: Optional[float] = None
    le_elevation_ft: Optional[float] = None
    he_ident: Optional[str] = None
    he_latitude: Optional[float] = None
    he_longitude: Optional[float] = None
    he_elevation_ft: Optional[float] = None


class RunwayResponse(RunwayBase):
    id: str
    model_config = ConfigDict(from_attributes=True)


# ---------------- Airport Schemas ----------------
class AirportSummary(BaseModel):
    id: str
    ident: str
    icao: Optional[str] = None
    iata: Optional[str] = None
    name: str
    airport_type: Optional[str] = None
    latitude: float
    longitude: float
    elevation_ft: Optional[float] = None
    municipality: Optional[str] = None
    iso_country: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class AirportDetail(AirportSummary):
    continent: Optional[str] = None
    iso_region: Optional[str] = None
    scheduled_service: bool = False
    gps_code: Optional[str] = None
    local_code: Optional[str] = None
    home_link: Optional[str] = None
    wikipedia_link: Optional[str] = None
    runways: List[RunwayResponse] = []
    model_config = ConfigDict(from_attributes=True)


class AirportListResponse(BaseModel):
    total: int
    items: List[AirportSummary]


# ---------------- Aircraft Profile Schemas ----------------
class AircraftProfileBase(BaseModel):
    identifier: str
    name: str
    category: str
    cruise_speed_kts: float = Field(..., gt=0)
    fuel_flow_kg_hr: float = Field(..., gt=0)
    climb_rate_fpm: float = 2000.0
    descent_rate_fpm: float = 1500.0
    service_ceiling_ft: int = 39000
    max_range_nm: float = Field(..., gt=0)
    description: Optional[str] = None
    model_source: Optional[str] = "Open Aviation Standard Estimates (Educational)"


class AircraftProfileCreate(AircraftProfileBase):
    pass


class AircraftProfileResponse(AircraftProfileBase):
    id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ---------------- Route Planning Schemas ----------------
class RouteWaypoint(BaseModel):
    id: Optional[str] = None
    ident: str
    name: Optional[str] = None
    node_type: str = "FIX"  # AIRPORT, VOR, NDB, FIX, WAYPOINT
    latitude: float
    longitude: float
    airway: Optional[str] = None
    leg_distance_nm: float = 0.0
    bearing_deg: float = 0.0
    cumulative_distance_nm: float = 0.0


class RoutePlanRequest(BaseModel):
    departure_ident: str
    destination_ident: str
    aircraft_id: Optional[str] = None
    aircraft_profile_ident: Optional[str] = "A320"
    routing_objective: str = "great_circle"  # great_circle, shortest_distance, lowest_time, lowest_fuel
    algorithm: Optional[str] = "A*"  # A*, Dijkstra


class RoutePerformance(BaseModel):
    distance_nm: float
    groundspeed_kts: float
    flight_time_hours: float
    flight_time_minutes: float
    flight_time_formatted: str
    trip_fuel_kg: float
    reserve_fuel_kg: float
    taxi_fuel_kg: float
    total_fuel_required_kg: float
    fuel_flow_kg_hr: float
    assumptions: str
    limitations: str


class RoutePlanResponse(BaseModel):
    departure: AirportSummary
    destination: AirportSummary
    aircraft: AircraftProfileResponse
    routing_objective: str
    algorithm: str
    total_distance_nm: float
    total_distance_km: float
    estimated_flight_time_min: float
    estimated_fuel_burn_kg: float
    performance: RoutePerformance
    waypoints: List[RouteWaypoint]
    great_circle_path: List[Dict[str, float]]
    visited_nodes_count: int


# ---------------- Flight Plan Persistence Schemas ----------------
class FlightPlanCreate(BaseModel):
    departure_ident: str
    destination_ident: str
    aircraft_id: str
    routing_objective: str = "great_circle"
    cruise_altitude_ft: int = 33000
    title: Optional[str] = None


class FlightPlanRevisionResponse(BaseModel):
    id: str
    revision_number: int
    changes_summary: Optional[str] = None
    route_summary: str
    total_distance_nm: float
    estimated_flight_time_min: float
    estimated_fuel_burn_kg: float
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class FlightPlanResponse(BaseModel):
    id: str
    plan_code: str
    title: Optional[str] = None
    departure_ident: str
    destination_ident: str
    departure: Optional[AirportSummary] = None
    destination: Optional[AirportSummary] = None
    aircraft_profile_id: str
    aircraft_profile: Optional[AircraftProfileResponse] = None
    routing_objective: str
    total_distance_nm: float
    estimated_flight_time_min: float
    estimated_fuel_burn_kg: float
    cruise_altitude_ft: int
    route_waypoints: List[RouteWaypoint]
    calculation_assumptions: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    revisions: List[FlightPlanRevisionResponse] = []
    model_config = ConfigDict(from_attributes=True)


class FlightPlanUpdate(BaseModel):
    title: Optional[str] = None
    aircraft_id: Optional[str] = None
    cruise_altitude_ft: Optional[int] = None
    routing_objective: Optional[str] = None
