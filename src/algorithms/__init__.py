"""
src/algorithms/__init__.py
--------------------------
Shared types used by all three algorithm modules.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AlgoResult:
    """Uniform result object returned by every algorithm."""

    algorithm: str          # "dijkstra" | "astar" | "bidirectional"
    cost: float             # total path cost (meters or seconds)
    path: list[int]         # ordered list of node IDs (source … target)
    explored_nodes: set[int] # set of all node IDs expanded from the heap
    nodes_expanded: int     # nodes popped from the priority queue
    time_ms: float          # wall-clock time in milliseconds
    peak_memory_mb: float   # peak heap memory allocated during the search

    # Convenience
    def __repr__(self) -> str:
        return (
            f"AlgoResult({self.algorithm}, cost={self.cost:.1f}, "
            f"expanded={self.nodes_expanded}, t={self.time_ms:.2f}ms, "
            f"mem={self.peak_memory_mb:.3f}MB)"
        )
