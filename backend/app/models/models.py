from datetime import datetime, timezone
import uuid
from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class DataSource(Base):
    """Metadata tracking external open data sources (e.g. OurAirports, Natural Earth)."""
    __tablename__ = "data_sources"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    url = Column(String(255), nullable=True)
    version = Column(String(50), nullable=True)
    license = Column(String(100), nullable=False)
    attribution = Column(Text, nullable=False)
    retrieved_at = Column(DateTime(timezone=True), default=utcnow)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    import_runs = relationship("DataImportRun", back_populates="data_source", cascade="all, delete-orphan")


class DataImportRun(Base):
    """Tracks batch data import history, counts, errors, and status."""
    __tablename__ = "data_import_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id = Column(String(36), ForeignKey("data_sources.id", ondelete="SET NULL"), nullable=True)
    dataset_name = Column(String(100), nullable=False)
    status = Column(String(20), default="PENDING")  # PENDING, RUNNING, COMPLETED, FAILED
    records_processed = Column(Integer, default=0)
    records_imported = Column(Integer, default=0)
    records_skipped = Column(Integer, default=0)
    records_rejected = Column(Integer, default=0)
    started_at = Column(DateTime(timezone=True), default=utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    log_details = Column(Text, nullable=True)

    data_source = relationship("DataSource", back_populates="import_runs")


class Airport(Base):
    """Worldwide airport information normalized from OurAirports dataset."""
    __tablename__ = "airports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ourairports_id = Column(Integer, nullable=True, index=True)
    ident = Column(String(20), nullable=False, unique=True, index=True)  # Primary unique key in OurAirports
    icao = Column(String(10), nullable=True, index=True)
    iata = Column(String(10), nullable=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    airport_type = Column(String(50), nullable=True)  # large_airport, medium_airport, small_airport, etc.
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    elevation_ft = Column(Float, nullable=True)
    continent = Column(String(10), nullable=True)
    iso_country = Column(String(10), nullable=True, index=True)
    iso_region = Column(String(20), nullable=True)
    municipality = Column(String(150), nullable=True, index=True)
    scheduled_service = Column(Boolean, default=False)
    gps_code = Column(String(20), nullable=True)
    local_code = Column(String(20), nullable=True)
    home_link = Column(String(255), nullable=True)
    wikipedia_link = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    runways = relationship("Runway", back_populates="airport", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_airport_lat_lon", "latitude", "longitude"),
        Index("idx_airport_codes", "icao", "iata", "ident"),
    )


class Runway(Base):
    """Runway geometry, surface, and threshold information for an airport."""
    __tablename__ = "runways"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    airport_id = Column(String(36), ForeignKey("airports.id", ondelete="CASCADE"), nullable=False, index=True)
    airport_ident = Column(String(20), nullable=True)
    length_ft = Column(Float, nullable=True)
    width_ft = Column(Float, nullable=True)
    surface = Column(String(100), nullable=True)
    lighted = Column(Boolean, default=False)
    closed = Column(Boolean, default=False)
    le_ident = Column(String(10), nullable=True)  # Low-end runway identifier (e.g., 09L)
    le_latitude = Column(Float, nullable=True)
    le_longitude = Column(Float, nullable=True)
    le_elevation_ft = Column(Float, nullable=True)
    he_ident = Column(String(10), nullable=True)  # High-end runway identifier (e.g., 27R)
    he_latitude = Column(Float, nullable=True)
    he_longitude = Column(Float, nullable=True)
    he_elevation_ft = Column(Float, nullable=True)

    airport = relationship("Airport", back_populates="runways")


class NavigationPoint(Base):
    """Aviation navigation fixes, waypoints, VORs, NDBs, DMEs."""
    __tablename__ = "navigation_points"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    identifier = Column(String(20), nullable=False, index=True)
    name = Column(String(100), nullable=True)
    point_type = Column(String(20), nullable=False)  # FIX, VOR, NDB, DME, AIRPORT_REF
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    elevation_ft = Column(Float, nullable=True)
    frequency_khz = Column(Float, nullable=True)
    country = Column(String(10), nullable=True)

    __table_args__ = (
        Index("idx_nav_lat_lon", "latitude", "longitude"),
    )


class NavigationEdge(Base):
    """Airway segments or routing connections between navigation points."""
    __tablename__ = "navigation_edges"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    from_point_id = Column(String(36), ForeignKey("navigation_points.id", ondelete="CASCADE"), nullable=False)
    to_point_id = Column(String(36), ForeignKey("navigation_points.id", ondelete="CASCADE"), nullable=False)
    airway_ident = Column(String(20), nullable=True)  # e.g., J101, V1, ATS
    distance_nm = Column(Float, nullable=False)
    base_altitude_ft = Column(Integer, nullable=True)
    top_altitude_ft = Column(Integer, nullable=True)
    is_bidirectional = Column(Boolean, default=True)


class AircraftProfile(Base):
    """Aircraft performance profile with cruise speed and fuel burn parameters."""
    __tablename__ = "aircraft_profiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    identifier = Column(String(20), nullable=False, unique=True, index=True)  # e.g., A320, B738, C172
    name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)  # Jet Airliner, Turboprop, Single-Engine Piston
    cruise_speed_kts = Column(Float, nullable=False)  # True Airspeed / groundspeed assumption in knots
    fuel_flow_kg_hr = Column(Float, nullable=False)  # Fuel burn in kg/hour
    climb_rate_fpm = Column(Float, default=2000.0)
    descent_rate_fpm = Column(Float, default=1500.0)
    service_ceiling_ft = Column(Integer, default=39000)
    max_range_nm = Column(Float, nullable=False)
    empty_weight_kg = Column(Float, nullable=True)
    mtow_kg = Column(Float, nullable=True)
    description = Column(Text, nullable=True)
    model_source = Column(String(200), default="Open Aviation Standard Estimates (Educational)")
    created_at = Column(DateTime(timezone=True), default=utcnow)


class FlightPlan(Base):
    """Saved flight plan entity."""
    __tablename__ = "flight_plans"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    plan_code = Column(String(30), nullable=False, unique=True, index=True)
    title = Column(String(150), nullable=True)
    departure_ident = Column(String(20), nullable=False, index=True)
    destination_ident = Column(String(20), nullable=False, index=True)
    aircraft_profile_id = Column(String(36), ForeignKey("aircraft_profiles.id", ondelete="RESTRICT"), nullable=False)
    routing_objective = Column(String(50), default="great_circle")  # great_circle, shortest_distance, lowest_time, lowest_fuel
    total_distance_nm = Column(Float, nullable=False)
    estimated_flight_time_min = Column(Float, nullable=False)
    estimated_fuel_burn_kg = Column(Float, nullable=False)
    cruise_altitude_ft = Column(Integer, default=33000)
    route_waypoints_json = Column(Text, nullable=False)  # Serialized list of waypoint dicts (lat, lon, ident, etc.)
    calculation_assumptions = Column(Text, nullable=True)
    status = Column(String(20), default="ACTIVE")
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    aircraft_profile = relationship("AircraftProfile")
    revisions = relationship("FlightPlanRevision", back_populates="flight_plan", cascade="all, delete-orphan", order_by="FlightPlanRevision.revision_number.desc()")


class FlightPlanRevision(Base):
    """Audit revision history for a modified flight plan."""
    __tablename__ = "flight_plan_revisions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    flight_plan_id = Column(String(36), ForeignKey("flight_plans.id", ondelete="CASCADE"), nullable=False)
    revision_number = Column(Integer, nullable=False)
    changes_summary = Column(String(255), nullable=True)
    route_summary = Column(Text, nullable=False)
    waypoints_json = Column(Text, nullable=False)
    total_distance_nm = Column(Float, nullable=False)
    estimated_flight_time_min = Column(Float, nullable=False)
    estimated_fuel_burn_kg = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    flight_plan = relationship("FlightPlan", back_populates="revisions")
