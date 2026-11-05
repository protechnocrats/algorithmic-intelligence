# Computational Geometry and CAD

The shared rules and table conventions in `ADVANCED-TECHNIQUES.md` apply to every table here.

## Computational geometry and CAD

Robustness decides correctness here: keep the original predicates, or use exact or adaptive-precision ones, and test the degenerate cases under "Behavior traps" below. Mesh and CAD files are input like any other: check declared vertex and face counts against the file size and a limit before allocating, and treat NaN or infinite coordinates as the original does ("Algorithmic complexity attacks" in `techniques/hostile-inputs.md`).

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Convex hull found by testing every candidate edge or point | Andrew's monotone chain or Graham scan | Collinear points on the hull, duplicates, fewer than three distinct points, all points collinear, and output order and orientation handled as the original does | O(n³) or O(n²) → O(n log n) |
| All intersecting pairs among many line segments | Bentley-Ottmann sweep line | Robust predicates; touching, overlapping, and vertical segments handled as the original does | O(n²) → O((n + k) log n) for k intersections |
| Closest pair of points | Divide and conquer, or a grid with cell size equal to the best distance so far | Ties resolved as the original does; the grid's expected bound needs the points inserted in random order; stop at distance zero (duplicate points), where a cell size of zero divides by zero | O(n²) → O(n log n), or O(n) expected |
| Many point-in-polygon tests against the same polygon | Precomputed structure: a grid over the polygon's edges, a trapezoidal decomposition, or binary search over a triangle fan for convex polygons | Points on the boundary classified exactly as the original does | O(e) per query for e edges → O(log e), or about O(1) per query with a grid on typical data |
| Ray casting, picking, or collision against many triangles or objects | Bounding volume hierarchy (BVH), built with the surface area heuristic | Exact intersection test still runs on candidates; the nearest-hit rule and tie-breaking match | O(n) per ray → about O(log n) |
| Triangulating a simple polygon by ear clipping | Partition into monotone pieces, then triangulate each | Produces a different valid triangulation, which callers may observe | O(n²) → O(n log n) |
| Delaunay triangulation by incremental insertion with a linear search for each point's triangle | Randomized incremental insertion with a point-location structure, or divide and conquer | Ties among cocircular points resolved as before | O(n²) → O(n log n) expected |
| Mesh adjacency queries (neighbors of a vertex, faces around an edge) answered by scanning all faces | Half-edge (or winged-edge) structure, or adjacency lists built once | Half-edge needs a manifold mesh; non-manifold meshes need a general adjacency structure | O(F) per query → O(degree) |
| Merging nearby vertices (welding) by comparing every pair | Spatial hash with cell size equal to the tolerance, checking the neighboring cells | Same tolerance rule and same choice of the surviving vertex; welding is not transitive (a near b and b near c, but a far from c), so the result depends on processing order, which is kept | O(n²) → O(n) expected |
| Polygon Boolean operations (union, intersection, difference) by testing every edge pair | Sweep-line clipping (Vatti, Martinez-Rueda) | Robust predicates; output orientation and vertex order match, or the difference is approved | O(n·m) → O((n + m + k) log(n + m)) |
| Evaluating Bezier or B-spline curves at many parameter values | Horner's method on the power form, or a Horner-style Bernstein evaluation; forward differencing for evenly spaced steps; de Casteljau or de Boor when numerical stability matters more than speed | Converting to the power form is ill-conditioned at high degree; forward differencing accumulates rounding error; any change of evaluation method changes floating-point results | Per point O(d²) (de Casteljau, de Boor) → O(d) for degree d with Horner; O(d) additions per step with forward differencing (O(1) for a fixed degree such as cubics) |
| Exact (arbitrary-precision) geometric predicates evaluated on every test | Floating-point filter with an exact fallback (adaptive-precision predicates, as in Shewchuk's) | Results identical to the exact predicate for finite inputs that do not overflow or underflow, which Shewchuk's predicates assume | Exact results at close to floating-point speed |

## Behavior traps

Rewrites that look equivalent but are not; check them alongside `BEHAVIOR-TRAPS.md`.

- **Predicate robustness.** Orientation, in-circle, and point-in-polygon tests on nearly degenerate input can flip sign when the same formula is evaluated in a different order or precision, and a flipped test changes topology: a different hull, a missing intersection, an invalid mesh.
- **Tolerances.** Changing an epsilon, where it is applied, or whether a comparison is strict changes which points merge, touch, or intersect.
- **Degenerate input.** Collinear and coincident points, zero-length edges, zero-area faces, self-touching polygons, and NaN or infinite coordinates are where rewrites differ; test them.
- **Orientation and winding.** Output vertex order (clockwise or counterclockwise), face winding, and the starting vertex are observable to callers and renderers.

## References

Sources for the claims in this file are in `references/techniques/geometry-and-cad.md`. Read them only to verify a claim.
