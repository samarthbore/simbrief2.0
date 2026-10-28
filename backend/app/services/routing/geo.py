import math
from typing import List, Tuple, Dict

# Earth radius in nautical miles (IUGG mean radius = 6371.0088 km / 1.852 = ~3440.065 nm)
EARTH_RADIUS_NM = 3440.065
EARTH_RADIUS_KM = 6371.009


def haversine_distance_nm(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the Great Circle distance between two points in Nautical Miles using the Haversine formula.
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    # Clamp 'a' to avoid floating point precision domain errors in asin/atan2
    a = min(1.0, max(0.0, a))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    return round(EARTH_RADIUS_NM * c, 2)


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great circle distance in kilometers."""
    return round(haversine_distance_nm(lat1, lon1, lat2, lon2) * 1.852, 2)


def initial_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate initial forward azimuth / bearing from point 1 to point 2 in degrees (0 - 360).
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_lambda = math.radians(lon2 - lon1)

    y = math.sin(delta_lambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)

    theta = math.atan2(y, x)
    bearing_deg = (math.degrees(theta) + 360.0) % 360.0
    return round(bearing_deg, 1)


def intermediate_great_circle_point(
    lat1: float, lon1: float, lat2: float, lon2: float, fraction: float
) -> Tuple[float, float]:
    """
    Compute an intermediate point along the great circle arc between point 1 and point 2.
    `fraction` is between 0.0 (start) and 1.0 (end).
    """
    if fraction <= 0.0:
        return (lat1, lon1)
    if fraction >= 1.0:
        return (lat2, lon2)

    phi1 = math.radians(lat1)
    lam1 = math.radians(lon1)
    phi2 = math.radians(lat2)
    lam2 = math.radians(lon2)

    delta_phi = phi2 - phi1
    delta_lambda = lam2 - lam1

    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    a = min(1.0, max(0.0, a))
    d = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    if d < 1e-9:
        return (lat1, lon1)

    A = math.sin((1.0 - fraction) * d) / math.sin(d)
    B = math.sin(fraction * d) / math.sin(d)

    x = A * math.cos(phi1) * math.cos(lam1) + B * math.cos(phi2) * math.cos(lam2)
    y = A * math.cos(phi1) * math.sin(lam1) + B * math.cos(phi2) * math.sin(lam2)
    z = A * math.sin(phi1) + B * math.sin(phi2)

    inter_phi = math.atan2(z, math.sqrt(x * x + y * y))
    inter_lam = math.atan2(y, x)

    return (
        round(math.degrees(inter_phi), 5),
        round(math.degrees(inter_lam), 5),
    )


def generate_great_circle_waypoints(
    lat1: float, lon1: float, lat2: float, lon2: float, num_intermediate_points: int = 15
) -> List[Dict[str, float]]:
    """
    Generate an array of coordinate points along the great circle path.
    """
    points = [{"latitude": lat1, "longitude": lon1}]
    for i in range(1, num_intermediate_points + 1):
        frac = i / (num_intermediate_points + 1)
        pt_lat, pt_lon = intermediate_great_circle_point(lat1, lon1, lat2, lon2, frac)
        points.append({"latitude": pt_lat, "longitude": pt_lon})
    points.append({"latitude": lat2, "longitude": lon2})
    return points
