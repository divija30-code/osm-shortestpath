# OSM Shortest Path Benchmarking

Ever wondered what actually happens when you ask Google Maps for directions? Under the hood, it's solving a shortest path problem on a massive graph. This project does exactly that — but instead of a polished product, it's a honest look at how three classic algorithms behave on real map data, with all the messiness that comes with it.

I picked three cities of very different sizes — Nagercoil (~3K nodes), Coimbatore (~25K), and Chennai (~120K) — so I could see not just *whether* the algorithms work, but *how they hold up as things get bigger*.

---

## What's in here

Three shortest path algorithms, all written from scratch in Python:

- **Dijkstra** — the classic. Explores everything equally outward from the source. Doesn't know where the destination is, doesn't care. Finds the right answer, just not always the fastest way.
- **A\*** — Dijkstra but smarter. Uses straight-line distance to the destination as a hint, so it focuses the search in the right direction. Noticeably faster on large cities.
- **Bidirectional Dijkstra** — searches from both ends at once and meets in the middle. The intuition is simple: half the search from each side means roughly half the work overall.

All three are verified to return identical path costs on every test pair. No shortcuts on correctness.

---

## Project layout

```
osm-shortestpath/
├── main.py                  # everything starts here
├── scratch.py               # turn place names into node IDs
├── requirements.txt
└── src/
    ├── graph_loader.py      # downloads OSM data, builds adjacency lists
    ├── benchmark.py         # runs the tests, writes CSVs
    ├── visualize.py         # draws paths on an interactive map
    ├── plots.py             # performance charts
    └── algorithms/
        ├── dijkstra.py
        ├── astar.py
        └── bidirectional.py
```

---

## Getting started

```bash
git clone https://github.com/<your-username>/osm-shortestpath.git
cd osm-shortestpath
pip install -r requirements.txt
```

---

## How to use it

```bash
# Pull the road graph for a city (cached after first run)
python main.py fetch --city "Chennai, India"

# Run a benchmark on one city
python main.py bench --city "Chennai, India" --pairs 100 --weight length

# Benchmark all three cities at once
python main.py bench-all --pairs 100

# See the path drawn on an actual map
python main.py visualize --city "Chennai, India" --src 278131704 --dst 298862346

# Generate the performance charts
python main.py report
```

Don't know the node IDs for a route you care about? Run `scratch.py` — give it place names like "Tambaram, Chennai" and it'll spit out the nearest node ID.

---

## What the map looks like

The visualizer renders an interactive HTML map. Each algorithm gets its own layer you can toggle on and off:

- 🔵 **Blue** — nodes Dijkstra explored
- 🔴 **Red** — nodes A\* explored
- 🟣 **Purple** — nodes Bidirectional explored

The difference in spread between Dijkstra and A\* is immediately obvious on Chennai. Dijkstra floods the whole city; A\* stays focused on the corridor between source and destination.

---

## What I found

The results were pretty much what theory predicts, but it's different seeing it on a real city rather than a textbook graph.

On a small city like Nagercoil, all three algorithms are fast enough that the differences don't matter much. On Chennai, Dijkstra starts expanding tens of thousands of nodes per query while A\* and Bidirectional stay lean. The log-log scaling plot makes this very clear — Dijkstra's curve bends upward much faster.

Memory follows the same pattern. Dijkstra keeps a large priority queue alive for a long time. Bidirectional runs two smaller ones, which in practice ends up comparable or slightly better.

One thing that surprised me: the correctness check flagged real bugs during development. A reversed lat/lon in the A\* heuristic, a subtle path reconstruction error in Bidirectional — both got caught immediately because they produced a cost even slightly different from Dijkstra's. Having a ground truth to check against was genuinely useful, not just a formality.

---

## Messy parts of real-world data

Working with OSM data means dealing with things that toy graphs never throw at you:

- **Disconnected components** — not every node can reach every other node. Nagercoil had more of these than expected. The benchmark skips unreachable pairs automatically.
- **Parallel edges** — OSM sometimes stores two directions of the same road as separate edges, or has duplicate entries. Only the minimum weight edge per pair is kept.
- **Missing speed tags** — most roads in Indian cities don't have `maxspeed` set. A fallback table by road type handles this, but it means travel time estimates are approximate.

---

## Travel time fallbacks

| Road type | Assumed speed |
|-----------|--------------|
| Motorway | 100 km/h |
| Primary | 60 km/h |
| Residential | 30 km/h |
| Living street | 15 km/h |
| Everything else | 30 km/h |

---

## Things I'd do differently / next steps

- Try **Contraction Hierarchies** — this is what production navigation actually uses and it's orders of magnitude faster at scale
- Better travel time modelling with real traffic data (OSRM, GraphHopper)
- A simple web UI where you click two points on a map and see the paths appear
- Test on something bigger — Delhi or a European capital would stress-test the scaling further
- Parallel benchmarking with `multiprocessing` to speed up data collection on large cities

---

## Dependencies

- [osmnx](https://github.com/gboeing/osmnx) — road network data from OpenStreetMap
- [folium](https://python-visualization.github.io/folium/) — interactive maps
- [matplotlib](https://matplotlib.org/) — performance charts
- Python's built-in `heapq` — priority queue for all three algorithms

---

*Built as part of an Algorithms / Design and Analysis of Algorithms course mini project.*  
Author: P Durga Divija Sri Sai 
