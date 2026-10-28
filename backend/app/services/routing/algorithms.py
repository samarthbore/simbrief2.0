import heapq
from typing import Dict, List, Optional, Tuple, Any
from backend.app.services.routing.graph import RoutingGraph, RouteNode, RouteEdge
from backend.app.services.routing.geo import haversine_distance_nm, initial_bearing


class UnreachableDestinationError(Exception):
    """Raised when no connected path exists between start and goal."""
    pass


class RoutePathResult:
    def __init__(
        self,
        nodes: List[RouteNode],
        edges: List[RouteEdge],
        total_distance_nm: float,
        algorithm_used: str,
        visited_nodes_count: int,
    ):
        self.nodes = nodes
        self.edges = edges
        self.total_distance_nm = round(total_distance_nm, 2)
        self.algorithm_used = algorithm_used
        self.visited_nodes_count = visited_nodes_count

    def to_dict(self) -> Dict[str, Any]:
        waypoint_list = []
        cumulative_dist = 0.0

        for i, node in enumerate(self.nodes):
            leg_dist = 0.0
            bearing = 0.0
            airway = None

            if i > 0:
                prev_node = self.nodes[i - 1]
                leg_dist = self.edges[i - 1].distance_nm
                airway = self.edges[i - 1].airway_ident
                bearing = initial_bearing(
                    prev_node.latitude, prev_node.longitude, node.latitude, node.longitude
                )
                cumulative_dist += leg_dist

            waypoint_list.append(
                {
                    "id": node.id,
                    "ident": node.identifier,
                    "name": node.name,
                    "node_type": node.node_type,
                    "latitude": node.latitude,
                    "longitude": node.longitude,
                    "airway": airway,
                    "leg_distance_nm": round(leg_dist, 2),
                    "bearing_deg": bearing,
                    "cumulative_distance_nm": round(cumulative_dist, 2),
                }
            )

        return {
            "total_distance_nm": self.total_distance_nm,
            "algorithm": self.algorithm_used,
            "visited_count": self.visited_nodes_count,
            "waypoints": waypoint_list,
        }


def dijkstra_shortest_path(
    graph: RoutingGraph,
    start_id: str,
    goal_id: str,
    cost_metric: str = "distance",
    cruise_speed_kts: float = 450.0,
    fuel_flow_kg_hr: float = 2400.0,
) -> RoutePathResult:
    """
    Computes shortest or lowest cost path using Dijkstra's algorithm.
    Time complexity: O((|V| + |E|) log |V|)
    """
    if start_id not in graph.nodes:
        raise ValueError(f"Start node '{start_id}' not found in routing graph.")
    if goal_id not in graph.nodes:
        raise ValueError(f"Goal node '{goal_id}' not found in routing graph.")

    if start_id == goal_id:
        node = graph.nodes[start_id]
        return RoutePathResult([node], [], 0.0, "Dijkstra", 1)

    # Priority queue: (cost, current_node_id)
    pq: List[Tuple[float, str]] = []
    heapq.heappush(pq, (0.0, start_id))

    distances: Dict[str, float] = {start_id: 0.0}
    predecessors: Dict[str, Tuple[Optional[str], Optional[RouteEdge]]] = {start_id: (None, None)}
    visited = set()

    while pq:
        curr_cost, curr_id = heapq.heappop(pq)

        if curr_id in visited:
            continue
        visited.add(curr_id)

        if curr_id == goal_id:
            break

        for edge in graph.get_neighbors(curr_id):
            neighbor_id = edge.to_node
            if neighbor_id in visited:
                continue

            # Calculate cost weight based on objective
            dist = edge.distance_nm
            if cost_metric == "time":
                # Cost in hours = dist / speed
                weight = dist / max(cruise_speed_kts, 1.0)
            elif cost_metric == "fuel":
                # Cost in kg = (dist / speed) * fuel_flow
                weight = (dist / max(cruise_speed_kts, 1.0)) * fuel_flow_kg_hr
            else:
                # Default: distance in nautical miles
                weight = dist

            new_cost = curr_cost + weight
            if new_cost < distances.get(neighbor_id, float("inf")):
                distances[neighbor_id] = new_cost
                predecessors[neighbor_id] = (curr_id, edge)
                heapq.heappush(pq, (new_cost, neighbor_id))

    if goal_id not in distances:
        raise UnreachableDestinationError(f"No navigable path exists between '{start_id}' and '{goal_id}'.")

    # Reconstruct path
    path_nodes: List[RouteNode] = []
    path_edges: List[RouteEdge] = []
    curr: Optional[str] = goal_id

    while curr is not None:
        path_nodes.append(graph.nodes[curr])
        prev, edge = predecessors[curr]
        if edge is not None:
            path_edges.append(edge)
        curr = prev

    path_nodes.reverse()
    path_edges.reverse()

    total_dist = sum(e.distance_nm for e in path_edges)
    return RoutePathResult(
        nodes=path_nodes,
        edges=path_edges,
        total_distance_nm=total_dist,
        algorithm_used="Dijkstra",
        visited_nodes_count=len(visited),
    )


def a_star_shortest_path(
    graph: RoutingGraph,
    start_id: str,
    goal_id: str,
    cost_metric: str = "distance",
    cruise_speed_kts: float = 450.0,
    fuel_flow_kg_hr: float = 2400.0,
) -> RoutePathResult:
    """
    Computes optimal path using A* search with an admissible Haversine distance heuristic.
    Since great circle distance is the shortest possible surface distance on Earth,
    h(n) <= true_cost(n, goal), ensuring admissibility and optimality.
    """
    if start_id not in graph.nodes:
        raise ValueError(f"Start node '{start_id}' not found in routing graph.")
    if goal_id not in graph.nodes:
        raise ValueError(f"Goal node '{goal_id}' not found in routing graph.")

    if start_id == goal_id:
        node = graph.nodes[start_id]
        return RoutePathResult([node], [], 0.0, "A*", 1)

    goal_node = graph.nodes[goal_id]

    def heuristic(node_id: str) -> float:
        n = graph.nodes[node_id]
        straight_nm = haversine_distance_nm(n.latitude, n.longitude, goal_node.latitude, goal_node.longitude)
        if cost_metric == "time":
            return straight_nm / max(cruise_speed_kts, 1.0)
        elif cost_metric == "fuel":
            return (straight_nm / max(cruise_speed_kts, 1.0)) * fuel_flow_kg_hr
        return straight_nm

    # Priority queue: (f_score, g_score, current_node_id)
    open_set: List[Tuple[float, float, str]] = []
    h_start = heuristic(start_id)
    heapq.heappush(open_set, (h_start, 0.0, start_id))

    g_score: Dict[str, float] = {start_id: 0.0}
    predecessors: Dict[str, Tuple[Optional[str], Optional[RouteEdge]]] = {start_id: (None, None)}
    closed_set = set()

    while open_set:
        f_curr, g_curr, curr_id = heapq.heappop(open_set)

        if curr_id in closed_set:
            continue
        closed_set.add(curr_id)

        if curr_id == goal_id:
            break

        for edge in graph.get_neighbors(curr_id):
            neighbor_id = edge.to_node
            if neighbor_id in closed_set:
                continue

            dist = edge.distance_nm
            if cost_metric == "time":
                weight = dist / max(cruise_speed_kts, 1.0)
            elif cost_metric == "fuel":
                weight = (dist / max(cruise_speed_kts, 1.0)) * fuel_flow_kg_hr
            else:
                weight = dist

            tentative_g = g_curr + weight

            if tentative_g < g_score.get(neighbor_id, float("inf")):
                g_score[neighbor_id] = tentative_g
                h_val = heuristic(neighbor_id)
                f_score = tentative_g + h_val
                predecessors[neighbor_id] = (curr_id, edge)
                heapq.heappush(open_set, (f_score, tentative_g, neighbor_id))

    if goal_id not in g_score:
        raise UnreachableDestinationError(f"No navigable path exists between '{start_id}' and '{goal_id}'.")

    # Reconstruct path
    path_nodes: List[RouteNode] = []
    path_edges: List[RouteEdge] = []
    curr: Optional[str] = goal_id

    while curr is not None:
        path_nodes.append(graph.nodes[curr])
        prev, edge = predecessors[curr]
        if edge is not None:
            path_edges.append(edge)
        curr = prev

    path_nodes.reverse()
    path_edges.reverse()

    total_dist = sum(e.distance_nm for e in path_edges)
    return RoutePathResult(
        nodes=path_nodes,
        edges=path_edges,
        total_distance_nm=total_dist,
        algorithm_used="A*",
        visited_nodes_count=len(closed_set),
    )
