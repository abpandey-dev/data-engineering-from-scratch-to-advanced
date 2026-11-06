from lib import *
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


LESSON("Basics", "Handling files bigger than your memory", """
<p>You've written <code>data = open("file").read()</code>. On a 50 GB file with a 16 GB laptop, that crashes. The fix is the most useful Python idea in data engineering: <b>process one piece at a time</b>.</p>
<pre><code class="py">with open("huge.log") as f:
    for line in f:           # reads one line at a time
        handle(line)</code></pre>
<p><b>Generators</b> let you build pipelines of steps that hold almost nothing in memory. <code>yield</code> hands out one value and pauses:</p>
<pre><code class="py">def parse(lines):
    for line in lines:
        try:
            yield float(line.split(",")[1])
        except (IndexError, ValueError):
            continue          # skip bad lines (better: count them!)

total = sum(a for a in parse(open("huge.csv")) if a > 5)</code></pre>
<p>By hand, for "a,10", "bad", "b,x", "c,3", "d,20" with minimum 5: parse yields 10, 3 and 20, the filter keeps 10 and 20, and the total is <b>30</b>. Only one value exists at a time.</p>
<p>The chart compares memory use. A list grows with the data, while a generator stays flat.</p>
<p><b>Writing in batches.</b> A database insert per row is slow, while a huge insert can fail. So group rows: 7 rows in batches of 3 gives [0,1,2], [3,4,5], [6]. Don't forget that last partial batch, which is a very common bug.</p>
<p><b>Top K and merging</b> also avoid loading everything. A heap of size k finds the top k from any size of stream, using memory for only k items. <code>heapq.merge</code> merges sorted files holding just one item per file.</p>
""", practice=["Chunk a Stream", "Generator Pipeline", "Merge Sorted Files", "Top K From a Huge Stream", "Reservoir Sampling"])


@LD
def memory_of_list_vs_generator():
    import sys
    sizes = [10 ** k for k in range(1, 7)]
    lists = [sys.getsizeof([i for i in range(n)]) for n in sizes]
    gens = [sys.getsizeof(i for i in range(n)) for n in sizes]
    print("list of 1,000,000 uses", lists[-1], "bytes; generator uses", gens[-1])
    fig, ax = plt.subplots(figsize=(4.6, 2.7))
    ax.loglog(sizes, lists, "o-", label="list")
    ax.loglog(sizes, gens, "s-", label="generator")
    ax.set_xlabel("items")
    ax.set_ylabel("bytes held by the container")
    ax.legend(fontsize=7)


LESSON("Basics", "Dates and time zones: where bugs live", """
<p>Date bugs are probably the most common in pipelines. Three rules prevent most of them.</p>
<p><b>Rule 1: store everything in UTC.</b> Convert to local time only for display. 01:30 in India (+05:30) on 5 January is 20:00 UTC on <b>4 January</b>, so a different day. Grouping by the wrong one puts revenue on the wrong date.</p>
<p><b>Rule 2: know which time you mean.</b></p>
<table><tr><th>Time</th><th>Meaning</th></tr>
<tr><td>Event time</td><td>when it actually happened</td></tr>
<tr><td>Ingestion time</td><td>when your system received it</td></tr>
<tr><td>Processing time</td><td>when you processed it</td></tr></table>
<p>A phone offline for 3 hours sends yesterday's clicks today. Reports should normally use event time.</p>
<p><b>Rule 3: use a library, and never do calendar maths by hand.</b> Months differ in length, and leap years exist. From 27 February 2026 to 2 March gives 27, 28, 1, 2. Daylight saving means some days have 23 or 25 hours.</p>
<p><b>Finding gaps</b> is a regular task: which daily partitions are missing? Put the loaded dates in a set, then walk the calendar. If 1, 2 and 5 January exist, then 3 and 4 are missing, and they need a backfill.</p>
<p>Use ISO format, YYYY-MM-DD. It sorts correctly as text and nobody confuses day and month.</p>
""", practice=["Dates in a Range", "Convert to UTC", "Find Missing Days", "Sliding Time Window Count"])


LESSON("Core", "Failures: retries, validation and bad data", """
<p><b>Assume everything fails.</b> APIs time out, files arrive broken and networks drop.</p>
<p><b>Retry with backoff.</b> Waiting longer each time gives a struggling service room to recover: 1, 2, 4, 8 seconds. Add random jitter so that many clients don't retry together. After 3 attempts with two failures, you've waited 1 + 2 = 3 seconds.</p>
<p>Only retry what can succeed. A timeout is worth retrying, while an invalid password isn't.</p>
<p><b>Validate at the door.</b> Check data as it arrives, and record <i>why</i> rows were rejected:</p>
<pre><code class="py">{"id": -1, "email": "x", "age": 200}  →  problems: age, email, id</code></pre>
<p>Keep rules in a table instead of a chain of ifs, so that adding a rule doesn't mean rewriting code.</p>
<p><b>Always reconcile counts.</b> Rows read must equal rows written plus rows rejected. 1000 read, 980 written, 10 rejected? Then 10 rows vanished, which is a bug that's found only because you checked.</p>
<p><b>Logs should answer "what happened?" at 3 am.</b></p>
<pre><code class="py">import logging
log = logging.getLogger(__name__)
log.info("loaded %d rows for %s in %.1fs", n, day, seconds)
log.error("rejected %d rows: %s", bad, reasons)</code></pre>
<p>Use <code>logging</code>, not print, and never log personal data. Mask it: asha@example.com becomes a***@example.com.</p>
""", practice=["Retry With Backoff", "Validate a Record", "Coerce Types With a Schema", "Run Summary Metrics", "Mask Personal Data", "Parse a Log Line", "Count Errors by Level"])


LESSON("Core", "Writing pipeline code that lasts", """
<p>Notebook-style scripts break in production. Five habits fix most of that.</p>
<p><b>1. Pure functions.</b> A transform should take data in and return new data, changing nothing else. It's then trivial to test:</p>
<pre><code class="py">def add_tax(orders, rate):
    return [{**r, "total": round(r["amt"] * (1 + rate), 2)} for r in orders]

def test_add_tax():
    assert add_tax([{"amt": 100}], 0.18)[0]["total"] == 118.0</code></pre>
<p><b>2. Config outside the code.</b> The same code should run in dev and production, with only settings changing. Merge layers: defaults, then environment, then overrides. Secrets belong in a secrets manager, never in Git.</p>
<p><b>3. Stable hashing.</b> To split data consistently, use a stable hash like md5. Python's <code>hash()</code> changes between runs for strings, so a user could land in a different bucket each day.</p>
<p><b>4. Group by key</b> with <code>defaultdict(list)</code>, a pattern you'll use constantly.</p>
<p><b>5. Report on each run:</b> rows read and written, time taken, and rows per second.</p>
<p><b>A small project layout:</b></p>
<pre><code class="py">my_pipeline/
  extract.py   transform.py   load.py   config.py
tests/
  test_transform.py
pyproject.toml   README.md</code></pre>
""", practice=["Testable Transform", "Read Config With Defaults", "Stable Hash Bucket", "Group Into Files by Key"])
