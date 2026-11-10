# Sources for `skills/techniques/machine-learning.md`

Where each claim in that file comes from, for maintainers and reviewers. Not part of the installed skill.

- Tri Dao et al., "FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness," NeurIPS 2022.
- Woosuk Kwon et al., "Efficient Memory Management for Large Language Model Serving with PagedAttention," SOSP 2023.
- Gyeong-In Yu et al., "Orca: A Distributed Serving System for Transformer-Based Generative Models," OSDI 2022 (iteration-level, or continuous, batching); Lianmin Zheng et al., "SGLang: Efficient Execution of Structured Language Model Programs," NeurIPS 2024 (prefix caching in a radix tree).
- Yaniv Leviathan, Matan Kalman, and Yossi Matias, "Fast Inference from Transformers via Speculative Decoding," ICML 2023.
- Charles Elkan, "Using the Triangle Inequality to Accelerate k-Means," ICML 2003; Greg Hamerly, "Making k-means Even Faster," SDM 2010.
- Tianqi Chen, Bing Xu, Chiyuan Zhang, and Carlos Guestrin, "Training Deep Nets with Sublinear Memory Cost," 2016 (arXiv:1604.06174): gradient checkpointing, activation memory O(√L) for one extra forward pass.
- Brandon T. Willard and Rémi Louf, "Efficient Guided Generation for Large Language Models," 2023 (arXiv:2307.09702): token masks precomputed per automaton state for constrained decoding.
- IEEE Standard for Floating-Point Arithmetic (IEEE 754-2008): the binary16 format (largest finite value 65,504). The bfloat16 format is not in IEEE 754: Intel, "BFLOAT16 – Hardware Numerics Definition" (white paper 338302, 2018), and Google Cloud's TPU guide "The bfloat16 numerical format" (cloud.google.com/tpu/docs/bfloat16).
- Andrei Z. Broder, "On the Resemblance and Containment of Documents," SEQUENCES 1997 (MinHash); Piotr Indyk and Rajeev Motwani, "Approximate Nearest Neighbors: Towards Removing the Curse of Dimensionality," STOC 1998 (locality-sensitive hashing).
- The priority-queue form of byte-pair-encoding tokenization and the top-k fallback for top-p sampling are implementation practice (as in the Hugging Face `tokenizers` library) with no single published source; verify against the project's tokenizer.
- Python documentation, `pickle` module (the warning at the top of docs.python.org/3/library/pickle.html that unpickling untrusted data can execute arbitrary code); PyTorch documentation, `torch.load` (pytorch.org/docs/stable/generated/torch.load.html) and its `weights_only` option.
- Chenchen Gu et al., "Auditing Prompt Caching in Language Model APIs," 2025: cache hits detectable by timing, revealing prompts shared across users.
