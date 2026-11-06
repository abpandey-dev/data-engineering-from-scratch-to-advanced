from lib import *
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np



LESSON("Basics", "Why plain data lakes break", """
<p>A folder of Parquet files is cheap, but it's missing what databases give you:</p>
<table><tr><th>Problem</th><th>What happens</th></tr>
<tr><td>No atomic writes</td><td>a reader sees half of a job's files</td></tr>
<tr><td>Two writers</td><td>they overwrite each other</td></tr>
<tr><td>No updates or deletes</td><td>you rewrite everything by hand</td></tr>
<tr><td>Listing files is slow</td><td>queries wait on millions of objects</td></tr>
<tr><td>Schema changes</td><td>old files break new readers</td></tr></table>
<p><b>Table formats (Apache Iceberg, Delta Lake, Apache Hudi) add a metadata layer that says exactly which files make up the table.</b></p>
<div class="pic">Catalog → current metadata → snapshot → manifests → data files
                                 (a list of files, with min/max per column)</div>
<p><b>The key trick is immutability.</b> Files never change. A write adds new files and creates a new <b>snapshot</b>, then atomically swaps one pointer. Readers see either the old version or the new one, never half.</p>
<table><tr><th>Commit</th><th>Snapshot's files</th></tr>
<tr><td>add f1</td><td>f1</td></tr><tr><td>add f2</td><td>f1, f2</td></tr><tr><td>add f3, remove f1</td><td>f2, f3</td></tr></table>
<p><b>Time travel</b> comes free: old snapshots still point to old files, so you can query yesterday's table or roll back a bad load. At time 25, with commits at 10, 20 and 30, you read the snapshot from 20.</p>
<pre><code class="py">SELECT * FROM orders FOR TIMESTAMP AS OF '2026-01-05 00:00:00';   -- Iceberg, in Spark SQL
spark.read.format("delta").option("versionAsOf", 12).load(path)    # Delta</code></pre>
""", practice=["Snapshot Commit", "Time Travel", "Read Delta's Log", "Incremental Read Between Snapshots"])


LESSON("Core", "Updating immutable files", """
<p>Files can't change, so how does UPDATE work?</p>
<table><tr><th></th><th>Copy-on-write</th><th>Merge-on-read</th></tr>
<tr><td>Update</td><td>rewrite the whole file</td><td>write a small delta file</td></tr>
<tr><td>Writes</td><td>slower</td><td>fast</td></tr>
<tr><td>Reads</td><td>fast</td><td>slower: merge at read time</td></tr>
<tr><td>Suits</td><td>read-heavy tables</td><td>frequent updates, CDC</td></tr></table>
<p><b>By hand.</b> Updating id 2 in a file holding ids 1 and 2 rewrites 2 rows to change 1. With 10 updates a day in files of 1,000 rows, copy-on-write rewrites 10,000 rows. With merge-on-read and 100 reads a day, readers merge 1,000 delta rows in total.</p>
<p><b>MERGE INTO</b> does upserts and deletes in one atomic statement, which is why CDC to a lake became practical:</p>
<pre><code class="py">MERGE INTO target t USING changes c ON t.id = c.id
WHEN MATCHED AND c.op = 'D' THEN DELETE
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *;</code></pre>
<p><b>Concurrent writers use optimistic concurrency.</b> Everyone assumes success, then tries to swap the pointer. If the table moved on, check for a real conflict. Two writers on d1 and d2 both succeed, and a second writer on d1 that read an old version conflicts and must retry.</p>
""", practice=["Copy-on-Write Update", "Merge-on-Read", "COW vs MOR Cost", "MERGE INTO on a Lake", "Optimistic Concurrency", "Choose a Table Strategy"])


LESSON("Core", "Keeping tables fast", """
<p><b>Metadata pruning.</b> Manifests store min and max per column for each file, so a query can pick files with no directory listing. Looking for 18 among files 1–10, 11–20 and 15–30 reads two of the three.</p>
<p><b>Clustering makes that work.</b> If values are spread randomly, every file's range covers everything. For values 1, 9, 5, 2, 9, 7, 3, 9, 8 in files of 3, looking for 5 reads <b>3 files</b>. Sorted, it reads <b>1</b>. The chart measures this at a larger scale: with 100,000 random values in files of 1,000 rows, an unsorted lookup reads all 100 files, and a sorted one reads 1.</p>
<p><b>Z-ordering</b> sorts on two columns at once, by interleaving their bits, so nearby points in both dimensions stay near each other on disk. It helps a little on each column, rather than perfectly on one.</p>
<p><b>Maintenance is your job:</b></p>
<table><tr><th>Task</th><th>Why</th><th>Example</th></tr>
<tr><td>Compaction</td><td>merges small files</td><td>half the files under 128 MB is a signal</td></tr>
<tr><td>Expire snapshots</td><td>time travel keeps old files, costing money</td><td>keeping only time 30 frees a and b</td></tr>
<tr><td>Remove orphans</td><td>failed writes leave junk</td><td>skip very new files: a write may be in progress</td></tr></table>
<p>Bin-packing files 10, 20, 30, 90 with a 128 MB target gives 60 and 90, leaving large files alone.</p>
""", practice=["Pick Files From Manifests", "Effect of Clustering", "Z-Order Key", "Bin-Pack Compaction", "Does This Table Need Compaction?", "Expire Old Snapshots", "Orphan Files"])


@LD
def clustering_chart():
    rng = np.random.default_rng(0)
    values = rng.integers(0, 100000, 100000)
    def files_read(data, file_rows):
        lows = [data[i:i + file_rows].min() for i in range(0, len(data), file_rows)]
        highs = [data[i:i + file_rows].max() for i in range(0, len(data), file_rows)]
        targets = rng.integers(0, 100000, 50)
        return np.mean([sum(a <= t <= b for a, b in zip(lows, highs)) for t in targets])
    sizes = [1000, 5000, 10000]
    unsorted = [files_read(values, s) for s in sizes]
    ordered = [files_read(np.sort(values), s) for s in sizes]
    print("files read, unsorted:", np.round(unsorted, 1))
    print("files read, sorted:  ", np.round(ordered, 1))
    fig, ax = plt.subplots(figsize=(4.6, 2.7))
    x = np.arange(3)
    ax.bar(x - 0.2, unsorted, 0.4, label="unsorted")
    ax.bar(x + 0.2, ordered, 0.4, label="sorted")
    ax.set_xticks(x, [f"{s} rows/file" for s in sizes], fontsize=7)
    ax.set_ylabel("files read per lookup")
    ax.legend(fontsize=7)


LESSON("Advanced", "Evolution, privacy and choosing a format", """
<p><b>Hidden partitioning (Iceberg).</b> Users filter on the timestamp, and Iceberg works out the partition. A query from 10 February to 5 March scans the 2026-02 and 2026-03 partitions, and nobody has to remember a special column. You can also change the partition scheme later without rewriting old data.</p>
<p><b>Safe schema evolution.</b> Files store column <b>ids</b>, not just names, so renaming is safe: id 1 can become "label" and still read old files, and a new column reads as None.</p>
<p><b>Privacy on immutable files.</b> Deleting a user rewrites only the files holding them: 2 files and 3 other rows here. But <b>old snapshots still hold the data</b>, until you expire them, so deletion isn't finished after the DELETE statement. This trips many teams up.</p>
<table><tr><th></th><th>Iceberg</th><th>Delta Lake</th><th>Hudi</th></tr>
<tr><td>Strength</td><td>open, wide engine support, hidden partitioning</td><td>tight Spark and Databricks integration</td><td>record-level upserts, streaming ingestion</td></tr></table>
<p>They've converged a lot, and tools can increasingly read across formats. Choose by your engines and team, and check current features, since this area changes quickly.</p>
""", practice=["Hidden Partitioning", "Schema Evolution by Column ID", "Delete for Privacy"])
