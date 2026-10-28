from dataclasses import dataclass, field
from typing import Dict, List, Optional
from backend.app.services.routing.geo import haversine_distance_nm


@dataclass
class RouteNode:
    id: str
    identifier: str
    name: str
    latitude: float
    longitude: float
    node_type: str = "FIX"  # AIRPORT, VOR, NDB, FIX, WAYPOINT


@dataclass
class RouteEdge:
    from_node: str
    to_node: str
    distance_nm: float
    airway_ident: Optional[str] = None
    bidirectional: bool = True


class RoutingGraph:
    """
    In-memory graph structure for aviation airway and waypoint routing.
    """

    def __init__(self):
        self.nodes: Dict[str, RouteNode] = {}
        self.adjacency: Dict[str, List[RouteEdge]] = {}

    def add_node(self, node: RouteNode) -> None:
        self.nodes[node.id] = node
        if node.id not in self.adjacency:
            self.adjacency[node.id] = []

    def add_edge(
        self,
        from_id: str,
        to_id: str,
        distance_nm: Optional[float] = None,
        airway_ident: Optional[str] = None,
        bidirectional: bool = True,
    ) -> None:
        if from_id not in self.nodes or to_id not in self.nodes:
            raise ValueError(f"Both nodes ({from_id}, {to_id}) must exist in graph before creating edge.")

        if distance_nm is None:
            n1 = self.nodes[from_id]
            n2 = self.nodes[to_id]
            distance_nm = haversine_distance_nm(n1.latitude, n1.longitude, n2.latitude, n2.longitude)

        edge1 = RouteEdge(
            from_node=from_id,
            to_node=to_id,
            distance_nm=distance_nm,
            airway_ident=airway_ident,
            bidirectional=bidirectional,
        )
        self.adjacency[from_id].append(edge1)

        if bidirectional:
            edge2 = RouteEdge(
                from_node=to_id,
                to_node=from_id,
                distance_nm=distance_nm,
                airway_ident=airway_ident,
                bidirectional=bidirectional,
            )
            self.adjacency[to_id].append(edge2)

    def get_neighbors(self, node_id: str) -> List[RouteEdge]:
        return self.adjacency.get(node_id, [])
