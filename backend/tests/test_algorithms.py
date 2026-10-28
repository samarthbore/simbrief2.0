import pytest
from backend.app.services.routing.graph import RoutingGraph, RouteNode
from backend.app.services.routing.algorithms import (
    dijkstra_shortest_path,
    a_star_shortest_path,
    UnreachableDestinationError,
)


def create_test_graph() -> RoutingGraph:
    """
    Creates a triangular test graph:
    A (0,0) -> B (0, 10) -> C (0, 20)
    A (0,0) -> D (10, 10) -> C (0, 20)
    Direct path A -> C is not connected directly.
    """
    g = RoutingGraph()
    g.add_node(RouteNode("A", "A", "Node A", 0.0, 0.0))
    g.add_node(RouteNode("B", "B", "Node B", 0.0, 10.0))
    g.add_node(RouteNode("C", "C", "Node C", 0.0, 20.0))
    g.add_node(RouteNode("D", "D", "Node D", 10.0, 10.0))
    g.add_node(RouteNode("ISOLATED", "ISOLATED", "Node Isolated", 50.0, 50.0))

    # Path 1: A -> B -> C (equatorial path, shorter)
    g.add_edge("A", "B", distance_nm=600.0, airway_ident="V1")
    g.add_edge("B", "C", distance_nm=600.0, airway_ident="V1")

    # Path 2: A -> D -> C (detour path, longer)
    g.add_edge("A", "D", distance_nm=850.0, airway_ident="V2")
    g.add_edge("D", "C", distance_nm=850.0, airway_ident="V2")

    return g


def test_dijkstra_finds_optimal_path():
    graph = create_test_graph()
    res = dijkstra_shortest_path(graph, "A", "C")
    assert res.total_distance_nm == 1200.0
    assert [n.id for n in res.nodes] == ["A", "B", "C"]
    assert res.algorithm_used == "Dijkstra"


def test_a_star_finds_optimal_path_and_matches_dijkstra():
    graph = create_test_graph()
    dijkstra_res = dijkstra_shortest_path(graph, "A", "C")
    astar_res = a_star_shortest_path(graph, "A", "C")

    assert astar_res.total_distance_nm == dijkstra_res.total_distance_nm
    assert [n.id for n in astar_res.nodes] == [n.id for n in dijkstra_res.nodes]
    # A* should visit fewer or equal nodes than Dijkstra
    assert astar_res.visited_nodes_count <= dijkstra_res.visited_nodes_count


def test_unreachable_destination_raises_error():
    graph = create_test_graph()
    with pytest.raises(UnreachableDestinationError):
        dijkstra_shortest_path(graph, "A", "ISOLATED")

    with pytest.raises(UnreachableDestinationError):
        a_star_shortest_path(graph, "A", "ISOLATED")


def test_invalid_node_raises_value_error():
    graph = create_test_graph()
    with pytest.raises(ValueError):
        dijkstra_shortest_path(graph, "A", "NON_EXISTENT")
