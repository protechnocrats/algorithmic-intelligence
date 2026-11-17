# Sources for `skills/algorithmic-intelligence/references/techniques/games-and-simulation.md`

Where each claim in that file comes from, for maintainers and reviewers. Not part of the installed skill.

- Christer Ericson, *Real-Time Collision Detection* (2004); Jason Gregory, *Game Engine Architecture*, 3rd ed. (2018).
- Daniel Harabor and Alban Grastien, "Online Graph Pruning for Pathfinding on Grid Maps," AAAI 2011 (jump point search); Adi Botea, Martin Müller, and Jonathan Schaeffer, "Near Optimal Hierarchical Path-Finding," *Journal of Game Development* 1(1), 2004 (HPA*).
- E. G. Gilbert, D. W. Johnson, and S. S. Keerthi, "A Fast Procedure for Computing the Distance Between Complex Objects in Three-Dimensional Space," *IEEE Journal on Robotics and Automation* 4(2), 1988 (GJK); Ingo Wald, "On Fast Construction of SAH-Based Bounding Volume Hierarchies," IEEE Symposium on Interactive Ray Tracing 2007.
- Donald E. Knuth and Ronald W. Moore, "An Analysis of Alpha-Beta Pruning," *Artificial Intelligence* 6(4), 1975.
- Albert L. Zobrist, "A New Hashing Method with Application for Game Playing" (1970).
- Cameron B. Browne et al., "A Survey of Monte Carlo Tree Search Methods," *IEEE Transactions on Computational Intelligence and AI in Games* 4(1), 2012.
- Ulrich Haar and Sebastian Aaltonen, "GPU-Driven Rendering Pipelines," SIGGRAPH 2015 course *Advances in Real-Time Rendering in Games*: GPU frustum and occlusion culling writing indirect draw arguments.
- Simon Green, "Particle Simulation using CUDA," NVIDIA (2010): particle state and grid kept on the GPU.
- NVIDIA PhysX 5.4.1 API reference, `PxSceneFlag::eENABLE_ENHANCED_DETERMINISM`: the default determinism guarantee (same scene, same insertion order, same time-stepping), and "this feature is not currently supported on GPU." NVIDIA Isaac Lab documentation, "Reproducibility and Determinism": identical results on the same hardware and PhysX version; results can vary across hardware configurations.
- Glenn Fiedler, "Floating Point Determinism," Gaffer On Games (2010): identical floating-point results across machines need the same compiler, architecture, and settings.
