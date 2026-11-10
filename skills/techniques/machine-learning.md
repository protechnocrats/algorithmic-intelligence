# Machine Learning and AI

The shared rules and table conventions in `ADVANCED-TECHNIQUES.md` apply.

## Machine learning and AI

For code that prepares data, trains or runs models, or calls model APIs.

- **Changing the model is not an optimization.** Quantization, pruning, distillation, approximate attention, lower precision, and a different tokenizer or sampling method change outputs: report the measured effect on the project's quality metrics and let the developer decide (rule 5). Techniques that compute the same function (KV caching, exact attention kernels, reordering a matrix chain) are optimizations, subject to floating-point rounding.
- **Find the bottleneck first.** Training and inference are often limited by data loading, host-to-device transfers, synchronization points, or memory rather than arithmetic; the framework's own profiler shows which.
- **Loading a model or data file can run code.** Pickle-based formats (`pickle`, `joblib`, `torch.load` without `weights_only=True`, `numpy.load` with `allow_pickle=True`) and `trust_remote_code=True` execute code from the file, so loading one counts as running a command ("Before running a command" in `SKILL.md`). Do not introduce these formats (a cache of decoded samples, a saved model) where anyone else can write the file; safetensors and plain arrays hold data only.
- **Keep request limits.** Sequence length, maximum new tokens, batch size, image size, and items per request bound memory (a KV cache grows with every token); raising one for throughput removes a defense ("Judge by the worst case" in `techniques/hostile-inputs.md`).

### Data and features

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Interpreted loop over array or tensor elements | Vectorized array operations (NumPy-style, the framework's tensor operations) | The same arithmetic in the same order, or the developer accepts reordered floating-point results | Same complexity; often 10 to 100 times faster |
| Pairwise distances computed in a double loop | Matrix form ‖a − b‖² = ‖a‖² + ‖b‖² − 2a·b, as one matrix multiply | Behavior change in floating point: cancellation makes small distances inaccurate or slightly negative, and equal points can get a small nonzero distance; clamp at zero and compare which pairs count as duplicates or ties | Same O(n·m·d), run as one optimized matrix multiply; much faster in practice |
| Near-duplicate detection across many documents (training-data deduplication) | MinHash with locality-sensitive hashing | Approximate: can miss or add pairs (behavior change). For exact duplicates, hash the normalized content instead | O(n²) comparisons → about O(n) expected |
| Exact repeated substrings across a large corpus | Suffix array (see "Strings" in `techniques/strings-and-text.md`) | — | O(n²) or worse → O(n log n) build |
| Categorical feature represented one-hot and multiplied by a weight matrix | Embedding lookup (index the weight row directly) | Identical for finite weights; a non-finite weight anywhere in the matrix (after a diverged step) makes the one-hot multiply NaN (0 × ∞) where the lookup returns a finite row | O(V·d) per item → O(d), for vocabulary size V and dimension d |
| Many small, irregular samples padded to the longest in each batch | Bucket samples by length, or pack several samples into one sequence with attention masking | Packing keeps samples from attending to each other; batch composition changes (a behavior change in training) | Less computation spent on padding |
| Data loading slower than the model step (the device waits) | Prefetching, parallel loader workers, caching decoded samples, binary formats instead of re-parsing text each epoch | Randomness per worker seeded so runs stay reproducible; sample order changes are a behavior change in training | Device utilization up; same results when order is preserved |

### Training

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Product of several matrices, or matrices applied to a vector, multiplied in a fixed order | Choose the multiplication order: matrix chain DP, or right-to-left when the chain ends in a vector, (A·B)·v → A·(B·v) | Floating-point results can differ in the last bits (behavior change if exact output matters) | For n×n matrices and a vector: O(n³) → O(n²); in general, the minimum-cost order |
| Gradients of a scalar loss with respect to many parameters computed by perturbing each parameter | Reverse-mode automatic differentiation (backpropagation) | The function is differentiable where evaluated. Finite differences are approximate and automatic differentiation is exact up to rounding, so the gradients and everything trained from them change: behavior change | O(n) evaluations for n parameters → about one forward and one backward pass |
| Host and device synchronizing inside the training loop (reading a scalar loss value, moving a tensor to the CPU, printing or logging device values every step) | Keep and accumulate values on the device; read back every k steps | What is logged and when changes (behavior change if logs are consumed) | Removes a stall per step |
| Many small kernel launches per step | Operator fusion via the framework's compiler or graph mode | Results usually identical or within floating-point rounding; compilation adds startup time | Constant factor; fewer memory round trips |
| Model or batch does not fit in device memory | Gradient checkpointing (recompute activations in the backward pass); gradient accumulation across smaller batches | Only when memory use exceeds the device budget at the required size: it trades time for memory, the exception to rule 2. Gradient accumulation can change results (batch normalization, summation order) | Activation memory O(L) → about O(√L) for L layers, for about one extra forward pass |
| Training in full precision on hardware with fast low-precision units | Mixed precision with loss scaling | Behavior change: numerics differ; compare quality metrics | Several times faster on supporting hardware; less memory |

### Inference and LLM serving

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Autoregressive decoding that recomputes attention over the whole prefix for every new token | Key-value (KV) cache: store each layer's keys and values for past tokens | Same model and inputs; results identical up to floating-point rounding | Per token: O(t²) → O(t) attention work at position t; whole sequence O(n³) → O(n²) |
| Many requests share the same prompt prefix (system prompt, few-shot examples, document) | Prefix caching: reuse the KV cache of a shared prefix, kept in a radix tree keyed by token sequence | Same model, weights, and tokenization; cache bounded (rule 1). A hit is faster, so timing reveals whether someone else sent the same prefix: share across users or tenants only for non-private prefixes, and key per tenant otherwise | Prefix computation once instead of per request |
| Attention over long sequences limited by memory traffic | Exact IO-aware attention kernels (tiled, online softmax, such as FlashAttention) | Exact attention; results within floating-point rounding | Same O(n²) compute; O(n) extra memory instead of O(n²); much faster |
| Attention cost too high even with exact kernels | Sliding-window, sparse, or linear attention | Changes the model: retraining or different outputs | O(n²) → O(n·w) or O(n) |
| Requests served one at a time on hardware idle between them | Dynamic batching; continuous (iteration-level) batching for generation | Latency per request may rise; results unchanged per request unless batch-dependent numerics apply | Throughput up several times |
| KV cache memory fragmented, limiting batch size | Paged KV cache (fixed-size blocks with a block table) | — | More concurrent sequences in the same memory |
| Decoding latency bound by one token per forward pass of a large model | Speculative decoding with a small draft model | Rejection sampling preserves the output distribution; greedy outputs stay identical up to floating point (batched verification can flip a near-tie); sampled outputs differ for the same seed (behavior change if seeded outputs are compared) | Fewer large-model passes per token |
| Full sort of the vocabulary for top-k or top-p sampling, or beam search | Partial selection (argpartition, heap of size k), then sort only the candidates | Tie order, and the placement of NaN scores, match the original when observable. For top-p the candidate count is not known in advance: select a top-k guess, and fall back to a larger k or a full sort whenever its cumulative probability is below p | O(V log V) → O(V + k log k) per step |
| Byte-pair-encoding tokenizer that rescans the whole sequence for the best pair after every merge | Priority queue of candidate pairs over a linked list of tokens | Merge priority and tie order identical, so tokens are identical | O(n²) → O(n log n) per sequence |
| Lower-precision or compressed weights | Quantization (8-bit, 4-bit), pruning, distillation | Changes the model: measure quality on the project's evaluation set | Less memory and faster inference |
| Constrained (structured) generation that checks every vocabulary token against a grammar or regular expression at each step | Compile the grammar or expression into an automaton once, and precompute an allowed-token mask per automaton state | Same grammar semantics, tokenization, and handling of tokens that span grammar boundaries. Full precomputation works for regular expressions; for context-free grammars the parser stack is unbounded, so precompute only tokens whose validity does not depend on the stack and check the rest per step | O(V · check) per step → one mask lookup per step, plus O(V) to apply it (regular expressions); most of the check removed (context-free grammars) |
| Retrieval (for example, retrieval-augmented generation) that scans every document or chunk per query | Inverted index for keyword search (see "Strings" in `techniques/strings-and-text.md`); exact or approximate vector index for embeddings (see "Classical machine learning" below, and "Spatial data" in `techniques/spatial-data.md`) | Approximate vector search is a behavior change | O(corpus) per query → index lookups |
| Re-embedding or reprocessing unchanged documents on every run | Cache results keyed by a collision-resistant hash (SHA-256, not a short or non-cryptographic hash) of the content plus the model name and version and the preprocessing settings | Same model and preprocessing; bounded storage | Work proportional to changed documents |

### Classical machine learning

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| k-means where most distance computations cannot change any assignment | Elkan's or Hamerly's algorithm (triangle-inequality bounds) | Exact in exact arithmetic from the same initialization, except ties: Lloyd's picks the first minimum, the bounded version keeps the current center, and in floating point near-ties can flip too. Compare assignments; any difference is a behavior change | Most distance computations skipped |
| k-means on data too large for full passes | Mini-batch k-means | Behavior change: different clusters | Each iteration O(b·k·d) instead of O(n·k·d) |
| Decision-tree split search that re-sorts feature values at every node | Pre-sort once and maintain order, or histogram-based splits (bin features once) | Pre-sorting is exact; histogram binning can choose different splits (behavior change) | O(n log n) per node per feature → O(n), or O(n + bins) with histograms |
| k-nearest-neighbor queries by full scan | k-d tree or ball tree in low dimensions; see "Spatial data" in `techniques/spatial-data.md` for high dimensions | Exact when the tree search is exact; ties broken as in the original | O(n) per query → about O(log n) on suitable data |
| Similarity search over embeddings (retrieval, recommendations, deduplication) | Exact: one matrix multiply against all vectors, then partial top-k selection. Approximate: HNSW, IVF, or product quantization (see "Spatial data" in `techniques/spatial-data.md`) | Approximate methods can miss true neighbors: behavior change | Exact: same O(n·d), vectorized. Approximate: sublinear queries in practice |

### Calling model APIs

Differential tests and benchmarks use a recorded or fake client: live calls cost money, send data off the machine, and do not return the same output twice.

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| One API call per item in a loop (embeddings, classifications) | Batch endpoints, or bounded concurrency within the provider's rate limits | Errors, retries, and partial failures handled per item as before; result order preserved | Fewer round trips; higher throughput |
| Same request sent repeatedly | Cache responses keyed by every input that affects the output: model name and version, full prompt, parameters, tools, and settings | With sampling (temperature above 0), a cache returns one fixed sample where the original produced a new one each time: behavior change. Bounded, invalidated when the model version changes. When the prompt, tools, or retrieved context depend on who asks, the key includes the user or tenant, or one user receives another's answer. The cache is a new copy of the prompts and outputs, which can hold personal or confidential data: give it the same access control and retention as the original data, especially on disk or in a shared store | API calls avoided |
| Long shared prompt prefix sent with every request | The provider's prompt caching, with the stable prefix placed first | Prompt content unchanged | Lower latency and cost for the cached prefix |

## Behavior traps

Rewrites that look equivalent but are not; check them alongside `BEHAVIOR-TRAPS.md`.

- **Random number consumption.** Reordering, batching, or parallelizing code that draws random numbers (initialization, dropout, shuffling, sampling) changes which number each draw receives, and so the results. Compare with the same seed and draw order, or treat the difference as a behavior change.
- **Nondeterministic kernels.** Some GPU operations (atomic accumulation, some convolution and scatter algorithms) give different bits on every run. Differential tests need the framework's deterministic mode, or a tolerance the developer approves (`DIFFERENTIAL-TESTING.md`).
- **Batch-dependent numerics.** Batch normalization statistics, kernel selection by shape, and reduction order all depend on the batch, so batching, padding, or a new batch size can change results.
- **Training versus inference mode.** Dropout and batch normalization behave differently in each mode; a rewrite that runs in or switches to the other mode changes outputs.
- **Data types and promotion.** Lower precision, implicit type promotion, or a different accumulator type changes results, and can overflow or lose precision. IEEE half precision (fp16) has a largest finite value of 65,504, and values from 65,520 up round to infinity; bfloat16 has the range of 32-bit floats, so it rarely overflows, but keeps only about 8 bits of precision.
- **Tokenization.** Any change to merge order, normalization, or special tokens changes model inputs and outputs for the same text.
