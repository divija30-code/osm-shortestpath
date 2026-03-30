"""
algorithms/astar.py
-------------------
A* algorithm with haversine distance heuristic.

Uses a heapq-based lazy-deletion priority queue (no decrease-key).
Terminates as soon as the target node is *settled* (popped from the heap).

Heuristic choice:
If edge weights are pure distance (meters), the haversine formula gives a 
straight-line distance that is guaranteed to be an underestimate (admissible)
on Earth's surface.
If edge weights are travel time (seconds), we divide the haversine distance 
by the maximum possible speed in the network to ensure admissibility.

Complexity: O((V + E) log V) in the worst case, but typically much less 
nodes expand than Dijkstra due to guidance near the target.
"""

from __future__ import annotations

import heapq
import math
import time
import tracemalloc
from math import atan2, cos, radians, sin, sqrt

from . import AlgoResult


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance in meters between two points 
    on the earth (specified in decimal degrees).
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    r = 6371000  # Radius of earth in meters
    return c * r


def run(
    graph: dict,
    coords: dict,
    source: int,
    target: int,
    weight_type: str = "length",
    max_speed_kmh: float = 120.0
) -> AlgoResult:
    """
    Run A* algorithm from *source* to *target*.

    Parameters
    ----------
    graph         : forward adjacency dict  {node: [(neighbor, weight), ...]}
    coords        : node coordinates dict   {node: (lat, lon)}
    source        : source node ID
    target        : target node ID
    weight_type   : "length" or "travel_time" - determines h(n) scaling
    max_speed_kmh : used to scale the heuristic if weight_type is "travel_time"

    Returns
    -------
    AlgoResult  (cost=inf and path=[] if target is unreachable)
    """
    tracemalloc.start()
    t0 = time.perf_counter()

    target_lat, target_lon = coords[target]

    def heuristic(u: int) -> float:
        lat, lon = coords[u]
        dist_m = haversine(lat, lon, target_lat, target_lon)
        if weight_type == "travel_time":
            # Time (seconds) = Distance (meters) / MaxSpeed (meters/second)
            return dist_m / (max_speed_kmh * 1000.0 / 3600.0)
        return dist_m

    # dist[node] = best known tentative distance from source (g-score)
    dist: dict[int, float] = {source: 0.0}
    
    # prev[node] = predecessor on the best known path
    prev: dict[int, int | None] = {source: None}
    
    # Min-heap entries: (f_score, node)  where f(n) = g(n) + h(n)
    heap: list[tuple[float, int]] = [(heuristic(source), source)]

    explored_nodes: set[int] = set()
    nodes_expanded = 0

    while heap:
        f, u = heapq.heappop(heap)

        # Lazy deletion — if we've found a better path to u since this entry was added,
        # we skip it. We use dist[u] (g-score) for this check.
        # Even though heap stores f-score, f(n) ordering ensures that the first time 
        # a node pops out, we've found the true shortest path to it.
        # Since h(n) is constant for node n, comparing f gives same result as comparing g.
        current_g = dist.get(u, math.inf)
        if f > current_g + heuristic(u):
            continue

        explored_nodes.add(u)
        nodes_expanded += 1

        if u == target:
            break

        for v, w in graph.get(u, []):
            tentative_g = current_g + w
            if tentative_g < dist.get(v, math.inf):
                dist[v] = tentative_g
                prev[v] = u
                f_score = tentative_g + heuristic(v)
                heapq.heappush(heap, (f_score, v))

    t1 = time.perf_counter()
    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    cost = dist.get(target, math.inf)
    path = _reconstruct(prev, source, target) if cost < math.inf else []

    return AlgoResult(
        algorithm="astar",
        cost=cost,
        path=path,
        explored_nodes=explored_nodes,
        nodes_expanded=nodes_expanded,
        time_ms=(t1 - t0) * 1000,
        peak_memory_mb=peak_bytes / 1_048_576,
    )


def _reconstruct(prev: dict, source: int, target: int) -> list[int]:
    """Walk backwards through *prev* to reconstruct the path."""
    path: list[int] = []
    node: int | None = target
    while node is not None:
        path.append(node)
        node = prev.get(node)
        if node == source:
            path.append(source)
            break
    path.reverse()
    return path
