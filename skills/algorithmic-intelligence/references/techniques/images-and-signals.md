# Image, Video, and Signal Processing

The shared rules and table conventions in `ADVANCED-TECHNIQUES.md` apply.

## Image, video, and signal processing

N is the number of pixels or samples and k the filter width. Outputs match the original exactly, borders, rounding, clamping, color space, and alpha included (see "Behavior traps").

File headers declare their own sizes, and a small file can declare 100,000 × 100,000 pixels: compute width × height × channels × bytes per sample with overflow checks and compare it with a limit before allocating any buffer, table, or pyramid. Raising or disabling a decoder's limit (such as Pillow's `MAX_IMAGE_PIXELS`) for speed is a security regression ("When the request itself is risky" in `SKILL.md`).

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Box (mean) filter, or sums over many rectangular windows | Summed-area table (integral image), or running sums along rows and then columns | Integer accumulators wide enough for the largest sum (for example, width × height × 255 for 8-bit channels); in floating point, reordered sums are a behavior change, and subtracting large corner totals loses precision far from the origin | O(N·k²) → O(N), independent of window size |
| 2D convolution with a separable kernel (Gaussian, box, the components of Sobel) | Two 1D passes: rows, then columns | Kernel is exactly separable; intermediate results kept at full precision, or the rounding difference approved (rounding after the first pass changes 8-bit output) | O(N·k²) → O(N·k) |
| Convolution with a large kernel that is not separable | FFT-based convolution, with padding that reproduces the original border handling | Floating-point results differ, a behavior change | O(N·k²) → O(N log N) |
| Gaussian blur with a large radius | Three successive box blurs, or a recursive (IIR) Gaussian filter | Approximate | O(N·k) → O(N), independent of radius |
| Median filter with a large window | Sliding histogram (Huang), or constant-time median filtering (Perreault-Hébert) | Integer pixels with a small value range (8-bit); exact | O(N·k² log k) → O(N·k), or O(N) |
| Erosion, dilation, or minimum and maximum over a window | van Herk/Gil-Werman algorithm, or a monotonic deque along rows and then columns | Rectangular (separable) structuring element; exact | O(N·k²) → O(N) |
| Per-pixel point operation on 8-bit or 16-bit channels (gamma, curves, levels, thresholds) | Lookup table with one entry per possible input value, built once | Output depends only on the input value and fixed parameters; exact | Expensive arithmetic (`pow`, `exp`) per pixel → one table read |
| Color transform that depends on all channels together (color grading, color space conversion) | 3D lookup table with interpolation | Approximate when interpolated; exact only at full resolution | Constant work per pixel |
| Labeling connected regions | Two-pass connected-component labeling with union-find | Same connectivity (4 or 8) and same label numbering, or relabeled to match | Repeated flood fills and rescans → O(N α(N)) |
| Distance from every pixel to the nearest feature pixel | Exact Euclidean distance transform (Felzenszwalb-Huttenlocher) | Exact; chamfer and other approximations are not | O(N · features) → O(N) |
| The same image processed at several scales (zoom levels, coarse-to-fine search, previews) | Image pyramid or mipmaps built once | Each level uses the same resampling filter as the original | Each scale computed once instead of per use |
| Per-pixel loops that walk memory out of order, or run in interpreted code | Process in memory order, in cache-sized tiles; vectorize with SIMD or the platform's image library | Identical rounding and saturation | Constant factor, often large |
| Video frames reprocessed in full when little changes between them | Process only changed regions (dirty rectangles, exact change masks) | Change detection compares exact pixel values; motion-estimated reuse is approximate | Work proportional to the change |
| Audio or signal filtering with a long FIR filter | FFT convolution with overlap-add or overlap-save | Floating-point results differ | O(n·k) → O(n log k) |

## Behavior traps

Rewrites that look equivalent but are not; check them alongside `BEHAVIOR-TRAPS.md`.

- **Border handling.** Filters treat pixels outside the image differently (clamp to edge, mirror, wrap, zero). A rewrite, separable split, or FFT must reproduce it at every border.
- **Rounding, clamping, and saturation.** 8-bit and 16-bit channels round and clamp at every stored step; floating-point images can hold NaN, which minimum, maximum, and median filters order differently depending on the comparison used. Splitting or fusing passes, or SIMD saturating arithmetic, moves where rounding happens and so changes output.
- **Color space and gamma.** Averaging, blending, or resizing gamma-encoded values differs from doing it in linear light; keep the original's color space for each step.
- **Premultiplied alpha.** Converting between straight and premultiplied alpha, or filtering one as if it were the other, changes edges and transparent pixels.
- **Channel order and layout.** RGBA versus BGRA, planar versus interleaved, and row padding (stride) must be preserved where callers or files observe them.
