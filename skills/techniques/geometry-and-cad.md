# Computational Geometry and CAD

Part of the advanced techniques. The shared rules in `ADVANCED-TECHNIQUES.md` apply to every table in this file; read them first. Tables are read as described there.

## Computational geometry and CAD

For CAD and CAM, GIS, 3D modeling, mesh processing, and geometry kernels. Robustness decides correctness: a rewrite that evaluates the same predicate in a different order can flip an orientation or in-out test on nearly degenerate input and produce different topology. Keep the original predicates, or use exact or adaptive-precision ones, and test degenerate cases (collinear, coincident, touching, zero-area): see "Geometry" in `BEHAVIOR-TRAPS.md`.

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Convex hull found by testing every candidate edge or point | Andrew's monotone chain or Graham scan | Collinear points on the hull, duplicates, and output order and orientation handled as the original does | O(n³) or O(n²) → O(n log n) |
| All intersecting pairs among many line segments | Bentley-Ottmann sweep line | Robust predicates; touching, overlapping, and vertical segments handled as the original does | O(n²) → O((n + k) log n) for k intersections |
| Closest pair of points | Divide and conquer, or a grid with cell size equal to the best distance so far | Ties resolved as the original does | O(n²) → O(n log n), or O(n) expected |
| Many point-in-polygon tests against the same polygon | Precomputed structure: a grid over the polygon's edges, a trapezoidal decomposition, or binary search over a triangle fan for convex polygons | Points on the boundary classified exactly as the original does | O(e) per query for e edges → O(log e), or about O(1) per query with a grid on typical data |
| Ray casting, picking, or collision against many triangles or objects | Bounding volume hierarchy (BVH), built with the surface area heuristic | Exact intersection test still runs on candidates; the nearest-hit rule and tie-breaking match | O(n) per ray → about O(log n) |
| Triangulating a simple polygon by ear clipping | Partition into monotone pieces, then triangulate each | Produces a different valid triangulation: behavior change when callers observe the triangles | O(n²) → O(n log n) |
| Delaunay triangulation by incremental insertion with a linear search for each point's triangle | Randomized incremental insertion with a point-location structure, or divide and conquer | Ties among cocircular points resolved as before, otherwise behavior change | O(n²) → O(n log n) expected |
| Mesh adjacency queries (neighbors of a vertex, faces around an edge) answered by scanning all faces | Half-edge (or winged-edge) structure, or adjacency lists built once | Half-edge needs a manifold mesh; non-manifold meshes need a general adjacency structure | O(F) per query → O(degree) |
| Merging nearby vertices (welding) by comparing every pair | Spatial hash with cell size equal to the tolerance, checking the neighboring cells | Same tolerance rule and same choice of the surviving vertex | O(n²) → O(n) expected |
| Polygon Boolean operations (union, intersection, difference) by testing every edge pair | Sweep-line clipping (Vatti, Martinez-Rueda) | Robust predicates; output orientation and vertex order match, or the difference is approved | O(n·m) → O((n + m + k) log(n + m)) |
| Evaluating Bezier or B-spline curves at many parameter values | De Casteljau or de Boor evaluation, or Horner's method on the power form; forward differencing for evenly spaced steps | Forward differencing accumulates rounding error: behavior change. Changing the evaluation method changes floating-point results | Per point O(d²) → O(d) for degree d; O(1) per step with forward differencing |
| Exact (arbitrary-precision) geometric predicates evaluated on every test | Floating-point filter with an exact fallback (adaptive-precision predicates, as in Shewchuk's) | Results identical to the exact predicate | Exact results at close to floating-point speed |

## References (for verifying claims; not required reading)

- de Berg, Cheong, van Kreveld, and Overmars, *Computational Geometry: Algorithms and Applications*, 3rd ed. (2008).
- Jonathan R. Shewchuk, "Adaptive Precision Floating-Point Arithmetic and Fast Robust Geometric Predicates" (1997).
