from lib import *

THEORY("Numbers everyone should know (rough)", """
<table><tr><th>Operation</th><th>Time</th></tr>
<tr><td>Read from memory, 1 MB</td><td>about 10–100 µs</td></tr>
<tr><td>Read from SSD, 1 MB</td><td>about 1 ms</td></tr>
<tr><td>Network within a data centre, round trip</td><td>about 0.5 ms</td></tr>
<tr><td>Read from disk, 1 MB</td><td>about 5–20 ms</td></tr>
<tr><td>Cross-continent round trip</td><td>about 100–150 ms</td></tr></table>
<p>These vary with hardware, but the gaps between them shape all data system design.</p>
""")
FAQ("Scale up vs scale out?", "<p>Scale up buys a bigger machine, which is simple but limited and costly. Scale out adds machines, which scales far, but brings partitioning, replication and failures.</p>")
FAQ("Partitioning vs replication?", "<p>Partitioning splits data across machines, for scale. Replication copies data, for safety and read capacity. Most systems use both.</p>")
FAQ("Explain the CAP theorem.", "<p>During a network partition, a system must give up either consistency or availability. Without a partition you can have both, though you still trade latency against consistency.</p>")
FAQ("What is eventual consistency?", "<p>Replicas may disagree for a while, but converge once updates stop arriving.</p>")
FAQ("What is data skew?", "<p>Uneven data across partitions. The largest partition determines job time, wasting the rest of the cluster.</p>")
FAQ("At-most-once, at-least-once, exactly-once?", "<p>Messages can be lost, repeated, or effectively processed once. In practice, exactly-once usually means at-least-once delivery with idempotent or transactional processing.</p>")
FAQ("Why is consistent hashing useful?", "<p>When machines join or leave, only a small share of keys move, rather than nearly all of them as with modulo hashing.</p>")
FAQ("Scenario: you doubled the cluster but the job only got 10% faster. Why?", "<p>A serial bottleneck (Amdahl), skew in one partition, a slow source or sink, or network shuffle limits. Find the bottleneck before adding hardware.</p>")
FAQ("Scenario: a job is stuck at 99% for an hour. What's happening?", "<p>Almost certainly skew, or a straggler. Look at per-task data sizes. Fix hot keys by salting, broadcasting or filtering NULL keys.</p>")
FAQ("Scenario: users sometimes don't see the data they just saved. Why?", "<p>Reads go to a replica with lag. Read from the leader after a write, use a read-your-writes approach, or increase quorums.</p>")
