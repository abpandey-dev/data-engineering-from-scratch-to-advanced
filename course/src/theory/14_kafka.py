from lib import *

THEORY("Kafka vs a queue", """
<table><tr><th></th><th>Kafka</th><th>Traditional queue (e.g. SQS, RabbitMQ)</th></tr>
<tr><td>After reading</td><td>messages stay until retention</td><td>usually removed</td></tr>
<tr><td>Replay</td><td>yes</td><td>generally no</td></tr>
<tr><td>Order</td><td>per partition</td><td>varies</td></tr>
<tr><td>Throughput</td><td>very high</td><td>moderate</td></tr>
<tr><td>Best for</td><td>event streams, many readers</td><td>task queues</td></tr></table>
""")
FAQ("Why is Kafka fast?", "<p>Sequential disk writes, page cache use, batching and compression, and zero-copy transfer. It's just appending to files.</p>")
FAQ("How does Kafka guarantee order?", "<p>Only within a partition. Use a key so related events go to the same partition.</p>")
FAQ("What is a consumer group?", "<p>Consumers sharing a topic, with each partition read by one member at a time. Different groups read independently.</p>")
FAQ("What is consumer lag?", "<p>The gap between the latest offset and the committed one. Growing lag means the consumer can't keep up.</p>")
FAQ("How do you get exactly-once?", "<p>Idempotent producers and transactions within Kafka. To outside systems, use at-least-once delivery with idempotent writes.</p>")
FAQ("What does acks=all do?", "<p>The leader waits for all in-sync replicas before confirming, which is the most durable option, especially with min.insync.replicas of 2 or more.</p>")
FAQ("What is log compaction?", "<p>Keeping only the latest value per key, with tombstones for deletes, so a topic can represent current state.</p>")
FAQ("Scenario: lag keeps growing. What do you do?", "<p>Check whether input rose or processing slowed. Add consumers up to the partition count, fix slow downstream calls, batch writes, or add partitions.</p>")
FAQ("Scenario: consumers rebalance constantly. Why?", "<p>Processing takes longer than max.poll.interval.ms, or heartbeats are missed. Reduce batch size, speed up processing, and tune timeouts.</p>")
FAQ("Scenario: orders appear out of sequence downstream. Why?", "<p>Probably no key or the wrong one, so events landed on different partitions, or retries reordered without idempotence. Use the order id as the key.</p>")
FAQ("Scenario: a bad message makes the consumer crash in a loop. How do you handle it?", "<p>Catch the error, send the message to a dead-letter topic with its reason, and continue. Alert on the dead-letter rate.</p>")
