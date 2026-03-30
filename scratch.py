import osmnx as ox
from src.graph_loader import fetch_and_cache

print("Loading Chennai graph (this might take a minute if not cached)...")
graph, rev_graph, coords = fetch_and_cache("Chennai, India")

# osmnx has a handy function to download the actual Node IDs in the graph
G = ox.load_graphml("data/chennai_india.graphml")

print("Geocoding Alwarthirunagar...")
lat_a, lon_a = ox.geocode("Alwarthirunagar, Chennai, India")
node_a = ox.distance.nearest_nodes(G, X=lon_a, Y=lat_a)

print("Geocoding Tambaram...")
lat_b, lon_b = ox.geocode("Tambaram, Chennai, India")
node_b = ox.distance.nearest_nodes(G, X=lon_b, Y=lat_b)

print(f"\n--- SUCCESS ---")
print(f"Alwarthirunagar Node ID: {node_a}")
print(f"Tambaram Node ID: {node_b}")
print(f"python main.py visualize --city \"Chennai, India\" --src {node_a} --dst {node_b}")
