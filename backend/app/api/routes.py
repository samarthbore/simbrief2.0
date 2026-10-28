from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.app.core.database import get_db
from backend.app.models.models import Airport, AircraftProfile, NavigationPoint, NavigationEdge
from backend.app.schemas.schemas import (
    RoutePlanRequest,
    RoutePlanResponse,
    RouteWaypoint,
    RoutePerformance,
    AirportSummary,
    AircraftProfileResponse,
)
from backend.app.services.routing.geo import (
    haversine_distance_nm,
    haversine_distance_km,
    initial_bearing,
    generate_great_circle_waypoints,
)
from backend.app.services.routing.graph import RoutingGraph, RouteNode
from backend.app.services.routing.algorithms import (
    dijkstra_shortest_path,
    a_star_shortest_path,
    UnreachableDestinationError,
)
from backend.app.services.performance.models import AircraftPerformanceModel

router = APIRouter()


def find_airport(db: Session, ident_or_code: str) -> Optional[Airport]:
    key = ident_or_code.strip()
    return (
        db.query(Airport)
        .filter(
            or_(
                Airport.id == key,
                Airport.ident == key.upper(),
                Airport.icao == key.upper(),
                Airport.iata == key.upper(),
            )
        )
        .first()
    )


def find_aircraft(db: Session, aircraft_id_or_ident: Optional[str]) -> Optional[AircraftProfile]:
    if not aircraft_id_or_ident:
        return db.query(AircraftProfile).filter(AircraftProfile.identifier == "A320").first()
    key = aircraft_id_or_ident.strip()
    return (
        db.query(AircraftProfile)
        .filter(
            or_(
                AircraftProfile.id == key,
                AircraftProfile.identifier == key.upper(),
            )
        )
        .first()
    )


@router.post("/routes/plan", response_model=RoutePlanResponse)
def plan_route(request: RoutePlanRequest, db: Session = Depends(get_db)):
    """
    Plan a flight route between departure and destination airports.
    Supports Great Circle direct routes as well as airway network graph routing (A* or Dijkstra).
    """
    dep = find_airport(db, request.departure_ident)
    if not dep:
        raise HTTPException(status_code=404, detail=f"Departure airport '{request.departure_ident}' not found.")

    dest = find_airport(db, request.destination_ident)
    if not dest:
        raise HTTPException(status_code=404, detail=f"Destination airport '{request.destination_ident}' not found.")

    if dep.id == dest.id:
        raise HTTPException(status_code=400, detail="Departure and destination airports cannot be identical.")

    ac_ident = request.aircraft_id or request.aircraft_profile_ident or "A320"
    ac = find_aircraft(db, ac_ident)
    if not ac:
        raise HTTPException(status_code=404, detail=f"Aircraft profile '{ac_ident}' not found.")

    perf_model = AircraftPerformanceModel(
        identifier=ac.identifier,
        name=ac.name,
        cruise_speed_kts=ac.cruise_speed_kts,
        fuel_flow_kg_hr=ac.fuel_flow_kg_hr,
        category=ac.category,
    )

    # Compute Great Circle geometry
    direct_dist_nm = haversine_distance_nm(dep.latitude, dep.longitude, dest.latitude, dest.longitude)
    direct_dist_km = haversine_distance_km(dep.latitude, dep.longitude, dest.latitude, dest.longitude)
    bearing = initial_bearing(dep.latitude, dep.longitude, dest.latitude, dest.longitude)
    gc_points = generate_great_circle_waypoints(dep.latitude, dep.longitude, dest.latitude, dest.longitude, 20)

    # Check if network graph routing is requested and graph nodes exist
    routing_obj = request.routing_objective.lower()
    algo_name = (request.algorithm or "A*").strip()

    # If routing objective is graph-based or specific algorithm requested and edges exist
    edges_count = db.query(NavigationEdge).count()
    use_graph_routing = routing_obj != "great_circle" and edges_count > 0

    waypoints: List[RouteWaypoint] = []
    final_dist_nm = direct_dist_nm
    visited_nodes = 2

    if use_graph_routing:
        # Build graph with db navigation points and edges plus start and goal
        graph = RoutingGraph()
        graph.add_node(RouteNode(id=dep.ident, identifier=dep.ident, name=dep.name, latitude=dep.latitude, longitude=dep.longitude, node_type="AIRPORT"))
        graph.add_node(RouteNode(id=dest.ident, identifier=dest.ident, name=dest.name, latitude=dest.latitude, longitude=dest.longitude, node_type="AIRPORT"))

        nav_points = db.query(NavigationPoint).all()
        for p in nav_points:
            graph.add_node(RouteNode(id=p.identifier, identifier=p.identifier, name=p.name or p.identifier, latitude=p.latitude, longitude=p.longitude, node_type=p.point_type))

        # Connect departure to nearest fixes and destination from nearest fixes
        for p in nav_points:
            d_dep = haversine_distance_nm(dep.latitude, dep.longitude, p.latitude, p.longitude)
            if d_dep <= 300.0:  # Within terminal area / 300nm
                graph.add_edge(dep.ident, p.identifier, distance_nm=d_dep, airway_ident="DEP-TRANS")
            d_dest = haversine_distance_nm(p.latitude, p.longitude, dest.latitude, dest.longitude)
            if d_dest <= 300.0:
                graph.add_edge(p.identifier, dest.ident, distance_nm=d_dest, airway_ident="ARR-TRANS")

        edges = db.query(NavigationEdge).all()
        for e in edges:
            p1 = db.query(NavigationPoint).filter(NavigationPoint.id == e.from_point_id).first()
            p2 = db.query(NavigationPoint).filter(NavigationPoint.id == e.to_point_id).first()
            if p1 and p2:
                graph.add_edge(p1.identifier, p2.identifier, distance_nm=e.distance_nm, airway_ident=e.airway_ident, bidirectional=e.is_bidirectional)

        cost_metric = "distance"
        if "time" in routing_obj:
            cost_metric = "time"
        elif "fuel" in routing_obj:
            cost_metric = "fuel"

        try:
            if algo_name == "Dijkstra":
                route_res = dijkstra_shortest_path(graph, dep.ident, dest.ident, cost_metric=cost_metric, cruise_speed_kts=ac.cruise_speed_kts, fuel_flow_kg_hr=ac.fuel_flow_kg_hr)
            else:
                route_res = a_star_shortest_path(graph, dep.ident, dest.ident, cost_metric=cost_metric, cruise_speed_kts=ac.cruise_speed_kts, fuel_flow_kg_hr=ac.fuel_flow_kg_hr)

            res_dict = route_res.to_dict()
            final_dist_nm = res_dict["total_distance_nm"]
            visited_nodes = res_dict["visited_count"]
            algo_name = res_dict["algorithm"]
            waypoints = [RouteWaypoint(**w) for w in res_dict["waypoints"]]
        except UnreachableDestinationError:
            # Fall back to direct great circle if no connected airway route
            algo_name = "Great Circle (Direct)"
            waypoints = [
                RouteWaypoint(
                    ident=dep.ident,
                    name=dep.name,
                    node_type="AIRPORT",
                    latitude=dep.latitude,
                    longitude=dep.longitude,
                    leg_distance_nm=0.0,
                    bearing_deg=bearing,
                    cumulative_distance_nm=0.0,
                ),
                RouteWaypoint(
                    ident=dest.ident,
                    name=dest.name,
                    node_type="AIRPORT",
                    latitude=dest.latitude,
                    longitude=dest.longitude,
                    leg_distance_nm=direct_dist_nm,
                    bearing_deg=bearing,
                    cumulative_distance_nm=direct_dist_nm,
                ),
            ]
    else:
        # Direct Great Circle
        algo_name = "Great Circle (Direct)"
        waypoints = [
            RouteWaypoint(
                ident=dep.ident,
                name=dep.name,
                node_type="AIRPORT",
                latitude=dep.latitude,
                longitude=dep.longitude,
                leg_distance_nm=0.0,
                bearing_deg=bearing,
                cumulative_distance_nm=0.0,
            ),
            RouteWaypoint(
                ident=dest.ident,
                name=dest.name,
                node_type="AIRPORT",
                latitude=dest.latitude,
                longitude=dest.longitude,
                leg_distance_nm=direct_dist_nm,
                bearing_deg=bearing,
                cumulative_distance_nm=direct_dist_nm,
            ),
        ]

    # Calculate aircraft performance
    perf_est = perf_model.calculate(final_dist_nm)

    return RoutePlanResponse(
        departure=AirportSummary.model_validate(dep),
        destination=AirportSummary.model_validate(dest),
        aircraft=AircraftProfileResponse.model_validate(ac),
        routing_objective=routing_obj,
        algorithm=algo_name,
        total_distance_nm=final_dist_nm,
        total_distance_km=round(final_dist_nm * 1.852, 2),
        estimated_flight_time_min=round(perf_est.flight_time_minutes, 1),
        estimated_fuel_burn_kg=round(perf_est.trip_fuel_kg, 1),
        performance=RoutePerformance(**perf_est.to_dict()),
        waypoints=waypoints,
        great_circle_path=gc_points,
        visited_nodes_count=visited_nodes,
    )


@router.post("/routes/compare")
def compare_routing_algorithms(
    departure_ident: str,
    destination_ident: str,
    aircraft_profile_ident: str = "A320",
    db: Session = Depends(get_db),
):
    """
    Compare Dijkstra and A* algorithms for execution time, visited node counts,
    and verify path cost optimality agreement.
    """
    import time
    dep = find_airport(db, departure_ident)
    dest = find_airport(db, destination_ident)
    if not dep or not dest:
        raise HTTPException(status_code=404, detail="One or both airports not found.")

    ac = find_aircraft(db, aircraft_profile_ident)
    if not ac:
        raise HTTPException(status_code=404, detail=f"Aircraft profile '{aircraft_profile_ident}' not found.")

    # Build benchmark test graph with surrounding navigation points
    graph = RoutingGraph()
    graph.add_node(RouteNode(id=dep.ident, identifier=dep.ident, name=dep.name, latitude=dep.latitude, longitude=dep.longitude, node_type="AIRPORT"))
    graph.add_node(RouteNode(id=dest.ident, identifier=dest.ident, name=dest.name, latitude=dest.latitude, longitude=dest.longitude, node_type="AIRPORT"))

    nav_points = db.query(NavigationPoint).limit(100).all()
    for p in nav_points:
        graph.add_node(RouteNode(id=p.identifier, identifier=p.identifier, name=p.name or p.identifier, latitude=p.latitude, longitude=p.longitude, node_type=p.point_type))
        # Add spatial edges
        d_dep = haversine_distance_nm(dep.latitude, dep.longitude, p.latitude, p.longitude)
        if d_dep <= 500.0:
            graph.add_edge(dep.ident, p.identifier, distance_nm=d_dep)
        d_dest = haversine_distance_nm(p.latitude, p.longitude, dest.latitude, dest.longitude)
        if d_dest <= 500.0:
            graph.add_edge(p.identifier, dest.ident, distance_nm=d_dest)

    # Direct edge fallback so destination is always reachable
    direct_nm = haversine_distance_nm(dep.latitude, dep.longitude, dest.latitude, dest.longitude)
    graph.add_edge(dep.ident, dest.ident, distance_nm=direct_nm, airway_ident="DIRECT")

    # Benchmark Dijkstra
    t0 = time.perf_counter()
    res_dijkstra = dijkstra_shortest_path(graph, dep.ident, dest.ident)
    t_dijkstra_ms = (time.perf_counter() - t0) * 1000.0

    # Benchmark A*
    t0 = time.perf_counter()
    res_astar = a_star_shortest_path(graph, dep.ident, dest.ident)
    t_astar_ms = (time.perf_counter() - t0) * 1000.0

    # Verify optimality equivalence
    cost_diff = abs(res_dijkstra.total_distance_nm - res_astar.total_distance_nm)
    is_optimal_match = cost_diff < 0.01

    return {
        "departure": dep.ident,
        "destination": dest.ident,
        "dijkstra": {
            "total_distance_nm": res_dijkstra.total_distance_nm,
            "visited_nodes": res_dijkstra.visited_nodes_count,
            "execution_time_ms": round(t_dijkstra_ms, 3),
        },
        "a_star": {
            "total_distance_nm": res_astar.total_distance_nm,
            "visited_nodes": res_astar.visited_nodes_count,
            "execution_time_ms": round(t_astar_ms, 3),
        },
        "costs_agree": is_optimal_match,
        "difference_nm": round(cost_diff, 4),
        "complexity_note": "Dijkstra explores radially O((V+E)logV); A* uses goal-directed Haversine heuristic h(n) <= true_cost reducing visited nodes count while preserving optimality.",
    }
