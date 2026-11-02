# Spatial Data

Part of the advanced techniques. The shared rules in `ADVANCED-TECHNIQUES.md` apply to every table in this file; read them first. Tables are read as described there.

## Spatial data

Spatial structures return candidates; the original exact geometric test still runs on each candidate, so results stay identical. The order in which results are returned usually changes: if callers observe it, sort the results back into the original order, or treat it as a behavior change. Workload shape decides the choice: dimensionality, object sizes, clustering, and how often objects move.

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Proximity or collision checks between all pairs of objects in 2D or 3D | Uniform grid or spatial hash, cell size near the query radius or typical object size | Objects are similar in size and spread fairly evenly | O(n²) → O(n + k) expected for k candidate pairs; degrades toward O(n²) when objects crowd into few cells |
| Moving objects checked every frame or tick | Rebuild a grid or spatial hash each tick, or sort and sweep along one axis (sort is nearly sorted from the last tick) | — | O(n²) per tick → O(n + k) or O(n log n), often nearly O(n) with insertion sort on nearly sorted input |
| Range, intersection, or containment queries over rectangles or polygons of mixed sizes (maps, GIS, CAD, UI hit testing) | R-tree; bulk-load with Sort-Tile-Recursive when the data is static | Queries use bounding boxes, with the exact test on candidates | O(n) per query → about O(log n + k) on typical data; no worst-case guarantee under heavy overlap |
| Points with uneven density in 2D or 3D | Quadtree (octree in 3D) | Maximum depth or minimum cell size bounded, so duplicate points cannot force unbounded subdivision | Per-query scan → proportional to depth plus output, workload-dependent |
| Nearest-neighbor or range search over points in low dimensions | k-d tree | Low dimensionality (roughly under 10); data mostly static | Build: O(n log n). Query: O(log n) average for well-distributed data, degrading toward O(n) for skewed data or higher dimensions; workload-dependent |
| Nearest neighbor in high dimensions (embeddings, feature vectors) | Exact: a well-vectorized linear scan usually beats trees above roughly 10 to 20 dimensions. Approximate: HNSW graphs, locality-sensitive hashing, product quantization | Approximate methods can miss true neighbors: **always a behavior change**, developer review | Exact scan: constant-factor gains only. Approximate: sublinear queries in practice |

## References (for verifying claims; not required reading)

- Hanan Samet, *Foundations of Multidimensional and Metric Data Structures* (2006).
- de Berg, Cheong, van Kreveld, and Overmars, *Computational Geometry: Algorithms and Applications*, 3rd ed. (2008).
