from lib import *

THEORY("Picking a format", """
<table><tr><th>Need</th><th>Choose</th></tr>
<tr><td>Analytics tables</td><td>Parquet (or ORC), with ZSTD or Snappy</td></tr>
<tr><td>Streaming messages</td><td>Avro or Protobuf with a schema registry</td></tr>
<tr><td>Raw capture of unknown data</td><td>JSON Lines, compressed</td></tr>
<tr><td>Sharing with people</td><td>CSV</td></tr>
<tr><td>Updates, deletes, time travel</td><td>a table format: Iceberg, Delta, Hudi</td></tr></table>
""")
FAQ("Why is Parquet faster than CSV?", "<p>It's columnar, so it reads only needed columns. It compresses better, stores types, and keeps min/max statistics that let readers skip data.</p>")
FAQ("Avro vs Parquet?", "<p>Avro is row-based, suited to writing records one at a time, as in Kafka. Parquet is columnar, suited to analytic reads.</p>")
FAQ("What is partition pruning?", "<p>Skipping entire partitions that a filter rules out, so the engine never reads those files.</p>")
FAQ("Partitioning vs bucketing?", "<p>Partitioning creates folders by value, helping filters on a moderate-cardinality column. Bucketing splits by a hash into a fixed number of files, helping joins and high-cardinality keys.</p>")
FAQ("What's the small file problem, and how do you fix it?", "<p>Many tiny files add per-file open and metadata costs. Fix with compaction, sensible partitioning, and repartitioning before writing.</p>")
FAQ("Why isn't S3 a normal file system?", "<p>Objects are written whole, listing is slow, and renames aren't atomic. That's why table formats keep their own metadata.</p>")
FAQ("Scenario: a daily job's query cost suddenly tripled. Where do you look?", "<p>A filter on the partition column may have been lost, a function may be wrapping it, or someone added SELECT *. Compare bytes scanned with the query plan.</p>")
FAQ("Scenario: a streaming job produced 500,000 tiny files. What now?", "<p>Compact them in a background job, then increase the trigger interval or file target size. A table format's compaction action can do this safely.</p>")
FAQ("Scenario: someone partitioned a table by user_id. What's wrong?", "<p>Millions of tiny partitions, with huge metadata overhead. Partition by date instead, and bucket or sort by user_id.</p>")
