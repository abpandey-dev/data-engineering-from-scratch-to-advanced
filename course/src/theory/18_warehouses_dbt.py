from lib import *

THEORY("dbt materializations", """
<table><tr><th>Type</th><th>Builds</th><th>Use for</th></tr>
<tr><td>view</td><td>a view</td><td>staging, light logic</td></tr>
<tr><td>table</td><td>a full table each run</td><td>small or medium marts</td></tr>
<tr><td>incremental</td><td>adds or merges new rows</td><td>large event tables</td></tr>
<tr><td>ephemeral</td><td>inlined as a CTE</td><td>small reusable steps</td></tr></table>
""")
FAQ("What does dbt do, and what doesn't it do?", "<p>It handles the T in ELT: dependency order, testing, documentation and versioning of SQL. It doesn't extract or load data, and it runs inside your warehouse.</p>")
FAQ("How does an incremental model work?", "<p>The first run builds it all. Later runs filter to new data and merge on a unique key. Include a lookback for late data, and do an occasional full refresh.</p>")
FAQ("Partitioning vs clustering in a warehouse?", "<p>Partitioning divides a table into coarse segments, usually by date. Clustering sorts data within them to improve block skipping.</p>")
FAQ("How does Snowflake or BigQuery separate storage and compute?", "<p>Data lives in object storage, while independent compute clusters read it, so several workloads can scale and be billed separately.</p>")
FAQ("View vs materialized view?", "<p>A view runs its query on each read. A materialized view stores results and refreshes them, trading storage and refresh cost for read speed.</p>")
FAQ("Scenario: the warehouse bill doubled this month. What do you do?", "<p>Break it down by user, tag and query shape. Look for new full scans, warehouses that don't suspend, or repeated dashboards. Fix the top few first.</p>")
FAQ("Scenario: an incremental model has drifted from the source. Why?", "<p>Late data outside the lookback, deletes that weren't handled, or logic changed without a full refresh. Compare with a full build, then widen the lookback or schedule refreshes.</p>")
FAQ("Scenario: two dashboards show different revenue. How do you resolve it?", "<p>Find each definition and trace its lineage. Agree on one with the business owner, define it centrally, and retire the other.</p>")
