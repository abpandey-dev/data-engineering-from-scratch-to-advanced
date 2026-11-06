from lib import *
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import gzip
import io
import csv
import json


LESSON("Basics", "Why file format changes everything", """
<p>The same data can cost 40 times more to query, purely because of how it's written.</p>
<table><tr><th>Format</th><th>Layout</th><th>Schema</th><th>Speed for analytics</th><th>Use</th></tr>
<tr><td>CSV</td><td>text, rows</td><td>none</td><td>slow</td><td>exchange with people</td></tr>
<tr><td>JSON Lines</td><td>text, rows</td><td>none</td><td>slow</td><td>raw events, nested data</td></tr>
<tr><td>Avro</td><td>binary, rows</td><td>built in</td><td>medium</td><td>Kafka, writing a row at a time</td></tr>
<tr><td>Parquet / ORC</td><td>binary, columns</td><td>built in</td><td>fast</td><td>analytics</td></tr></table>
<p><b>Rows vs columns on disk:</b></p>
<div class="pic">Row:     1 Asha Pune | 2 Ben Delhi | 3 Chen Pune
Column:  1 2 3 | Asha Ben Chen | Pune Delhi Pune</div>
<p><b>Query cost example.</b> 1 TB of data, 50 columns, a query using 5, and Parquet compressing 4 times:</p>
<ul><li>CSV reads everything: 1,000 GB.</li><li>Parquet: 1000 × 5/50 ÷ 4 = <b>25 GB</b>, which is 40 times less.</li></ul>
<p>If your warehouse charges per byte scanned, that's also 40 times cheaper.</p>
<p><b>What's inside a Parquet file?</b> It's split into <b>row groups</b>, say 128 MB each. Each holds column chunks, split into pages. The footer stores the schema, plus <b>min and max values</b> per chunk. A query for values 15 to 22, with groups covering 1–10, 11–20 and 21–30, can skip the first group without reading it.</p>
""", practice=["Rows to Columns", "Compare Query Cost by Format", "Min/Max Skipping", "Nested to Parquet-Friendly"])


LESSON("Core", "How compression really works", """
<p>Columnar files compress well because similar values sit together. Encodings run first, then general compression such as Snappy or ZSTD.</p>
<table><tr><th>Encoding</th><th>Idea</th><th>Example</th></tr>
<tr><td>Run-length</td><td>store value + count</td><td>a a a b a → a×3, b×1, a×1</td></tr>
<tr><td>Dictionary</td><td>store distinct values once, plus small ids</td><td>IN US IN IN → [IN, US] + 0 1 0 0</td></tr>
<tr><td>Delta</td><td>store differences</td><td>1000 1001 1003 → 1000, 1, 2</td></tr></table>
<p><b>Which wins depends on the data.</b> With 2,000 values of two letters, stored plainly at 4,000 bytes:</p>
<table><tr><th>Data</th><th>Plain</th><th>RLE (value + 4-byte count)</th></tr>
<tr><td>IN×1000, US×1000</td><td>4,000</td><td><b>12</b></td></tr>
<tr><td>a, b, a, b, … alternating</td><td>2,000</td><td>10,000: worse!</td></tr></table>
<p>RLE is amazing on long runs, and it backfires on data with none. Formats pick encodings automatically, per column.</p>
<p>Real dictionary encoding doesn't use 4 bytes per id. Two distinct values need only <b>1 bit</b> each, so 1,000 values take 125 bytes.</p>
<p><b>Sorting improves compression</b>, because it creates long runs. The demo compresses 100,000 random city names: about 44,600 bytes shuffled, and just 744 bytes sorted. Real data won't always be this dramatic. Sorting data by a low-cardinality column before writing is a cheap trick that often gives a big saving, and it also improves min/max skipping.</p>
<table><tr><th>Codec</th><th>Ratio</th><th>Speed</th></tr>
<tr><td>Snappy</td><td>lower</td><td>very fast</td></tr><tr><td>ZSTD</td><td>high</td><td>good: a strong default</td></tr><tr><td>Gzip</td><td>high</td><td>slower</td></tr></table>
""", practice=["Run-Length Encoding", "Dictionary Encoding", "Delta Encoding", "Encoded Size Comparison", "Bit-Width of a Dictionary", "Sorted Data Compresses Better"])


@LD
def sorting_helps_compression():
    rng = np.random.default_rng(0)
    cities = rng.choice(["Pune", "Delhi", "Goa", "Agra"], 100000).tolist()
    shuffled = len(gzip.compress(",".join(cities).encode(), 6, mtime=0))
    ordered = len(gzip.compress(",".join(sorted(cities)).encode(), 6, mtime=0))
    print("raw bytes:", len(",".join(cities)))
    print("gzip, shuffled:", shuffled)
    print("gzip, sorted:  ", ordered)
    fig, ax = plt.subplots(figsize=(4.2, 2.5))
    ax.bar(["shuffled", "sorted"], [shuffled, ordered])
    ax.set_ylabel("compressed bytes")


LESSON("Core", "Partitioning and the small file problem", """
<p><b>Partitioning</b> splits a table into folders by a column, so a query can skip whole folders: partition pruning.</p>
<pre><code class="py">lake/orders/year=2026/month=01/day=05/part-0.parquet</code></pre>
<p>A query for one day out of three, sized 100, 200 and 300 MB, reads 200 MB, not 600.</p>
<p><b>Choosing the column is a real design decision:</b></p>
<table><tr><th>1 TB partitioned by</th><th>Partitions</th><th>Average size</th><th>Verdict</th></tr>
<tr><td>date (1 year)</td><td>365</td><td>2.74 GB</td><td>good</td></tr>
<tr><td>country code flag</td><td>2</td><td>500 GB</td><td>too few</td></tr>
<tr><td>user id</td><td>10 million</td><td>100 KB</td><td><b>terrible</b></td></tr></table>
<p>Partition by what queries filter on, with moderate cardinality. Never by a high-cardinality column like user id.</p>
<p><b>The small file problem.</b> Opening a file has a cost whatever its size. Reading 1 GB with 2 ms per file open and 1 MB per ms:</p>
<table><tr><th>Files</th><th>Opening</th><th>Reading</th><th>Total</th></tr>
<tr><td>4</td><td>8 ms</td><td>1,000 ms</td><td>about 1 s</td></tr>
<tr><td>10,000</td><td>20,000 ms</td><td>1,000 ms</td><td><b>21 s</b></td></tr></table>
<p>The chart shows this. Streaming jobs and over-partitioned tables often produce thousands of tiny files. The fix is <b>compaction</b>, merging them into files of about 128 MB to 1 GB. So 10 GB at 128 MB needs 79 files.</p>
<p><b>Bucketing</b> splits by hash of a column, such as <code>id % n</code>, inside partitions. Equal keys are then always in the same bucket number, which makes joins on that key much cheaper, as you'll see in Spark.</p>
""", practice=["Partition Pruning", "Choosing a Partition Column", "The Small File Problem", "Compact Small Files", "How Many Output Files?", "Hive-Style Partition Paths", "Bucket for Sampling and Joins"])


@LD
def small_files_chart():
    files = np.array([1, 10, 100, 1000, 10000, 100000])
    fig, ax = plt.subplots(figsize=(4.6, 2.7))
    ax.semilogx(files, (files * 2 + 1000) / 1000, "o-")
    ax.set_xlabel("files holding the same 1 GB")
    ax.set_ylabel("seconds to read")


LESSON("Advanced", "Object storage, schema changes and tiers", """
<p><b>Object storage</b> (S3, GCS, Azure Blob) is where lakes live. It's cheap and nearly unlimited, but it's <b>not a normal disk</b>:</p>
<ul><li>A "folder" is just a name prefix, so listing many files is slow.</li>
<li>You replace whole objects; you can't edit a part of a file.</li>
<li>A rename is really a copy and a delete, so it isn't atomic for many files. That's why renaming a folder to commit results isn't safe, and table formats exist.</li></ul>
<p><b>Separating storage and compute</b> is the big architectural change of the last decade. Data sits in cheap object storage while compute scales on demand, and you pay for compute only when running.</p>
<p><b>Schema evolution.</b> What can change safely?</p>
<table><tr><th>Change</th><th>Safe?</th></tr><tr><td>Add an optional column</td><td>yes</td></tr><tr><td>Remove a column</td><td>no: readers may need it</td></tr><tr><td>Rename a column</td><td>no: it looks like remove + add</td></tr><tr><td>Change a type</td><td>usually not; widening int to long often is</td></tr></table>
<p><b>Storage tiers</b> trade access speed against price. Keep recent data hot and move old data to cold, with lifecycle rules. With made-up prices, 100 GB hot, 200 GB warm and 1,000 GB cold costs 2.3 + 2.5 + 4 = 8.8 a month. Remember that cold tiers often charge for retrieval.</p>
<p><b>Verify files.</b> Keep checksums in a manifest, because files can arrive truncated, and a checksum catches it at once.</p>
""", practice=["Schema Evolution: What's Safe?", "Storage Tier Choice", "Checksums Catch Corruption"])
