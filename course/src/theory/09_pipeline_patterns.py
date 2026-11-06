from lib import *

THEORY("Loading patterns compared", """
<table><tr><th>Pattern</th><th>Idempotent?</th><th>Handles deletes?</th><th>Use for</th></tr>
<tr><td>Full reload</td><td>yes</td><td>yes</td><td>small tables</td></tr>
<tr><td>Overwrite partition</td><td>yes</td><td>within the partition</td><td>immutable events by date</td></tr>
<tr><td>Append</td><td>no</td><td>no</td><td>only with a unique key to dedupe on</td></tr>
<tr><td>Upsert / MERGE</td><td>yes</td><td>if told</td><td>mutable records</td></tr>
<tr><td>CDC</td><td>if applied by key</td><td>yes</td><td>fresh copies of databases</td></tr></table>
""")
FAQ("What does idempotent mean, and why does it matter?", "<p>Running a job repeatedly gives the same result as running it once. Pipelines fail and get retried, so this makes recovery safe.</p>")
FAQ("How do you make a pipeline idempotent?", "<p>Overwrite a partition, or upsert on a unique key. Parameterise by date rather than using the current time, and avoid side effects such as blind appends.</p>")
FAQ("Full vs incremental load?", "<p>Full is simple and catches deletes, but costs grow with table size. Incremental is efficient, but more complex, and it can miss deletes and late rows.</p>")
FAQ("What is CDC, and why use it?", "<p>Reading a database's transaction log to capture every change. It sees deletes and intermediate states, with low load on the source, and it enables near real-time copies.</p>")
FAQ("How do you handle late-arriving data?", "<p>Use event time, reprocess affected partitions, set a cut-off, and make runs idempotent. In streaming, use watermarks.</p>")
FAQ("What is write-audit-publish?", "<p>Write to staging, run quality checks, then publish atomically only on success, so users never see unverified data.</p>")
FAQ("Scenario: a job failed halfway and left partial data. How do you recover?", "<p>If it's idempotent, simply rerun it. If it isn't, find what was written, delete it, fix the job so that it's idempotent, and add atomic publishing.</p>")
FAQ("Scenario: revenue doubled for one day. What's your first guess?", "<p>A rerun with append, or a duplicated source file. Check duplicates on the unique key and the load history, then replace that partition and fix the pattern.</p>")
FAQ("Scenario: you need to backfill 2 years without affecting production. How?", "<p>Split it into chunks, limit concurrency, schedule off-peak, write to a separate table, compare with existing data, then swap atomically. Make it resumable.</p>")
FAQ("Scenario: your incremental load keeps missing a few rows each day. Why?", "<p>Likely long transactions committing with older timestamps, or clock differences. Add a lookback window with an idempotent merge, or move to CDC.</p>")
