from backend.app.services.briefing.pdf import generate_flight_briefing_pdf


def test_pdf_generation():
    sample_plan = {
        "plan_code": "FP-261028-TEST",
        "title": "JFK to LHR Test Plan",
        "departure": {
            "ident": "KJFK",
            "icao": "KJFK",
            "iata": "JFK",
            "name": "John F Kennedy International Airport",
            "municipality": "New York",
            "iso_country": "US",
            "elevation_ft": 13,
        },
        "destination": {
            "ident": "EGLL",
            "icao": "EGLL",
            "iata": "LHR",
            "name": "London Heathrow Airport",
            "municipality": "London",
            "iso_country": "GB",
            "elevation_ft": 83,
        },
        "aircraft": {
            "identifier": "A320",
            "name": "Airbus A320-200",
            "category": "Jet Airliner",
            "cruise_speed_kts": 450.0,
            "fuel_flow_kg_hr": 2400.0,
        },
        "cruise_altitude_ft": 37000,
        "routing_objective": "great_circle",
        "total_distance_nm": 3000.0,
        "estimated_flight_time_min": 400.0,
        "estimated_fuel_burn_kg": 16000.0,
        "performance": {
            "trip_fuel_kg": 16000.0,
            "reserve_fuel_kg": 1800.0,
            "taxi_fuel_kg": 200.0,
            "total_fuel_required_kg": 18000.0,
            "flight_time_formatted": "6h 40m",
            "assumptions": "Zero-wind educational model",
        },
        "waypoints": [
            {
                "ident": "KJFK",
                "node_type": "AIRPORT",
                "latitude": 40.64,
                "longitude": -73.78,
                "leg_distance_nm": 0.0,
                "bearing_deg": 52.0,
                "cumulative_distance_nm": 0.0,
            },
            {
                "ident": "EGLL",
                "node_type": "AIRPORT",
                "latitude": 51.47,
                "longitude": -0.46,
                "leg_distance_nm": 3000.0,
                "bearing_deg": 52.0,
                "cumulative_distance_nm": 3000.0,
            },
        ],
    }

    pdf_bytes = generate_flight_briefing_pdf(sample_plan, branding_title="Aviation Planner")
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    # PDF magic byte signature
    assert pdf_bytes.startswith(b"%PDF")
