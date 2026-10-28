import pytest
from backend.app.services.performance.models import AircraftPerformanceModel


def test_performance_calculation_a320():
    model = AircraftPerformanceModel(
        identifier="A320",
        name="Airbus A320-200",
        cruise_speed_kts=450.0,
        fuel_flow_kg_hr=2400.0,
        category="Jet Airliner",
        taxi_fuel_kg=200.0,
    )

    # 900 NM route at 450 KTAS should take exactly 2.0 hours
    res = model.calculate(900.0)
    assert res.flight_time_hours == 2.0
    assert res.flight_time_minutes == 120.0
    assert res.trip_fuel_kg == 4800.0  # 2 hours * 2400 kg/hr

    # 45 min reserve = 0.75 hr * 2400 kg/hr = 1800 kg
    assert res.reserve_fuel_kg == 1800.0
    assert res.taxi_fuel_kg == 200.0
    assert res.total_fuel_required_kg == 4800.0 + 1800.0 + 200.0  # 6800 kg

    # Verify assumptions mention zero-wind
    assert "Zero-wind condition assumed" in res.assumptions
    assert "Educational simplified performance model" in res.limitations


def test_performance_zero_distance():
    model = AircraftPerformanceModel("C172", "Cessna 172", 120.0, 35.0)
    res = model.calculate(0.0)
    assert res.flight_time_hours == 0.0
    assert res.trip_fuel_kg == 0.0
    assert res.total_fuel_required_kg > 0.0  # Still requires reserves and taxi fuel


def test_performance_negative_distance_raises_error():
    model = AircraftPerformanceModel("C172", "Cessna 172", 120.0, 35.0)
    with pytest.raises(ValueError):
        model.calculate(-50.0)
