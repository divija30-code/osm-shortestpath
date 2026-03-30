"""
src/visualize.py
----------------
Render the shortest path and explored nodes on an interactive folium map.
"""

from __future__ import annotations

import os
from pathlib import Path

import folium

from src.algorithms import astar, bidirectional, dijkstra
from src.graph_loader import fetch_and_cache


def _get_color(algo: str) -> str:
    return {
        "dijkstra": "blue",
        "astar": "red",
        "bidirectional": "purple"
    }.get(algo, "black")


def render_path_map(
    place: str,
    source: int,
    target: int,
    weight: str = "length",
    data_dir: str = "data",
    results_dir: str = "results"
) -> None:
    """
    Run all three algorithms on (source -> target) and render an interactive
    HTML map with toggleable layers for each algorithm's path and explored nodes.
    """
    print(f"\n--- Visualizing: {place} ({source} -> {target}) ---")

    graph, rev_graph, coords = fetch_and_cache(place, weight=weight, data_dir=data_dir)

    print("Running Dijkstra...")
    res_dij = dijkstra.run(graph, coords, source, target)
    print("Running A*...")
    res_ast = astar.run(graph, coords, source, target, weight_type=weight)
    print("Running Bidirectional Dijkstra...")
    res_bid = bidirectional.run(graph, rev_graph, source, target)

    if not res_dij.path:
        print("[Error] No path found between these nodes!")
        return

    # Initialize map centered around the source node
    m = folium.Map(location=[coords[source][0], coords[source][1]], zoom_start=14)

    # Add markers for Source and Target
    folium.Marker(
        location=[coords[source][0], coords[source][1]],
        popup=f"Source: {source}",
        icon=folium.Icon(color="green", icon="play")
    ).add_to(m)

    folium.Marker(
        location=[coords[target][0], coords[target][1]],
        popup=f"Target: {target}",
        icon=folium.Icon(color="red", icon="stop")
    ).add_to(m)

    # Add algorithm layers
    for res in [res_dij, res_ast, res_bid]:
        algo_name = res.algorithm.capitalize()
        color = _get_color(res.algorithm)
        
        # Feature group allows toggling the entire algorithm's visualization at once
        fg = folium.FeatureGroup(name=f"{algo_name} (Cost: {res.cost:.1f}, Nodes Expanded: {res.nodes_expanded})")

        # 1. Shaded explored nodes
        # To avoid massive file sizes for 100k nodes, we can plot a subset or use CircleMarker
        # We will plot all of them but keep them small
        for node in res.explored_nodes:
            folium.CircleMarker(
                location=[coords[node][0], coords[node][1]],
                radius=1.5,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.3,
                weight=0
            ).add_to(fg)

        # 2. Shortest path polyline
        path_coords = [[coords[n][0], coords[n][1]] for n in res.path]
        folium.PolyLine(
            locations=path_coords,
            color="black" if res.algorithm == "dijkstra" else color,  # contrast
            weight=4,
            opacity=0.8,
            tooltip=f"{algo_name} Path"
        ).add_to(fg)

        fg.add_to(m)

    # Add layer control to toggle algorithms
    folium.LayerControl().add_to(m)

    os.makedirs(results_dir, exist_ok=True)
    city_slug = place.lower().replace(",", "").replace(" ", "_")
    output_html = Path(results_dir) / f"map_{city_slug}_{source}_{target}.html"
    
    m.save(output_html)
    print(f"Map saved to: {output_html}")
