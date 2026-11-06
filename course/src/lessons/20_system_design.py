from lib import *
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np



LESSON("Basics", "How to approach any design question", """
<p>"Design a pipeline for clickstream data." Nothing is specified, and that's the test. Senior engineers ask questions, estimate, and explain trade-offs, and they don't jump straight to naming tools.</p>
<table><tr><th>Step</th><th>Ask yourself</th><th>Time (of 45 min)</th></tr>
<tr><td>1. Requirements</td><td>Who uses it? Which questions? How fresh? How correct?</td><td>5–8</td></tr>
<tr><td>2. Size it</td><td>Events per second? GB per day? Retention? Peak?</td><td>3–5</td></tr>
<tr><td>3. Data model</td><td>What's the grain? Keys? Partitions?</td><td>5</td></tr>
<tr><td>4. Architecture</td><td>Ingest, store, process, serve</td><td>15</td></tr>
<tr><td>5. Failure</td><td>Reruns? Late data? Duplicates? Bad data?</td><td>5–8</td></tr>
<tr><td>6. Operate</td><td>Monitoring, cost, security, growth</td><td>5</td></tr></table>
<p><b>Sizing, worked.</b> 10 million users, 50 events each, 1 KB per event, peak 3×:</p>
<ul><li>500 million events a day ÷ 86,400 ≈ <b>5,787 per second</b>, with a peak of about <b>17,400</b>.</li>
<li>500 million × 1 KB = <b>500 GB a day</b>.</li>
<li>Raw kept 30 days: 15 TB. Clean Parquet, 5× smaller, kept a year: 36.5 TB.</li>
<li>Peak of 17 MB/s, doubled for headroom, at 10 MB/s per partition: <b>4 Kafka partitions</b>.</li>
<li>A 5 TB batch in a 2-hour window at 20 MB/s per core and 70% efficiency: <b>50 cores</b>.</li></ul>
<p><b>Choosing based on need:</b></p>
<table><tr><th>Need</th><th>Choice</th></tr>
<tr><td>Freshness in seconds</td><td>streaming</td></tr><tr><td>Minutes</td><td>micro-batch</td></tr><tr><td>Hours or a day</td><td>batch (simplest)</td></tr>
<tr><td>Serve by key in under 50 ms</td><td>key-value store (DynamoDB, Redis)</td></tr>
<tr><td>Fast aggregates under 1 s</td><td>real-time OLAP (Pinot, Druid, ClickHouse)</td></tr>
<tr><td>Everything else</td><td>warehouse</td></tr></table>
<p><b>Say the trade-off out loud:</b> "I'd choose hourly batch rather than streaming, because the dashboard's read daily, and it's far simpler to run. If that changes, we can move to streaming from the same Kafka topic."</p>
""", practice=["Size the Ingest", "Storage Over Time", "Kafka Partitions for the Peak", "Will the Batch Finish in Time?", "Batch, Micro-Batch or Streaming?", "Pick a Serving Store", "End-to-End Latency Budget"])


LESSON("Core", "Walkthrough: clickstream analytics", """
<p><b>Requirements:</b> a website wants daily active users, funnels and an hourly traffic view. 500 GB a day, and some phones send events late.</p>
<div class="pic">Browser → Collector API → Kafka → (a) raw to S3, partitioned by hour
                                  (b) Spark: clean, dedupe, sessionise
                                       → Iceberg silver table
                                       → dbt marts → Warehouse → BI
                 Airflow schedules batch; alerts on freshness and volume</div>
<p><b>Why these choices?</b></p>
<table><tr><th>Choice</th><th>Why</th></tr>
<tr><td>A collector API</td><td>validates events, and keeps the app separate from Kafka</td></tr>
<tr><td>Kafka</td><td>absorbs spikes, and lets many consumers read</td></tr>
<tr><td>Keep raw</td><td>so bugs can be fixed by reprocessing</td></tr>
<tr><td>Partition by event date</td><td>queries filter by day; late data updates old days</td></tr></table>
<p><b>Grain:</b> one row per event, with a unique event_id. Then one row per session, and one per user per day.</p>
<p><b>Failure cases to raise:</b></p>
<ul><li><b>Duplicates:</b> dedupe on event_id. DAU uses distinct users, so duplicates don't inflate it: events a, a, b on d1 give 2.</li>
<li><b>Bots:</b> filter them out, or they'll distort everything. A user with 3 events against a limit of 2 is dropped here, and real rules are subtler.</li>
<li><b>Late events:</b> reprocess the last 3 days each run, overwriting partitions.</li>
<li><b>Outage:</b> with 7 days of Kafka retention, a 6-hour outage can replay. At 3× speed, it catches up in 3 hours.</li></ul>
<p><b>Real-time view:</b> a Flink or Spark job writes per-minute counts, and hourly rollups make dashboards fast: minutes 0 and 59 roll into hour 0.</p>
""", practice=["Clickstream: Bot Filter", "Daily Active Users From Events", "Real-Time Counter With Rollups", "How Long Can You Replay?", "Fan-Out to Many Consumers"])


LESSON("Core", "Walkthrough: replicate a database to the lake", """
<p><b>Requirements:</b> copy production PostgreSQL tables to the lake within 15 minutes, including deletes, with no load on the app.</p>
<div class="pic">Postgres → WAL → Debezium → Kafka → Spark micro-batch → MERGE into Iceberg → dbt</div>
<table><tr><th>Decision</th><th>Reason</th></tr>
<tr><td>CDC instead of a daily dump</td><td>sees deletes, fresher, light on the source</td></tr>
<tr><td>Primary key as Kafka key</td><td>keeps each row's changes in order</td></tr>
<tr><td>Merge-on-read</td><td>frequent updates; compact in the background</td></tr>
<tr><td>Initial snapshot, then CDC</td><td>the log doesn't hold all of history</td></tr></table>
<p><b>Compact before merging.</b> Keep the highest sequence per id. Out-of-order events (seq 2: B, seq 1: OLD) must end at B.</p>
<p><b>Hard parts to mention:</b></p>
<ul><li><b>Schema changes:</b> a new column must flow through, so use a schema registry and agreed rules.</li>
<li><b>Backfills:</b> a new table needs a snapshot, and then a switch to the stream.</li>
<li><b>Replication slots:</b> if the consumer stops, the database keeps its log and can fill its disk. Monitor this.</li>
<li><b>Reconciliation:</b> compare counts and sums between source and lake each day.</li></ul>
""", practice=["CDC Into a Lake: Plan the Merge", "Design a Partition Layout"])


LESSON("Advanced", "Scale, cost and the human side", """
<p><b>Partition layout.</b> Choose the coarsest grain under your size limit: 10 GB a day with a 500 GB limit suits monthly partitions; 500 GB a day with a 100 GB limit suits days, and 5 TB a day needs hours.</p>
<p><b>Serving at scale.</b> Reads of 100,000 per second at 10,000 per shard, writes of 10,000 at 2,000 per shard, and 2 TB at 500 GB per shard: 10, 5 and 4 shards are needed, so <b>10</b>.</p>
<p><b>Noisy neighbours.</b> One customer shouldn't starve others. With demands 10, 50 and 100 and capacity 90, max-min fairness gives 10, 40 and 40.</p>
<p><b>Estimate cost in the design.</b> 100 TB at 23, 300 hours × 10 nodes × 0.5, and 50 MB/s of streaming comes to 5,260 a month, with storage the largest, at these made-up prices. Would batch be cheaper? Say so.</p>
<p><b>Will it last?</b> Load of 100, capacity 400, growing 10% monthly: 15 months. Know when your design breaks.</p>
<p><b>Rank your risks</b> by likelihood × impact. Schema change (4 × 4 = 16) comes before late data (10) and source outage (10). Say what you'd do about the top ones.</p>
<p><b>Data mesh</b> gives domain teams ownership of their data as a product, with a central platform team. It solves a central team becoming a bottleneck, and needs mature teams. Datasets with no owner, or one team owning everything, are warning signs.</p>
<p><b>What separates the very best?</b></p>
<ul><li>They ask what decision the data supports.</li>
<li>They pick the simplest thing that works, and say what would change that.</li>
<li>They design for failure, and measure cost.</li>
<li>They explain to non-engineers clearly.</li></ul>
""", practice=["Monthly Cost Estimate", "Rank the Risks", "Sharding a Key-Value Table", "Tenant Quotas", "Data Mesh Ownership", "Growth Headroom"])
