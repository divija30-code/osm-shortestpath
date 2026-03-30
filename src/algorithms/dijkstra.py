"""
algorithms/dijkstra.py
----------------------
Standard single-source shortest path — Dijkstra's algorithm.

Uses a heapq-based lazy-deletion priority queue (no decrease-key).
Terminates as soon as the target node is *settled* (popped from the heap).

Complexity: O((V + E) log V)
"""

from __future__ import annotations

import heapq
import math
import time
import tracemalloc

from . import AlgoResult


def run(
    graph: dict,
    coords: dict,
    source: int,
    target: int,
) -> AlgoResult:
    """
    Run Dijkstra's algorithm from *source* to *target*.

    Parameters
    ----------
    graph   : forward adjacency dict  {node: [(neighbor, weight), ...]}
    coords  : node coordinates dict   {node: (lat, lon)}   (unused here)
    source  : source node ID
    target  : target node ID

    Returns
    -------
    AlgoResult  (cost=inf and path=[] if target is unreachable)
    """
    tracemalloc.start()
    t0 = time.perf_counter()

    # dist[node] = best known tentative distance from source
    dist: dict[int, float] = {source: 0.0}
    # prev[node] = predecessor on the best known path
    prev: dict[int, int | None] = {source: None}
    # Min-heap entries: (distance, node)
    heap: list[tuple[float, int]] = [(0.0, source)]

    explored_nodes: set[int] = set()
    nodes_expanded = 0

    while heap:
        d, u = heapq.heappop(heap)

        # Lazy deletion — skip stale entries
        if d > dist.get(u, math.inf):
            continue

        explored_nodes.add(u)
        nodes_expanded += 1

        if u == target:
            break

        for v, w in graph.get(u, []):
            nd = d + w
            if nd < dist.get(v, math.inf):
                dist[v] = nd
                prev[v] = u
                heapq.heappush(heap, (nd, v))

    t1 = time.perf_counter()
    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    cost = dist.get(target, math.inf)
    path = _reconstruct(prev, source, target) if cost < math.inf else []

    return AlgoResult(
        algorithm="dijkstra",
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
