from lib import *
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


LESSON("Basics", "What does a data engineer actually do?", """
<p>Imagine a huge city. Water comes from rivers and rain. Before you can drink it, someone must collect it, clean it, store it and pipe it to every home. No one thanks the water engineers until a tap runs dry.</p>
<p><b>A data engineer does this for data.</b> A company's data starts scattered across apps, payment systems and sensors. Analysts, scientists and AI models need it clean, connected and on time. You build the pipes between them.</p>
<div class="pic">Sources      Ingest       Store        Transform     Serve        Users
apps    ──▶  collect ──▶  raw lake ──▶ clean, join ─▶ warehouse ─▶ dashboards
payments     in batches   (keep it     and model      or API       ML models
sensors      or streams   all)         the data                    AI apps</div>
<table><tr><th>Role</th><th>Main question</th><th>Typical output</th></tr>
<tr><td><b>Data engineer</b></td><td>Is the right data arriving, correct and on time?</td><td>reliable pipelines and tables</td></tr>
<tr><td>Data analyst</td><td>What happened, and why?</td><td>dashboards, reports</td></tr>
<tr><td>Data scientist</td><td>What will happen? What should we try?</td><td>models, experiments</td></tr>
<tr><td>ML engineer</td><td>How do we run this model in production?</td><td>model services</td></tr></table>
<p><b>What separates good from great?</b> Beginners ask "does it run?". Strong engineers ask: what if it runs twice? What if yesterday's data arrives today? What if the source adds a column? How will I know it broke before my users do? This course teaches those questions along with the tools, and tools change while these questions don't.</p>
""", practice=["Which Tool for the Job?"])


LESSON("Basics", "ETL by hand: your first pipeline", """
<p>Every pipeline, however large, does three things. <b>Extract</b> takes data from a source. <b>Transform</b> cleans and shapes it. <b>Load</b> writes it where people can use it.</p>
<p>Say this file arrives:</p>
<pre><code class="py">city,amount
Pune,10
Delhi,5
Pune,x        ← bad value
Pune,2.5</code></pre>
<table><tr><th>Step</th><th>What happens</th><th>Result</th></tr>
<tr><td>Extract</td><td>read 4 rows</td><td>4 dictionaries of text</td></tr>
<tr><td>Transform</td><td>convert amount to a number; "x" fails</td><td>3 good, 1 bad</td></tr>
<tr><td>Load</td><td>total per city</td><td>Delhi 5, Pune 12.5</td></tr></table>
<p><b>Lesson 1: never quietly lose data.</b> The bad row should go somewhere you can look at it, called a <b>dead-letter</b> location. Otherwise your total is wrong and nobody knows.</p>
<p><b>Lesson 2: keep steps separate.</b> If extract, transform and load are separate functions, each can be tested alone.</p>
<p><b>ETL vs ELT.</b> Traditionally you cleaned data first (ETL), because storage was expensive. Now storage is cheap and warehouses are powerful, so teams often <b>load raw data first, then transform it inside the warehouse (ELT)</b>. If your logic has a bug, the raw data's still there, so you can fix it and rebuild.</p>
<p><b>Real data is messy:</b> CSV values contain commas, so use a real parser. JSON is nested, so you flatten it. Sources send duplicates, so you remove them. Columns change, so you check the schema when data arrives.</p>
""", practice=["Extract: Parse CSV Text", "Transform: Clean One Record", "Load: Good Rows and Bad Rows", "A Tiny ETL Pipeline", "Flatten a JSON Event", "Parse JSON Lines", "Remove Exact Duplicates", "Schema Check on Arrival"])


LESSON("Basics", "Two kinds of database: OLTP and OLAP", """
<p>A shop's till and its yearly accounts need very different things.</p>
<table><tr><th></th><th>OLTP (the till)</th><th>OLAP (the accounts)</th></tr>
<tr><td>Purpose</td><td>run the app</td><td>analyse the business</td></tr>
<tr><td>Typical query</td><td>"get order 123"</td><td>"revenue by city for 3 years"</td></tr>
<tr><td>Rows touched</td><td>a few</td><td>billions</td></tr>
<tr><td>Writes</td><td>constant small updates</td><td>big scheduled loads</td></tr>
<tr><td>Examples</td><td>PostgreSQL, MySQL</td><td>Snowflake, BigQuery, Redshift</td></tr>
<tr><td>Storage</td><td>row by row</td><td>column by column</td></tr></table>
<p><b>Why do columns help analytics?</b> Take 1 million rows, 50 columns of 8 bytes each, and a query that uses just 2 columns:</p>
<ul><li><b>Row store:</b> reads everything: 1,000,000 × 50 × 8 = <b>400 MB</b>.</li>
<li><b>Column store:</b> reads only 2 columns: 1,000,000 × 2 × 8 = <b>16 MB</b>, which is 25 times less.</li></ul>
<p>Similar values also sit next to each other, so they compress well. A file might shrink 4 times, saving 75%. The chart shows how the saving grows with table width.</p>
<p><b>This is why you don't run analytics on the production database.</b> One big report can slow the app for real customers. So data engineers copy data out to a separate analytics system.</p>
""", practice=["Row Store vs Column Store Cost", "Compression Savings"])


@LD
def column_saving():
    widths = np.array([5, 10, 20, 50, 100, 200])
    fig, ax = plt.subplots(figsize=(4.6, 2.7))
    ax.plot(widths, 1000000 * widths * 8 / 1e6, "o-", label="row store reads all columns")
    ax.plot(widths, np.full(len(widths), 1000000 * 2 * 8 / 1e6), "s-", label="column store reads 2 columns")
    ax.set_xlabel("columns in the table")
    ax.set_ylabel("MB read for 1M rows")
    ax.legend(fontsize=7)


LESSON("Core", "Batch or streaming?", """
<p><b>Batch</b> is like a bus: it waits, collects passengers, and leaves on a schedule. <b>Streaming</b> is like a taxi: each passenger leaves right away.</p>
<table><tr><th>Run every</th><th>Average wait</th><th>Worst wait</th></tr>
<tr><td>24 hours</td><td>12 hours</td><td>24 hours</td></tr>
<tr><td>60 minutes</td><td>30 minutes</td><td>60 minutes</td></tr>
<tr><td>1 minute</td><td>30 seconds</td><td>1 minute</td></tr></table>
<p>Streaming feels better, so why isn't everything streaming? Because it's harder and more expensive: data arrives out of order, the system must run all day, and fixing mistakes is more difficult.</p>
<p><b>Ask: what decision depends on this data, and how quickly?</b></p>
<ul><li>Block a fraudulent card: seconds, so streaming.</li>
<li>Update a live operations board: minutes, so micro-batch.</li>
<li>Monthly finance report: a day is fine, so batch.</li></ul>
<p>A very common mistake is building streaming because it sounds advanced, for data that someone reads once a day. Choosing the simpler option is a mark of seniority.</p>
<p><b>Freshness</b> is how old your newest data is. If the latest event loaded was 10 minutes ago and your promise (an <b>SLA</b>) is 15 minutes, you're fine. If it's 33 minutes, you've broken it, and someone should be alerted.</p>
""", practice=["Batch Size vs Latency", "Data Freshness"])


LESSON("Core", "Thinking in numbers", """
<p>Before building anything, estimate. It takes a minute and prevents very expensive mistakes.</p>
<p><b>Volume.</b> 1,000 events per second at 500 bytes each:</p>
<ul><li>A day has 86,400 seconds, so 86,400,000 events.</li>
<li>86,400,000 × 500 bytes = <b>43.2 GB a day</b>.</li>
<li>× 365 = <b>15.77 TB a year</b>.</li></ul>
<p><b>Time.</b> Processing 100 GB at 50 MB/s takes 2,000 seconds, or <b>33 minutes</b>. With 10 workers and perfect scaling, it's 3.3 minutes. In practice you won't get perfect scaling, for reasons you'll learn in the Spark topics.</p>
<p><b>Cost.</b> 500 GB a day kept for 90 days is 45,000 GB. At a made-up $0.02 per GB per month, that's $900 a month. If you compress it 4 times, it's $225.</p>
<p><b>Peaks.</b> Hourly counts of 100, 100, 400, 200 average 200, but the peak's 400, a ratio of 2. Systems must handle the peak, not the average.</p>
<p><b>Reliability multiplies.</b> A chain of 10 steps, each 99% reliable, succeeds only 0.99¹⁰ = <b>90.4%</b> of the time. Run daily, that's about <b>35 failures a year</b>. At 99.9% per step, it's about 3.6. So you need retries and alerts, as failure is normal rather than rare. The chart shows how quickly reliability falls as a pipeline gets longer.</p>
<table><tr><th>Handy numbers</th><th></th></tr><tr><td>Seconds in a day</td><td>86,400 (about 10⁵)</td></tr><tr><td>1 GB</td><td>1,000 MB</td></tr><tr><td>1 TB</td><td>1,000 GB</td></tr></table>
""", practice=["How Much Data per Day?", "How Long to Process It?", "Storage Cost", "Peak vs Average Load", "Pipeline Reliability"])


@LD
def reliability_chart():
    steps = np.arange(1, 51)
    fig, ax = plt.subplots(figsize=(4.6, 2.7))
    for p in [0.999, 0.99, 0.95]:
        ax.plot(steps, p ** steps, label=f"each step {p}")
    ax.set_xlabel("steps in the pipeline")
    ax.set_ylabel("chance a run succeeds")
    ax.legend(fontsize=7)


LESSON("Core", "The lake, the warehouse and who depends on what", """
<p><b>Layers.</b> Most platforms keep data at several levels of refinement. It's often called the <b>medallion</b> pattern:</p>
<table><tr><th>Layer</th><th>Holds</th><th>Who uses it</th></tr>
<tr><td>Bronze (raw)</td><td>exactly what arrived</td><td>engineers, to reprocess</td></tr>
<tr><td>Silver (clean)</td><td>typed, deduplicated, joined</td><td>analysts, scientists</td></tr>
<tr><td>Gold (business)</td><td>metrics ready to use</td><td>dashboards, reports</td></tr></table>
<p><b>Partitioning.</b> Lakes store files in folders by date, like <code>lake/orders/year=2026/month=01/day=05/</code>. A query about one day then reads just one folder, rather than years of data.</p>
<p><b>Lineage</b> is the family tree of your tables. If <code>clean</code> breaks, what else is wrong?</p>
<div class="pic">raw → clean → daily → dashboard
          └──→ users</div>
<p>A failure in <code>clean</code> affects daily, users and dashboard. That's a graph search. Knowing this lets you warn the right people before they find out by themselves.</p>
<p><b>Your first 90 days on any data team:</b> learn one pipeline from source to dashboard, find out who uses it, and what they'd notice if it broke.</p>
""", practice=["Daily Partition Path", "Lineage: What Breaks Downstream?"])
