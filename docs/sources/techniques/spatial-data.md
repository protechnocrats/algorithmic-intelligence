# Sources for `skills/algorithmic-intelligence/references/techniques/spatial-data.md`

Where each claim in that file comes from, for maintainers and reviewers. Not part of the installed skill.

- Hanan Samet, *Foundations of Multidimensional and Metric Data Structures* (2006).
- de Berg, Cheong, van Kreveld, and Overmars, *Computational Geometry: Algorithms and Applications*, 3rd ed. (2008): k-d trees and range searching.
- Antonin Guttman, "R-Trees: A Dynamic Index Structure for Spatial Searching," SIGMOD 1984; Scott T. Leutenegger, Mario A. Lopez, and Jeffrey Edgington, "STR: A Simple and Efficient Algorithm for R-Tree Packing," ICDE 1997.
- Roger Weber, Hans-Jörg Schek, and Stephen Blott, "A Quantitative Analysis and Performance Study for Similarity-Search Methods in High-Dimensional Spaces," VLDB 1998: a linear scan beats tree indexes above roughly 10 to 20 dimensions.
- Yury A. Malkov and Dmitry A. Yashunin, "Efficient and Robust Approximate Nearest Neighbor Search Using Hierarchical Navigable Small World Graphs," *IEEE TPAMI* 42(4), 2020 (HNSW).
- Simon Green, "Particle Simulation using CUDA," NVIDIA (2010): uniform grid built on the GPU by sorting particles by cell index. Christian Lauterbach et al., "Fast BVH Construction on GPUs," *Computer Graphics Forum* 28(2), 2009, and Tero Karras, "Maximizing Parallelism in the Construction of BVHs, Octrees, and k-d Trees," HPG 2012: linear BVH from Morton codes.
- NVIDIA, *CUDA Programming Guide*, "Compute Capabilities" appendix, Table 33: FP32-to-FP64 throughput ratio 64:1 for compute capabilities 8.6, 8.9, and 12.x (32:1 for 7.5), against 2:1 on data-center parts.
