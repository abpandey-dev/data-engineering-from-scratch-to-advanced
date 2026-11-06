from lib import *

THEORY("Settings worth knowing", """
<table><tr><th>Setting</th><th>Controls</th></tr>
<tr><td><code>spark.sql.shuffle.partitions</code></td><td>partitions after a shuffle (default 200)</td></tr>
<tr><td><code>spark.sql.adaptive.enabled</code></td><td>Adaptive Query Execution</td></tr>
<tr><td><code>spark.sql.autoBroadcastJoinThreshold</code></td><td>the largest table auto-broadcast</td></tr>
<tr><td><code>spark.sql.files.maxPartitionBytes</code></td><td>input partition size</td></tr>
<tr><td><code>spark.executor.memoryOverhead</code></td><td>non-heap memory</td></tr>
<tr><td><code>spark.sql.sources.partitionOverwriteMode</code></td><td><code>dynamic</code> overwrites only the partitions written</td></tr></table>
""")
FAQ("What is a broadcast join, and when should you use it?", "<p>The small table is sent to all executors, so no shuffle's needed. Use it when one side fits comfortably in memory.</p>")
FAQ("What is data skew, and how do you fix it?", "<p>Uneven key sizes make a few tasks huge. Filter NULLs, enable AQE, broadcast, isolate hot keys or salt.</p>")
FAQ("What does AQE do?", "<p>It re-optimises during execution using real sizes: merging small partitions, splitting skewed ones and switching join strategies.</p>")
FAQ("How do you decide shuffle partitions?", "<p>Aim for about 100–200 MB per partition, based on shuffle size. With AQE, set it high and let it coalesce.</p>")
FAQ("Sort-merge vs broadcast hash join?", "<p>Sort-merge handles any size by shuffling and sorting both sides. Broadcast avoids shuffles, but one side must be small.</p>")
FAQ("Driver OOM vs executor OOM?", "<p>Driver OOM usually comes from bringing data back, as with collect or a large broadcast. Executor OOM comes from skew, big partitions or too little memory.</p>")
FAQ("Scenario: a daily job suddenly takes 10× longer with no code change. What do you check?", "<p>Data volume, new skew from a key, small files upstream, schema or plan changes, and cluster contention. Compare with the last good run in the Spark UI.</p>")
FAQ("Scenario: a job writes 50,000 tiny files. How do you fix it?", "<p>Repartition by the partition column before writing, tune the shuffle partitions, set maxRecordsPerFile, or run compaction afterward.</p>")
FAQ("Scenario: your join output is much larger than either input. What's happening?", "<p>A many-to-many key match is exploding rows. Check key uniqueness on both sides, and aggregate or deduplicate before joining.</p>")
FAQ("Scenario: you keep adding memory but it still fails. What now?", "<p>Stop adding it, and find the cause: one skewed task, a collect, or a huge cartesian join. Memory rarely fixes skew.</p>")
