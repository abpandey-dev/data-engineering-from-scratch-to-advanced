from lib import *
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np



LESSON("Basics", "How a cloud warehouse works", """
<p>Snowflake, BigQuery, Redshift and Databricks SQL differ in details, but share these ideas:</p>
<ul><li><b>Columnar storage</b> with compression and min/max per block.</li>
<li><b>Massively parallel:</b> a query is split across many workers.</li>
<li><b>Storage separate from compute,</b> in most modern designs, so each scales alone.</li></ul>
<table><tr><th>Warehouse</th><th>You pay for</th><th>Optimise by</th></tr>
<tr><td>BigQuery (on-demand)</td><td>bytes scanned</td><td>partitioning, clustering, fewer columns</td></tr>
<tr><td>Snowflake</td><td>running time × warehouse size</td><td>auto-suspend, right size</td></tr>
<tr><td>Redshift</td><td>nodes per hour, or serverless</td><td>sort and distribution keys</td></tr></table>
<p><b>Scanning cost.</b> A 10 TB table at a made-up 5 per TB costs 50 for a full scan. Using 10% of columns costs 5. Filtering to 5% of partitions as well costs <b>0.25</b>. <code>SELECT *</code> on a big table can be a very expensive habit.</p>
<p><b>Sizing compute.</b> Each size up doubles the price per hour. If it also halves the time, the cost doesn't change, and you simply get answers faster: 8 hours at size 1 costs 8, and 2 hours at size 4 also costs 8. If scaling is imperfect, at 1.5 times faster per step, the same jump costs 14.2.</p>
<p><b>Auto-suspend.</b> A warehouse busy 4 hours a day bills 24 hours without suspending. With a 6-minute idle timeout across 10 jobs, it bills 5 hours: 79% less.</p>
<p><b>Result caches</b> return identical queries for free, until the data changes.</p>
""", practice=["Pay per Byte Scanned", "Warehouse Size vs Time", "Auto-Suspend Saves Money", "Result Cache"])


LESSON("Core", "Physical design: sort and distribution", """
<p><b>Clustering or sort keys</b> keep similar values together, so min/max per block can skip most data. Filtering 12–25 across blocks 1–10, 11–20, 21–30 and 31–40 reads only 2 of them. Choose columns people filter on, starting with date.</p>
<p><b>Distribution keys (Redshift-style).</b> Choose how rows spread across nodes:</p>
<table><tr><th>Style</th><th>How</th><th>Good for</th></tr>
<tr><td>Key</td><td>hash of a column</td><td>tables often joined on it, as no shuffle's needed</td></tr>
<tr><td>Even</td><td>round robin</td><td>no clear join key</td></tr>
<tr><td>All</td><td>a copy on each node</td><td>small dimensions</td></tr></table>
<p>A bad key causes skew. In 10 rows with 8 from "in", distributing by country on 2 nodes gives a skew of 1.6, while user id gives 1.0.</p>
<p><b>Concurrency.</b> Warehouses limit how many queries run at once. Durations 10, 10, 10, 5 with 2 slots give waits of 0, 0, 10, 10, so the fourth query waits 10 seconds to do 5 seconds of work. Separate heavy jobs from dashboards.</p>
<p><b>View, table or materialized view?</b></p>
<table><tr><th>Type</th><th>Pays at</th><th>Fresh?</th><th>Use when</th></tr>
<tr><td>View</td><td>each read</td><td>always</td><td>few reads, or cheap logic</td></tr>
<tr><td>Table</td><td>each rebuild</td><td>as of the last build</td><td>many reads</td></tr>
<tr><td>Materialized view</td><td>on refresh</td><td>managed</td><td>supported, simple aggregations</td></tr></table>
<p>A query costing 10, read 100 times and rebuilt once a day: a view costs 1,000, and a table costs 10. Read once, with hourly rebuilds, a view costs 10 and a table 240.</p>
""", practice=["Sort Key Pruning", "Choose a Distribution Key", "Queue Wait", "View, Table or Materialized View?"])


LESSON("Core", "dbt: software engineering for SQL", """
<p>A warehouse full of unversioned SQL scripts soon becomes unmaintainable. <b>dbt</b> treats SQL as code: each model is a SELECT in a file, in Git, with tests and documentation.</p>
<pre><code class="py">-- models/staging/stg_orders.sql
SELECT DISTINCT id, day, amount
FROM {{ source('shop', 'raw_orders') }}
WHERE status = 'paid'

-- models/marts/daily_revenue.sql
SELECT day, SUM(amount) AS total
FROM {{ ref('stg_orders') }}
GROUP BY day</code></pre>
<p><code>ref()</code> is the key idea. dbt reads these references to build a graph, so it knows that stg_orders must run first. Questions here rebuild that logic: finding refs, ordering models and compiling them to real SQL.</p>
<table><tr><th>Layer</th><th>Purpose</th></tr>
<tr><td>Staging</td><td>one clean model per source: rename, cast, dedupe</td></tr>
<tr><td>Intermediate</td><td>reusable joins and logic</td></tr>
<tr><td>Marts</td><td>tables for the business</td></tr></table>
<p>In the practice data, order 3 appears twice and order 2 failed. Staging removes both issues, so the mart can't double count: d2's revenue is 7, not 14.</p>
<p><b>Selecting what to run:</b> <code>b+</code> means b and everything downstream; <code>+c</code> means c and everything upstream.</p>
<p><b>Tests</b> compile to queries that should return no rows, such as unique_id and not_null_id. Run them in CI, on a small sample, with every pull request.</p>
<p><b>Your QA experience applies directly here.</b></p>
""", practice=["Find ref() Dependencies", "Build Order of Models", "Compile a Model", "A Staging Model", "A Mart Built on Staging", "dbt run --select", "Generate dbt Tests"])


LESSON("Advanced", "Incremental models, snapshots and cost control", """
<p><b>Incremental models</b> process only new data. Reprocessing recent days catches late rows. With existing {d1: 10, d2: 5} and new rows d2: 3, d2: 4, d3: 1, d1: 99, cut-off d2 gives {d1: 10, d2: 7, d3: 1}. The old d1 row's ignored, and that's the trade-off: very late data needs a full refresh.</p>
<p><b>Snapshots</b> build SCD 2 from a source that only holds current values. Each run compares and closes changed rows: b→B closes row 2 and opens a new version; a new id 3 opens a row. Without snapshots, you can't get that history back later.</p>
<p><b>One definition of each metric.</b> Sales counts paid + shipped as 15, and finance counts only paid as 10. Now two teams argue in a meeting over "revenue". A <b>semantic layer</b> defines metrics once, in code, and every tool uses that definition. Often the hardest part is getting people to agree, not the technology.</p>
<p><b>Control costs by measuring them.</b> Tag queries by team and report it: team a used 3 credits, and team b 2. Normalise queries to find repeated shapes: two queries that differ only in id are one shape costing 200, more than a one-off at 150.</p>
<ol><li>Find the top 10 most expensive query shapes.</li><li>Partition, cluster, and stop using SELECT *.</li><li>Materialise heavy shared logic.</li><li>Set auto-suspend and budgets.</li></ol>
""", practice=["Incremental Model", "dbt Snapshot", "One Definition of a Metric", "Cost by Team", "Most Expensive Queries"])
