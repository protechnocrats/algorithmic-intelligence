# Data at Scale: Streaming and Storage

The shared rules and table conventions in `ADVANCED-TECHNIQUES.md` apply to every table here.

**Contents:** Streaming and external memory · Storage and indexing · Change propagation · Compression and encoding

## Streaming and external memory

For data larger than memory or a fixed memory budget: state the budget. Disk is a budget too: spill files go to a bounded temporary directory, are deleted on success and on failure, and are readable only by the process when the data is private. Benchmark with generated data, growing the size step by step, after checking free disk.

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Sorting data larger than memory | External merge sort: sort chunks that fit, then k-way merge | Stable variant when the original sort was stable | Works within the memory budget; O(n log n) with sequential I/O |
| Aggregation (group by, counts, sums) over huge inputs | Streaming aggregation with bounded state; hash partitioning with spill to disk when keys exceed memory | Output order matches the original; floating-point sums combined in a different order give different results; one key can hold most rows (skewed or attacker-chosen data), so test that case against the budget | Memory bounded by the budget instead of input size |
| Joining two large datasets | Sort-merge join or partitioned hash join with spilling | Join semantics (nulls, duplicates, ordering) match the original | Fits the memory budget |
| Uniform random sample from a stream of unknown length | Reservoir sampling | A behavior change unless it replaces an equivalent sample with the same seed semantics | O(k) memory for a sample of k |
| Top-k or heavy hitters over a stream | Bounded heap (exact top-k); Misra-Gries or Space-Saving (approximate) | Approximate methods change results | O(k) memory |

## Storage and indexing

For storage engines, databases, file systems, and any index larger than memory, count block or page I/O, not comparisons: one page read from disk costs as much as many thousands of comparisons. The choice depends on the workload (read and write mix, point versus range queries, key distribution, data size relative to memory) and on the durability and crash-recovery contract, so record both first.

Read amplification (pages read per lookup), write amplification (bytes written per byte of new data), and space amplification (bytes stored per byte of live data) trade against each other; lowering one usually raises another (the RUM conjecture, not a proven bound). State which one the workload needs lowered, and measure the other two.

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Ordered index too large for memory, or point and range lookups through a page cache | B+ tree with node size matched to the page or block size | Ordered keys with a fixed comparator | Page reads per lookup: O(log₂ n) for a binary tree → O(log_B n) for fanout B; a range scan reads consecutive leaves |
| In-memory ordered map where pointer chasing in a binary tree dominates | B-tree with small fixed-size nodes (a few cache lines) | Iteration order and comparator unchanged | Same O(log n); fewer cache misses |
| Write-heavy index where random in-place page updates dominate | Log-structured merge (LSM) tree | Deletes become tombstones; reads may check several runs; durability, crash recovery, and read-after-write timing match the original contract | Random page writes → sequential batched writes; reads pay read amplification across runs |
| Readers and writers block each other on row or page locks | Multi-version concurrency control (MVCC) | The isolation level callers see is unchanged (snapshot isolation allows write skew that serializable execution prevents); old versions are garbage-collected | Reads no longer wait for writes; storage pays for versions |
| Choosing LSM compaction | Leveled compaction (lower read and space amplification, higher write amplification) or tiered compaction (the reverse) | Measured read and write mix | A trade-off, not a free win; benchmark both |
| LSM or on-disk lookups for keys that are often absent | Bloom or cuckoo filter per run or file, plus fence pointers (the first key of each page) in memory | Filter used only to skip reads, never to answer a lookup | Most negative lookups need no disk read; a positive lookup reads about one page in the run that holds the key, plus a page for each other run whose filter gives a false positive |
| Sorted keys with long shared prefixes (paths, URLs, composite keys) | Prefix compression within pages; suffix truncation of separator keys in inner nodes | Key comparison results unchanged | Higher fanout, so fewer levels and page reads |
| Large static sorted integer sets (posting lists, ID sets) | Delta encoding with varint or bit packing, Elias-Fano, Roaring bitmaps | Set and order semantics unchanged | Several times less memory and I/O; intersections and unions run on compressed data |
| Sparse map from integer keys (page offsets, file descriptors, IDs) with ordered iteration | Radix tree (for example, the Linux kernel XArray) | Keys are integers of bounded width | O(log n) comparisons → O(key bits / bits per level) steps; no rebalancing |
| Scans of large tables or files where filters select a narrow range of values | Data skipping: minimum and maximum (zone maps, block range indexes) per block, page, or row group; skip blocks whose range cannot match | The statistics are updated on every write or marked stale; skipping uses the same comparison semantics as the filter, including nulls, collation, and NaN | Blocks read: all → only those whose range overlaps the filter; best when data is clustered by the filtered column |
| Sequential or strided reads issued one block at a time, each paying full device or network latency | Readahead: fetch the next blocks before they are requested (the kernel's readahead window, `posix_fadvise`, `madvise`, asynchronous I/O such as `io_uring`), sized to the measured access pattern | Access pattern measured as sequential or predictable; memory for prefetched blocks is bounded; a wrong prefetch only wastes I/O | Latency per block overlapped with processing; throughput approaches device bandwidth |

## Change propagation

Rescanning everything to find what changed costs O(data) per update; when changes are small relative to the data, propagate them instead. First record the read-after-write contract: how soon a reader must see a change. Any delay the original did not have is a behavior change.

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| The same aggregate or join recomputed from base data on every query, while the base data changes slowly | Materialized view with incremental view maintenance: apply each insert, update, and delete to the stored result as a delta | The aggregate is incrementally maintainable (sum and count are; average needs sum and count; minimum and maximum need extra state to handle deletes; distinct counts need a count per value); refresh timing meets the read-after-write contract; access rules on the base data (row-level security, tenant filters, soft deletes) still apply to every read of the view | O(base data) per query → O(delta) per write and O(result) per read |
| Polling that rescans a whole table, directory, or dataset to find what changed | Consume a change feed: change data capture from the write-ahead log or binlog, change streams, file-system notifications (`inotify`, FSEvents, `ReadDirectoryChangesW`), or an indexed modification-time watermark | The feed is complete and ordered, or every gap is detected (notification queue overflow, restarts, log truncation) and falls back to a full rescan; restarts resume from a durable position; delivery is at least once, so applying a change twice has the same effect as once, or the position is stored atomically with the change's effect | O(data) per poll → O(changes) |
| Replicas or caches synchronized by copying or comparing everything | Ship the log of changes, or compare hash trees (Merkle trees) to find the differing ranges | Applying changes in log order reproduces the source state, and replay after a restart is harmless (idempotent apply or an atomically stored position); the hash tree uses a collision-resistant hash (SHA-256 or similar), since equal hashes are taken as equal data and a non-cryptographic hash lets attacker-chosen content hide a difference | O(data) per sync → O(changes), or O(differences × log n) to locate them |

## Compression and encoding

Random or already-compressed data does not compress (Shannon's source coding theorem), so measure ratio and CPU cost on real data before proposing compression. A changed on-disk or wire format is a behavior change for every reader of it. Compressing secrets together with attacker-controlled data leaks the secrets through the compressed size, and decompressing untrusted input needs limits on output size and ratio (`techniques/hostile-inputs.md`).

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Few distinct values stored, compared, or grouped as long strings or wide keys | Dictionary encoding: store small integer codes, compare and group by code | Code equality matches the original equality exactly; codes preserve order only if the dictionary is sorted, so range comparisons need an order-preserving dictionary | O(key length) comparisons → O(1); less memory and I/O |
| Long runs of repeated values (sorted columns, flags, bitmaps) | Run-length encoding, and operating directly on runs | Runs are long on real data (measure) | O(n) work → O(runs) |
| Transfer or storage bound by bytes moved, with CPU to spare | A fast general-purpose codec chosen by measured ratio and speed (for example LZ4, Zstandard, Snappy, or the platform's built-in compression) | CPU headroom measured; a codec outside the standard library is a dependency (rule 7) | Bytes moved reduced by the measured ratio |
| Custom encoding of symbols whose frequencies are skewed (compressors, codecs, index formats) | Huffman coding, or arithmetic coding or asymmetric numeral systems (ANS) to get closer to the entropy | Encoder and decoder change together; output bits change | Average code length within 1 bit of the entropy (Huffman), or very close to it (arithmetic coding, ANS) |
