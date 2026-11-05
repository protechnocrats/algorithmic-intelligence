# Distributed Systems

The shared rules and table conventions in `ADVANCED-TECHNIQUES.md` apply to every table here.

For code spread across processes or machines. A fast local algorithm still loses to network round trips, coordination, and data movement, so count those first: messages and round trips per operation, bytes moved, and machines each operation waits for.

Consistency is part of the contract: letting a reader see older data, letting replicas disagree temporarily, or changing which writes win is a behavior change.

Duplicates are the default. A call can fail after the other side acted, so retrying, hedging, replaying a log, rerunning a slow task (speculative execution), or resending after a rebalance can run a side effect twice. Each of these needs the operation to be idempotent or to carry an idempotency key the receiver stores atomically with the effect. "Exactly once" across a network holds only through such deduplication, whatever a framework's name or documentation says.

Measure on a local cluster, an emulator, or a simulated network with generated data.

## Placement and partitioning

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Keys assigned to servers by `hash(key) mod N`, so adding or removing a server moves almost every key | Consistent hashing with virtual nodes, rendezvous (highest-random-weight) hashing, or jump consistent hash for numbered buckets | Migration is planned for moved keys; untrusted keys need a keyed hash; jump consistent hash only when buckets are numbered 0..N−1 and nodes leave only from the end, or an indirection table maps bucket numbers to live nodes (removing a middle bucket renumbers the rest and moves far more than 1/N of the keys) | Keys moved per membership change: almost all → about 1/N |
| Queries or transactions that fan out to every shard (scatter-gather) because data is split by an unrelated key | Partition by the key that queries filter or join on, and co-locate data accessed together | Measured access patterns; skewed keys create hot partitions (next row) | Shards touched per operation: all → one, removing the slowest-shard tail |
| One hot key or partition saturates a single server while others idle | Split the hot key (salting or sub-keys) and combine the parts on read, or replicate read-mostly hot data | The combine is correct for the operation (sums and counts combine; uniqueness checks do not) | Load spread across servers; reads may cost one fan-out to the parts |
| Large tables scanned in full although queries filter on a date, tenant, or region | Table partitioning by that column, so the planner skips partitions that cannot match (partition pruning) | Queries filter on the partition key; partition count stays moderate; a schema change (rule 5) | Rows scanned: all → only matching partitions |

## Data movement in batch and stream processing

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Every record shuffled across the network before aggregating (map-reduce, group-by in a dataflow engine) | Pre-aggregate on each producer before the shuffle (a combiner, or partial aggregation) | The aggregate is associative and commutative (sum, count, min, max; average as sum and count); regrouped floating-point sums change results | Bytes shuffled: proportional to records → proportional to distinct keys per producer |
| A few keys receive most records, so one reducer or worker runs far longer than the rest | Skew handling: split heavy keys across workers and merge partial results, or broadcast the small side of a join | Heavy keys found from a sample or statistics; merging is correct for the aggregate; tasks with external side effects are not run twice by retries or speculative copies | Job time bounded by average rather than worst partition |
| Sorting a dataset spread over many machines by collecting it in one place | Sample sort: choose splitters from a sample, range-partition by them, sort each partition locally | The comparator is the same everywhere; ties across partitions ordered as the original | One machine's capacity → parallel sort with one shuffle |

## Coordination

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Every update to shared, mergeable state (counters, sets, presence, collaborative text) takes a lock or a consensus round | Conflict-free replicated data types (CRDTs): replicas update locally and merge with a commutative, idempotent merge | Replicas converge eventually instead of agreeing immediately (a behavior change); metadata (tombstones, version vectors) is bounded or compacted; last-writer-wins by wall-clock time silently drops writes when clocks differ or move backward | Updates without coordination; latency of a local write |
| A consensus log (Raft, Paxos) commits one entry per round trip, and reads also go through the log | Batch and pipeline log entries; serve linearizable reads with a read index or a leader lease instead of a log write | Leases rely on bounded clock drift (state the assumption); follower reads without these checks may be stale | Throughput: one entry per round trip → many; reads without a log write |
| A distributed transaction (two-phase commit) on every operation | Partition so most transactions touch one shard; for remaining cross-shard steps, consider a saga with compensating actions | Sagas give up isolation between steps (a behavior change); every step and compensation is idempotent, since each may be retried | Round trips and blocking of two-phase commit avoided for single-shard operations |
| A distributed lock acquired for every operation | Ownership by partition (one owner per key range) or leases, with fencing tokens checked by the storage layer | Storage rejects writes with an old fencing token, so a paused former holder cannot corrupt data | Lock round trips removed from the common path |
| Membership and failure detection by every node pinging every other node | Gossip-based dissemination and SWIM-style failure detection | Detection is probabilistic, with a configured false-positive rate and detection time | Messages per period: O(n²) → O(n); updates reach all nodes in O(log n) rounds |
| Reads or writes wait for every replica, so the slowest replica sets the latency | Quorums: write to W and read from R of N replicas with R + W > N, taking the fastest responders; hedged requests (`techniques/queues-and-latency.md`) | Lowering R or W below that condition gives stale reads | Latency set by the R-th or W-th fastest replica, not the slowest |

## References

Sources for the claims in this file are in `references/techniques/distributed-systems.md`. Read them only to verify a claim.
