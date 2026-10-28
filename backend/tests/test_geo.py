import pytest
from backend.app.services.routing.geo import (
    haversine_distance_nm,
    haversine_distance_km,
    initial_bearing,
    intermediate_great_circle_point,
    generate_great_circle_waypoints,
)


def test_haversine_distance_known_routes():
    # JFK (40.64, -73.78) to LHR (51.47, -0.46) is approx 2990-3010 NM
    jfk_lat, jfk_lon = 40.639801, -73.7789
    lhr_lat, lhr_lon = 51.4706, -0.461941

    dist_nm = haversine_distance_nm(jfk_lat, jfk_lon, lhr_lat, lhr_lon)
    assert 2980 < dist_nm < 3020

    dist_km = haversine_distance_km(jfk_lat, jfk_lon, lhr_lat, lhr_lon)
    assert dist_km == pytest.approx(dist_nm * 1.852, rel=1e-2)


def test_haversine_zero_distance():
    assert haversine_distance_nm(10.0, 20.0, 10.0, 20.0) == 0.0


def test_initial_bearing():
    # Due North: bearing should be 0 deg
    bearing_n = initial_bearing(0.0, 0.0, 10.0, 0.0)
    assert bearing_n == 0.0

    # Due East on equator: bearing should be 90 deg
    bearing_e = initial_bearing(0.0, 0.0, 0.0, 10.0)
    assert bearing_e == 90.0

    # Due South: bearing should be 180 deg
    bearing_s = initial_bearing(10.0, 0.0, 0.0, 0.0)
    assert bearing_s == 180.0

    # Due West: bearing should be 270 deg
    bearing_w = initial_bearing(0.0, 10.0, 0.0, 0.0)
    assert bearing_w == 270.0


def test_intermediate_great_circle_point():
    lat1, lon1 = 40.0, -74.0
    lat2, lon2 = 50.0, 0.0

    start_pt = intermediate_great_circle_point(lat1, lon1, lat2, lon2, 0.0)
    assert start_pt == (lat1, lon1)

    end_pt = intermediate_great_circle_point(lat1, lon1, lat2, lon2, 1.0)
    assert end_pt == (lat2, lon2)

    mid_lat, mid_lon = intermediate_great_circle_point(lat1, lon1, lat2, lon2, 0.5)
    # On a sphere, the great circle route between NY (40N) and London/Europe (50N)
    # reaches a higher northern vertex (curves northward towards ~51N).
    assert 40.0 < mid_lat <= 55.0
    assert lon1 < mid_lon < lon2


def test_generate_great_circle_waypoints():
    pts = generate_great_circle_waypoints(10.0, 10.0, 20.0, 20.0, num_intermediate_points=5)
    # Total points = 1 (start) + 5 + 1 (end) = 7
    assert len(pts) == 7
    assert pts[0]["latitude"] == 10.0
    assert pts[-1]["latitude"] == 20.0
