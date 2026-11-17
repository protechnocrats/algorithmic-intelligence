# Sources for `skills/algorithmic-intelligence/references/techniques/geometry-and-cad.md`

Where each claim in that file comes from, for maintainers and reviewers. Not part of the installed skill.

- de Berg, Cheong, van Kreveld, and Overmars, *Computational Geometry: Algorithms and Applications*, 3rd ed. (2008).
- Jonathan R. Shewchuk, "Adaptive Precision Floating-Point Arithmetic and Fast Robust Geometric Predicates," *Discrete & Computational Geometry* 18(3), 1997.
- Bala R. Vatti, "A Generic Solution to Polygon Clipping," *CACM* 35(7), 1992; Francisco Martínez, Antonio Jesús Rueda, and Francisco Ramón Feito, "A New Algorithm for Computing Boolean Operations on Polygons," *Computers & Geosciences* 35(6), 2009.
- Ingo Wald, "On Fast Construction of SAH-Based Bounding Volume Hierarchies," IEEE Symposium on Interactive Ray Tracing 2007 (the BVH row; also cited in `docs/sources/techniques/games-and-simulation.md`).
- Christian Lauterbach et al., "Fast BVH Construction on GPUs," *Computer Graphics Forum* 28(2), 2009 (linear BVH from Morton codes, compared with SAH builds for quality); Tero Karras, "Maximizing Parallelism in the Construction of BVHs, Octrees, and k-d Trees," HPG 2012.
- Nathan Whitehead and Alex Fit-Florea, "Precision & Performance: Floating Point and IEEE 754 Compliance for NVIDIA GPUs," NVIDIA (2011): fused multiply-add rounds once, so contracted expressions give different results. NVIDIA, *CUDA Programming Guide*, "Compute Capabilities" appendix, Table 33: FP64 at 1/64 of FP32 throughput on many consumer GPUs.
