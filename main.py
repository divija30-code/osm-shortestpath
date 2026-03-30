import argparse
import os
import random
from pathlib import Path

from src import benchmark, visualize, plots
from src.graph_loader import fetch_and_cache

CITIES_DEFAULT = [
    ("Nagercoil, India", 3000),
    ("Coimbatore, India", 25000),
    ("Chennai, India", 120000),
]


def cmd_fetch(args):
    """Download and cache the OSM graph for a city."""
    print(f"Fetching graph for {args.city} (weight={args.weight})...")
    fetch_and_cache(args.city, weight=args.weight, data_dir=args.data_dir)
    print("Done.")


def cmd_bench(args):
    """Run benchmark against a specific city."""
    benchmark.run_benchmark(
        place=args.city,
        n_pairs=args.pairs,
        weight=args.weight,
        data_dir=args.data_dir,
        results_dir=args.results_dir
    )


def cmd_bench_all(args):
    """Run benchmark for all default cities (Nagercoil, Coimbatore, Chennai)."""
    for city, _ in CITIES_DEFAULT:
        if args.include_delhi or city != "Delhi, India":
            benchmark.run_benchmark(
                place=city,
                n_pairs=args.pairs,
                weight=args.weight,
                data_dir=args.data_dir,
                results_dir=args.results_dir
            )


def cmd_visualize(args):
    """Generate a folium map for a single (source -> dst) query."""
    src = args.src
    dst = args.dst
    
    # If src/dst are not provided, we need to pick random valid ones
    if src is None or dst is None:
        print(f"Loading graph to pick random start/end nodes...")
        _, _, coords = fetch_and_cache(args.city, weight=args.weight, data_dir=args.data_dir)
        nodes = list(coords.keys())
        src = random.choice(nodes) if src is None else src
        dst = random.choice(nodes) if dst is None else dst
        print(f"Randomly selected: {src} -> {dst}")
        
    visualize.render_path_map(
        place=args.city,
        source=src,
        target=dst,
        weight=args.weight,
        data_dir=args.data_dir,
        results_dir=args.results_dir
    )


def cmd_report(args):
    """Generate all matplotlib charts from the benchmark CSV files."""
    results_dir = Path(args.results_dir)
    if not results_dir.exists():
        print(f"Results directory '{results_dir}' not found.")
        return
        
    csv_files = list(results_dir.glob("*_benchmark.csv"))
    if not csv_files:
        print(f"No benchmark CSV files found in {results_dir}.")
        return
        
    for csv_file in csv_files:
        print(f"Generating charts for {csv_file.name}...")
        plots.plot_metrics(csv_file, output_dir=results_dir)
        
    # Attempt to plot scaling
    # We map the found CSV files back to their approx sizes
    cities_with_sizes = dict(CITIES_DEFAULT)
    if args.include_delhi:
        cities_with_sizes["Delhi, India"] = 300000

    csv_paths = []
    sizes = []
    names = []
    
    for city, size in cities_with_sizes.items():
        city_slug = city.lower().replace(",", "").replace(" ", "_")
        csv_file = results_dir / f"{city_slug}_benchmark.csv"
        if csv_file.exists():
            csv_paths.append(csv_file)
            sizes.append(size)
            names.append(city)
            
    if len(csv_paths) > 1:
        print("Generating scaling plot across cities...")
        plots.plot_scaling_across_cities(csv_paths, sizes, names, output_dir=results_dir)
        
    print(f"All charts generated in {results_dir}/")


def main():
    parser = argparse.ArgumentParser(description="OSM Shortest Path Benchmarking")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Common options block
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument("--city", type=str, default="Nagercoil, India", help="City name (e.g. 'Chennai, India')")
    parent_parser.add_argument("--weight", type=str, choices=["length", "travel_time"], default="length", help="Edge weight attribute")
    parent_parser.add_argument("--data-dir", type=str, default="data", help="Directory for cached graphs")
    parent_parser.add_argument("--results-dir", type=str, default="results", help="Directory for outputs")
    
    # Subcommand: fetch
    p_fetch = subparsers.add_parser("fetch", parents=[parent_parser], help="Download and cache city graph")
    
    # Subcommand: bench
    p_bench = subparsers.add_parser("bench", parents=[parent_parser], help="Benchmark algorithms on a city")
    p_bench.add_argument("--pairs", type=int, default=100, help="Number of random pairs to test")
    
    # Subcommand: bench-all
    p_benchall = subparsers.add_parser("bench-all", parents=[parent_parser], help="Benchmark default cities")
    p_benchall.add_argument("--pairs", type=int, default=100, help="Number of random pairs to test")
    p_benchall.add_argument("--include-delhi", action="store_true", help="Include Delhi (~300k nodes, careful!)")

    # Subcommand: visualize
    p_vis = subparsers.add_parser("visualize", parents=[parent_parser], help="Generate Folium map for a query")
    p_vis.add_argument("--src", type=int, default=None, help="Source node ID (random if None)")
    p_vis.add_argument("--dst", type=int, default=None, help="Target node ID (random if None)")

    # Subcommand: report
    p_rep = subparsers.add_parser("report", help="Generate all plots from benchmark CSVs")
    p_rep.add_argument("--results-dir", type=str, default="results", help="Directory containing CSVs")
    p_rep.add_argument("--include-delhi", action="store_true", help="Expect Delhi in the charts if available")

    args = parser.parse_args()

    if args.command == "fetch":
        cmd_fetch(args)
    elif args.command == "bench":
        cmd_bench(args)
    elif args.command == "bench-all":
        cmd_bench_all(args)
    elif args.command == "visualize":
        cmd_visualize(args)
    elif args.command == "report":
        cmd_report(args)


if __name__ == "__main__":
    main()
