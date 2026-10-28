from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class PerformanceEstimate:
    distance_nm: float
    groundspeed_kts: float
    flight_time_hours: float
    flight_time_minutes: float
    trip_fuel_kg: float
    reserve_fuel_kg: float  # 45 min statutory IFR reserve
    taxi_fuel_kg: float     # Estimated 200 kg for jets, 15 kg for piston
    total_fuel_required_kg: float
    fuel_flow_kg_hr: float
    assumptions: str
    limitations: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "distance_nm": round(self.distance_nm, 1),
            "groundspeed_kts": round(self.groundspeed_kts, 1),
            "flight_time_hours": round(self.flight_time_hours, 2),
            "flight_time_minutes": round(self.flight_time_minutes, 1),
            "flight_time_formatted": f"{int(self.flight_time_minutes // 60)}h {int(self.flight_time_minutes % 60):02d}m",
            "trip_fuel_kg": round(self.trip_fuel_kg, 1),
            "reserve_fuel_kg": round(self.reserve_fuel_kg, 1),
            "taxi_fuel_kg": round(self.taxi_fuel_kg, 1),
            "total_fuel_required_kg": round(self.total_fuel_required_kg, 1),
            "fuel_flow_kg_hr": round(self.fuel_flow_kg_hr, 1),
            "assumptions": self.assumptions,
            "limitations": self.limitations,
        }


class AircraftPerformanceModel:
    """
    Pluggable aircraft performance estimation engine.
    Calculates flight time, block time, trip fuel, reserve fuel, and operational margins.
    """

    def __init__(
        self,
        identifier: str,
        name: str,
        cruise_speed_kts: float,
        fuel_flow_kg_hr: float,
        category: str = "Jet Airliner",
        taxi_fuel_kg: float = 200.0,
    ):
        self.identifier = identifier
        self.name = name
        self.cruise_speed_kts = cruise_speed_kts
        self.fuel_flow_kg_hr = fuel_flow_kg_hr
        self.category = category
        self.taxi_fuel_kg = taxi_fuel_kg

    def calculate(self, distance_nm: float) -> PerformanceEstimate:
        """
        Estimate flight time and fuel consumption for a given nautical mile distance.
        """
        if distance_nm < 0:
            raise ValueError("Distance must be non-negative.")

        # Simplified groundspeed estimate (zero-wind assumption)
        groundspeed_kts = max(self.cruise_speed_kts, 10.0)
        flight_time_hours = distance_nm / groundspeed_kts
        flight_time_minutes = flight_time_hours * 60.0

        trip_fuel_kg = flight_time_hours * self.fuel_flow_kg_hr
        # Standard 45-minute IFR reserve
        reserve_fuel_kg = (45.0 / 60.0) * self.fuel_flow_kg_hr
        taxi_fuel_kg = self.taxi_fuel_kg
        total_fuel_kg = trip_fuel_kg + reserve_fuel_kg + taxi_fuel_kg

        assumptions = (
            f"Zero-wind condition assumed (Groundspeed = True Airspeed = {groundspeed_kts} kts). "
            f"Constant cruise fuel flow of {self.fuel_flow_kg_hr} kg/hr. "
            f"Standard 45-minute IFR reserve ({round(reserve_fuel_kg, 1)} kg) "
            f"and taxi fuel allowance ({round(taxi_fuel_kg, 1)} kg) included."
        )

        limitations = (
            "Educational simplified performance model. Real-world flight dispatch requires "
            "accounting for winds aloft, step climbs, aircraft gross takeoff weight, temperature "
            "deviations (ISA delta), and airport arrival holding patterns."
        )

        return PerformanceEstimate(
            distance_nm=distance_nm,
            groundspeed_kts=groundspeed_kts,
            flight_time_hours=flight_time_hours,
            flight_time_minutes=flight_time_minutes,
            trip_fuel_kg=trip_fuel_kg,
            reserve_fuel_kg=reserve_fuel_kg,
            taxi_fuel_kg=taxi_fuel_kg,
            total_fuel_required_kg=total_fuel_kg,
            fuel_flow_kg_hr=self.fuel_flow_kg_hr,
            assumptions=assumptions,
            limitations=limitations,
        )
