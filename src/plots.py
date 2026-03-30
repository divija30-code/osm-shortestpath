"""
src/plots.py
------------
Generate matplotlib charts from benchmark CSV results.
"""

from __future__ import annotations

import os
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def plot_nodes_expanded(csv_file: str | Path, output_dir: str | Path = "results") -> None:
    """Bar chart comparing the average nodes expanded per algorithm."""
    df = pd.read_csv(csv_file)
    
    # Calculate means
    means = df.groupby("algorithm")["nodes_expanded"].mean().reset_index()
    
    # Ensure correct order: dijkstra, astar, bidirectional
    algo_order = ["dijkstra", "astar", "bidirectional"]
    means["algorithm"] = pd.Categorical(means["algorithm"], categories=algo_order, ordered=True)
    means = means.sort_values("algorithm")

    plt.figure(figsize=(8, 6))
    bars = plt.bar(
        means["algorithm"],
        means["nodes_expanded"],
        color=["#1f77b4", "#ff7f0e", "#2ca02c"]
    )
    
    plt.title("Average Nodes Expanded per Algorithm", fontsize=14)
    plt.ylabel("Nodes Expanded", fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Add value labels on top of bars
    for bar in bars:
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width()/2., 
            height,
            f'{int(height):,}',
            ha='center', va='bottom'
        )

    out_path = Path(output_dir) / f"{Path(csv_file).stem}_nodes_expanded.png"
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved plot: {out_path}")


def plot_metrics(csv_file: str | Path, output_dir: str | Path = "results") -> None:
    """Generate multiple performance comparison plots from a benchmark CSV."""
    os.makedirs(output_dir, exist_ok=True)
    plot_nodes_expanded(csv_file, output_dir)
    
    df = pd.read_csv(csv_file)
    algo_order = ["dijkstra", "astar", "bidirectional"]

    # 1. Query Time Plot
    means_time = df.groupby("algorithm")["time_ms"].mean().reindex(algo_order).reset_index()
    plt.figure(figsize=(8, 6))
    bars = plt.bar(
        means_time["algorithm"],
        means_time["time_ms"],
        color=["#1f77b4", "#ff7f0e", "#2ca02c"]
    )
    plt.title("Average Query Time per Algorithm", fontsize=14)
    plt.ylabel("Time (ms)", fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height, f'{height:.1f}', ha='center', va='bottom')
    
    out_path_time = Path(output_dir) / f"{Path(csv_file).stem}_time.png"
    plt.savefig(out_path_time, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved plot: {out_path_time}")

    # 2. Peak Memory Plot
    means_mem = df.groupby("algorithm")["peak_memory_mb"].mean().reindex(algo_order).reset_index()
    plt.figure(figsize=(8, 6))
    bars = plt.bar(
        means_mem["algorithm"],
        means_mem["peak_memory_mb"],
        color=["#1f77b4", "#ff7f0e", "#2ca02c"]
    )
    plt.title("Average Peak Heap Memory per Algorithm", fontsize=14)
    plt.ylabel("Memory (MB)", fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height, f'{height:.2f}', ha='center', va='bottom')
    
    out_path_mem = Path(output_dir) / f"{Path(csv_file).stem}_memory.png"
    plt.savefig(out_path_mem, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved plot: {out_path_mem}")


def plot_scaling_across_cities(benchmark_csvs: list[str|Path], city_sizes: list[int], city_names: list[str], output_dir: str | Path = "results") -> None:
    """
    Line plot: query time vs. approximate node count (graph size) across different cities.
    """
    if not benchmark_csvs:
        return
        
    os.makedirs(output_dir, exist_ok=True)
    algo_order = ["dijkstra", "astar", "bidirectional"]
    colors = {"dijkstra": "#1f77b4", "astar": "#ff7f0e", "bidirectional": "#2ca02c"}
    
    times = {algo: [] for algo in algo_order}
    sizes_sorted = sorted(zip(city_sizes, city_names, benchmark_csvs), key=lambda x: x[0])
    
    valid_sizes = []
    valid_names = []
    
    for size, name, csv_file in sizes_sorted:
        if not os.path.exists(csv_file):
            continue
        df = pd.read_csv(csv_file)
        means = df.groupby("algorithm")["time_ms"].mean()
        for algo in algo_order:
            times[algo].append(means.get(algo, 0.0))
        valid_sizes.append(size)
        valid_names.append(name)
        
    if not valid_sizes:
        print("[Skipping] No valid benchmark CSVs found for scaling plot.")
        return

    plt.figure(figsize=(10, 6))
    for algo in algo_order:
        plt.plot(
            valid_sizes, 
            times[algo], 
            marker='o', 
            linewidth=2, 
            markersize=8,
            color=colors[algo], 
            label=algo.capitalize()
        )
        
    plt.title("Query Time vs. Graph Size", fontsize=14)
    plt.xlabel("Graph Size (Approx. Nodes)", fontsize=12)
    plt.ylabel("Average Time (ms)", fontsize=12)
    plt.xscale('log')
    plt.yscale('log')
    
    # Add city name labels
    for i, txt in enumerate(valid_names):
        plt.annotate(
            txt, 
            (valid_sizes[i], plt.ylim()[0]), 
            textcoords="offset points", 
            xytext=(0,10), 
            ha='center'
        )

    plt.grid(True, which="both", ls="--", alpha=0.5)
    plt.legend(fontsize=11)
    
    out_path = Path(output_dir) / "scaling_time_vs_size.png"
    plt.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved plot: {out_path}")
