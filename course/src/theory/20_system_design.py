from lib import *

THEORY("Design questions to practise aloud", """
<table><tr><th>Prompt</th><th>Must mention</th></tr>
<tr><td>Clickstream analytics</td><td>collector, Kafka, dedupe, sessions, late data</td></tr>
<tr><td>Replicate a database</td><td>CDC, ordering, merge, schema changes</td></tr>
<tr><td>Ride-share live metrics</td><td>streaming windows, real-time OLAP, surge by area</td></tr>
<tr><td>Payments ledger reporting</td><td>exactly-once, reconciliation, audit, immutability</td></tr>
<tr><td>IoT sensors at huge scale</td><td>partitioning, downsampling, retention tiers</td></tr>
<tr><td>Feature store</td><td>online and offline, point-in-time correctness</td></tr>
<tr><td>Company data platform</td><td>lakehouse, catalog, access control, cost, ownership</td></tr>
<tr><td>Search or RAG ingestion</td><td>incremental updates, deletes, freshness</td></tr></table>
""")
FAQ("How do you choose between Lambda and Kappa?", "<p>Kappa is simpler if one stream path can do everything, and replay is feasible. Lambda may suit heavy historical computation alongside real-time needs, at the cost of two code paths.</p>")
FAQ("How do you handle a sudden 10× traffic spike?", "<p>Kafka buffers it, consumers autoscale, and backpressure limits intake. Dashboards may lag briefly but no data's lost, as long as retention covers the catch-up.</p>")
FAQ("Warehouse or lakehouse?", "<p>A warehouse is simplest for SQL analytics. A lakehouse suits very large or mixed workloads, machine learning, and using several engines on open formats.</p>")
FAQ("How do you guarantee no data loss?", "<p>Durable ingest with replication, acks=all, keeping raw data, checkpoints, reconciliation, and alerts when counts differ.</p>")
FAQ("How do you make a design cheaper?", "<p>Reduce freshness where it isn't needed, use columnar formats and partitions, tier old data, autoscale, use spot instances for batch, and remove unused tables.</p>")
FAQ("Scenario: design a daily sales report for 1,000 stores.", "<p>Probably batch: extract nightly or via CDC, load raw, build a star schema with dbt, add quality checks and reconciliation against totals, then publish atomically. Avoid streaming unless needed.</p>")
FAQ("Scenario: you must add real-time fraud features to a batch platform.", "<p>Add a stream from Kafka for velocity features, stored in a low-latency store. Share definitions with batch to avoid skew, and keep batch as the source of truth for training.</p>")
FAQ("Scenario: the interviewer pushes back on your choice. How do you respond?", "<p>Treat it as useful information. Ask what constraint they're thinking of, explain your trade-off again, and change your design if the new information justifies it.</p>")
