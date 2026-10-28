import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.aviation_data.seed import seed_database


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    seed_database()


@pytest.fixture
def client():
    return TestClient(app)


def test_health_endpoint(client):
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "healthy" in data["database"]


def test_airports_list_and_search(client):
    # Test listing airports
    res = client.get("/api/v1/airports?limit=10")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] > 0
    assert len(data["items"]) <= 10

    # Test search by ICAO code
    res = client.get("/api/v1/airports?query=KJFK")
    assert res.status_code == 200
    data = res.json()
    assert any(a["ident"] == "KJFK" or a["icao"] == "KJFK" for a in data["items"])

    # Test search by city name
    res = client.get("/api/v1/airports?query=London")
    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) > 0


def test_airport_detail_by_id_or_ident(client):
    res = client.get("/api/v1/airports/KJFK")
    assert res.status_code == 200
    data = res.json()
    assert data["ident"] == "KJFK"
    assert data["name"] == "John F Kennedy International Airport"
    assert "runways" in data


def test_airport_not_found(client):
    res = client.get("/api/v1/airports/ZZZZ_UNKNOWN")
    assert res.status_code == 404


def test_aircraft_profiles(client):
    res = client.get("/api/v1/aircraft")
    assert res.status_code == 200
    profiles = res.json()
    assert len(profiles) >= 3
    idents = [p["identifier"] for p in profiles]
    assert "A320" in idents
    assert "B738" in idents


def test_route_plan_great_circle(client):
    payload = {
        "departure_ident": "KJFK",
        "destination_ident": "EGLL",
        "aircraft_profile_ident": "A320",
        "routing_objective": "great_circle",
    }
    res = client.post("/api/v1/routes/plan", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["departure"]["ident"] == "KJFK"
    assert data["destination"]["ident"] == "EGLL"
    assert data["total_distance_nm"] > 2900
    assert data["estimated_flight_time_min"] > 0
    assert data["estimated_fuel_burn_kg"] > 0
    assert len(data["waypoints"]) >= 2
    assert len(data["great_circle_path"]) > 10


def test_route_compare_endpoint(client):
    res = client.post("/api/v1/routes/compare?departure_ident=KJFK&destination_ident=EGLL")
    assert res.status_code == 200
    data = res.json()
    assert "dijkstra" in data
    assert "a_star" in data
    assert data["costs_agree"] is True


def test_flight_plan_lifecycle_and_briefing(client):
    # 1. Create a flight plan
    create_payload = {
        "departure_ident": "KJFK",
        "destination_ident": "EGLL",
        "aircraft_id": "A320",
        "title": "Transatlantic Test Flight",
        "cruise_altitude_ft": 36000,
    }
    res = client.post("/api/v1/flight-plans", json=create_payload)
    assert res.status_code == 201
    plan = res.json()
    plan_id = plan["id"]
    plan_code = plan["plan_code"]
    assert plan["departure_ident"] == "KJFK"
    assert plan["destination_ident"] == "EGLL"
    assert len(plan["revisions"]) == 1

    # 2. Get saved flight plan
    res = client.get(f"/api/v1/flight-plans/{plan_id}")
    assert res.status_code == 200
    assert res.json()["id"] == plan_id

    # 3. Patch flight plan (e.g. altitude change) -> triggers revision 2
    patch_payload = {
        "title": "Updated JFK-LHR Route",
        "cruise_altitude_ft": 38000,
    }
    res = client.patch(f"/api/v1/flight-plans/{plan_id}", json=patch_payload)
    assert res.status_code == 200
    updated_plan = res.json()
    assert updated_plan["title"] == "Updated JFK-LHR Route"
    assert updated_plan["cruise_altitude_ft"] == 38000
    assert len(updated_plan["revisions"]) == 2

    # 4. Check revisions list
    res = client.get(f"/api/v1/flight-plans/{plan_id}/revisions")
    assert res.status_code == 200
    revisions = res.json()
    assert len(revisions) == 2

    # 5. Download PDF briefing
    res = client.get(f"/api/v1/flight-plans/{plan_id}/briefing")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert res.content.startswith(b"%PDF")
