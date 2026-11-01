# Machine Learning and AI

Part of the advanced techniques. The shared rules in `ADVANCED-TECHNIQUES.md` apply to every table in this file; read them first. Tables are read as described there.

## Machine learning and AI

For code that prepares data, trains or runs models (classical machine learning, deep learning, large language models), or calls model APIs. The rules apply unchanged, with these points made explicit:

- **Changing the model is not an optimization.** A technique that changes model outputs (quantization, pruning, distillation, approximate attention, lower precision, a different tokenizer or sampling method) changes behavior. Report it with the measured effect on outputs and on the project's quality metrics, and let the developer decide (rule 5). Techniques that compute the same function (KV caching, exact attention kernels, reordering a matrix chain) are optimizations, subject to floating-point rounding: see "Machine learning" in `BEHAVIOR-TRAPS.md`.
- **Find the bottleneck first.** Training and inference are often limited by data loading, host-to-device transfers, synchronization points, or memory, not arithmetic. Profile with the framework's own profiler before choosing a technique (rule 8).
- **Interpreted loops over array elements are a hidden cost.** In Python and other interpreted hosts, an element-by-element loop over arrays or tensors runs orders of magnitude slower than one vectorized library call that does the same work.

### Data and features

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Interpreted loop over array or tensor elements | Vectorized array operations (NumPy-style, the framework's tensor operations) | The same arithmetic in the same order, or the developer accepts reordered floating-point results | Same complexity; often 10 to 100 times faster |
| Pairwise distances computed in a double loop | Matrix form: ‖a − b‖² = ‖a‖² + ‖b‖² − 2a·b, as one matrix multiply | Behavior change in floating point: cancellation can make small distances inaccurate or slightly negative; clamp at zero and compare the results | O(n·m·d) operations either way, run as one optimized matrix multiply; much faster in practice |
| Near-duplicate detection across many documents (training-data deduplication) | MinHash with locality-sensitive hashing | Approximate: can miss or add pairs. **Behavior change**: developer review. Exact duplicates: hash the normalized content instead | O(n²) comparisons → about O(n) expected |
| Exact repeated substrings across a large corpus | Suffix array (see "Strings" in `techniques/strings-and-text.md`) | — | O(n²) or worse → O(n log n) build |
| Categorical feature represented one-hot and multiplied by a weight matrix | Embedding lookup (index the weight row directly) | Same values; identical results | O(V·d) per item → O(d), for vocabulary size V and dimension d |
| Many small, irregular samples padded to the longest in each batch | Bucket samples by length, or pack several samples into one sequence with attention masking | Packing must keep samples from attending to each other; batch composition changes, which is a behavior change in training | Less computation spent on padding |
| Data loading slower than the model step (the device waits) | Prefetching, parallel loader workers, caching decoded samples, binary formats instead of re-parsing text each epoch | Randomness per worker seeded so runs stay reproducible; sample order changes are a behavior change in training | Device utilization up; same results when order is preserved |

### Training

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Product of several matrices, or matrices applied to a vector, multiplied in a fixed order | Choose the multiplication order: matrix chain DP, or simply right-to-left when the chain ends in a vector, (A·B)·v → A·(B·v) | Floating-point results can differ in the last bits (behavior change if exact output matters) | For n×n matrices and a vector: O(n³) → O(n²); in general, the minimum-cost order |
| Gradients of a scalar loss with respect to many parameters computed by perturbing each parameter | Reverse-mode automatic differentiation (backpropagation) | The function is differentiable where evaluated | O(n) evaluations for n parameters → about one forward and one backward pass |
| Host and device synchronizing inside the training loop (reading a scalar loss value, moving a tensor to the CPU, printing or logging device values every step) | Keep values on the device, accumulate on the device, read back every k steps | What is logged and when changes (behavior change if logs are consumed) | Removes a stall per step |
| Many small kernel launches per step | Operator fusion via the framework's compiler or graph mode | Results usually identical or within floating-point rounding; compilation adds startup time | Constant factor; fewer memory round trips |
| Model or batch does not fit in device memory | Gradient checkpointing (recompute activations in the backward pass); gradient accumulation across smaller batches | Only when the current memory use exceeds the device budget at the required model or batch size: it trades time for memory, the exception to rule 2. Gradient accumulation can change results (batch normalization, floating-point summation order) | Activation memory O(L) → about O(√L) for L layers, for about one extra forward pass |
| Training in full precision on hardware with fast low-precision units | Mixed precision with loss scaling | **Behavior change**: numerics differ; compare quality metrics | Several times faster on supporting hardware; less memory |

### Inference and LLM serving

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Autoregressive decoding that recomputes attention over the whole prefix for every new token | Key-value (KV) cache: store each layer's keys and values for past tokens | Same model and inputs; results identical up to floating-point rounding | Per token: O(t²) → O(t) attention work at position t; whole sequence O(n³) → O(n²) |
| Many requests share the same prompt prefix (system prompt, few-shot examples, document) | Prefix caching: reuse the KV cache of a shared prefix, kept in a radix tree keyed by token sequence | Same model, weights, and tokenization; cache bounded with eviction (rule 1) | Prefix computation once instead of per request |
| Attention over long sequences limited by memory traffic | Exact IO-aware attention kernels (tiled, online softmax, such as FlashAttention) | Exact attention; results within floating-point rounding | Same O(n²) compute; O(n) extra memory instead of O(n²); much faster |
| Attention cost too high even with exact kernels | Sliding-window, sparse, or linear attention | **Changes the model**: requires retraining or produces different outputs. Developer decision | O(n²) → O(n·w) or O(n) |
| Requests served one at a time on hardware that is idle between them | Dynamic batching; continuous (iteration-level) batching for generation | Latency per request may rise; results unchanged per request unless batch-dependent numerics apply | Throughput up several times |
| KV cache memory fragmented, limiting batch size | Paged KV cache (fixed-size blocks with a block table) | — | More concurrent sequences in the same memory |
| Decoding latency bound by one token per forward pass of a large model | Speculative decoding with a small draft model | With rejection sampling it preserves the output distribution; greedy outputs stay identical; individual sampled outputs differ for the same seed (behavior change if seeded outputs are compared) | Fewer large-model passes per token |
| Full sort of the vocabulary for top-k or top-p sampling, or beam search | Partial selection (argpartition, heap of size k), then sort only the candidates | Tie order matches the original when it is observable | O(V log V) → O(V + k log k) per step |
| Byte-pair-encoding tokenizer that rescans the whole sequence for the best pair after every merge | Priority queue of candidate pairs over a linked list of tokens | Merge priority and tie order identical, so tokens are identical | O(n²) → O(n log n) per sequence |
| Lower-precision or compressed weights | Quantization (8-bit, 4-bit), pruning, distillation | **Changes the model**: measure quality on the project's evaluation set. Developer decision | Less memory and faster inference |
| Constrained (structured) generation that checks every vocabulary token against a grammar or regular expression at each step | Compile the grammar or expression into an automaton once, and precompute for each automaton state the set of allowed tokens (a token mask) | Same grammar semantics, tokenization, and handling of tokens that span grammar boundaries | O(V · check) per step → one mask lookup per step, plus O(V) to apply it |
| Retrieval (for example, retrieval-augmented generation) that scans every document or chunk per query | Inverted index for keyword search (see "Strings" in `techniques/strings-and-text.md`); exact or approximate vector index for embeddings (see "Classical machine learning" and "Spatial data" in `techniques/spatial-data.md`) | Approximate vector search is a behavior change | O(corpus) per query → index lookups |
| Re-embedding or reprocessing unchanged documents on every run | Cache results keyed by a hash of the content plus the model name and version and the preprocessing settings | Same model and preprocessing; bounded storage (rule 1) | Work proportional to changed documents |

### Classical machine learning

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| k-means where most distance computations cannot change any assignment | Elkan's or Hamerly's algorithm (triangle-inequality bounds) | Exact: same assignments as standard Lloyd iterations from the same initialization | Most distance computations skipped |
| k-means on data too large for full passes | Mini-batch k-means | **Behavior change**: different clusters. Developer decision | Each iteration O(b·k·d) instead of O(n·k·d) |
| Decision-tree split search that re-sorts feature values at every node | Pre-sort once and maintain order, or histogram-based splits (bin features once) | Pre-sorting is exact; histogram binning can choose different splits (behavior change) | O(n log n) per node per feature → O(n), or O(n + bins) with histograms |
| k-nearest-neighbor queries by full scan | k-d tree or ball tree in low dimensions; see "Spatial data" in `techniques/spatial-data.md` for high dimensions | Exact when the tree search is exact; ties must be broken as the original does | O(n) per query → about O(log n) on suitable data |
| Similarity search over embeddings (retrieval, recommendations, deduplication) | Exact: one matrix multiply against all vectors, then partial top-k selection. Approximate: HNSW, IVF, or product quantization (see "Spatial data" in `techniques/spatial-data.md`) | Approximate methods can miss true neighbors: **behavior change**, developer review | Exact: same O(n·d), vectorized. Approximate: sublinear queries in practice |

### Calling model APIs

Model API calls are network calls: rule 10 applies.

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| One API call per item in a loop (embeddings, classifications) | Batch endpoints, or bounded concurrency within the provider's rate limits | Errors, retries, and partial failures handled per item as before; ordering of results preserved | Fewer round trips; higher throughput |
| Same request sent repeatedly | Cache responses keyed by every input that affects the output: model name and version, full prompt, parameters, tools, and settings | Cached output must be acceptable as the answer. With sampling (temperature above 0), a cache returns one fixed sample where the original produced a new one each time: **behavior change**. Bounded, with invalidation when the model version changes | API calls avoided |
| Long shared prompt prefix sent with every request | The provider's prompt caching, with the stable prefix placed first | Prompt content unchanged | Lower latency and cost for the cached prefix |

## References (for verifying claims; not required reading)

- Tri Dao et al., "FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness," NeurIPS 2022.
- Woosuk Kwon et al., "Efficient Memory Management for Large Language Model Serving with PagedAttention," SOSP 2023.
- Yaniv Leviathan, Matan Kalman, and Yossi Matias, "Fast Inference from Transformers via Speculative Decoding," ICML 2023.
- Charles Elkan, "Using the Triangle Inequality to Accelerate k-Means," ICML 2003.
