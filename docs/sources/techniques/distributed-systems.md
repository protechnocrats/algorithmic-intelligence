# Sources for `skills/techniques/distributed-systems.md`

Where each claim in that file comes from, for maintainers and reviewers. Not part of the installed skill.

- David Karger et al., "Consistent Hashing and Random Trees," STOC 1997; David G. Thaler and Chinya V. Ravishankar, "Using Name-Based Mappings to Increase Hit Rates" (rendezvous hashing), *IEEE/ACM Transactions on Networking* 6(1), 1998; John Lamping and Eric Veach, "A Fast, Minimal Memory, Consistent Hash Algorithm" (2014).
- Jeffrey Dean and Sanjay Ghemawat, "MapReduce: Simplified Data Processing on Large Clusters," OSDI 2004.
- Marc Shapiro et al., "Conflict-Free Replicated Data Types," SSS 2011.
- Diego Ongaro and John Ousterhout, "In Search of an Understandable Consensus Algorithm" (Raft), USENIX ATC 2014.
- Abhinandan Das, Indranil Gupta, and Ashish Motivala, "SWIM: Scalable Weakly-consistent Infection-style Process Group Membership Protocol," DSN 2002.
- Martin Kleppmann, *Designing Data-Intensive Applications* (2017): partitioning, replication, transactions, fencing tokens, idempotence and exactly-once processing, and why last-writer-wins by wall-clock time loses writes.
- Giuseppe DeCandia et al., "Dynamo: Amazon's Highly Available Key-value Store," SOSP 2007: sloppy quorums and hinted handoff, section 4.6. Strict quorums are not linearizable under concurrent writes without read repair: Hagit Attiya, Amotz Bar-Noy, and Danny Dolev, "Sharing Memory Robustly in Message-Passing Systems," *Journal of the ACM* 42(1), 1995 (the ABD algorithm, whose reads write back what they read); Kleppmann (above), chapter 5, "Limitations of Quorum Consistency."
