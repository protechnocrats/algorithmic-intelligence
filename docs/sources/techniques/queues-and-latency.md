# Sources for `skills/algorithmic-intelligence/references/techniques/queues-and-latency.md`

Where each claim in that file comes from, for maintainers and reviewers. Not part of the installed skill.

- Brendan Gregg, *Systems Performance: Enterprise and the Cloud*, 2nd ed. (2020): the USE method, profiling, and latency analysis.
- Mor Harchol-Balter, *Performance Modeling and Design of Computer Systems: Queueing Theory in Action* (2013).
- John D. C. Little, "A Proof for the Queuing Formula: L = λW," *Operations Research* 9(3), 1961.
- Jeffrey Dean and Luiz André Barroso, "The Tail at Scale," *CACM* 56(2), 2013.
- Michael Mitzenmacher, "The Power of Two Choices in Randomized Load Balancing," *IEEE TPDS* 12(10), 2001.
- Kathleen Nichols and Van Jacobson, "Controlling Queue Delay" (CoDel), *ACM Queue* 10(5), 2012; Van Jacobson, "Congestion Avoidance and Control," SIGCOMM 1988.
- Betsy Beyer et al., eds., *Site Reliability Engineering* (2016), chapters "Handling Overload" and "Addressing Cascading Failures": retry budgets, retries multiplied across layers, and load shedding.
- Gil Tene, "How NOT to Measure Latency" (talks from 2013 on, and the HdrHistogram README at github.com/HdrHistogram/HdrHistogram): coordinated omission. The M/M/1 waiting-time formula and the pooling result are derived in Harchol-Balter (above).
