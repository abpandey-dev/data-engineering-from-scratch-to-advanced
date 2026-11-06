from lib import *

THEORY("Core concepts", """
<table><tr><th>Term</th><th>Meaning</th></tr>
<tr><td>DAG</td><td>tasks and their dependencies</td></tr>
<tr><td>Task / operator</td><td>one unit of work / a template for one</td></tr>
<tr><td>DAG run</td><td>one execution, for one logical date</td></tr>
<tr><td>Sensor</td><td>a task that waits for a condition</td></tr>
<tr><td>XCom</td><td>small values passed between tasks</td></tr>
<tr><td>Pool</td><td>a concurrency limit for a shared resource</td></tr>
<tr><td>Connection</td><td>stored credentials for an external system</td></tr></table>
""")
FAQ("What is a DAG, and why must it be acyclic?", "<p>A graph of tasks with directed dependencies. A cycle would mean tasks waiting on each other forever, so no valid order exists.</p>")
FAQ("What is the logical date in Airflow?", "<p>The start of the data interval a run covers, not when it runs. A daily run for 5 January actually starts when the interval ends, on 6 January.</p>")
FAQ("What's catchup?", "<p>Airflow creates runs for all past intervals since the start date. Turn it off unless you want that.</p>")
FAQ("Why not put heavy work in Airflow tasks?", "<p>Airflow is a coordinator. Heavy work belongs in Spark or warehouses, which scale, while workers stay light and reliable.</p>")
FAQ("What should you avoid in XCom?", "<p>Large data, since it goes in the metadata database. Store files in object storage, and pass the path.</p>")
FAQ("How do you make Airflow tasks idempotent?", "<p>Use the logical date for parameters, and overwrite or upsert outputs, so retries and backfills give the same result.</p>")
FAQ("Scenario: a task is stuck in 'queued'. What do you check?", "<p>Worker availability, pool and concurrency limits, and the executor's health. Also look at the scheduler's logs.</p>")
FAQ("Scenario: the DAG ran at the time you expected, but processed the wrong day. Why?", "<p>It probably used the current date instead of the logical date, or misunderstood that runs occur after their interval ends. Use ds or the data interval.</p>")
FAQ("Scenario: after deployment, hundreds of runs started at once. What happened?", "<p>Catchup was on with an old start date. Pause the DAG, clear runs as needed, set catchup=False and limit max_active_runs.</p>")
