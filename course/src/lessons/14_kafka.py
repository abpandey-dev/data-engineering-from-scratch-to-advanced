from lib import *
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np



LESSON("Basics", "Kafka is a log", """
<p>Service A wants to tell services B, C and D about each order. Direct calls tangle everything together, and if D is down, data's lost. <b>Kafka</b> sits in the middle: A writes events, and each reader goes at its own pace, independently.</p>
<p><b>The core idea is an append-only log.</b> New messages go at the end, and each gets a number, its <b>offset</b>. Reading doesn't delete anything.</p>
<div class="pic">offset:   0    1    2    3    4
        [a]  [b]  [c]  [d]  [e]  ← new writes
                   ↑         ↑
             consumer A   consumer B (each tracks its own place)</div>
<p>Because a consumer is just a position in a log, you can <b>replay history</b> by moving back. That's very different from a traditional queue, which removes messages once read.</p>
<table><tr><th>Term</th><th>Meaning</th></tr>
<tr><td>Topic</td><td>a named stream, such as "orders"</td></tr>
<tr><td>Partition</td><td>one log; a topic has many, for scale</td></tr>
<tr><td>Broker</td><td>a Kafka server</td></tr>
<tr><td>Producer / consumer</td><td>writes / reads</td></tr>
<tr><td>Offset</td><td>a position in a partition</td></tr></table>
<p><b>Order is only guaranteed within a partition.</b> With a key, all records for that key go to one partition, and stay in order. So use the order id or user id as the key for events that must stay in sequence.</p>
<p>Choose keys with care. Using "country" could send 82% of traffic to one partition, and overload it.</p>
<p>The code examples here need a running Kafka, so questions model the behaviour in Python.</p>
<pre><code class="py">from confluent_kafka import Producer
p = Producer({"bootstrap.servers": "localhost:9092", "enable.idempotence": True, "acks": "all"})
p.produce("orders", key=str(order_id), value=payload)
p.flush()</code></pre>
""", practice=["Append to a Log", "Choose a Partition by Key", "Does Order Hold?", "Find the Hot Partition"])


LESSON("Core", "Consumer groups, offsets and lag", """
<p><b>A consumer group shares the work.</b> Each partition goes to exactly one member, so partitions cap your parallelism: 4 partitions with 2 consumers gives each 2. With 3 consumers on 2 partitions, one sits idle.</p>
<p><b>Different groups are independent,</b> so analytics and fraud detection can read the same topic at their own speeds.</p>
<p><b>Lag</b> is how far behind a consumer is: latest offset minus committed offset. It's the most important Kafka metric to alert on. Partition 0 at 100 with committed 90 has a lag of 10.</p>
<p><b>Will it catch up?</b> With lag 1,000, producing 100/s and consuming 200/s, you gain 100/s, so 10 seconds. If you consume slower than you produce, it never catches up, so add consumers (up to the partition count) or speed up processing.</p>
<p><b>Rebalancing.</b> When a member joins or dies, partitions are reassigned. With the old "eager" approach, everyone stops. Going from 2 consumers to 3 with 8 partitions, sticky or cooperative assignment moves only 2 partitions rather than all 8.</p>
<p><b>Sizing partitions.</b> Target 100 MB/s, with 10 MB/s per partition on produce and 20 on consume: at least 10. You can add partitions later, but this changes which partition a key maps to, so plan ahead.</p>
<p><b>Disk:</b> 50 MB/s, 7 days, replication 3 takes about 91 TB.</p>
""", practice=["Consumer Group Assignment", "Consumer Lag", "How Long to Catch Up?", "Partitions Needed", "Rebalance Movement", "Kafka Disk Sizing"])


LESSON("Core", "Delivery guarantees in practice", """
<p>The order of two steps decides what a crash does:</p>
<table><tr><th>Consumer does</th><th>Crash between them</th><th>Result</th></tr>
<tr><td>Commit, then process</td><td>message never processed</td><td><b>at most once</b>: can lose</td></tr>
<tr><td>Process, then commit</td><td>message processed again</td><td><b>at least once</b>: can repeat</td></tr></table>
<p><b>At-least-once by hand.</b> Messages a to e, committing every 2, crashing after c. The last commit is at 2, so we restart there: a, b, c, <b>c</b>, d, e. One duplicate.</p>
<p><b>The practical answer: at-least-once plus idempotent processing.</b> Applying (1, 10), (2, 5), (1, 10), (3, 1), ignoring repeated ids, gives 16 rather than 26. Store the processed id in the <b>same transaction</b> as the result, or use upserts.</p>
<p><b>Producer duplicates.</b> A producer that doesn't get an acknowledgement retries, and might write twice. With <code>enable.idempotence=True</code>, brokers deduplicate using a producer id and sequence number. It also prevents reordering on retry, where b1 fails, b2 succeeds, and b1 lands after it.</p>
<p><b>Kafka transactions</b> give exactly-once between Kafka topics, by writing output and offsets atomically. To an external system, you still need idempotence.</p>
<p><b>The outbox pattern.</b> Writing to a database and to Kafka separately can fail in between: 3 rows but 2 events. Instead, write the row and an "outbox" event in one database transaction, and let a relay or CDC publish it. Database and stream can't disagree.</p>
""", practice=["Commit After Processing", "Idempotent Consumer", "Producer Retries Reorder", "Outbox Pattern"])


LESSON("Advanced", "Replication, retention and schemas", """
<p><b>Replication.</b> Each partition has one leader and several followers. <b>In-sync replicas (ISR)</b> are those keeping up.</p>
<p><code>acks=all</code> waits for all in-sync replicas. With <code>min.insync.replicas=2</code> and replication 3, you can lose a broker with no data loss. If too few remain, writes are refused: consistency over availability.</p>
<p><b>High watermark.</b> Consumers can read only what's on all in-sync replicas. With offsets 100, 95, 98, they read up to 95, so a new leader can't lose what anyone has read.</p>
<p><b>Retention.</b> Kafka deletes old segments by time or size. <b>Log compaction</b> instead keeps the last value per key, like a table: a:1, b:2, a:3, b:None, c:9 keeps a:3 and c:9. A None value, called a tombstone, means delete. It's ideal for "current state" topics.</p>
<p><b>Batching.</b> Producers wait up to <code>linger.ms</code> to fill a batch, so you trade some latency for much better throughput.</p>
<p><b>Schemas.</b> A consumer breaks when a producer changes a message. A <b>schema registry</b> checks compatibility. Backward compatible means new readers can read old data, so added fields need defaults.</p>
<table><tr><th>Change</th><th>Backward compatible?</th></tr>
<tr><td>Add a field with a default</td><td>yes</td></tr>
<tr><td>Add a required field</td><td>no</td></tr>
<tr><td>Remove a field</td><td>yes for backward, but check forward</td></tr></table>
""", practice=["Log Compaction", "Retention by Time and Size", "In-Sync Replicas", "High Watermark", "Schema Compatibility", "Batching Trade-off"])
