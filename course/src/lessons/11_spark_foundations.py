from lib import *
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np



LESSON("Basics", "What Spark is, and how a job runs", """
<p>Spark lets you write what looks like ordinary data code, and it runs across hundreds of machines. It's the most widely used big data engine, so it's a core skill.</p>
<div class="pic">        ┌ Driver: your program. Makes the plan.
        │
Cluster │  Executor   Executor   Executor
        └  [task][task] [task][task] [task][task]
            partition  partition  partition</div>
<table><tr><th>Part</th><th>Role</th></tr>
<tr><td>Driver</td><td>runs your code, plans the work, gathers results</td></tr>
<tr><td>Executor</td><td>a process on a worker machine that runs tasks</td></tr>
<tr><td>Task</td><td>one unit of work on one partition, using one core</td></tr>
<tr><td>Partition</td><td>a chunk of data</td></tr></table>
<p><b>The chain:</b> an action starts a <b>job</b>, which is split into <b>stages</b> at each shuffle, and each stage has one <b>task</b> per partition.</p>
<p>10 tasks of 60 s on 4 cores take 3 rounds: <b>180 s</b>.</p>
<p><b>Your first PySpark, as used in the lab:</b></p>
<pre><code class="py">from pyspark.sql import SparkSession, functions as F

spark = SparkSession.builder.appName("orders").getOrCreate()
df = spark.read.parquet("s3://lake/orders/")
out = (df.filter(F.col("amount") > 0)
         .groupBy("city")
         .agg(F.sum("amount").alias("total")))
out.write.mode("overwrite").parquet("s3://lake/city_totals/")</code></pre>
<p>This course's browser IDE can't run Spark, so questions here use a miniature Spark in Python, which shows the mechanics directly. <b>Run the real thing with <code>labs/spark_lab.py</code></b>, or in Colab.</p>
""", practice=["Split Data Into Partitions", "Map Over Partitions", "Parallel Time on a Cluster"])


LESSON("Core", "Lazy evaluation: Spark plans before it works", """
<p><b>Transformations</b> (filter, select, join, groupBy) only describe work. <b>Actions</b> (count, collect, write, show) make it happen. In the chain filter, select, count, groupBy, write: <b>2 jobs</b> run.</p>
<p>In our mini-Spark, mapping and filtering 1, 2, 3 does <b>0</b> work until collect, and then 6 operations.</p>
<p><b>Why wait? Because seeing the whole plan lets Spark optimise it.</b> The Catalyst optimiser rewrites your query:</p>
<table><tr><th>Optimisation</th><th>What it does</th><th>Example saving</th></tr>
<tr><td><b>Predicate pushdown</b></td><td>moves filters toward the data</td><td>expensive step handles 3 rows rather than 6</td></tr>
<tr><td><b>Column pruning</b></td><td>reads only needed columns</td><td>16 KB rather than 546 KB</td></tr>
<tr><td><b>Partition pruning</b></td><td>skips folders</td><td>read 1 day rather than 365</td></tr></table>
<p><b>Read the plan with <code>df.explain()</code>:</b> learn to look for these:</p>
<table><tr><th>In the plan</th><th>Meaning</th></tr>
<tr><td><code>Exchange</code></td><td>a shuffle: expensive</td></tr>
<tr><td><code>PushedFilters: [...]</code></td><td>the file reader's filtering early</td></tr>
<tr><td><code>PartitionFilters</code></td><td>folders are being skipped</td></tr>
<tr><td><code>BroadcastHashJoin</code></td><td>no shuffle for that join</td></tr>
<tr><td><code>SortMergeJoin</code></td><td>both sides were shuffled and sorted</td></tr></table>
<p><b>Trap:</b> applying a Python UDF, or casting a column in a filter, can stop pushdown working.</p>
""", practice=["Action or Transformation?", "Lazy Evaluation", "Predicate Pushdown", "Column Pruning", "Read a Plan"])


LESSON("Core", "Narrow and wide: the idea behind Spark performance", """
<p><b>If you remember one thing about Spark performance, remember this.</b></p>
<table><tr><th></th><th>Narrow</th><th>Wide (shuffle)</th></tr>
<tr><td>Data moves?</td><td>no</td><td><b>yes, across the network</b></td></tr>
<tr><td>Examples</td><td>filter, select, withColumn, map</td><td>groupBy, join, distinct, sort, repartition</td></tr>
<tr><td>Cost</td><td>cheap</td><td>expensive: network, disk, memory</td></tr></table>
<p>Each wide operation starts a new stage. read, filter, groupBy, select, join, write has 2 wide steps, so it's <b>3 stages</b>.</p>
<p><b>A shuffle, step by step:</b> to group by key, all rows with the same key must reach the same machine. Each task splits its output by <code>hash(key) % partitions</code> and writes it to disk, and the next stage's tasks then fetch their share.</p>
<p><b>groupBy is smarter than it looks.</b> Each partition first sums locally, so it sends far less. Rows a:1, a:2, b:3 and a:4 send only 3 partial results rather than 4 raw rows. With millions of rows per key, this saving is huge. <code>collect_list</code> can't benefit, which is one reason it's expensive.</p>
<p><b>Fault tolerance.</b> Spark remembers each partition's <b>lineage</b>: how it was built. If an executor dies, only the lost partitions are recomputed, by rerunning their steps. No replication of the working data is needed.</p>
""", practice=["Narrow or Wide?", "Stages From a Plan", "Shuffle by Key", "groupBy + sum, Spark Style", "Lineage: Recompute a Lost Partition"])


LESSON("Core", "The DataFrame API you'll use daily", """
<pre><code class="py">from pyspark.sql import functions as F, Window

df = spark.read.option("header", True).csv(path)      # or .parquet, .json
df.printSchema()

clean = (df
    .withColumn("amount", F.col("amount").cast("double"))
    .filter(F.col("amount").isNotNull())
    .withColumn("day", F.to_date("ts"))
    .dropDuplicates(["id"]))

totals = clean.groupBy("city", "day").agg(
    F.sum("amount").alias("total"),
    F.countDistinct("user").alias("users"))

w = Window.partitionBy("city").orderBy(F.desc("day"))
latest = totals.withColumn("rn", F.row_number().over(w)).filter("rn = 1")

(latest.write.mode("overwrite")
    .partitionBy("day").parquet(out_path))</code></pre>
<p><b>You can also just use SQL:</b> <code>df.createOrReplaceTempView("t"); spark.sql("SELECT ...")</code>. It compiles to the same plan.</p>
<p><b>Arrays:</b> <code>F.explode</code> gives one row per item, dropping empty ones (use <code>explode_outer</code> to keep them).</p>
<p><b>Avoid Python UDFs where you can.</b> Each row has to travel from the JVM to Python and back. With built-ins at 200 ms and UDFs at 5,000 ms per million rows, it's <b>25 times slower</b> here. Check <code>pyspark.sql.functions</code> first. If you must, a pandas UDF works in batches, and is much faster.</p>
<p><b>Never <code>collect()</code> big data.</b> It pulls everything to the driver, which crashes. Use <code>limit</code> or write it out.</p>
<p><b>Cache only when it pays:</b> reused 5 times, a 100 s build costs 500 s without a cache and 120 s with one. Used once, caching makes it slower. Remember <code>unpersist</code>.</p>
""", practice=["A Tiny DataFrame", "Explode and Collect", "UDF vs Built-in Cost", "Cache or Recompute?"])


LESSON("Advanced", "Partitions and sizing a cluster", """
<p><b>Too few partitions:</b> tasks are huge, and may run out of memory. <b>Too many:</b> scheduling overhead and tiny files. A common target is around <b>128 MB per partition</b>, so 100 GB needs about 782.</p>
<p><b>Rule of thumb:</b> at least 2–4 times as many partitions as total cores, so that tasks balance out. With 10 executors of 4 cores, 40 tasks run at once.</p>
<table><tr><th></th><th>coalesce(n)</th><th>repartition(n)</th></tr>
<tr><td>Shuffle?</td><td><b>no</b></td><td>yes</td></tr>
<tr><td>Can grow?</td><td>no, only shrink</td><td>yes</td></tr>
<tr><td>Result</td><td>may be uneven</td><td>even</td></tr>
<tr><td>Sizes 10, 10, 100, 10 to 2</td><td>20, 110</td><td>65, 65</td></tr></table>
<p>Use coalesce to cheaply reduce file count, and repartition to fix skew, or to control the layout by a column.</p>
<p><b>Sizing executors.</b> On nodes of 16 cores and 64 GB, keep 1 core and 1 GB for the system. A common starting point is about 5 cores per executor, as too many cores per executor hurts I/O. That's 3 executors per node, of 21 GB each, less about 10% overhead: <b>18.9 GB</b>.</p>
<pre><code class="py">spark-submit --num-executors 30 --executor-cores 5 \\
  --executor-memory 18g --driver-memory 4g job.py</code></pre>
<p>These are starting points. Measure with the Spark UI, and adjust.</p>
""", practice=["How Many Partitions?", "Sizing an Executor", "Coalesce vs Repartition"])
