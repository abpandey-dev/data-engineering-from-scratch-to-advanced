from lib import *
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import hashlib


LESSON("Basics", "Why one computer isn't enough", """
<p>Your laptop reads perhaps 500 MB/s from an SSD. A 100 TB dataset would take over 2 days just to read. You could buy a bigger machine (<b>scale up</b>), but prices climb steeply and there's a limit. Or you can use many ordinary machines (<b>scale out</b>).</p>
<p><b>The two basic tools:</b></p>
<ul><li><b>Partitioning:</b> split data across machines, so each holds a part. This gives speed.</li>
<li><b>Replication:</b> keep copies on several machines. This gives safety.</li></ul>
<p><b>MapReduce</b> is the idea that started modern big data. Word count on "a b a" and "b c":</p>
<div class="pic">Map (each machine)     Shuffle (by key)     Reduce (each key)
(a,1)(b,1)(a,1)  ──▶   a: 1,1          ──▶  a: 2
(b,1)(c,1)             b: 1,1               b: 2
                       c: 1                 c: 1</div>
<p>The insight: <b>bring code to the data</b>, and group by key so each machine can finish its part alone. Spark, Flink and warehouses all build on this.</p>
<p><b>How to split data?</b></p>
<table><tr><th>Method</th><th>How</th><th>Good for</th><th>Weakness</th></tr>
<tr><td>Hash</td><td>hash(key) % n</td><td>even spread, equality lookups</td><td>range queries touch everything</td></tr>
<tr><td>Range</td><td>a–m, n–z</td><td>range queries, sorting</td><td>hot ranges, such as "today"</td></tr></table>
<p><b>Failure becomes normal.</b> If one machine fails 0.1% of days, then among 1,000 machines, at least one fails on <b>63%</b> of days. Software must expect it.</p>
""", practice=["Word Count With MapReduce", "Hash Partitioning", "Range Partitioning", "Chance of Failure at Scale"])


LESSON("Core", "Skew, stragglers and why more machines stop helping", """
<p><b>A distributed job is only as fast as its slowest piece.</b></p>
<table><tr><th>Partition sizes</th><th>Largest ÷ average</th><th>Time at 10 rows/s</th></tr>
<tr><td>100, 100, 100, 100</td><td>1.0</td><td>10 s</td></tr>
<tr><td>10, 10, 10, 370</td><td><b>3.7</b></td><td><b>37 s</b></td></tr></table>
<p>The same 400 rows take 3.7 times as long. This is <b>skew</b>, usually from a hot key: one huge customer, or NULL as a key. A job stuck at 99% is the classic symptom.</p>
<p><b>Salting</b> breaks up a hot key by adding a suffix: 7 rows of "us" become us#0: 3, us#1: 2, us#2: 2. Spark topics cover this in more detail.</p>
<p><b>Amdahl's law:</b> if 5% of a job can't run in parallel, then more machines soon stop helping.</p>
<table><tr><th>Workers</th><th>Speedup (95% parallel)</th></tr>
<tr><td>10</td><td>6.9×</td></tr><tr><td>1,000</td><td><b>19.6×</b></td></tr><tr><td>Infinite</td><td>at most 20×</td></tr></table>
<p>The chart shows these curves flattening. A long <b>collect to driver</b> or single-threaded write is your 5%.</p>
<p><b>The network's a real cost.</b> With 10 machines, hash partitioning sends 90% of the data across the network: 900 GB for 1 TB. At 10 Gbps, that's 12 minutes before any processing.</p>
<p><b>Broadcast or shuffle?</b> To join a 1 GB table with a 1 TB one on 10 machines, copy the small one everywhere: 10 GB moved, versus about 900 GB. That's why broadcast joins are so effective.</p>
<p><b>Stragglers.</b> A sick machine can make one task very slow. <b>Speculative execution</b> starts a backup copy on another machine, and takes whichever finishes first: 100 s becomes 32 s here.</p>
""", practice=["Measure Skew", "Salting a Hot Key", "Amdahl's Law", "Speculative Execution", "Shuffle Volume", "Broadcast or Shuffle?"])


@LD
def amdahl_chart():
    n = np.logspace(0, 4, 40)
    fig, ax = plt.subplots(figsize=(4.6, 2.7))
    for p in [0.5, 0.9, 0.95, 0.99]:
        ax.semilogx(n, 1 / ((1 - p) + p / n), label=f"{int(p * 100)}% parallel")
    ax.set_xlabel("workers")
    ax.set_ylabel("speedup")
    ax.legend(fontsize=7)


LESSON("Core", "Replication and consistency", """
<p>Copies add safety, but keeping them in step is hard.</p>
<p><b>Replication lag.</b> A write at time 10 reaches a replica 5 seconds later. A read from that replica at time 14 misses it. So your app may not show what you just wrote: this is <b>eventual consistency</b>.</p>
<p><b>Quorums.</b> With N copies, wait for W acknowledgements on write, and R on read. If <b>R + W &gt; N</b>, any read overlaps any write, so it must see the latest.</p>
<table><tr><th>N, W, R</th><th>Sees the latest?</th><th>Failures tolerated (write, read)</th></tr>
<tr><td>3, 2, 2</td><td>yes</td><td>1, 1</td></tr>
<tr><td>3, 1, 1</td><td>no, but fast</td><td>2, 2</td></tr>
<tr><td>5, 3, 3</td><td>yes</td><td>2, 2</td></tr></table>
<p><b>CAP theorem.</b> When a network splits machines apart (P), you must choose: refuse some requests to stay correct (<b>C</b>onsistency), or answer anyway and risk stale data (<b>A</b>vailability). A bank balance needs C; a social media like count can use A.</p>
<p><b>Leaders.</b> Many systems choose one leader to order writes. A candidate needs a <b>strict majority</b>, so a split network can't elect two leaders: 3 of 5 wins, and 2–2 of 5 elects nobody. Failures are noticed through <b>heartbeats</b>: a worker silent for 30 seconds is presumed dead.</p>
<p><b>Time is unreliable.</b> Clocks on different machines disagree, so timestamps can't always order events. <b>Vector clocks</b> keep one counter per machine. [1, 2] came before [1, 3], while [2, 1] and [1, 2] are concurrent: neither knew of the other.</p>
""", practice=["Quorum Reads and Writes", "Replication Lag: Stale Read?", "Leader Election by Majority", "Heartbeats: Who's Dead?", "Vector Clocks: Which Came First?", "Reassign Tasks After a Failure"])


LESSON("Advanced", "Rebalancing and delivery guarantees", """
<p><b>What happens when you add a machine?</b> With <code>key % n</code>, going from 4 to 5 machines moves <b>80%</b> of keys, and from 100 to 101 moves about 90%.</p>
<p><b>Consistent hashing</b> places machines and keys on a ring, and each key goes to the next machine clockwise. Adding a machine only takes keys from its neighbour. In our test, going from 4 to 5 nodes moves 38% of keys rather than 80%. That's above the ideal 20%, as with so few points the ring is uneven. Real systems give each machine many <b>virtual nodes</b> to even it out.</p>
<p><b>Delivery guarantees.</b> A consumer reads a message, processes it, and records progress. A crash can fall between those steps:</p>
<table><tr><th>Order</th><th>On a crash</th><th>Guarantee</th></tr>
<tr><td>Record, then process</td><td>message lost</td><td><b>at most once</b></td></tr>
<tr><td>Process, then record</td><td>message repeated</td><td><b>at least once</b></td></tr>
<tr><td>Both atomically, or idempotent processing</td><td>looks like once</td><td><b>exactly once</b> (effectively)</td></tr></table>
<p>With 5 messages and a crash at the third: recording first means one is lost, leaving 4 processed. Processing first means 6 processings, with one duplicate.</p>
<p><b>The practical recipe: at-least-once delivery + idempotent processing = effectively exactly once.</b> Give each request an idempotency key, and apply each key once. With a, b, a, you apply 15 rather than 25.</p>
<p>You'll see all of this again in Kafka and Spark, because they're built on these ideas.</p>
""", practice=["Rehash Cost: Mod vs Consistent", "Consistent Hashing", "Delivery Semantics", "Retries Without Double Effects"])
