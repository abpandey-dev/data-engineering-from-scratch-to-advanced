from lib import *

THEORY("Lake vs warehouse vs lakehouse", """
<table><tr><th></th><th>Lake</th><th>Warehouse</th><th>Lakehouse</th></tr>
<tr><td>Storage</td><td>open files</td><td>managed by the vendor</td><td>open files + table format</td></tr>
<tr><td>ACID</td><td>no</td><td>yes</td><td>yes</td></tr>
<tr><td>Engines</td><td>many</td><td>one</td><td>many</td></tr>
<tr><td>Cost</td><td>low</td><td>higher</td><td>low storage, varied compute</td></tr></table>
""")
FAQ("What does a table format add to Parquet?", "<p>A metadata layer of snapshots and file lists, giving atomic commits, time travel, schema evolution, updates, and fast planning without listing files.</p>")
FAQ("How can ACID work on S3?", "<p>Files are immutable, and a commit atomically updates a single metadata pointer, via a catalog or conditional write. Readers see one complete snapshot.</p>")
FAQ("Copy-on-write vs merge-on-read?", "<p>Copy-on-write rewrites files on update, favouring reads. Merge-on-read writes deltas, favouring writes, and needs compaction.</p>")
FAQ("What is time travel, and what does it cost?", "<p>Querying an older snapshot. Old data files must be kept until the snapshot expires, which costs storage.</p>")
FAQ("What is Z-ordering?", "<p>Sorting by an interleaving of several columns' bits, so that files have tight min/max ranges on each of those columns, improving data skipping.</p>")
FAQ("Scenario: a lakehouse table has become slow to query. What do you check?", "<p>Small files, too many delete files, missing clustering, and the number of snapshots. Run compaction, then expire old snapshots.</p>")
FAQ("Scenario: you ran a bad MERGE. How do you recover?", "<p>Roll back to the previous snapshot with time travel, then fix the job. Check nothing downstream consumed the bad version.</p>")
FAQ("Scenario: legal asks you to erase a user from the lake. What's your plan?", "<p>Delete across all tables, including derived ones found via lineage, compact as needed, then expire snapshots and remove old files, and log the evidence.</p>")
