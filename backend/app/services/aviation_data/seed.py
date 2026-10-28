import os
import logging
from sqlalchemy.orm import Session
from backend.app.core.database import engine, Base, SessionLocal
from backend.app.models.models import (
    AircraftProfile,
    NavigationPoint,
    NavigationEdge,
    Airport,
)
from backend.app.services.aviation_data.importer import OurAirportsImporter
from backend.app.services.routing.geo import haversine_distance_nm

logger = logging.getLogger(__name__)

STANDARD_AIRCRAFT = [
    {
        "identifier": "A320",
        "name": "Airbus A320-200 (CFM56)",
        "category": "Jet Airliner",
        "cruise_speed_kts": 450.0,
        "fuel_flow_kg_hr": 2400.0,
        "climb_rate_fpm": 2500.0,
        "descent_rate_fpm": 1800.0,
        "service_ceiling_ft": 39000,
        "max_range_nm": 3300.0,
        "description": "Standard short-to-medium range twin-engine jet airliner.",
        "model_source": "Open Aircraft Performance Estimates",
    },
    {
        "identifier": "B738",
        "name": "Boeing 737-800",
        "category": "Jet Airliner",
        "cruise_speed_kts": 453.0,
        "fuel_flow_kg_hr": 2450.0,
        "climb_rate_fpm": 2400.0,
        "descent_rate_fpm": 1800.0,
        "service_ceiling_ft": 41000,
        "max_range_nm": 2930.0,
        "description": "Popular narrow-body twinjet airliner with CFM56-7B engines.",
        "model_source": "Open Aircraft Performance Estimates",
    },
    {
        "identifier": "B77W",
        "name": "Boeing 777-300ER",
        "category": "Wide-Body Jet Airliner",
        "cruise_speed_kts": 490.0,
        "fuel_flow_kg_hr": 7400.0,
        "climb_rate_fpm": 2000.0,
        "descent_rate_fpm": 1500.0,
        "service_ceiling_ft": 43100,
        "max_range_nm": 7370.0,
        "description": "Long-range wide-body twin-engine jet airliner powered by GE90-115B.",
        "model_source": "Open Aircraft Performance Estimates",
    },
    {
        "identifier": "AT76",
        "name": "ATR 72-600",
        "category": "Turboprop",
        "cruise_speed_kts": 275.0,
        "fuel_flow_kg_hr": 750.0,
        "climb_rate_fpm": 1400.0,
        "descent_rate_fpm": 1200.0,
        "service_ceiling_ft": 25000,
        "max_range_nm": 825.0,
        "description": "Twin-engine regional turboprop aircraft.",
        "model_source": "Open Aircraft Performance Estimates",
    },
    {
        "identifier": "C172",
        "name": "Cessna 172 Skyhawk",
        "category": "Single-Engine Piston",
        "cruise_speed_kts": 122.0,
        "fuel_flow_kg_hr": 35.0,  # ~10 US gal/hr 100LL
        "climb_rate_fpm": 730.0,
        "descent_rate_fpm": 600.0,
        "service_ceiling_ft": 14000,
        "max_range_nm": 640.0,
        "description": "Four-seat single-engine light general aviation training aircraft.",
        "model_source": "POH Educational Parameters",
    },
]

SAMPLE_NAV_POINTS = [
    # Waypoints around trans-Atlantic / US / European routes for graph testing
    {"identifier": "MERIT", "name": "Merit Waypoint", "point_type": "FIX", "latitude": 41.381, "longitude": -71.558},
    {"identifier": "BOSOX", "name": "Bosox Fix", "point_type": "FIX", "latitude": 42.112, "longitude": -70.125},
    {"identifier": "TOPPS", "name": "Topps Oceanic Gate", "point_type": "FIX", "latitude": 45.340, "longitude": -61.050},
    {"identifier": "DOGAL", "name": "Dogal Shanwick Entry", "point_type": "FIX", "latitude": 53.000, "longitude": -15.000},
    {"identifier": "BEDRA", "name": "Bedra Waypoint", "point_type": "FIX", "latitude": 52.420, "longitude": -5.600},
    {"identifier": "MAY", "name": "Mayfield VOR", "point_type": "VOR", "latitude": 51.018, "longitude": 0.057},
    # Indian Subcontinent route fixes (VABB - VIDP corridor)
    {"identifier": "EXOLU", "name": "Exolu Fix", "point_type": "FIX", "latitude": 20.350, "longitude": 73.500},
    {"identifier": "EPKOS", "name": "Epkos Waypoint", "point_type": "FIX", "latitude": 22.800, "longitude": 74.900},
    {"identifier": "IKABA", "name": "Ikaba Waypoint", "point_type": "FIX", "latitude": 25.400, "longitude": 76.100},
]


def seed_database(db: Optional[Session] = None):
    """
    Ensure tables are created, aircraft profiles seeded, and sample airports ingested.
    """
    Base.metadata.create_all(bind=engine)

    owns_session = False
    if db is None:
        db = SessionLocal()
        owns_session = True

    try:
        # 1. Seed Aircraft
        for ac_data in STANDARD_AIRCRAFT:
            existing = db.query(AircraftProfile).filter(AircraftProfile.identifier == ac_data["identifier"]).first()
            if not existing:
                ac = AircraftProfile(**ac_data)
                db.add(ac)
        db.commit()

        # 2. Seed Navigation Points and Edges
        nav_cache = {}
        for p_data in SAMPLE_NAV_POINTS:
            existing = db.query(NavigationPoint).filter(NavigationPoint.identifier == p_data["identifier"]).first()
            if not existing:
                pt = NavigationPoint(**p_data)
                db.add(pt)
                db.flush()
                nav_cache[p_data["identifier"]] = pt
            else:
                nav_cache[p_data["identifier"]] = existing
        db.commit()

        # Connect consecutive sample nav points with edges
        transatlantic_seq = ["MERIT", "BOSOX", "TOPPS", "DOGAL", "BEDRA", "MAY"]
        for i in range(len(transatlantic_seq) - 1):
            p1_ident = transatlantic_seq[i]
            p2_ident = transatlantic_seq[i + 1]
            p1 = nav_cache.get(p1_ident)
            p2 = nav_cache.get(p2_ident)
            if p1 and p2:
                existing_edge = db.query(NavigationEdge).filter(
                    NavigationEdge.from_point_id == p1.id,
                    NavigationEdge.to_point_id == p2.id,
                ).first()
                if not existing_edge:
                    dist = haversine_distance_nm(p1.latitude, p1.longitude, p2.latitude, p2.longitude)
                    edge = NavigationEdge(
                        from_point_id=p1.id,
                        to_point_id=p2.id,
                        airway_ident="NAT-DEMO",
                        distance_nm=dist,
                        is_bidirectional=True,
                    )
                    db.add(edge)

        india_seq = ["EXOLU", "EPKOS", "IKABA"]
        for i in range(len(india_seq) - 1):
            p1_ident = india_seq[i]
            p2_ident = india_seq[i + 1]
            p1 = nav_cache.get(p1_ident)
            p2 = nav_cache.get(p2_ident)
            if p1 and p2:
                existing_edge = db.query(NavigationEdge).filter(
                    NavigationEdge.from_point_id == p1.id,
                    NavigationEdge.to_point_id == p2.id,
                ).first()
                if not existing_edge:
                    dist = haversine_distance_nm(p1.latitude, p1.longitude, p2.latitude, p2.longitude)
                    edge = NavigationEdge(
                        from_point_id=p1.id,
                        to_point_id=p2.id,
                        airway_ident="W13-DEMO",
                        distance_nm=dist,
                        is_bidirectional=True,
                    )
                    db.add(edge)
        db.commit()

        # 3. Import sample airports and runways if database has few/no airports
        kjfk = db.query(Airport).filter(Airport.ident == "KJFK").first()
        if not kjfk:
            root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
            sample_airports_path = os.path.join(root_dir, "data", "samples", "airports_sample.csv")
            sample_runways_path = os.path.join(root_dir, "data", "samples", "runways_sample.csv")

            importer = OurAirportsImporter(db)
            if os.path.exists(sample_airports_path):
                with open(sample_airports_path, "r", encoding="utf-8") as f:
                    importer.import_airports_csv(f)
            if os.path.exists(sample_runways_path):
                with open(sample_runways_path, "r", encoding="utf-8") as f:
                    importer.import_runways_csv(f)

    finally:
        if owns_session:
            db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Seeding database...")
    seed_database()
    print("Database seeding completed.")
