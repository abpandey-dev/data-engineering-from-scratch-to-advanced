from lib import *
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np



LESSON("Core", "Join strategies: the biggest performance lever", """
<p>Joins usually dominate a Spark job's cost. Spark chooses among these:</p>
<table><tr><th>Join</th><th>When</th><th>Shuffle?</th></tr>
<tr><td><b>Broadcast hash</b></td><td>one side's small (default limit 10 MB)</td><td>none</td></tr>
<tr><td><b>Sort-merge</b></td><td>both large (the default)</td><td>both sides</td></tr>
<tr><td><b>Shuffle hash</b></td><td>one side moderately small</td><td>both sides</td></tr>
<tr><td><b>Bucketed</b></td><td>both bucketed the same way</td><td>none</td></tr></table>
<p><b>Broadcast</b> sends the small table to every executor, so each partition of the big table joins locally:</p>
<pre><code class="py">from pyspark.sql import functions as F
big.join(F.broadcast(small), "key")</code></pre>
<p>In the lab you can see <code>BroadcastHashJoin</code> in the plan. Don't broadcast something that's too big, though, as it has to fit in the driver and every executor.</p>
<p><b>Bucketing pays once.</b> Joining 100 GB with 900 GB daily for 30 days shuffles 30,000 GB. Bucketed, you shuffle 1,000 GB once, at write time.</p>
<p><b>Filter via a join: dynamic partition pruning.</b> Joining a fact table to a dimension filtered to one day lets Spark read only that day's partitions: 1 instead of 5.</p>
<p><b>Your checklist for a slow join:</b></p>
<ol><li>Can you filter or select columns first?</li><li>Can one side be broadcast?</li><li>Is the key skewed? Are there NULLs?</li><li>Is there a many-to-many explosion on the key?</li></ol>
""", practice=["Pick a Join Strategy", "Broadcast Join Simulation", "Bucketed Join Avoids Shuffle", "Dynamic Partition Pruning"])


LESSON("Core", "Skew: why jobs get stuck at 99%", """
<p>199 tasks finish in a minute, and one runs for two hours. That's <b>data skew</b>, the most common real Spark problem.</p>
<p><b>Spot it in the Spark UI:</b> open the stage, and compare the median and max under Input, Shuffle Read and Duration. A max far above the median means skew. With tasks (60 s, 900 MB) when the median is (11 s, 100 MB), it's skew. A slow task with normal input (50 s, 100 MB) points to a sick node instead.</p>
<p><b>Causes:</b> a hot key (a big customer), or NULLs, which all hash to one partition. If 60% of keys are NULL, filter those first; they can't match in an inner join anyway.</p>
<table><tr><th>Fix</th><th>How</th><th>Trade-off</th></tr>
<tr><td>Filter NULLs</td><td>simply drop or treat separately</td><td>trivial; try first</td></tr>
<tr><td><b>AQE skew join</b></td><td>Spark splits big partitions automatically</td><td>the easy option in Spark 3+</td></tr>
<tr><td>Broadcast</td><td>no shuffle, so no skew</td><td>needs a small side</td></tr>
<tr><td>Isolate hot keys</td><td>handle them separately, union the results</td><td>more code</td></tr>
<tr><td><b>Salting</b></td><td>add a random suffix to split a key</td><td>replicates the other side</td></tr></table>
<p><b>Salting by hand.</b> Key "us" has 3 rows, and with 2 salts it becomes us#0 and us#1, with the largest group going from 3 to 2. The other table must have every salted version of each key: "us" appears as both us#0 and us#1, so the join still matches. In the lab, salting 10 ways reduces the largest group of a hot key from 9,500 to 1,000.</p>
<pre><code class="py">salted = big.withColumn("k", F.concat("key", F.lit("#"), (F.rand() * 10).cast("int")))
small2 = small.crossJoin(spark.range(10)).withColumn("k", F.concat("key", F.lit("#"), "id"))
salted.join(small2, "k")</code></pre>
<p><b>AQE decides skew</b> with a rule: bigger than 5 times the median, and bigger than 256 MB (the defaults).</p>
""", practice=["Find the Skewed Partitions", "Null Keys Cause Skew", "Isolate the Hot Key", "Salted Join", "Spot the Straggler Task"])


LESSON("Core", "Shuffle tuning and adaptive execution", """
<p><code>spark.sql.shuffle.partitions</code> sets the partitions after a shuffle, and it defaults to <b>200</b>, which suits almost nobody:</p>
<table><tr><th>Shuffle size</th><th>Average with 200</th><th>Problem</th><th>At 128 MB each</th></tr>
<tr><td>1 TB</td><td>5,000 MB</td><td>huge tasks, spilling</td><td>7,813 partitions</td></tr>
<tr><td>2 GB</td><td>10 MB</td><td>tiny tasks and files</td><td>16 partitions</td></tr></table>
<p><b>Adaptive Query Execution (AQE)</b> re-optimises mid-job, using real sizes. It's been on by default since Spark 3.2:</p>
<ul><li><b>Coalesces small partitions:</b> 10, 20, 30, 100, 5, 5 with a 64 MB target becomes 60, 100, 10.</li>
<li><b>Splits skewed partitions.</b></li>
<li><b>Switches join strategy,</b> for example to broadcast if a side turned out small after filtering.</li></ul>
<p>So set a high shuffle partition count, and let AQE merge down. That usually beats guessing.</p>
<p><b>Spilling:</b> when sorting data doesn't fit in memory, Spark writes sorted runs to disk and merges them. 1,000 MB with 300 MB of memory makes 4 runs. It still works, but it's slow, so look for "Spill" in the UI.</p>
<p><b>Writing files.</b> With <code>partitionBy</code>, each task writes one file per value it holds: 200 tasks × 30 days = <b>6,000 small files</b>. Fix it with repartition first:</p>
<pre><code class="py">df.repartition("day").write.partitionBy("day").parquet(path)   # 30 files, one per day</code></pre>
<p>If a day's too large for one file, add a salt, or set <code>maxRecordsPerFile</code>.</p>
<p>A window with no <code>partitionBy</code> moves everything to one task: Spark warns you about it, and it's a performance trap.</p>
""", practice=["Shuffle Partitions Setting", "AQE: Coalesce Small Partitions", "Sort-Merge Spill", "Files Written per Partition", "Parquet Target File Count", "Window With No Partition"])


LESSON("Advanced", "Memory and out-of-memory errors", """
<p>An 8 GB executor's memory is divided like this:</p>
<div class="pic">8 GB
├─ 300 MB reserved
└─ the rest (7.71 GB)
   ├─ 60% unified: 4.62 GB
   │   ├─ execution (joins, sorts, shuffles)
   │   └─ storage (cache); they borrow from each other
   └─ 40% user memory: 3.08 GB (your objects, UDFs)</div>
<p>On top of this, there's <b>overhead memory</b> outside the JVM, including Python workers. Containers killed by YARN or Kubernetes for exceeding limits usually need more overhead, not heap.</p>
<table><tr><th>Error</th><th>Likely cause</th><th>Try this</th></tr>
<tr><td>Driver OOM</td><td><code>collect</code>, <code>toPandas</code>, big broadcast</td><td>write out instead; lower broadcast threshold</td></tr>
<tr><td>Executor OOM on one task</td><td>skew</td><td>fix the skew</td></tr>
<tr><td>Executor OOM on many tasks</td><td>partitions too big</td><td>more partitions</td></tr>
<tr><td>Container killed</td><td>overhead exceeded</td><td>raise <code>memoryOverhead</code></td></tr>
<tr><td>Shuffle fetch failed</td><td>executor died or was overloaded</td><td>look at why it died; often memory</td></tr></table>
<p><b>Never treat more memory as the first answer.</b> It's expensive, and it hides the cause.</p>
<p><b>Dynamic allocation</b> scales executors with the backlog: 100 pending tasks at 4 cores wants 25, capped at a limit.</p>
<p><b>Cost.</b> 10 nodes for 2 hours costs the same as 20 nodes for 1 hour, if scaling's perfect, and it finishes twice as fast. If doubling nodes only cuts the time to 1.5 hours, it costs 50% more.</p>
""", practice=["Executor Memory Breakdown", "Diagnose an Out-of-Memory", "Dynamic Allocation", "Cost of a Cluster Run"])


LESSON("Advanced", "A debugging routine for any slow job", """
<p><b>Follow the same steps every time.</b></p>
<ol><li><b>Find the slowest stage</b> in the Spark UI. If shuffle takes 80 of 100 seconds, even making it infinitely fast gives a limit of 5×. That's where you start, not on the 10-second read.</li>
<li><b>Look at task distribution:</b> median against max for duration, input and shuffle read.</li>
<li><b>Read the SQL tab's plan:</b> rows at each step. A join outputting far more rows than its inputs is an explosion.</li>
<li><b>Check for spills, and garbage collection time.</b> GC above about 10% of task time means memory pressure.</li></ol>
<table><tr><th>Symptom</th><th>Diagnosis</th></tr>
<tr><td>One task much slower, more input</td><td>skew</td></tr>
<tr><td>One task slower, same input</td><td>bad node, speculation helps</td></tr>
<tr><td>All tasks slow, high GC</td><td>too little memory, partitions too big</td></tr>
<tr><td>Thousands of tiny tasks</td><td>too many partitions, or small files</td></tr>
<tr><td>Output rows far above input</td><td>many-to-many join</td></tr>
<tr><td>Long time reading</td><td>missing pruning, small files, a CSV source</td></tr></table>
<p><b>The order to try fixes:</b> read less data (filters, columns, partitions), then fix the join, then fix skew, then tune settings, and only then add hardware.</p>
""", practice=["Debug a Slow Job"])
