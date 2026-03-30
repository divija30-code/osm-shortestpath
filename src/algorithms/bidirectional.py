"""
algorithms/bidirectional.py
---------------------------
Bidirectional Dijkstra's algorithm.

Runs two simultaneous Dijkstra searches:
- Forward search from `source`
- Backward search from `target` (on the reversed graph)

Crucially, the algorithm stops when:
  best_known_path_cost <= fwd_dist(u) + bwd_dist(u)
for the newly popped node `u` in either direction.
It is a common mistake to stop as soon as a node is expanded in both
directions. The strict upper-bound check (mu / best_path_cost) guarantees
that we have found the absolute shortest path.

Complexity: O((V + E) log V), but practically often faster than standard 
Dijkstra because it explores two smaller circles/diamonds rather than 
one large one.
"""

from __future__ import annotations

import heapq
import math
import time
import tracemalloc

from . import AlgoResult


def run(
    graph: dict,
    rev_graph: dict,
    source: int,
    target: int,
) -> AlgoResult:
    """
    Run Bidirectional Dijkstra from *source* to *target*.

    Parameters
    ----------
    graph      : forward adjacency dict   {node: [(neighbor, weight), ...]}
    rev_graph  : backward adjacency dict  {node: [(neighbor, weight), ...]}
    source     : source node ID
    target     : target node ID

    Returns
    -------
    AlgoResult
    """
    tracemalloc.start()
    t0 = time.perf_counter()

    if source == target:
        tracemalloc.stop()
        return AlgoResult("bidirectional", 0.0, [source], {source}, 0, (time.perf_counter()-t0)*1000, 0)

    # dist[node]
    dist_fwd: dict[int, float] = {source: 0.0}
    dist_bwd: dict[int, float] = {target: 0.0}

    # prev[node]
    prev_fwd: dict[int, int | None] = {source: None}
    prev_bwd: dict[int, int | None] = {target: None}

    # min-heap
    heap_fwd: list[tuple[float, int]] = [(0.0, source)]
    heap_bwd: list[tuple[float, int]] = [(0.0, target)]
    
    # Track settled nodes in both directions
    settled_fwd = set()
    settled_bwd = set()

    # best known path length mu
    mu = math.inf
    meeting_node = None
    
    nodes_expanded = 0

    while heap_fwd and heap_bwd:
        # peek the minimums
        top_fwd = heap_fwd[0][0]
        top_bwd = heap_bwd[0][0]

        # Termination condition: when the sum of the minimums in both heaps
        # exceeds the best found complete path length, no better path can be found.
        if top_fwd + top_bwd >= mu:
            break

        # Expand the smaller heap (helps balance the search frontiers)
        if len(heap_fwd) <= len(heap_bwd):
            # Forward expansion
            d, u = heapq.heappop(heap_fwd)
            if d > dist_fwd.get(u, math.inf):
                continue
            
            nodes_expanded += 1
            settled_fwd.add(u)

            # Check if this node was already reached by backward search and updates mu
            if u in dist_bwd:
                path_len = d + dist_bwd[u]
                if path_len < mu:
                    mu = path_len
                    meeting_node = u
            
            # Relax edges
            for v, w in graph.get(u, []):
                nd = d + w
                if nd < dist_fwd.get(v, math.inf):
                    dist_fwd[v] = nd
                    prev_fwd[v] = u
                    heapq.heappush(heap_fwd, (nd, v))

        else:
            # Backward expansion
            d, u = heapq.heappop(heap_bwd)
            if d > dist_bwd.get(u, math.inf):
                continue
            
            nodes_expanded += 1
            settled_bwd.add(u)

            # Check if this node was already reached by forward search and updates mu
            if u in dist_fwd:
                path_len = dist_fwd[u] + d
                if path_len < mu:
                    mu = path_len
                    meeting_node = u
            
            # Relax edges
            for v, w in rev_graph.get(u, []):
                nd = d + w
                if nd < dist_bwd.get(v, math.inf):
                    dist_bwd[v] = nd
                    prev_bwd[v] = u
                    heapq.heappush(heap_bwd, (nd, v))

    t1 = time.perf_counter()
    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    if mu == math.inf or meeting_node is None:
        cost = math.inf
        path = []
    else:
        cost = mu
        path = _reconstruct(prev_fwd, prev_bwd, source, target, meeting_node)

    return AlgoResult(
        algorithm="bidirectional",
        cost=cost,
        path=path,
        explored_nodes=settled_fwd | settled_bwd,
        nodes_expanded=nodes_expanded,
        time_ms=(t1 - t0) * 1000,
        peak_memory_mb=peak_bytes / 1_048_576,
    )


def _reconstruct(
    prev_fwd: dict, 
    prev_bwd: dict, 
    source: int, 
    target: int, 
    meeting_node: int
) -> list[int]:
    """
    Reconstruct bidirectional path by walking backwards from meeting_node
    in both prev_fwd and prev_bwd dictionaries.
    """
    # Forward half
    path_fwd: list[int] = []
    node: int | None = meeting_node
    while node is not None:
        path_fwd.append(node)
        node = prev_fwd.get(node)
        if node == source:
            path_fwd.append(source)
            break
    path_fwd.reverse()

    # Backward half
    path_bwd: list[int] = []
    node = prev_bwd.get(meeting_node) # start from previous of meeting_node
    while node is not None:
        path_bwd.append(node)
        node = prev_bwd.get(node)
        if node == target:
            path_bwd.append(target)
            break
            
    return path_fwd + path_bwd
