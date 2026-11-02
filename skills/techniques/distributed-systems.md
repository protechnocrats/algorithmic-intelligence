# Distributed Systems

Part of the advanced techniques. The shared rules in `ADVANCED-TECHNIQUES.md` apply to every table in this file; read them first. Tables are read as described there.

For code spread across processes or machines: sharded databases and caches, replicated stores, consensus-based services, batch and stream processing, service meshes, and cluster membership. A fast local algorithm can still lose to network round trips, coordination, and data movement. Count those first: messages and round trips per operation, bytes moved across the network, and how many machines each operation must wait for.

Consistency is part of the contract. Any change that lets a reader see older data, lets replicas disagree for a while, or changes which writes win is a behavior change (rule 5), however much faster it is.

## Placement and partitioning

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Keys assigned to servers by `hash(key) mod N`, so adding or removing a server moves almost every key | Consistent hashing with virtual nodes, rendezvous (highest-random-weight) hashing, or jump consistent hash for numbered buckets | Data migration is planned for the keys that do move; with untrusted keys, a keyed hash (`techniques/hostile-inputs.md`) | Keys moved per membership change: almost all → about 1/N |
| Queries or transactions that fan out to every shard (scatter-gather) because data is split by an unrelated key | Partition by the key that queries filter or join on, and co-locate data that is accessed together | Measured access patterns; skewed keys create hot partitions (next row) | Shards touched per operation: all → one, removing the slowest-shard tail |
| One hot key or partition saturates a single server while others idle | Split the hot key (salting or sub-keys) and combine the parts on read, or replicate read-mostly hot data | The combine is correct for the operation (sums and counts combine; uniqueness checks do not) | Load spread across servers; reads may cost one fan-out to the parts |
| Large tables scanned in full although queries filter on a date, tenant, or region | Table partitioning by that column, so the planner skips partitions that cannot match (partition pruning) | Queries filter on the partition key; partition count stays moderate; schema change agreed with the developer | Rows scanned: all → only matching partitions |

## Data movement in batch and stream processing

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Every record shuffled across the network before aggregating (map-reduce, group-by in a dataflow engine) | Pre-aggregate on each producer before the shuffle (a combiner, or partial aggregation) | The aggregate is associative and commutative (sum, count, min, max; average as sum and count) | Bytes shuffled: proportional to records → proportional to distinct keys per producer |
| A few keys receive most records, so one reducer or worker runs far longer than the rest | Skew handling: split heavy keys across workers and merge partial results, or broadcast the small side of a join | Heavy keys found from a sample or statistics; merging is correct for the aggregate | Job time bounded by average rather than worst partition |
| Sorting a dataset spread over many machines by collecting it in one place | Sample sort: choose splitters from a sample, range-partition by them, sort each partition locally | The comparator is the same everywhere; ties across partitions ordered as the original | One machine's capacity → parallel sort with one shuffle |

## Coordination

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Every update to shared, mergeable state (counters, sets, presence, collaborative text) takes a lock or a consensus round | Conflict-free replicated data types (CRDTs): replicas update locally and merge with a commutative, idempotent merge | **Behavior change**: replicas converge eventually instead of agreeing immediately; metadata (tombstones, version vectors) is bounded or compacted | Updates without coordination; latency of a local write |
| A consensus log (Raft, Paxos) commits one entry per round trip, and reads also go through the log | Batch and pipeline log entries; serve linearizable reads with a read index or a leader lease instead of a log write | Leases rely on bounded clock drift (state the assumption); follower reads without these checks may be stale, a behavior change | Throughput: one entry per round trip → many; reads without a log write |
| A distributed transaction (two-phase commit) on every operation | Partition so that most transactions touch one shard; where cross-shard steps remain, consider a saga with compensating actions | Sagas give up isolation between steps: a behavior change the developer must approve | Round trips and blocking of two-phase commit avoided for single-shard operations |
| A distributed lock acquired for every operation | Ownership by partition (one owner per key range) or leases, with fencing tokens checked by the storage layer | The storage rejects writes with an old fencing token, so a paused former holder cannot corrupt data | Lock round trips removed from the common path |
| Membership and failure detection by every node pinging every other node | Gossip-based dissemination and SWIM-style failure detection | Detection is probabilistic, with a configured false-positive rate and detection time | Messages per period: O(n²) → O(n); updates reach all nodes in O(log n) rounds |
| Reads or writes wait for every replica, so the slowest replica sets the latency | Quorums: write to W and read from R of N replicas with R + W > N, taking the fastest responders; hedged requests (`techniques/queues-and-latency.md`) | Lowering R or W below that condition gives stale reads: a behavior change | Latency set by the R-th or W-th fastest replica, not the slowest |

## References (for verifying claims; not required reading)

- David Karger et al., "Consistent Hashing and Random Trees," STOC 1997; David G. Thaler and Chinya V. Ravishankar, "Using Name-Based Mappings to Increase Hit Rates" (rendezvous hashing), *IEEE/ACM Transactions on Networking* 6(1), 1998; John Lamping and Eric Veach, "A Fast, Minimal Memory, Consistent Hash Algorithm" (2014).
- Jeffrey Dean and Sanjay Ghemawat, "MapReduce: Simplified Data Processing on Large Clusters," OSDI 2004.
- Marc Shapiro et al., "Conflict-Free Replicated Data Types," SSS 2011.
- Diego Ongaro and John Ousterhout, "In Search of an Understandable Consensus Algorithm" (Raft), USENIX ATC 2014.
- Abhinandan Das, Indranil Gupta, and Ashish Motivala, "SWIM: Scalable Weakly-consistent Infection-style Process Group Membership Protocol," DSN 2002.
- Martin Kleppmann, *Designing Data-Intensive Applications* (2017): partitioning, replication, transactions, and fencing tokens.
