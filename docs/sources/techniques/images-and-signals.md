# Sources for `skills/algorithmic-intelligence/references/techniques/images-and-signals.md`

Where each claim in that file comes from, for maintainers and reviewers. Not part of the installed skill.

- Rafael C. Gonzalez and Richard E. Woods, *Digital Image Processing*, 4th ed. (2018).
- Franklin C. Crow, "Summed-Area Tables for Texture Mapping," SIGGRAPH 1984.
- Richard Szeliski, *Computer Vision: Algorithms and Applications*, 2nd ed. (2022).
- T. S. Huang, G. J. Yang, and G. Y. Tang, "A Fast Two-Dimensional Median Filtering Algorithm," *IEEE Transactions on Acoustics, Speech, and Signal Processing* 27(1), 1979; Simon Perreault and Patrick Hébert, "Median Filtering in Constant Time," *IEEE Transactions on Image Processing* 16(9), 2007.
- Marcel van Herk, "A Fast Algorithm for Local Minimum and Maximum Filters on Rectangular and Octagonal Kernels," *Pattern Recognition Letters* 13(7), 1992; Joseph Gil and Michael Werman, "Computing 2-D Min, Median, and Max Filters," *IEEE TPAMI* 15(5), 1993.
- Pedro F. Felzenszwalb and Daniel P. Huttenlocher, "Distance Transforms of Sampled Functions," *Theory of Computing* 8, 2012.
- NVIDIA, *cuFFT Library User's Guide* (docs.nvidia.com/cuda/cufft), accuracy and determinism: results are bitwise reproducible only with the same plan parameters, cuFFT version, and GPU model; half-precision transforms have limited range.
- NVIDIA, *CUDA C Programming Guide* v9.2 (2018), texture object addressing modes (border, clamp, wrap, mirror) and the "Texture Fetching" appendix: linear-filtering weights are stored in 9-bit fixed point with 8 fractional bits.
- IEEE 754-2019, binary16 format: an 11-bit significand, so integers are exact only up to 2048.
- Chris Gregg and Kim Hazelwood, "Where Is the Data? Why You Cannot Debate CPU vs. GPU Performance Without the Answer," ISPASS 2011: host-device transfers decide whether offload pays.
