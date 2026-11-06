from lib import *

THEORY("RDD, DataFrame, Dataset", """
<table><tr><th>API</th><th>What</th><th>Use</th></tr>
<tr><td>RDD</td><td>low-level collection of objects</td><td>rarely; no query optimisation</td></tr>
<tr><td>DataFrame</td><td>table with a schema, optimised</td><td>almost always</td></tr>
<tr><td>Dataset</td><td>typed DataFrame (Scala/Java)</td><td>when type safety matters</td></tr></table>
""")
FAQ("Transformations vs actions?", "<p>Transformations are lazy and build a plan. Actions trigger execution and return or write results.</p>")
FAQ("Why is Spark lazy?", "<p>Seeing the whole plan allows optimisations, such as pushing filters down and pruning columns, before any work is done.</p>")
FAQ("Narrow vs wide transformation?", "<p>Narrow needs no data movement. Wide needs a shuffle, which starts a new stage and costs network, disk and memory.</p>")
FAQ("Job, stage, task?", "<p>An action creates a job. Shuffles split it into stages. Each stage has one task per partition.</p>")
FAQ("What does the driver do?", "<p>It runs your program, builds the plan, schedules tasks and collects results. It's a single point of failure and should not hold large data.</p>")
FAQ("How does Spark handle a failed executor?", "<p>It reruns lost tasks using lineage on other executors, retrying up to a limit.</p>")
FAQ("coalesce vs repartition?", "<p>coalesce reduces partitions without a shuffle, and may be uneven. repartition does a full shuffle, and can grow or shrink, giving an even result.</p>")
FAQ("Why avoid Python UDFs?", "<p>Rows are serialised between the JVM and Python, which is slow and blocks some optimisations. Use built-in functions, or pandas UDFs if necessary.</p>")
FAQ("cache vs persist?", "<p>cache stores at the default level. persist lets you choose memory, disk or both. Both are lazy, and only worthwhile if data is reused.</p>")
FAQ("Scenario: your job OOMs on the driver. What's the likely cause?", "<p>A collect, toPandas or big broadcast pulling too much data to the driver. Write results out instead, or limit them.</p>")
FAQ("Scenario: a count takes as long as the whole job. Why?", "<p>Because of laziness, it runs all preceding transformations. Avoid unnecessary counts, or cache if you truly need the data several times.</p>")
