# Data Engineering from Scratch to Advanced

21 topics · theory with 193 theory questions · 91 lessons from basics to advanced · 420 practice questions · A step-by-step and an efficient answer for each, which you can watch run line by line.

**Live site:** https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/

Every solution is run against its test cases by `build.py` before the site is generated, and each animation is recorded from a real run of the code you see.

## Topics

- [How Data Flows](#how-data-flows) — What a data engineer actually does: the data lifecycle, ETL vs ELT, OLTP vs OLAP, batch vs streaming, and how to think about volume, freshness and reliability. No experience needed.
- [Python for Pipelines](#python-for-pipelines) — The Python a data engineer uses every day: dates and time zones, processing files too big for memory with generators, batching, retries, validation, logging and writing code you can test.
- [SQL Foundations](#sql-foundations) — The most important skill in data engineering, from your very first query: SELECT, WHERE, sorting, aggregates, GROUP BY, HAVING, all the joins, NULLs, CASE and subqueries, on a real database.
- [Advanced SQL](#advanced-sql) — The SQL that separates beginners from professionals: CTEs, every window function, top-N per group, running totals, sessionisation, gaps and islands, deduplication, retention, funnels and recursive queries.
- [How Databases Work](#how-databases-work) — What's inside a database: pages, B-trees and indexes, query plans and join algorithms, transactions and isolation levels, write-ahead logs, locks, MVCC and LSM trees. You'll build each one in miniature.
- [Data Modelling](#data-modelling) — How to design tables people can trust: grain, keys, normalisation, star schemas, facts and dimensions, slowly changing dimensions, snapshots and surrogate keys. This is what separates senior engineers.
- [Files, Formats & Storage](#files-formats-storage) — How data is laid out on disk and why it decides your speed and bill: CSV vs JSON vs Parquet, columnar storage, compression, run-length and dictionary encoding, partitioning, the small-file problem and object storage.
- [Engineering Toolbox](#engineering-toolbox) — The everyday skills around the data: Linux commands, Git, Docker, cron, testing, CI/CD and environments. Each idea is modelled in Python, so you understand what the tools are really doing.
- [Pipeline Patterns](#pipeline-patterns) — The heart of the job: idempotent loads, incremental processing, watermarks, merge and upsert, change data capture, backfills, late data, deduplication, dead-letter queues and designing for failure.
- [Distributed Systems](#distributed-systems) — Why big data tools work the way they do: partitioning, MapReduce, replication, quorums, consistent hashing, CAP, failures, Amdahl's law and exactly-once. Understand this and Spark and Kafka make sense.
- [Spark Foundations](#spark-foundations) — Apache Spark from zero: the driver and executors, lazy evaluation, transformations vs actions, narrow vs wide, DataFrames and PySpark's API. You build a tiny Spark in plain Python to see how it works, then run the real thing in the labs.
- [Spark Tuning & Internals](#spark-tuning-internals) — Make Spark fast and stop it crashing: join strategies, broadcast, skew and salting, shuffle tuning, adaptive execution, memory, out-of-memory errors, file sizes, reading the Spark UI, and real debugging.
- [Orchestration With Airflow](#orchestration-with-airflow) — Running pipelines reliably: DAGs and topological order, schedules and data intervals, catchup and backfills, retries, sensors, XComs, pools and common mistakes. You'll build a tiny scheduler to see how it works.
- [Kafka & Messaging](#kafka-messaging) — The backbone of streaming: logs, topics and partitions, keys and ordering, consumer groups, offsets and lag, delivery guarantees, replication, retention and compaction, schemas. You'll build a tiny Kafka in Python.
- [Stream Processing](#stream-processing) — Processing data that never ends: event time vs processing time, tumbling, sliding and session windows, watermarks and late data, stateful processing, stream joins, checkpoints and exactly-once, with Spark and Flink in mind.
- [Data Quality & Observability](#data-quality-observability) — Trustworthy data: the dimensions of quality, tests for nulls, uniqueness, ranges and freshness, anomaly detection, reconciliation, data contracts, lineage and running incidents. This is where a QA background becomes a superpower.
- [Lakehouse & Table Formats](#lakehouse-table-formats) — Database features on cheap files: why plain lakes break, how Iceberg and Delta use snapshots and manifests, ACID on object storage, time travel, MERGE, copy-on-write vs merge-on-read, compaction and clustering.
- [Warehouses & dbt](#warehouses-dbt) — Modern analytics engineering: how cloud warehouses store and bill, clustering and distribution keys, views vs tables vs materialized views, and dbt's models, tests, incremental loads and snapshots. You'll build a tiny dbt.
- [Cloud, Cost & Security](#cloud-cost-security) — Running data platforms on AWS responsibly: S3, Glue, EMR, Athena and Redshift, IAM permissions, encryption, masking and pseudonymising personal data, access control, privacy law, reliability targets and controlling the bill.
- [Data System Design](#data-system-design) — How senior engineers think: a repeatable design framework, sizing, choosing tools and walkthroughs of clickstream analytics, CDC to a lake, real-time dashboards and data platforms, with the trade-offs interviewers want to hear.
- [Data Engineering for AI](#data-engineering-for-ai) — The data behind models and LLMs: feature stores and point-in-time joins, leakage, dataset versioning, RAG ingestion pipelines, incremental embedding, deduplication, PII scrubbing and evaluation data. It's a bridge from data engineering to AI engineering.

## How Data Flows

| # | Question | Level | Concept |
|---|---|---|---|
| 1 | [Extract: Parse CSV Text](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/big-picture/extract-parse-csv-text) | Easy | The E in ETL |
| 2 | [Transform: Clean One Record](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/big-picture/transform-clean-one-record) | Easy | The T in ETL |
| 3 | [Load: Good Rows and Bad Rows](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/big-picture/load-good-rows-and-bad-rows) | Easy | Don't lose data silently |
| 4 | [A Tiny ETL Pipeline](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/big-picture/a-tiny-etl-pipeline) | Medium | All three steps together |
| 5 | [How Much Data per Day?](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/big-picture/how-much-data-per-day) | Easy | Thinking in volume |
| 6 | [How Long to Process It?](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/big-picture/how-long-to-process-it) | Easy | Will it finish in time? |
| 7 | [Row Store vs Column Store Cost](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/big-picture/row-store-vs-column-store-cost) | Medium | Why analytics uses columns |
| 8 | [Data Freshness](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/big-picture/data-freshness) | Easy | How old is the data? |
| 9 | [Batch Size vs Latency](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/big-picture/batch-size-vs-latency) | Easy | The core trade-off |
| 10 | [Flatten a JSON Event](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/big-picture/flatten-a-json-event) | Medium | Nested to tabular |
| 11 | [Parse JSON Lines](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/big-picture/parse-json-lines) | Easy | The standard log format |
| 12 | [Remove Exact Duplicates](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/big-picture/remove-exact-duplicates) | Easy | Sources send things twice |
| 13 | [Which Tool for the Job?](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/big-picture/which-tool-for-the-job) | Easy | Latency decides |
| 14 | [Pipeline Reliability](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/big-picture/pipeline-reliability) | Medium | Chains multiply failures |
| 15 | [Storage Cost](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/big-picture/storage-cost) | Easy | Everything costs money |
| 16 | [Compression Savings](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/big-picture/compression-savings) | Easy | Why formats matter |
| 17 | [Peak vs Average Load](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/big-picture/peak-vs-average-load) | Easy | Design for the peak |
| 18 | [Lineage: What Breaks Downstream?](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/big-picture/lineage-what-breaks-downstream) | Medium | Who depends on what |
| 19 | [Daily Partition Path](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/big-picture/daily-partition-path) | Easy | How lakes are organised |
| 20 | [Schema Check on Arrival](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/big-picture/schema-check-on-arrival) | Medium | Catch changes early |

## Python for Pipelines

| # | Question | Level | Concept |
|---|---|---|---|
| 1 | [Chunk a Stream](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/python-for-de/chunk-a-stream) | Easy | Write in batches |
| 2 | [Generator Pipeline](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/python-for-de/generator-pipeline) | Medium | Process more than fits in memory |
| 3 | [Dates in a Range](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/python-for-de/dates-in-a-range) | Easy | Every backfill needs this |
| 4 | [Convert to UTC](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/python-for-de/convert-to-utc) | Medium | Store times in UTC |
| 5 | [Find Missing Days](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/python-for-de/find-missing-days) | Medium | Gaps in a partition list |
| 6 | [Retry With Backoff](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/python-for-de/retry-with-backoff) | Medium | Networks fail |
| 7 | [Parse a Log Line](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/python-for-de/parse-a-log-line) | Easy | Regex for logs |
| 8 | [Count Errors by Level](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/python-for-de/count-errors-by-level) | Easy | Log aggregation |
| 9 | [Validate a Record](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/python-for-de/validate-a-record) | Medium | Reject bad data with reasons |
| 10 | [Group Into Files by Key](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/python-for-de/group-into-files-by-key) | Easy | Partitioning by hand |
| 11 | [Sliding Time Window Count](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/python-for-de/sliding-time-window-count) | Medium | Rate per minute |
| 12 | [Merge Sorted Files](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/python-for-de/merge-sorted-files) | Medium | External sorting |
| 13 | [Top K From a Huge Stream](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/python-for-de/top-k-from-a-huge-stream) | Medium | Don't sort everything |
| 14 | [Reservoir Sampling](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/python-for-de/reservoir-sampling) | Hard | A fair sample of an unknown length |
| 15 | [Stable Hash Bucket](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/python-for-de/stable-hash-bucket) | Medium | Same key, same place |
| 16 | [Coerce Types With a Schema](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/python-for-de/coerce-types-with-a-schema) | Medium | Text in, typed out |
| 17 | [Mask Personal Data](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/python-for-de/mask-personal-data) | Easy | Never log it raw |
| 18 | [Read Config With Defaults](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/python-for-de/read-config-with-defaults) | Easy | Same code, every environment |
| 19 | [Run Summary Metrics](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/python-for-de/run-summary-metrics) | Medium | Every run should report |
| 20 | [Testable Transform](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/python-for-de/testable-transform) | Easy | Pure functions |

## SQL Foundations

| # | Question | Level | Concept |
|---|---|---|---|
| 1 | [Select Some Columns](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/sql-foundations/select-some-columns) | Easy | SELECT, ORDER BY |
| 2 | [Filter Rows](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/sql-foundations/filter-rows) | Easy | WHERE |
| 3 | [IN, BETWEEN and LIKE](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/sql-foundations/in-between-and-like) | Easy | More filters |
| 4 | [Finding NULLs](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/sql-foundations/finding-nulls) | Easy | NULL isn't a value |
| 5 | [Aggregates](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/sql-foundations/aggregates) | Easy | COUNT, SUM, AVG, MIN, MAX |
| 6 | [GROUP BY](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/sql-foundations/group-by) | Easy | One row per group |
| 7 | [HAVING](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/sql-foundations/having) | Easy | Filter groups |
| 8 | [INNER JOIN](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/sql-foundations/inner-join) | Easy | Combine tables |
| 9 | [LEFT JOIN to Find What's Missing](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/sql-foundations/left-join-to-find-whats-missing) | Medium | Users with no orders |
| 10 | [Revenue per Category](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/sql-foundations/revenue-per-category) | Medium | Join, then aggregate |
| 11 | [CASE Expressions](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/sql-foundations/case-expressions) | Easy | If/else in SQL |
| 12 | [COALESCE](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/sql-foundations/coalesce) | Easy | Defaults for NULL |
| 13 | [COUNT Traps](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/sql-foundations/count-traps) | Easy | Rows vs values |
| 14 | [Joins Multiply Rows](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/sql-foundations/joins-multiply-rows) | Medium | The classic revenue bug |
| 15 | [Subquery vs Average](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/sql-foundations/subquery-vs-average) | Medium | Compare against a total |
| 16 | [EXISTS](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/sql-foundations/exists) | Medium | Is there any? |
| 17 | [Monthly Totals](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/sql-foundations/monthly-totals) | Medium | Grouping by date |
| 18 | [Top Spender](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/sql-foundations/top-spender) | Medium | Putting it together |
| 19 | [UNION vs UNION ALL](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/sql-foundations/union-vs-union-all) | Easy | Stacking rows |
| 20 | [Share of Paid Orders](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/sql-foundations/share-of-paid-orders) | Medium | Conditional aggregation |

## Advanced SQL

| # | Question | Level | Concept |
|---|---|---|---|
| 1 | [Readable Steps With a CTE](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/sql-advanced/readable-steps-with-a-cte) | Easy | WITH |
| 2 | [Number the Rows](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/sql-advanced/number-the-rows) | Easy | ROW_NUMBER |
| 3 | [RANK vs DENSE_RANK](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/sql-advanced/rank-vs-dense-rank) | Medium | Ties |
| 4 | [Top Sale per Region](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/sql-advanced/top-sale-per-region) | Medium | Top N per group |
| 5 | [Running Total](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/sql-advanced/running-total) | Medium | SUM OVER |
| 6 | [Moving Average](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/sql-advanced/moving-average) | Medium | Frames |
| 7 | [Compare With the Previous Row](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/sql-advanced/compare-with-the-previous-row) | Medium | LAG |
| 8 | [Share Within a Group](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/sql-advanced/share-within-a-group) | Medium | Window without collapsing |
| 9 | [Latest Row per Key](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/sql-advanced/latest-row-per-key) | Medium | The most-used dedupe |
| 10 | [Find Exact Duplicates](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/sql-advanced/find-exact-duplicates) | Easy | Data quality |
| 11 | [Sessionise Clicks](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/sql-advanced/sessionise-clicks) | Hard | New session after 30 minutes |
| 12 | [Longest Login Streak](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/sql-advanced/longest-login-streak) | Hard | Gaps and islands |
| 13 | [Find Gaps in a Sequence](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/sql-advanced/find-gaps-in-a-sequence) | Medium | Missing ranges |
| 14 | [Funnel Conversion](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/sql-advanced/funnel-conversion) | Medium | Who reached each step? |
| 15 | [Weekly Retention](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/sql-advanced/weekly-retention) | Hard | Cohorts |
| 16 | [Pivot Rows to Columns](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/sql-advanced/pivot-rows-to-columns) | Medium | Reports |
| 17 | [Walk a Hierarchy](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/sql-advanced/walk-a-hierarchy) | Hard | Recursive CTE |
| 18 | [Generate a Date Spine](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/sql-advanced/generate-a-date-spine) | Medium | Fill the missing days |
| 19 | [First and Last in a Group](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/sql-advanced/first-and-last-in-a-group) | Medium | FIRST_VALUE |
| 20 | [Split Into Buckets](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/sql-advanced/split-into-buckets) | Medium | NTILE |

## How Databases Work

| # | Question | Level | Concept |
|---|---|---|---|
| 1 | [Scan vs Index: Comparisons](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/database-internals/scan-vs-index-comparisons) | Easy | Why indexes exist |
| 2 | [Index Lookup in a Sorted List](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/database-internals/index-lookup-in-a-sorted-list) | Easy | The core idea |
| 3 | [B-Tree Height](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/database-internals/b-tree-height) | Medium | Why so few disk reads? |
| 4 | [Range Scan With an Index](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/database-internals/range-scan-with-an-index) | Easy | Sorted data helps ranges |
| 5 | [Composite Index: Leftmost Rule](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/database-internals/composite-index-leftmost-rule) | Medium | Column order matters |
| 6 | [Selectivity](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/database-internals/selectivity) | Easy | Is the index worth using? |
| 7 | [Nested Loop Join](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/database-internals/nested-loop-join) | Easy | The simplest join |
| 8 | [Hash Join](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/database-internals/hash-join) | Medium | The workhorse |
| 9 | [Sort-Merge Join](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/database-internals/sort-merge-join) | Hard | When both sides are sorted |
| 10 | [Rows per Page](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/database-internals/rows-per-page) | Easy | Disk works in pages |
| 11 | [Atomic Transfer](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/database-internals/atomic-transfer) | Medium | All or nothing |
| 12 | [Recover From a Write-Ahead Log](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/database-internals/recover-from-a-write-ahead-log) | Medium | Durability |
| 13 | [Lost Update](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/database-internals/lost-update) | Medium | Why isolation matters |
| 14 | [MVCC: Which Version Do I See?](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/database-internals/mvcc-which-version-do-i-see) | Hard | Readers don't block writers |
| 15 | [Deadlock Detection](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/database-internals/deadlock-detection) | Hard | A cycle in who waits for whom |
| 16 | [A Tiny LSM Tree](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/database-internals/a-tiny-lsm-tree) | Hard | Write-optimised storage |
| 17 | [Bloom Filter](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/database-internals/bloom-filter) | Hard | Definitely not, or maybe |
| 18 | [Estimate Rows After a Filter](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/database-internals/estimate-rows-after-a-filter) | Medium | What the planner guesses |
| 19 | [Pick a Join Strategy](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/database-internals/pick-a-join-strategy) | Medium | The optimizer's choice |
| 20 | [Write Amplification](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/database-internals/write-amplification) | Medium | Indexes aren't free |

## Data Modelling

| # | Question | Level | Concept |
|---|---|---|---|
| 1 | [Is This Column a Key?](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-modeling/is-this-column-a-key) | Easy | Check before trusting |
| 2 | [Find the Grain](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-modeling/find-the-grain) | Medium | One row per what? |
| 3 | [Normalise a Flat Table](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-modeling/normalise-a-flat-table) | Medium | Each fact in one place |
| 4 | [Spot the Update Anomaly](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-modeling/spot-the-update-anomaly) | Easy | Why normalise? |
| 5 | [Star Schema Query](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-modeling/star-schema-query) | Easy | Fact joined to dimensions |
| 6 | [Point-in-Time Join](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-modeling/point-in-time-join) | Hard | SCD 2: what was true then? |
| 7 | [SCD Type 1: Overwrite](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-modeling/scd-type-1-overwrite) | Easy | No history kept |
| 8 | [SCD Type 2: Keep History](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-modeling/scd-type-2-keep-history) | Hard | Close the old, open the new |
| 9 | [Check SCD 2 Integrity](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-modeling/check-scd-2-integrity) | Medium | No gaps or overlaps |
| 10 | [Surrogate Keys](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-modeling/surrogate-keys) | Easy | Stable internal ids |
| 11 | [Hash Key From Several Columns](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-modeling/hash-key-from-several-columns) | Medium | Deterministic keys |
| 12 | [Build a Date Dimension](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-modeling/build-a-date-dimension) | Easy | Every warehouse has one |
| 13 | [Additive or Not?](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-modeling/additive-or-not) | Medium | Which measures can you SUM? |
| 14 | [Daily Snapshot From Events](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-modeling/daily-snapshot-from-events) | Medium | Accumulate to a state |
| 15 | [Bridge Table: Avoid Double Counting](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-modeling/bridge-table-avoid-double-counting) | Hard | Many-to-many |
| 16 | [Unknown Dimension Member](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-modeling/unknown-dimension-member) | Medium | Don't drop facts |
| 17 | [Wide Table or Star?](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-modeling/wide-table-or-star) | Easy | Storage trade-offs |
| 18 | [Late-Arriving Fact](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-modeling/late-arriving-fact) | Hard | Which dimension row applies? |
| 19 | [Check Foreign Keys](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-modeling/check-foreign-keys) | Easy | Referential integrity |
| 20 | [Rollup Must Reconcile](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-modeling/rollup-must-reconcile) | Easy | Trust but verify |

## Files, Formats & Storage

| # | Question | Level | Concept |
|---|---|---|---|
| 1 | [Rows to Columns](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/storage-formats/rows-to-columns) | Easy | The columnar idea |
| 2 | [Run-Length Encoding](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/storage-formats/run-length-encoding) | Easy | Repeated values shrink |
| 3 | [Dictionary Encoding](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/storage-formats/dictionary-encoding) | Easy | Few distinct values |
| 4 | [Delta Encoding](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/storage-formats/delta-encoding) | Easy | Timestamps compress well |
| 5 | [Encoded Size Comparison](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/storage-formats/encoded-size-comparison) | Medium | Which encoding wins? |
| 6 | [Sorted Data Compresses Better](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/storage-formats/sorted-data-compresses-better) | Medium | Order matters |
| 7 | [Partition Pruning](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/storage-formats/partition-pruning) | Easy | Skip whole folders |
| 8 | [Min/Max Skipping](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/storage-formats/min-max-skipping) | Medium | Row group statistics |
| 9 | [Choosing a Partition Column](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/storage-formats/choosing-a-partition-column) | Medium | Too few or too many |
| 10 | [The Small File Problem](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/storage-formats/the-small-file-problem) | Medium | Metadata overhead |
| 11 | [Compact Small Files](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/storage-formats/compact-small-files) | Medium | Merge into target size |
| 12 | [How Many Output Files?](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/storage-formats/how-many-output-files) | Easy | Sizing a write |
| 13 | [Hive-Style Partition Paths](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/storage-formats/hive-style-partition-paths) | Easy | Parse them back |
| 14 | [Schema Evolution: What's Safe?](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/storage-formats/schema-evolution-whats-safe) | Medium | Change without breaking readers |
| 15 | [Bucket for Sampling and Joins](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/storage-formats/bucket-for-sampling-and-joins) | Medium | Hash partitioning |
| 16 | [Compare Query Cost by Format](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/storage-formats/compare-query-cost-by-format) | Medium | Priced per byte scanned |
| 17 | [Storage Tier Choice](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/storage-formats/storage-tier-choice) | Medium | Hot, warm, cold |
| 18 | [Nested to Parquet-Friendly](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/storage-formats/nested-to-parquet-friendly) | Medium | Explode arrays |
| 19 | [Checksums Catch Corruption](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/storage-formats/checksums-catch-corruption) | Medium | Trust, but verify |
| 20 | [Bit-Width of a Dictionary](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/storage-formats/bit-width-of-a-dictionary) | Medium | Why real encodings are tiny |

## Engineering Toolbox

| # | Question | Level | Concept |
|---|---|---|---|
| 1 | [Build grep in Python](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/engineering-toolbox/build-grep-in-python) | Easy | Search lines |
| 2 | [sort | uniq -c | sort -rn](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/engineering-toolbox/sort-uniq-c-sort-rn) | Easy | The most useful one-liner |
| 3 | [awk: Pick a Column](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/engineering-toolbox/awk-pick-a-column) | Easy | Field extraction |
| 4 | [tail -n](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/engineering-toolbox/tail-n) | Easy | Last lines without loading everything |
| 5 | [Does Cron Match This Time?](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/engineering-toolbox/does-cron-match-this-time) | Medium | Scheduling basics |
| 6 | [Next Cron Runs](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/engineering-toolbox/next-cron-runs) | Medium | When will it fire? |
| 7 | [Git: Which Commits Are New?](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/engineering-toolbox/git-which-commits-are-new) | Medium | Commits form a graph |
| 8 | [Semantic Version Bump](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/engineering-toolbox/semantic-version-bump) | Easy | Releases |
| 9 | [Docker Layer Cache](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/engineering-toolbox/docker-layer-cache) | Medium | Why order matters |
| 10 | [Environment Variables With Defaults](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/engineering-toolbox/environment-variables-with-defaults) | Easy | Twelve-factor config |
| 11 | [Find Secrets Before Committing](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/engineering-toolbox/find-secrets-before-committing) | Medium | Never commit a key |
| 12 | [Unit Test Runner](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/engineering-toolbox/unit-test-runner) | Medium | What pytest does |
| 13 | [Mock an External Call](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/engineering-toolbox/mock-an-external-call) | Medium | Test without the network |
| 14 | [CI Pipeline Order](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/engineering-toolbox/ci-pipeline-order) | Medium | Fail fast |
| 15 | [Disk Usage Report](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/engineering-toolbox/disk-usage-report) | Easy | du in Python |
| 16 | [Merge Conflict Check](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/engineering-toolbox/merge-conflict-check) | Medium | Three-way merge |
| 17 | [Log Rotation](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/engineering-toolbox/log-rotation) | Easy | Don't fill the disk |
| 18 | [Dependency Pin Check](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/engineering-toolbox/dependency-pin-check) | Easy | Reproducible builds |
| 19 | [Parse Exit Codes](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/engineering-toolbox/parse-exit-codes) | Easy | Did the job really succeed? |
| 20 | [File Permissions](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/engineering-toolbox/file-permissions) | Easy | chmod 640 |

## Pipeline Patterns

| # | Question | Level | Concept |
|---|---|---|---|
| 1 | [Naive Append Isn't Idempotent](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/pipeline-patterns/naive-append-isnt-idempotent) | Easy | The classic bug |
| 2 | [Overwrite a Partition](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/pipeline-patterns/overwrite-a-partition) | Easy | The simplest safe pattern |
| 3 | [Upsert (MERGE)](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/pipeline-patterns/upsert-merge) | Medium | Insert or update by key |
| 4 | [Upsert Keeps Only Newer](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/pipeline-patterns/upsert-keeps-only-newer) | Medium | Out-of-order updates |
| 5 | [High-Watermark Incremental Load](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/pipeline-patterns/high-watermark-incremental-load) | Medium | Only what's new |
| 6 | [Watermark With a Lookback](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/pipeline-patterns/watermark-with-a-lookback) | Medium | Don't miss late rows |
| 7 | [Apply Change Data Capture](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/pipeline-patterns/apply-change-data-capture) | Medium | Replay inserts, updates and deletes |
| 8 | [Compact a CDC Batch](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/pipeline-patterns/compact-a-cdc-batch) | Medium | Last event per key wins |
| 9 | [Soft Deletes](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/pipeline-patterns/soft-deletes) | Easy | Keep the history |
| 10 | [Plan a Backfill](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/pipeline-patterns/plan-a-backfill) | Medium | Reprocess history in pieces |
| 11 | [Find What's Left to Backfill](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/pipeline-patterns/find-whats-left-to-backfill) | Easy | Safe to resume |
| 12 | [Write-Audit-Publish](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/pipeline-patterns/write-audit-publish) | Medium | Never show bad data |
| 13 | [Dead-Letter Queue](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/pipeline-patterns/dead-letter-queue) | Medium | One bad row shouldn't stop the pipeline |
| 14 | [Row Hash for Change Detection](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/pipeline-patterns/row-hash-for-change-detection) | Medium | What actually changed? |
| 15 | [Dedupe a Stream With a TTL](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/pipeline-patterns/dedupe-a-stream-with-a-ttl) | Hard | Don't remember forever |
| 16 | [Which Partitions to Rerun?](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/pipeline-patterns/which-partitions-to-rerun) | Medium | Late data |
| 17 | [Atomic Swap](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/pipeline-patterns/atomic-swap) | Medium | Readers never see half a load |
| 18 | [Reconcile Source and Target](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/pipeline-patterns/reconcile-source-and-target) | Easy | Did everything arrive? |
| 19 | [Checkpoint and Resume](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/pipeline-patterns/checkpoint-and-resume) | Medium | Don't start from zero |
| 20 | [Choose Full or Incremental](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/pipeline-patterns/choose-full-or-incremental) | Easy | Simple until it isn't |

## Distributed Systems

| # | Question | Level | Concept |
|---|---|---|---|
| 1 | [Word Count With MapReduce](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/distributed-systems/word-count-with-mapreduce) | Easy | The original big data idea |
| 2 | [Hash Partitioning](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/distributed-systems/hash-partitioning) | Easy | Where does each key live? |
| 3 | [Range Partitioning](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/distributed-systems/range-partitioning) | Medium | Sorted across machines |
| 4 | [Measure Skew](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/distributed-systems/measure-skew) | Medium | One slow partition slows everything |
| 5 | [Salting a Hot Key](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/distributed-systems/salting-a-hot-key) | Medium | Break up skew |
| 6 | [Rehash Cost: Mod vs Consistent](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/distributed-systems/rehash-cost-mod-vs-consistent) | Hard | Adding a machine |
| 7 | [Consistent Hashing](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/distributed-systems/consistent-hashing) | Hard | Move little when machines change |
| 8 | [Quorum Reads and Writes](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/distributed-systems/quorum-reads-and-writes) | Medium | R + W > N |
| 9 | [Replication Lag: Stale Read?](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/distributed-systems/replication-lag-stale-read) | Easy | Eventually consistent |
| 10 | [Amdahl's Law](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/distributed-systems/amdahls-law) | Medium | Why more machines stop helping |
| 11 | [Chance of Failure at Scale](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/distributed-systems/chance-of-failure-at-scale) | Easy | Failure is normal |
| 12 | [Retries Without Double Effects](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/distributed-systems/retries-without-double-effects) | Medium | Idempotency keys |
| 13 | [Delivery Semantics](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/distributed-systems/delivery-semantics) | Medium | At most, at least, exactly once |
| 14 | [Vector Clocks: Which Came First?](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/distributed-systems/vector-clocks-which-came-first) | Hard | No shared clock |
| 15 | [Leader Election by Majority](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/distributed-systems/leader-election-by-majority) | Medium | Who's in charge? |
| 16 | [Heartbeats: Who's Dead?](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/distributed-systems/heartbeats-whos-dead) | Easy | Detecting failures |
| 17 | [Reassign Tasks After a Failure](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/distributed-systems/reassign-tasks-after-a-failure) | Medium | Lineage rebuilds work |
| 18 | [Speculative Execution](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/distributed-systems/speculative-execution) | Medium | Beat the stragglers |
| 19 | [Shuffle Volume](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/distributed-systems/shuffle-volume) | Medium | Network is the bottleneck |
| 20 | [Broadcast or Shuffle?](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/distributed-systems/broadcast-or-shuffle) | Medium | The cost of a join |

## Spark Foundations

| # | Question | Level | Concept |
|---|---|---|---|
| 1 | [Split Data Into Partitions](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/spark-foundations/split-data-into-partitions) | Easy | The unit of parallelism |
| 2 | [Map Over Partitions](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/spark-foundations/map-over-partitions) | Easy | Narrow transformation |
| 3 | [Lazy Evaluation](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/spark-foundations/lazy-evaluation) | Medium | Nothing runs until an action |
| 4 | [Predicate Pushdown](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/spark-foundations/predicate-pushdown) | Medium | Why laziness saves work |
| 5 | [Column Pruning](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/spark-foundations/column-pruning) | Easy | Read only what you need |
| 6 | [Narrow or Wide?](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/spark-foundations/narrow-or-wide) | Easy | Does data move? |
| 7 | [Stages From a Plan](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/spark-foundations/stages-from-a-plan) | Medium | Shuffles cut stages |
| 8 | [Shuffle by Key](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/spark-foundations/shuffle-by-key) | Medium | Bring keys together |
| 9 | [groupBy + sum, Spark Style](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/spark-foundations/groupby-sum-spark-style) | Medium | Partial, shuffle, final |
| 10 | [A Tiny DataFrame](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/spark-foundations/a-tiny-dataframe) | Medium | select, filter, withColumn |
| 11 | [Parallel Time on a Cluster](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/spark-foundations/parallel-time-on-a-cluster) | Easy | Tasks and slots |
| 12 | [How Many Partitions?](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/spark-foundations/how-many-partitions) | Medium | A common rule of thumb |
| 13 | [Sizing an Executor](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/spark-foundations/sizing-an-executor) | Medium | Memory per core |
| 14 | [Cache or Recompute?](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/spark-foundations/cache-or-recompute) | Medium | Spend memory to save time |
| 15 | [Coalesce vs Repartition](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/spark-foundations/coalesce-vs-repartition) | Medium | Shrinking without a shuffle |
| 16 | [Lineage: Recompute a Lost Partition](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/spark-foundations/lineage-recompute-a-lost-partition) | Medium | Fault tolerance |
| 17 | [UDF vs Built-in Cost](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/spark-foundations/udf-vs-built-in-cost) | Easy | Why avoid Python UDFs |
| 18 | [Read a Plan](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/spark-foundations/read-a-plan) | Medium | Does it use pushdown? |
| 19 | [Explode and Collect](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/spark-foundations/explode-and-collect) | Easy | Array columns |
| 20 | [Action or Transformation?](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/spark-foundations/action-or-transformation) | Easy | What triggers a job? |

## Spark Tuning & Internals

| # | Question | Level | Concept |
|---|---|---|---|
| 1 | [Pick a Join Strategy](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/spark-internals/pick-a-join-strategy) | Medium | What Spark chooses |
| 2 | [Broadcast Join Simulation](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/spark-internals/broadcast-join-simulation) | Medium | Each partition joins locally |
| 3 | [Find the Skewed Partitions](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/spark-internals/find-the-skewed-partitions) | Medium | Spark's AQE rule |
| 4 | [Salted Join](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/spark-internals/salted-join) | Hard | Fix a hot key |
| 5 | [Isolate the Hot Key](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/spark-internals/isolate-the-hot-key) | Medium | Another fix for skew |
| 6 | [Null Keys Cause Skew](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/spark-internals/null-keys-cause-skew) | Easy | The classic surprise |
| 7 | [Shuffle Partitions Setting](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/spark-internals/shuffle-partitions-setting) | Medium | The default is rarely right |
| 8 | [AQE: Coalesce Small Partitions](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/spark-internals/aqe-coalesce-small-partitions) | Medium | Adaptive execution |
| 9 | [Executor Memory Breakdown](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/spark-internals/executor-memory-breakdown) | Medium | Where does memory go? |
| 10 | [Diagnose an Out-of-Memory](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/spark-internals/diagnose-an-out-of-memory) | Medium | Driver or executor? |
| 11 | [Files Written per Partition](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/spark-internals/files-written-per-partition) | Medium | How jobs make small files |
| 12 | [Spot the Straggler Task](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/spark-internals/spot-the-straggler-task) | Easy | Read the Spark UI |
| 13 | [Dynamic Allocation](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/spark-internals/dynamic-allocation) | Medium | Scale to the backlog |
| 14 | [Cost of a Cluster Run](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/spark-internals/cost-of-a-cluster-run) | Easy | Time × machines |
| 15 | [Bucketed Join Avoids Shuffle](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/spark-internals/bucketed-join-avoids-shuffle) | Medium | Pay once at write time |
| 16 | [Dynamic Partition Pruning](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/spark-internals/dynamic-partition-pruning) | Medium | Filter via the join |
| 17 | [Sort-Merge Spill](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/spark-internals/sort-merge-spill) | Medium | Memory runs out, disk takes over |
| 18 | [Window With No Partition](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/spark-internals/window-with-no-partition) | Medium | A hidden single-task trap |
| 19 | [Debug a Slow Job](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/spark-internals/debug-a-slow-job) | Hard | Find the real bottleneck |
| 20 | [Parquet Target File Count](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/spark-internals/parquet-target-file-count) | Easy | repartition before write |

## Orchestration With Airflow

| # | Question | Level | Concept |
|---|---|---|---|
| 1 | [Is This a Valid DAG?](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/airflow/is-this-a-valid-dag) | Medium | No cycles allowed |
| 2 | [Run Order](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/airflow/run-order) | Medium | Topological sort |
| 3 | [Parallel Levels](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/airflow/parallel-levels) | Medium | What can run at once? |
| 4 | [Critical Path](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/airflow/critical-path) | Hard | The minimum time for a DAG |
| 5 | [Daily Data Intervals](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/airflow/daily-data-intervals) | Medium | Airflow's most confusing idea |
| 6 | [How Many Runs Will Catchup Create?](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/airflow/how-many-runs-will-catchup-create) | Easy | A classic surprise |
| 7 | [Retries With Exponential Delay](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/airflow/retries-with-exponential-delay) | Easy | When does each retry happen? |
| 8 | [Task State After Attempts](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/airflow/task-state-after-attempts) | Easy | Success, retry or failed |
| 9 | [Upstream Failed](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/airflow/upstream-failed) | Medium | Trigger rules |
| 10 | [What Needs Rerunning?](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/airflow/what-needs-rerunning) | Medium | Clear downstream |
| 11 | [Sensor: Wait for a File](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/airflow/sensor-wait-for-a-file) | Easy | Poke until ready |
| 12 | [Pool Scheduling](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/airflow/pool-scheduling) | Hard | Limit concurrency |
| 13 | [Is the SLA Met?](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/airflow/is-the-sla-met) | Easy | Alert before anyone complains |
| 14 | [Don't Pass Data Through XCom](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/airflow/dont-pass-data-through-xcom) | Easy | Pass a reference |
| 15 | [Find Top-Level Work in a DAG File](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/airflow/find-top-level-work-in-a-dag-file) | Medium | The scheduler parses it constantly |
| 16 | [Render a Date Template](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/airflow/render-a-date-template) | Easy | Jinja in Airflow |
| 17 | [Backfill With a Concurrency Limit](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/airflow/backfill-with-a-concurrency-limit) | Medium | Don't overload |
| 18 | [A Tiny Scheduler](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/airflow/a-tiny-scheduler) | Hard | Put it all together |
| 19 | [Duration Anomaly](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/airflow/duration-anomaly) | Medium | Spot slowdowns early |
| 20 | [Which Tasks Are Ready?](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/airflow/which-tasks-are-ready) | Easy | The scheduler's core loop |

## Kafka & Messaging

| # | Question | Level | Concept |
|---|---|---|---|
| 1 | [Append to a Log](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/kafka/append-to-a-log) | Easy | The core data structure |
| 2 | [Choose a Partition by Key](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/kafka/choose-a-partition-by-key) | Easy | Same key, same partition |
| 3 | [Does Order Hold?](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/kafka/does-order-hold) | Medium | Only within a partition |
| 4 | [Consumer Group Assignment](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/kafka/consumer-group-assignment) | Medium | Each partition goes to one member |
| 5 | [Consumer Lag](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/kafka/consumer-lag) | Easy | The number to alert on |
| 6 | [How Long to Catch Up?](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/kafka/how-long-to-catch-up) | Medium | Is the consumer keeping up? |
| 7 | [Partitions Needed](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/kafka/partitions-needed) | Easy | Sizing a topic |
| 8 | [Commit After Processing](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/kafka/commit-after-processing) | Medium | At-least-once |
| 9 | [Idempotent Consumer](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/kafka/idempotent-consumer) | Medium | Exactly-once in effect |
| 10 | [Producer Retries Reorder](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/kafka/producer-retries-reorder) | Medium | max.in.flight |
| 11 | [Log Compaction](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/kafka/log-compaction) | Medium | Keep the latest per key |
| 12 | [Retention by Time and Size](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/kafka/retention-by-time-and-size) | Medium | Old data goes away |
| 13 | [In-Sync Replicas](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/kafka/in-sync-replicas) | Medium | Durability trade-off |
| 14 | [High Watermark](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/kafka/high-watermark) | Medium | What consumers can read |
| 15 | [Rebalance Movement](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/kafka/rebalance-movement) | Medium | Eager vs sticky |
| 16 | [Schema Compatibility](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/kafka/schema-compatibility) | Medium | Don't break consumers |
| 17 | [Batching Trade-off](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/kafka/batching-trade-off) | Easy | Latency vs throughput |
| 18 | [Kafka Disk Sizing](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/kafka/kafka-disk-sizing) | Medium | Capacity planning |
| 19 | [Find the Hot Partition](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/kafka/find-the-hot-partition) | Easy | A bad key choice |
| 20 | [Outbox Pattern](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/kafka/outbox-pattern) | Hard | Database and Kafka together |

## Stream Processing

| # | Question | Level | Concept |
|---|---|---|---|
| 1 | [Tumbling Windows](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/streaming/tumbling-windows) | Easy | Fixed buckets |
| 2 | [Sliding Windows](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/streaming/sliding-windows) | Medium | One event, many windows |
| 3 | [Session Windows](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/streaming/session-windows) | Medium | Activity bursts |
| 4 | [Event Time vs Processing Time](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/streaming/event-time-vs-processing-time) | Easy | Which bucket? |
| 5 | [Compute the Watermark](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/streaming/compute-the-watermark) | Easy | How late is too late? |
| 6 | [Drop Late Events](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/streaming/drop-late-events) | Medium | Watermarks in action |
| 7 | [When Does a Window Fire?](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/streaming/when-does-a-window-fire) | Medium | Output mode: append |
| 8 | [Running Count With State](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/streaming/running-count-with-state) | Easy | Stateful processing |
| 9 | [State Growth](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/streaming/state-growth) | Medium | State can blow up |
| 10 | [Stream-Static Join](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/streaming/stream-static-join) | Easy | Enrich events |
| 11 | [Stream-Stream Join](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/streaming/stream-stream-join) | Hard | Both sides arrive over time |
| 12 | [Checkpoint and Replay](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/streaming/checkpoint-and-replay) | Medium | Fault tolerance |
| 13 | [Micro-Batch Latency](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/streaming/micro-batch-latency) | Easy | Spark's model |
| 14 | [Approximate Distinct Counts](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/streaming/approximate-distinct-counts) | Hard | HyperLogLog's idea |
| 15 | [Count-Min Sketch](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/streaming/count-min-sketch) | Hard | Frequencies with little memory |
| 16 | [Backpressure](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/streaming/backpressure) | Medium | When input outruns output |
| 17 | [Deduplicate With a Watermark](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/streaming/deduplicate-with-a-watermark) | Medium | Bound the state |
| 18 | [Lambda or Kappa?](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/streaming/lambda-or-kappa) | Easy | Two architectures |
| 19 | [Top K per Window](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/streaming/top-k-per-window) | Medium | Trending items |
| 20 | [Replays Need an Idempotent Sink](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/streaming/replays-need-an-idempotent-sink) | Medium | Exactly-once in effect |

## Data Quality & Observability

| # | Question | Level | Concept |
|---|---|---|---|
| 1 | [Null Rate per Column](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-quality/null-rate-per-column) | Easy | Completeness |
| 2 | [Uniqueness Check](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-quality/uniqueness-check) | Easy | Primary keys |
| 3 | [Accepted Values](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-quality/accepted-values) | Easy | Validity |
| 4 | [Range Check](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-quality/range-check) | Easy | Impossible values |
| 5 | [Referential Integrity](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-quality/referential-integrity) | Easy | Do the keys exist? |
| 6 | [Volume Anomaly](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-quality/volume-anomaly) | Medium | Is today's row count normal? |
| 7 | [Weekly Seasonality](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-quality/weekly-seasonality) | Medium | Don't alert every Sunday |
| 8 | [Distribution Drift](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-quality/distribution-drift) | Medium | PSI |
| 9 | [Freshness per Table](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-quality/freshness-per-table) | Easy | SLA dashboards |
| 10 | [A Small Test Framework](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-quality/a-small-test-framework) | Medium | How dbt tests work |
| 11 | [Severity: Warn or Stop?](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-quality/severity-warn-or-stop) | Medium | Not all failures are equal |
| 12 | [Quarantine Bad Rows](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-quality/quarantine-bad-rows) | Medium | Don't block the good ones |
| 13 | [Reconcile Totals](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-quality/reconcile-totals) | Easy | Do the sums agree? |
| 14 | [Check a Data Contract](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-quality/check-a-data-contract) | Medium | Promises between teams |
| 15 | [Impact Analysis](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-quality/impact-analysis) | Medium | Who's affected? |
| 16 | [Find Where Rows Were Lost](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-quality/find-where-rows-were-lost) | Medium | Debug by layer |
| 17 | [Alert Fatigue](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-quality/alert-fatigue) | Easy | Measure your alerts |
| 18 | [Incident Metrics](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-quality/incident-metrics) | Easy | Learn from failures |
| 19 | [Compare Two Versions of a Table](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-quality/compare-two-versions-of-a-table) | Medium | Test your change safely |
| 20 | [Profile a Column](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-quality/profile-a-column) | Easy | Know your data first |

## Lakehouse & Table Formats

| # | Question | Level | Concept |
|---|---|---|---|
| 1 | [Snapshot Commit](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/lakehouse/snapshot-commit) | Medium | ACID on files |
| 2 | [Time Travel](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/lakehouse/time-travel) | Medium | Query the past |
| 3 | [Optimistic Concurrency](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/lakehouse/optimistic-concurrency) | Hard | Two writers at once |
| 4 | [Copy-on-Write Update](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/lakehouse/copy-on-write-update) | Medium | Rewrite the file |
| 5 | [Merge-on-Read](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/lakehouse/merge-on-read) | Medium | Apply deletes at read time |
| 6 | [COW vs MOR Cost](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/lakehouse/cow-vs-mor-cost) | Medium | Choosing a strategy |
| 7 | [MERGE INTO on a Lake](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/lakehouse/merge-into-on-a-lake) | Medium | Upsert with deletes |
| 8 | [Pick Files From Manifests](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/lakehouse/pick-files-from-manifests) | Medium | Metadata pruning |
| 9 | [Effect of Clustering](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/lakehouse/effect-of-clustering) | Medium | Sorted files skip better |
| 10 | [Z-Order Key](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/lakehouse/z-order-key) | Hard | Sort on two columns at once |
| 11 | [Bin-Pack Compaction](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/lakehouse/bin-pack-compaction) | Medium | Merge small files |
| 12 | [Expire Old Snapshots](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/lakehouse/expire-old-snapshots) | Medium | Time travel has a cost |
| 13 | [Orphan Files](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/lakehouse/orphan-files) | Easy | Failed writes leave debris |
| 14 | [Hidden Partitioning](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/lakehouse/hidden-partitioning) | Medium | Iceberg's idea |
| 15 | [Schema Evolution by Column ID](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/lakehouse/schema-evolution-by-column-id) | Medium | Rename safely |
| 16 | [Delete for Privacy](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/lakehouse/delete-for-privacy) | Medium | GDPR on immutable files |
| 17 | [Read Delta's Log](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/lakehouse/read-deltas-log) | Medium | The transaction log |
| 18 | [Choose a Table Strategy](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/lakehouse/choose-a-table-strategy) | Easy | COW, MOR or append |
| 19 | [Incremental Read Between Snapshots](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/lakehouse/incremental-read-between-snapshots) | Medium | Read only what changed |
| 20 | [Does This Table Need Compaction?](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/lakehouse/does-this-table-need-compaction) | Easy | Measure small files |

## Warehouses & dbt

| # | Question | Level | Concept |
|---|---|---|---|
| 1 | [Find ref() Dependencies](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/warehouses-dbt/find-ref-dependencies) | Easy | How dbt builds its graph |
| 2 | [Build Order of Models](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/warehouses-dbt/build-order-of-models) | Medium | dbt run |
| 3 | [Compile a Model](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/warehouses-dbt/compile-a-model) | Easy | Jinja to SQL |
| 4 | [A Staging Model](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/warehouses-dbt/a-staging-model) | Easy | One clean version of each source |
| 5 | [A Mart Built on Staging](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/warehouses-dbt/a-mart-built-on-staging) | Medium | Layers of models |
| 6 | [Incremental Model](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/warehouses-dbt/incremental-model) | Medium | Only new days |
| 7 | [dbt Snapshot](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/warehouses-dbt/dbt-snapshot) | Medium | SCD 2 from a table |
| 8 | [dbt run --select](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/warehouses-dbt/dbt-run-select) | Medium | Run part of the graph |
| 9 | [View, Table or Materialized View?](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/warehouses-dbt/view-table-or-materialized-view) | Medium | Pay at read or at write |
| 10 | [Pay per Byte Scanned](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/warehouses-dbt/pay-per-byte-scanned) | Easy | On-demand pricing |
| 11 | [Warehouse Size vs Time](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/warehouses-dbt/warehouse-size-vs-time) | Medium | Pay for compute time |
| 12 | [Auto-Suspend Saves Money](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/warehouses-dbt/auto-suspend-saves-money) | Easy | Idle compute costs |
| 13 | [Choose a Distribution Key](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/warehouses-dbt/choose-a-distribution-key) | Medium | MPP warehouses |
| 14 | [Sort Key Pruning](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/warehouses-dbt/sort-key-pruning) | Medium | Zone maps |
| 15 | [Result Cache](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/warehouses-dbt/result-cache) | Easy | Same query, no compute |
| 16 | [Cost by Team](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/warehouses-dbt/cost-by-team) | Easy | Make spending visible |
| 17 | [Most Expensive Queries](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/warehouses-dbt/most-expensive-queries) | Easy | Where to start tuning |
| 18 | [Queue Wait](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/warehouses-dbt/queue-wait) | Medium | Concurrency limits |
| 19 | [One Definition of a Metric](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/warehouses-dbt/one-definition-of-a-metric) | Medium | The semantic layer |
| 20 | [Generate dbt Tests](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/warehouses-dbt/generate-dbt-tests) | Easy | Tests from a config |

## Cloud, Cost & Security

| # | Question | Level | Concept |
|---|---|---|---|
| 1 | [IAM Policy Evaluation](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/cloud-security/iam-policy-evaluation) | Medium | Explicit deny wins |
| 2 | [Find Overly Broad Policies](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/cloud-security/find-overly-broad-policies) | Easy | Least privilege |
| 3 | [Role-Based Access](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/cloud-security/role-based-access) | Easy | Roles, not people |
| 4 | [Row-Level Security](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/cloud-security/row-level-security) | Medium | Same table, different rows |
| 5 | [Column Masking](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/cloud-security/column-masking) | Easy | Hide what isn't needed |
| 6 | [Pseudonymise With a Secret](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/cloud-security/pseudonymise-with-a-secret) | Medium | Hashes alone can be reversed |
| 7 | [How Easily Can It Be Reversed?](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/cloud-security/how-easily-can-it-be-reversed) | Easy | Small spaces fall fast |
| 8 | [k-Anonymity](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/cloud-security/k-anonymity) | Medium | Can someone be singled out? |
| 9 | [Find Personal Data](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/cloud-security/find-personal-data) | Medium | Scan before you share |
| 10 | [Retention Policy](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/cloud-security/retention-policy) | Easy | Keep it only as long as needed |
| 11 | [Who Touched This Data?](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/cloud-security/who-touched-this-data) | Easy | Audit logs |
| 12 | [Rotate Old Keys](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/cloud-security/rotate-old-keys) | Easy | Secrets expire |
| 13 | [Spot vs On-Demand](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/cloud-security/spot-vs-on-demand) | Medium | Cheap but interruptible |
| 14 | [Athena or a Cluster?](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/cloud-security/athena-or-a-cluster) | Medium | Break-even |
| 15 | [Data Transfer Costs](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/cloud-security/data-transfer-costs) | Easy | The hidden bill |
| 16 | [S3 Lifecycle Rule](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/cloud-security/s3-lifecycle-rule) | Easy | Move and expire automatically |
| 17 | [Multipart Upload](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/cloud-security/multipart-upload) | Easy | Large files in pieces |
| 18 | [Availability Math](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/cloud-security/availability-math) | Medium | What do the nines mean? |
| 19 | [Recovery Objectives](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/cloud-security/recovery-objectives) | Medium | RPO and RTO |
| 20 | [Tag Everything](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/cloud-security/tag-everything) | Easy | Find what has no owner |

## Data System Design

| # | Question | Level | Concept |
|---|---|---|---|
| 1 | [Size the Ingest](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/system-design/size-the-ingest) | Easy | Start with numbers |
| 2 | [Storage Over Time](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/system-design/storage-over-time) | Easy | Layers and retention |
| 3 | [Kafka Partitions for the Peak](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/system-design/kafka-partitions-for-the-peak) | Easy | Handle bursts |
| 4 | [Will the Batch Finish in Time?](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/system-design/will-the-batch-finish-in-time) | Medium | Check the window |
| 5 | [Batch, Micro-Batch or Streaming?](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/system-design/batch-micro-batch-or-streaming) | Easy | Match the need |
| 6 | [Pick a Serving Store](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/system-design/pick-a-serving-store) | Medium | It depends on the query |
| 7 | [End-to-End Latency Budget](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/system-design/end-to-end-latency-budget) | Easy | Add up the hops |
| 8 | [Clickstream: Bot Filter](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/system-design/clickstream-bot-filter) | Medium | Clean before counting |
| 9 | [Daily Active Users From Events](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/system-design/daily-active-users-from-events) | Easy | A core metric |
| 10 | [CDC Into a Lake: Plan the Merge](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/system-design/cdc-into-a-lake-plan-the-merge) | Medium | Compact, then merge |
| 11 | [Real-Time Counter With Rollups](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/system-design/real-time-counter-with-rollups) | Medium | Fast dashboards |
| 12 | [Fan-Out to Many Consumers](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/system-design/fan-out-to-many-consumers) | Easy | Kafka vs point-to-point |
| 13 | [Tenant Quotas](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/system-design/tenant-quotas) | Medium | One customer shouldn't starve the rest |
| 14 | [How Long Can You Replay?](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/system-design/how-long-can-you-replay) | Medium | Retention vs recovery |
| 15 | [Monthly Cost Estimate](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/system-design/monthly-cost-estimate) | Medium | Every design has a price |
| 16 | [Design a Partition Layout](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/system-design/design-a-partition-layout) | Medium | Year, month, day or hour? |
| 17 | [Rank the Risks](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/system-design/rank-the-risks) | Easy | Likelihood × impact |
| 18 | [Sharding a Key-Value Table](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/system-design/sharding-a-key-value-table) | Medium | Scale reads and writes |
| 19 | [Data Mesh Ownership](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/system-design/data-mesh-ownership) | Medium | Who owns which data? |
| 20 | [Growth Headroom](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/system-design/growth-headroom) | Easy | When will it break? |

## Data Engineering for AI

| # | Question | Level | Concept |
|---|---|---|---|
| 1 | [Point-in-Time Feature Join](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-for-ai/point-in-time-feature-join) | Hard | No peeking at the future |
| 2 | [What a Leak Looks Like](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-for-ai/what-a-leak-looks-like) | Medium | Too good to be true |
| 3 | [Rolling Feature](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-for-ai/rolling-feature) | Medium | Spend in the last 7 days |
| 4 | [Stable Train/Test Split](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-for-ai/stable-train-test-split) | Medium | Same split every run |
| 5 | [Version a Dataset](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-for-ai/version-a-dataset) | Medium | Which data trained this model? |
| 6 | [Label Balance](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-for-ai/label-balance) | Easy | Know your classes |
| 7 | [Clean Text for Ingestion](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-for-ai/clean-text-for-ingestion) | Easy | Garbage in, garbage out |
| 8 | [Chunk With Overlap](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-for-ai/chunk-with-overlap) | Easy | Splitting for retrieval |
| 9 | [Embed Only What Changed](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-for-ai/embed-only-what-changed) | Medium | Embeddings cost money |
| 10 | [Embedding Cost and Time](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-for-ai/embedding-cost-and-time) | Easy | Plan the backfill |
| 11 | [Batch for an Embedding API](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-for-ai/batch-for-an-embedding-api) | Medium | Respect both limits |
| 12 | [Near-Duplicate Documents](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-for-ai/near-duplicate-documents) | Medium | Don't index ten copies |
| 13 | [MinHash: Similarity at Scale](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-for-ai/minhash-similarity-at-scale) | Hard | Avoid comparing every pair |
| 14 | [Scrub Personal Data](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-for-ai/scrub-personal-data) | Medium | Before embedding or training |
| 15 | [Freshness of a Vector Index](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-for-ai/freshness-of-a-vector-index) | Easy | Is the answer out of date? |
| 16 | [Build a Training File](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-for-ai/build-a-training-file) | Medium | JSON Lines for LLM evaluation or tuning |
| 17 | [Check an Eval Set](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-for-ai/check-an-eval-set) | Medium | Test data needs testing |
| 18 | [Serving Features: Online vs Offline](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-for-ai/serving-features-online-vs-offline) | Medium | Training-serving skew |
| 19 | [Which Embedding Model Built This?](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-for-ai/which-embedding-model-built-this) | Medium | Mixed vectors are useless |
| 20 | [Find Bad Retrieval Sources](https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced/course/#/q/data-for-ai/find-bad-retrieval-sources) | Medium | Feedback into the pipeline |

## Build

```bash
python3 handbook/build.py --book course
```

Sources live in `course/src/`: `topics/` (questions and solutions), `lessons/` and `theory/`.
