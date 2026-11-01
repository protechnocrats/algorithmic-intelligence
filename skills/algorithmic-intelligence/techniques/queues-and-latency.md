# Queues, Latency, and Throughput

Part of the advanced techniques. The shared rules in `ADVANCED-TECHNIQUES.md` apply to every table in this file; read them first. Tables are read as described there.

For any code that serves requests or moves work between stages: kernel I/O and CPU schedulers, network stacks, database engines and connection pools, message brokers and middleware, backend services, thread pools, and event loops. Every function can be optimal while response time is poor, because work waits in queues. Measure waiting time separately from service time before changing either.

## Laws to apply first

- **Little's Law.** L = λ · W: the average number of items in a system equals the arrival rate times the average time each spends there. It holds for any stable system, whatever the distributions. Use it to check measurements against each other, and to size pools and buffers: a pool needs about λ · W slots to avoid queueing.
- **Utilization drives waiting.** For a single server with random arrivals and service times (M/M/1), the average time in the system is W = 1 / (μ − λ) for service rate μ and arrival rate λ. As utilization ρ = λ / μ approaches 1, waiting grows without bound: going from 80% to 95% busy quadruples the average time in the system. A small cut in service time near saturation removes a large share of the waiting. Real systems are not exactly M/M/1, so treat this as the shape of the curve, not a prediction.
- **Pooling.** One shared queue in front of c servers (M/M/c) waits less than c separate queues with one server each at the same total load, because no server sits idle while work waits elsewhere.
- **Tail latency under fan-out.** A request that waits for N parallel sub-requests is as slow as the slowest. If each is slow 1% of the time, a fan-out of 100 is slow about 63% of the time (1 − 0.99¹⁰⁰). Optimize and measure the high percentiles of the parts, not their averages.
- **Measure without coordinated omission.** A load generator that waits for each reply before sending the next hides queueing delay. Measure latency from the time each request was scheduled to be sent, at a fixed arrival rate.

## Techniques

Most techniques here change behavior under load: which requests wait, which are rejected, and in what order they complete. Those changes need developer review (rule 5), even when the result for each request is unchanged.

| Signal | Technique | Valid when | Typical result |
|---|---|---|---|
| Queues grow without bound under bursts, memory climbs, and latency rises for everything | Bounded queues with backpressure (block or slow the producer) or admission control (reject early) | **Behavior change**: callers now wait or receive rejections they did not before; the rejection signal is part of the contract | Bounded memory and bounded waiting; overload becomes visible instead of cascading |
| One slow item delays everything behind it in a single queue or connection (head-of-line blocking) | Separate queues per class or destination, multiplexed streams, or out-of-order completion with request IDs | Ordering guarantees that callers rely on are kept, or the change is reviewed | Fast work no longer waits behind slow work |
| Many independent queues or servers, some idle while others have backlogs | One shared queue, work stealing, or routing to the least loaded of two randomly chosen servers ("power of two choices") | Work items are interchangeable between servers; affinity (caches, sessions, locality) is preserved where it matters | Lower and more even waiting time; two random choices cut the maximum load from O(log n / log log n) to O(log log n) |
| Short and long tasks mixed in one first-in, first-out queue | Shortest-job-first or shortest-remaining-time scheduling, size-based queues, or priorities | **Behavior change** in completion order; long tasks need a starvation bound (aging) | Lower average waiting time; first-in, first-out keeps the variance of waiting time lower, not the average |
| Overloaded queue where old requests are already past their deadlines | Drop requests whose deadline has passed; under overload, serve newest first (adaptive LIFO) or apply CoDel-style queue management | **Behavior change**: some requests fail fast instead of succeeding late; deadlines must be known | Capacity is spent on requests that can still succeed |
| Per-item overhead dominates (system calls, network round trips, disk syncs, lock acquisitions) | Batching: combine items up to a size or a time limit (group commit, Nagle-style coalescing, vectored I/O) | The added delay (up to the time limit) is acceptable, which is a behavior change for latency-sensitive callers; failures within a batch are handled per item as before | Per-item overhead divided by the batch size; latency rises by up to the batch window |
| A few slow replies dominate the tail latency of reads that can be served by several replicas | Hedged requests: send a second request if the first has not answered by about the 95th-percentile latency, and use the first reply; cancel the other | Requests are idempotent and safe to duplicate; extra load is measured (typically a few percent) | Tail latency cut sharply for little extra load |
| Retries after failures arrive in synchronized waves and overload a recovering service | Exponential backoff with jitter, retry budgets, circuit breakers | **Behavior change** in timing and in when callers see errors | Load stays below capacity during recovery |
| A fixed rate limit or pool size that is wrong as conditions change (congestion, autoscaling, I/O depth) | Feedback control: additive increase and multiplicative decrease (AIMD, as in TCP congestion control), latency-based limits (Vegas-style or gradient limiters), token buckets for sustained rate with bursts | The control loop is stable: gains and sampling interval tested under load steps, so the limit does not oscillate; **behavior change** in admitted rate | Throughput tracks available capacity without manual tuning |
| Threads blocked on I/O while CPU sits idle, or a thread per connection exhausting memory | Event-driven I/O (`epoll`, `kqueue`, `io_uring`, I/O completion ports) or asynchronous tasks with a bounded number of worker threads | Threading and ordering are part of the contract (rule 11); blocking calls are kept off the event loop | Concurrency limited by memory per connection instead of threads; fewer context switches |

## References (for verifying claims; not required reading)

- Brendan Gregg, *Systems Performance: Enterprise and the Cloud*, 2nd ed. (2020): the USE method, profiling, and latency analysis.
- Mor Harchol-Balter, *Performance Modeling and Design of Computer Systems: Queueing Theory in Action* (2013).
- John D. C. Little, "A Proof for the Queuing Formula: L = λW," *Operations Research* 9(3), 1961.
- Jeffrey Dean and Luiz André Barroso, "The Tail at Scale," *CACM* 56(2), 2013.
- Michael Mitzenmacher, "The Power of Two Choices in Randomized Load Balancing," *IEEE TPDS* 12(10), 2001.
- Kathleen Nichols and Van Jacobson, "Controlling Queue Delay" (CoDel), *ACM Queue* 10(5), 2012; Van Jacobson, "Congestion Avoidance and Control," SIGCOMM 1988.
