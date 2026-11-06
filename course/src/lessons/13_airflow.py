from lib import *
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np



LESSON("Basics", "Why you need an orchestrator", """
<p>Your pipeline has steps: extract, then transform, then load, then a report. Cron can run a script at 2 am, but who handles the rest?</p>
<table><tr><th>Question</th><th>Cron</th><th>Airflow</th></tr>
<tr><td>Run in dependency order?</td><td>you guess the timing</td><td>yes</td></tr>
<tr><td>Retry a failure?</td><td>no</td><td>yes</td></tr>
<tr><td>Rerun last Tuesday?</td><td>by hand</td><td>one click</td></tr>
<tr><td>See what ran, and alert when it fails?</td><td>no</td><td>yes</td></tr></table>
<p><b>A DAG</b> (directed acyclic graph) describes the tasks and their order. Directed means arrows have a direction. Acyclic means there are no loops, as A waiting for B while B waits for A could never finish.</p>
<div class="pic">extract ─┬→ transform ─→ load
         └→ audit</div>
<p><b>Topological sort</b> finds a valid order: extract, audit, transform, load. Tasks in the same <b>level</b> can run at once.</p>
<p><b>Critical path.</b> With tasks a (1 s), then b (5 s) or c (2 s), then d (1 s): even with unlimited workers it takes 1 + 5 + 1 = <b>7 s</b>. Speeding up c gains nothing. Only the longest path matters.</p>
<pre><code class="py">from airflow.decorators import dag, task
from datetime import datetime

@dag(schedule="@daily", start_date=datetime(2026, 1, 1), catchup=False)
def orders_pipeline():

    @task(retries=3)
    def extract(ds=None):                 # ds: the date this run is for
        path = f"s3://lake/raw/orders/{ds}.json"
        ...
        return path                       # pass the path, not the data

    @task
    def load(path):
        ...

    load(extract())

orders_pipeline()</code></pre>
<p>Airflow doesn't run in this site's browser, so questions here build a tiny scheduler in Python, which shows you exactly what Airflow does.</p>
""", practice=["Is This a Valid DAG?", "Run Order", "Parallel Levels", "Critical Path", "Which Tasks Are Ready?"])


LESSON("Core", "Dates: the idea that confuses everyone", """
<p><b>A daily DAG's run for 5 January starts on 6 January.</b> That's not a bug. It processes the data <i>for</i> 5 January, which isn't complete until the day ends.</p>
<table><tr><th>Term</th><th>Value</th></tr>
<tr><td>Logical date (<code>ds</code>)</td><td>2026-01-05</td></tr>
<tr><td>Data interval</td><td>05 Jan 00:00 to 06 Jan 00:00</td></tr>
<tr><td>Actually runs at</td><td>06 Jan 00:00</td></tr></table>
<p><b>Always use the logical date in your code, never "now".</b> Then rerunning 5 January a month later reads the right data. This is what makes runs idempotent.</p>
<pre><code class="py">s3://lake/dt={{ ds }}/part-{{ ds_nodash }}.parquet
→ s3://lake/dt=2026-01-05/part-20260105.parquet</code></pre>
<p><b>Catchup.</b> Deploy a daily DAG with a start date 10 days ago, with catchup on, and Airflow immediately creates <b>10 runs</b>. It has surprised many people, and has hammered many databases. Set <code>catchup=False</code> unless you want that.</p>
<p><b>Backfills</b> rerun history deliberately. 30 days at 10 minutes each, with at most 5 at once, takes 60 minutes. Limit the concurrency, so you don't overload what's downstream.</p>
""", practice=["Daily Data Intervals", "How Many Runs Will Catchup Create?", "Render a Date Template", "Backfill With a Concurrency Limit"])


LESSON("Core", "Failures, retries and dependencies", """
<p><b>Retries:</b> a task's states go queued, running, then success or failed. With 3 retries, it gets 4 tries. Use growing delays, such as 60, 120, 240 seconds, as a struggling service needs time.</p>
<p><b>Trigger rules</b> decide if a task runs, given what happened upstream:</p>
<table><tr><th>Rule</th><th>Runs when</th><th>Use for</th></tr>
<tr><td><code>all_success</code> (default)</td><td>all upstream succeeded</td><td>normal steps</td></tr>
<tr><td><code>all_done</code></td><td>all finished, however they ended</td><td>clean-up</td></tr>
<tr><td><code>one_failed</code></td><td>any failed</td><td>send an alert</td></tr></table>
<p>If b fails in a → b → c, then c is marked <b>upstream_failed</b>, not run.</p>
<p><b>Clearing a task</b> reruns it and everything downstream. Clear b in a→b→c, a→d, and b and c rerun, while d stays as it is.</p>
<p><b>Sensors</b> wait for something, like a file. Checking every 30 s for a file that shows up at 90 s means 4 pokes. Waiting sensors can hold a worker slot, so use <code>mode="reschedule"</code> or deferrable versions for long waits.</p>
<p><b>Pools</b> limit concurrency for a shared resource. Tasks 4, 2, 8, 3 with 2 slots finish at 10.</p>
<p><b>SLAs and anomaly detection.</b> Alert on lateness: a task finishing at 8:30 for an 8:00 promise is 30 minutes late. Past runs give another signal: durations 100, 110, 90, 100 set a limit around 121, so 200 is worth a look even if nothing failed.</p>
""", practice=["Retries With Exponential Delay", "Task State After Attempts", "Upstream Failed", "What Needs Rerunning?", "Sensor: Wait for a File", "Pool Scheduling", "Is the SLA Met?", "Duration Anomaly", "A Tiny Scheduler"])


LESSON("Advanced", "Airflow mistakes and alternatives", """
<p><b>Airflow should orchestrate, not process.</b> Have it tell Spark or a warehouse what to do. Don't load 10 GB into a Python task.</p>
<p><b>Common mistakes:</b></p>
<table><tr><th>Mistake</th><th>Why it hurts</th><th>Do this instead</th></tr>
<tr><td>Heavy code at the top level of a DAG file</td><td>the scheduler parses files constantly, so it runs every time</td><td>put it inside tasks</td></tr>
<tr><td>Big data in XCom</td><td>it's stored in the metadata database</td><td>write to storage, pass the path</td></tr>
<tr><td>Using "now" in tasks</td><td>reruns get the wrong data</td><td>use the logical date</td></tr>
<tr><td>Non-idempotent tasks</td><td>retries duplicate data</td><td>overwrite or upsert</td></tr>
<tr><td>Dynamic start_date</td><td>confuses scheduling</td><td>use a fixed date</td></tr></table>
<p><b>Parts of Airflow:</b> the <b>scheduler</b> decides what's ready; <b>workers</b> run tasks; the <b>metadata database</b> stores state; and a <b>web server</b> shows it. Executors include Local, Celery and Kubernetes.</p>
<table><tr><th>Tool</th><th>Focus</th></tr>
<tr><td>Airflow</td><td>task-centred, the industry default</td></tr>
<tr><td>Dagster</td><td>asset-centred, focused on the data produced</td></tr>
<tr><td>Prefect</td><td>Python-native flows</td></tr>
<tr><td>Cloud (Step Functions, ADF)</td><td>tightly integrated, less portable</td></tr></table>
""", practice=["Don't Pass Data Through XCom", "Find Top-Level Work in a DAG File"])
