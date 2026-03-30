"""
graph_loader.py
---------------
Fetches OSM road network data via osmnx, converts it into lightweight Python
adjacency lists, and caches/restores the raw graph to disk to avoid repeated
API calls.

Public API
----------
fetch_and_cache(place, network_type, weight, data_dir) -> (graph, rev_graph, coords)
load_cached(place, data_dir)                           -> ox.MultiDiGraph | None
build_adjacency(G, weight)                             -> (graph, rev_graph, coords)
"""

from __future__ import annotations

import os
import math
from collections import defaultdict
from pathlib import Path
from typing import Literal

import osmnx as ox

# Speed fallbacks (km/h) when OSM maxspeed tag is absent, keyed by highway type
_SPEED_FALLBACK: dict[str, float] = {
    "motorway": 100,
    "trunk": 80,
    "primary": 60,
    "secondary": 50,
    "tertiary": 40,
    "residential": 30,
    "living_street": 15,
    "unclassified": 30,
    "service": 20,
}
_DEFAULT_SPEED_KMH = 30.0


def _place_to_filename(place: str) -> str:
    """Convert 'Chennai, India' -> 'chennai_india'."""
    return place.lower().replace(",", "").replace(" ", "_")


def _get_cache_path(place: str, data_dir: str | Path) -> Path:
    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / f"{_place_to_filename(place)}.graphml"


# ---------------------------------------------------------------------------
# OSM fetching / caching
# ---------------------------------------------------------------------------

def load_cached(place: str, data_dir: str | Path = "data") -> ox.MultiDiGraph | None:
    """Return cached MultiDiGraph or None if not cached yet."""
    cache_path = _get_cache_path(place, data_dir)
    if cache_path.exists():
        print(f"[graph_loader] Loading cached graph: {cache_path}")
        return ox.load_graphml(cache_path)
    return None


def fetch_and_cache(
    place: str,
    network_type: str = "drive",
    weight: Literal["length", "travel_time"] = "length",
    data_dir: str | Path = "data",
) -> tuple[dict, dict, dict]:
    """
    Fetch (or load from cache) the OSM graph for *place*, build adjacency
    lists, and return ``(graph, rev_graph, coords)``.

    Parameters
    ----------
    place        : OSM place name, e.g. "Chennai, India"
    network_type : osmnx network type (default "drive")
    weight       : edge attribute to use as cost ("length" or "travel_time")
    data_dir     : directory where .graphml files are cached

    Returns
    -------
    graph      : dict[node_id -> list[(neighbor_id, weight)]]  (forward)
    rev_graph  : dict[node_id -> list[(neighbor_id, weight)]]  (backward)
    coords     : dict[node_id -> (lat, lon)]
    """
    G = load_cached(place, data_dir)
    if G is None:
        print(f"[graph_loader] Downloading OSM graph for '{place}' …")
        try:
            G = ox.graph_from_place(place, network_type=network_type)
        except Exception as e:
            print(f"[graph_loader] 'graph_from_place' failed ({e}). Falling back to a 5km radius around center...")
            # Fallback for places that OSM only tracks as a Point instead of a Polygon
            G = ox.graph_from_address(place, dist=5000, network_type=network_type)
            
        cache_path = _get_cache_path(place, data_dir)
        ox.save_graphml(G, cache_path)
        print(f"[graph_loader] Saved to {cache_path}")

    if weight == "travel_time":
        G = _add_travel_time(G)

    return build_adjacency(G, weight)


# ---------------------------------------------------------------------------
# Travel-time enrichment
# ---------------------------------------------------------------------------

def _add_travel_time(G: ox.MultiDiGraph) -> ox.MultiDiGraph:
    """
    Add a 'travel_time' attribute (seconds) to every edge.
    Uses OSM maxspeed when available; falls back to highway-type defaults.
    """
    for u, v, data in G.edges(data=True):
        length_m = data.get("length", 0.0)

        # Try to parse maxspeed
        maxspeed = data.get("maxspeed")
        speed_kmh = _parse_speed(maxspeed, data.get("highway"))
        data["travel_time"] = (length_m / 1000.0) / speed_kmh * 3600.0  # seconds

    return G


def _parse_speed(maxspeed, highway) -> float:
    """Return speed in km/h from OSM maxspeed tag (may be str/list/None)."""
    if maxspeed is None:
        return _SPEED_FALLBACK.get(highway, _DEFAULT_SPEED_KMH)

    # maxspeed can be a list when multiple values exist for parallel edges
    if isinstance(maxspeed, list):
        maxspeed = maxspeed[0]

    try:
        return float(str(maxspeed).split()[0])
    except (ValueError, AttributeError):
        return _SPEED_FALLBACK.get(highway, _DEFAULT_SPEED_KMH)


# ---------------------------------------------------------------------------
# Adjacency list construction
# ---------------------------------------------------------------------------

def build_adjacency(
    G: ox.MultiDiGraph,
    weight: Literal["length", "travel_time"] = "length",
) -> tuple[dict, dict, dict]:
    """
    Convert an osmnx MultiDiGraph into plain Python dicts.

    For parallel edges between the same (u, v) pair only the *minimum* weight
    edge is kept — this is consistent with how a simple road router behaves.

    Returns
    -------
    graph      : forward adjacency  dict[u -> list[(v, w)]]
    rev_graph  : backward adjacency dict[v -> list[(u, w)]]
    coords     : dict[node_id -> (lat, lon)]
    """
    # Collect best (minimum) edge weight per directed pair
    best: dict[tuple, float] = {}
    for u, v, data in G.edges(data=True):
        w = data.get(weight)
        if w is None:
            # fall back to length if requested weight is missing
            w = data.get("length", 1.0)
        w = float(w)
        if w <= 0:
            w = 1.0  # guard against zero-weight edges
        key = (u, v)
        if key not in best or w < best[key]:
            best[key] = w

    graph: dict = defaultdict(list)
    rev_graph: dict = defaultdict(list)

    for (u, v), w in best.items():
        graph[u].append((v, w))
        rev_graph[v].append((u, w))

    # Node coordinates
    coords: dict = {}
    for node, data in G.nodes(data=True):
        lat = data.get("y")  # osmnx stores lat as 'y'
        lon = data.get("x")  # and lon as 'x'
        if lat is not None and lon is not None:
            coords[node] = (lat, lon)

    print(
        f"[graph_loader] Graph built: {len(coords):,} nodes, "
        f"{sum(len(v) for v in graph.values()):,} directed edges  (weight='{weight}')"
    )
    return dict(graph), dict(rev_graph), coords
