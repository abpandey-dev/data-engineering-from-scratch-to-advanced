from lib import *
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np



LESSON("Basics", "Thinking in streams", """
<p>A batch job has an end. A stream doesn't, so "total sales today" has no obvious moment to finish. Stream processing answers this with <b>windows</b>, which cut an endless stream into finite pieces.</p>
<table><tr><th>Window</th><th>Shape</th><th>Use</th></tr>
<tr><td>Tumbling</td><td>fixed, no overlap</td><td>counts per minute</td></tr>
<tr><td>Sliding</td><td>fixed, overlapping</td><td>a 10-minute average, updated every 5</td></tr>
<tr><td>Session</td><td>ends after a gap</td><td>user visits</td></tr></table>
<div class="pic">Tumbling (60s): [0───60)[60──120)[120─180)
Sliding (10s, every 5s): [0──10) [5──15) [10─20)
Session (gap 5): 1 2 ····· 10 11 12 ········ 30</div>
<p><b>By hand.</b> Times 1, 2, 61, 62, 130 in 60-second tumbling windows: window start = t − t % 60, giving {0: 2, 60: 2, 120: 1}.</p>
<p>In a sliding window of size 10 every 5, an event at 12 belongs to the windows starting at 5 and 10. Times 1, 2, 10, 11, 12, 30 with a session gap of 5 make 3 sessions: 1–2, 10–12 and 30.</p>
<pre><code class="py">counts = (events
    .withWatermark("ts", "10 minutes")
    .groupBy(F.window("ts", "5 minutes"), "page")
    .count())
query = counts.writeStream.outputMode("append").format("parquet") \\
    .option("path", out).option("checkpointLocation", ckpt).start()</code></pre>
<p>This Structured Streaming code needs a running source, so it's shown as text here. The practice questions model the same logic in plain Python.</p>
""", practice=["Tumbling Windows", "Sliding Windows", "Session Windows", "Top K per Window"])


LESSON("Core", "Event time and watermarks", """
<p><b>Events arrive late and out of order.</b> A click at 55 s might arrive at 62 s. Grouping by arrival time would put it in the wrong minute: for events (55, 62), (58, 59), (61, 65), event time gives {minute 0: 2, minute 1: 1}, while arrival time gives {minute 0: 1, minute 1: 2}.</p>
<p>So group by event time. But then when can you close a window? You can't wait forever. A <b>watermark</b> is the system's estimate of how far event time has got:</p>
<p style="text-align:center"><b>watermark = largest event time seen − allowed lateness</b></p>
<p>Times 10, 20, 15, 30 with lateness 5 give watermarks 5, 15, 15, 25. It never goes backward.</p>
<p><b>What it controls:</b> a window closes when the watermark passes its end. Events for closed windows are dropped, and that window's state can be freed. Window [0, 60) with lateness 10 closes once an event at 70 arrives.</p>
<table><tr><th>Lateness setting</th><th>Result</th></tr>
<tr><td>Small</td><td>fast results, more dropped events</td></tr>
<tr><td>Large</td><td>complete results, slower, more state</td></tr></table>
<p>The chart shows the watermark trailing the maximum event time, and a late event falling behind it. <b>Choose lateness from measured delays</b>, and count what's dropped.</p>
""", practice=["Event Time vs Processing Time", "Compute the Watermark", "Drop Late Events", "When Does a Window Fire?"])


@LD
def watermark_chart():
    rng = np.random.default_rng(0)
    arrivals = np.arange(100)
    event_time = arrivals - rng.exponential(5, 100)
    top = np.maximum.accumulate(event_time)
    watermark = top - 10
    late = event_time < watermark
    print("late events dropped:", int(late.sum()), "of", len(late))
    fig, ax = plt.subplots(figsize=(4.8, 2.8))
    ax.scatter(arrivals, event_time, s=8, label="events")
    ax.scatter(arrivals[late], event_time[late], s=22, color="tab:red", label="too late")
    ax.plot(arrivals, watermark, color="black", label="watermark")
    ax.set_xlabel("arrival order")
    ax.set_ylabel("event time")
    ax.legend(fontsize=7)


LESSON("Core", "State and joins", """
<p><b>Counting needs memory.</b> A running count per key is <b>state</b>, and with a stream that runs for years, state can grow until it crashes. Four keys seen forever is fine, but a billion isn't. A <b>TTL</b> or a watermark removes old state: of 3 keys seen, only 2 are still live after a 30-second TTL.</p>
<p><b>State stores:</b> Flink and Spark can keep large state in RocksDB on local disk, and checkpoint it to object storage.</p>
<table><tr><th>Join</th><th>How</th><th>State</th></tr>
<tr><td>Stream-static</td><td>look each event up in a table</td><td>none</td></tr>
<tr><td>Stream-stream</td><td>buffer both sides until a match can no longer arrive</td><td>grows with the time range</td></tr></table>
<p><b>Stream-stream by hand.</b> Impressions and clicks, with a click valid within 30 s. The impression at 10 and click at 15 match. The click at 90 for an impression at 20 is too late. The click for ad 3 has no impression. Without a time limit, you'd need to buffer forever.</p>
<p><b>Deduplication</b> also needs state, limited by a window. Ids older than the window are forgotten, so a very late repeat can get through. That's a deliberate trade-off.</p>
<p><b>Approximate answers save huge amounts of state:</b></p>
<table><tr><th>Sketch</th><th>Answers</th><th>Note</th></tr>
<tr><td>HyperLogLog</td><td>how many distinct?</td><td>about 1–2% error in kilobytes</td></tr>
<tr><td>Count-Min</td><td>how often?</td><td>may overestimate, never under</td></tr>
<tr><td>Bloom filter</td><td>seen before?</td><td>"maybe" or "definitely not"</td></tr></table>
<p>Our single-counter HyperLogLog sketch estimates 2,048 for 1,000 distinct items, as one counter is very rough. Real HLL averages thousands of buckets.</p>
""", practice=["Running Count With State", "State Growth", "Stream-Static Join", "Stream-Stream Join", "Deduplicate With a Watermark", "Approximate Distinct Counts", "Count-Min Sketch"])


LESSON("Advanced", "Failure, exactly-once and architecture", """
<p><b>Checkpoints.</b> A job periodically saves its input offsets and state together. After a crash it restores both and replays. With a checkpoint every 4 events and a crash at 7, it restores 4 and replays 3, and still ends on the right total of 10.</p>
<p><b>End-to-end exactly-once needs three things:</b> a replayable source, checkpointed state, and an idempotent or transactional sink. Replaying a record into an append sink gives 3 rows for 2 records, and an upsert sink gives 2.</p>
<p><b>Spark vs Flink:</b></p>
<table><tr><th></th><th>Spark Structured Streaming</th><th>Flink</th></tr>
<tr><td>Model</td><td>micro-batches</td><td>record at a time</td></tr>
<tr><td>Latency</td><td>seconds</td><td>milliseconds possible</td></tr>
<tr><td>Strength</td><td>same API as batch</td><td>advanced state and event time</td></tr></table>
<p><b>Micro-batch stability.</b> With a 10 s trigger and 2 s runtime, average latency is 7 s and the worst is 12 s. A 15 s runtime on a 10 s trigger means it falls further behind forever.</p>
<p><b>Backpressure.</b> Arrivals of 5, 20, 5, 5 with capacity 10 give a queue of 0, 10, 5, 0. It recovers. If average input exceeds capacity, the queue never recovers.</p>
<table><tr><th>Architecture</th><th>Idea</th><th>Trade-off</th></tr>
<tr><td>Lambda</td><td>separate batch and stream paths</td><td>accurate, but two code bases</td></tr>
<tr><td>Kappa</td><td>one stream path; replay to reprocess</td><td>simpler, needs long retention</td></tr></table>
""", practice=["Checkpoint and Replay", "Replays Need an Idempotent Sink", "Micro-Batch Latency", "Backpressure", "Lambda or Kappa?"])
