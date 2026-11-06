from lib import *

THEORY("Libraries worth knowing", """
<table><tr><th>Library</th><th>Used for</th></tr>
<tr><td>csv, json, gzip, pathlib</td><td>reading and writing files</td></tr>
<tr><td>datetime, zoneinfo</td><td>dates and time zones</td></tr>
<tr><td>logging</td><td>recording what happened</td></tr>
<tr><td>pytest</td><td>testing</td></tr>
<tr><td>requests / httpx</td><td>calling APIs</td></tr>
<tr><td>pandas, polars, pyarrow</td><td>data on one machine, and Parquet</td></tr>
<tr><td>sqlalchemy, psycopg</td><td>talking to databases</td></tr>
<tr><td>boto3</td><td>AWS services</td></tr></table>
""")
FAQ("Why use generators in pipelines?", "<p>They process one item at a time, so memory stays flat however big the input is. They can also be chained into clean, testable steps.</p>")
FAQ("How do you handle a file bigger than memory?", "<p>Stream it line by line or in chunks, process with generators, and write out in batches. For heavy work, use a columnar format and a tool like DuckDB, Polars or Spark.</p>")
FAQ("Why store timestamps in UTC?", "<p>It's unambiguous and has no daylight saving jumps. Local time is applied only when displaying data.</p>")
FAQ("Event time vs processing time?", "<p>Event time is when something happened. Processing time is when your system handled it. They differ when data is late, and reports should normally use event time.</p>")
FAQ("How do you make Python pipelines testable?", "<p>Keep transforms as pure functions, isolate input and output at the edges, use small fixture data, and test edge cases like empty input and bad rows.</p>")
FAQ("Why not use Python's hash() to partition data?", "<p>String hashes are randomised per process, so results differ between runs. Use a stable hash such as md5 or murmur.</p>")
FAQ("Scenario: your job's memory grows until it crashes. How do you debug it?", "<p>Look for lists or dictionaries growing without limit, such as collecting all rows or an unbounded cache. Stream instead, process in chunks, and measure with a profiler on a sample.</p>")
FAQ("Scenario: an API returns errors randomly during your load. What do you build?", "<p>Retries with exponential backoff and jitter, timeouts, respect for rate limits, and a way to resume from the last good point instead of restarting. Alert if it keeps failing.</p>")
FAQ("Scenario: revenue is right in total but wrong per day. What's the likely cause?", "<p>Time zones or the day boundary. Check whether grouping used UTC or local time, and event time or ingestion time.</p>")
