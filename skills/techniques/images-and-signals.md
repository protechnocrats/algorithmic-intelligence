# Image, Video, and Signal Processing

Part of the advanced techniques. First read `ADVANCED-TECHNIQUES.md`: its shared rules apply to every table in this file and explain how to read the tables.

## Image, video, and signal processing

For photo editing, image and video pipelines, computer vision, rendering, and audio. N is the number of pixels or samples and k the filter width. Outputs must match the original exactly, including border handling, rounding, clamping to the channel range, color space, and alpha handling: see "Behavior traps" below. Filters that only approximate the original are behavior changes, however close they look.

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Box (mean) filter, or sums over many rectangular windows | Summed-area table (integral image), or running sums along rows and then columns | Integer accumulators wide enough for the largest sum (for example, width × height × 255 for 8-bit channels); in floating point, reordered sums are a behavior change | O(N·k²) → O(N), independent of window size |
| 2D convolution with a separable kernel (Gaussian, box, the components of Sobel) | Two 1D passes: rows, then columns | Kernel is exactly separable; intermediate results kept at full precision, or the rounding difference approved (rounding after the first pass changes 8-bit output) | O(N·k²) → O(N·k) |
| Convolution with a large kernel that is not separable | FFT-based convolution, with padding that reproduces the original border handling | Floating-point results differ: behavior change | O(N·k²) → O(N log N) |
| Gaussian blur with a large radius | Three successive box blurs, or a recursive (IIR) Gaussian filter | **Approximate**: behavior change, developer review | O(N·k) → O(N), independent of radius |
| Median filter with a large window | Sliding histogram (Huang), or constant-time median filtering (Perreault-Hébert) | Integer pixels with a small value range (8-bit); exact | O(N·k² log k) → O(N·k), or O(N) |
| Erosion, dilation, or minimum and maximum over a window | van Herk/Gil-Werman algorithm, or a monotonic deque along rows and then columns | Rectangular (separable) structuring element; exact | O(N·k²) → O(N) |
| Per-pixel point operation on 8-bit or 16-bit channels (gamma, curves, levels, thresholds) | Lookup table with one entry per possible input value, built once | Output depends only on the input value and fixed parameters; exact | Expensive arithmetic (`pow`, `exp`) per pixel → one table read |
| Color transform that depends on all channels together (color grading, color space conversion) | 3D lookup table with interpolation | **Approximate** when interpolated: behavior change; exact only at full resolution | Constant work per pixel |
| Labeling connected regions | Two-pass connected-component labeling with union-find | Same connectivity (4 or 8) and same label numbering, or relabeled to match | Repeated flood fills and rescans → O(N α(N)) |
| Distance from every pixel to the nearest feature pixel | Exact Euclidean distance transform (Felzenszwalb-Huttenlocher) | Exact; chamfer and other approximations are behavior changes | O(N · features) → O(N) |
| The same image processed at several scales (zoom levels, coarse-to-fine search, previews) | Image pyramid or mipmaps built once | Each level uses the same resampling filter as the original | Each scale computed once instead of per use |
| Per-pixel loops that walk memory out of order, or run in interpreted code | Process in memory order, in cache-sized tiles; vectorize with SIMD or the platform's image library | Identical results, including rounding and saturation | Constant factor, often large |
| Video frames reprocessed in full when little changes between them | Process only changed regions (dirty rectangles, exact change masks) | Change detection compares exact pixel values; motion-estimated reuse is a behavior change | Work proportional to the change |
| Audio or signal filtering with a long FIR filter | FFT convolution with overlap-add or overlap-save | Floating-point differences: behavior change | O(n·k) → O(n log k) |

## Behavior traps

Rewrites in this domain that look equivalent but are not. Walk these with `BEHAVIOR-TRAPS.md` for every candidate in this domain, under the same rules.

- **Border handling.** Filters treat pixels outside the image differently (clamp to edge, mirror, wrap, zero). A rewrite, a separable split, or an FFT must reproduce the original's choice at every border.
- **Rounding, clamping, and saturation.** 8-bit and 16-bit channels round and clamp at every stored step. Splitting a filter into passes, fusing passes, or using SIMD saturating arithmetic changes where rounding happens, and therefore the output.
- **Color space and gamma.** Averaging, blending, or resizing in gamma-encoded values gives different results than doing it in linear light. Keep the original's color space for each step.
- **Premultiplied alpha.** Converting between straight and premultiplied alpha, or filtering one as if it were the other, changes edges and transparent pixels.
- **Channel order and layout.** RGBA versus BGRA, planar versus interleaved, and row padding (stride) must be preserved where callers or files observe them.

## References

Sources for the claims in this file are in `references/techniques/images-and-signals.md`. Read them only to verify a claim.
