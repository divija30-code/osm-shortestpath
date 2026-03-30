"""
src/benchmark.py
----------------
Benchmarking harness for the three shortest path algorithms.
Runs each algorithm on a set of random source-destination pairs and 
records performance metrics (time, nodes expanded, memory) to a CSV.
"""

from __future__ import annotations

import csv
import math
import os
import random
from pathlib import Path
from typing import Literal

from tqdm import tqdm

from src.algorithms import astar, bidirectional, dijkstra
from src.graph_loader import fetch_and_cache


def run_benchmark(
    place: str,
    n_pairs: int = 100,
    weight: Literal["length", "travel_time"] = "length",
    data_dir: str | Path = "data",
    results_dir: str | Path = "results"
) -> None:
    """
    Run the full benchmark for a given city and save results to CSV.

    Parameters
    ----------
    place       : OSM place name, e.g. "Chennai, India"
    n_pairs     : Number of random source-destination pairs to sample
    weight      : Edge weight to use ("length" or "travel_time")
    data_dir    : Directory for caching OSM graphs
    results_dir : Directory to save the CSV
    """
    print(f"\n--- Benchmarking: {place} ({n_pairs} pairs, weight='{weight}') ---")
    
    # 1. Load Graph
    graph, rev_graph, coords = fetch_and_cache(place, weight=weight, data_dir=data_dir)
    nodes = list(coords.keys())

    # Create results directory if needed
    os.makedirs(results_dir, exist_ok=True)
    city_slug = place.lower().replace(",", "").replace(" ", "_")
    csv_file = Path(results_dir) / f"{city_slug}_benchmark.csv"

    # 2. Open CSV for writing
    with open(csv_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "pair_id", "source", "target", "algorithm", 
            "cost", "nodes_expanded", "time_ms", "peak_memory_mb"
        ])
        
        # 3. Sample pairs and benchmark
        # We need pairs that are actually connected. Rather than doing a full
        # BFS to check components, we'll try random pairs and discard them if 
        # Dijkstra says unreachable, up to n_pairs times.
        
        reached_pairs = 0
        pbar = tqdm(total=n_pairs, desc="Benchmarking")
        
        while reached_pairs < n_pairs:
            src = random.choice(nodes)
            dst = random.choice(nodes)
            
            if src == dst:
                continue

            # Run standard Dijkstra first to verify reachability and get baseline
            res_dijk = dijkstra.run(graph, coords, src, dst)
            if res_dijk.cost == math.inf:
                # Disconnected pair, try another
                continue
                
            # It's reachable! Run A* and Bidirectional
            res_ast = astar.run(graph, coords, src, dst, weight_type=weight)
            res_bid = bidirectional.run(graph, rev_graph, src, dst)

            # Correctness Check
            # Allow small floating point tolerance
            tol = 1e-3
            diff_ast = abs(res_ast.cost - res_dijk.cost)
            diff_bid = abs(res_bid.cost - res_dijk.cost)

            if diff_ast > tol or diff_bid > tol:
                print(f"\n[WARNING] Correctness failure on pair ({src} -> {dst}):")
                print(f"  Dijkstra: {res_dijk.cost}")
                print(f"  A*      : {res_ast.cost}")
                print(f"  Bi-D    : {res_bid.cost}")
                # We won't crash, but it will be flagged in the data since the costs differ

            # Write results
            # pair_id | source | target | algorithm | cost | nodes_exp | time | max_mem
            for res in [res_dijk, res_ast, res_bid]:
                writer.writerow([
                    reached_pairs,
                    src,
                    dst,
                    res.algorithm,
                    res.cost,
                    res.nodes_expanded,
                    res.time_ms,
                    res.peak_memory_mb
                ])
                
            f.flush()
            reached_pairs += 1
            pbar.update(1)

        pbar.close()

    print(f"Saved benchmark results to: {csv_file}")
