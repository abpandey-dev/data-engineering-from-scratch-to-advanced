from lib import *
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np



LESSON("Basics", "Why a query can take 1 ms or 1 hour", """
<p>Disks read data in blocks called <b>pages</b>, often about 8 KB each. Reading from disk is vastly slower than from memory, so database design is largely about reading as few pages as possible.</p>
<p>With 1,000,000 rows of 100 bytes, 8,000-byte pages hold 80 rows each. That's 12,500 pages, or 100 MB.</p>
<p><b>An index is like the index at the back of a book.</b> Without one, finding a row may mean reading everything:</p>
<table><tr><th>Rows</th><th>Full scan, worst case</th><th>Index (binary search)</th></tr>
<tr><td>1 million</td><td>1,000,000 comparisons</td><td><b>20</b></td></tr>
<tr><td>1 billion</td><td>1,000,000,000 comparisons</td><td><b>30</b></td></tr></table>
<p>The chart shows how differently these grow.</p>
<p><b>A B-tree</b> is the usual index. It's not a binary tree: each node is a whole page, holding hundreds of keys, so the tree is wide and very short. With 500 children per node, 1 billion rows need only <b>4 levels</b>, or about 4 page reads, and the top levels are usually already in memory. Leaves are linked in order, so ranges are fast too: find the start, then walk along.</p>
<p><b>Indexes aren't free.</b> Each insert updates every index. With 4 indexes, 1,000 inserts cost 5,000 writes, which is 5 times the work. Don't index everything.</p>
""", practice=["Scan vs Index: Comparisons", "Index Lookup in a Sorted List", "B-Tree Height", "Range Scan With an Index", "Rows per Page", "Write Amplification"])


@LD
def scan_vs_index_chart():
    n = np.logspace(2, 9, 8)
    fig, ax = plt.subplots(figsize=(4.6, 2.7))
    ax.loglog(n, n, "o-", label="full scan")
    ax.loglog(n, np.ceil(np.log2(n)), "s-", label="binary search")
    ax.loglog(n, np.ceil(np.log(n) / np.log(500)), "^-", label="B-tree page reads (fanout 500)")
    ax.set_xlabel("rows")
    ax.set_ylabel("steps")
    ax.legend(fontsize=7)


LESSON("Core", "When indexes help, and when they don't", """
<p><b>Column order matters in a composite index.</b> An index on (last_name, first_name) works like a phone book. You can find "Smith", or "Smith, Sam", but not everyone named "Sam".</p>
<table><tr><th>Index (a, b, c), query filters on</th><th>Columns usable</th></tr>
<tr><td>a, b</td><td>2</td></tr><tr><td>b, c</td><td>0</td></tr><tr><td>a, c</td><td>1, because the run stops at the gap</td></tr></table>
<p><b>Selectivity</b> is distinct values ÷ rows. With 900,000 emails in 1M rows, it's 0.9, so an index helps enormously. With a true/false column, it's almost 0. An index would jump around the disk fetching half the table, so a scan is often faster, and the optimiser knows this.</p>
<p><b>Things that stop an index being used:</b></p>
<ul><li>A function on the column: <code>WHERE YEAR(d) = 2026</code>. Write a range instead.</li>
<li>A leading wildcard: <code>LIKE '%son'</code>.</li>
<li>A type mismatch between the column and the value.</li></ul>
<p><b>Read the plan.</b> <code>EXPLAIN</code> shows what the database will do. Learning to read plans is one of the highest-value database skills there is.</p>
<pre><code class="py">EXPLAIN ANALYZE SELECT * FROM orders WHERE user_id = 7;
-- Index Scan using idx_user ... rows=12 ... time=0.05ms   good
-- Seq Scan on orders ... rows=9000000 ... time=4000ms     look closer</code></pre>
""", practice=["Composite Index: Leftmost Rule", "Selectivity", "Estimate Rows After a Filter"])


LESSON("Core", "How joins actually run", """
<p>You write JOIN, and the optimiser chooses an algorithm. Spark and warehouses use the same ones, so this pays off for your whole career.</p>
<p><b>Nested loop:</b> for each left row, check every right row. 2 × 3 rows means 6 comparisons, but with a million rows each side, that's 10¹². It's only good when one side is tiny and the other has an index.</p>
<p><b>Hash join:</b> build a dictionary on the smaller side, then probe with the larger. It's O(n + m), which makes it the workhorse for equality joins, but it needs memory for the hash table.</p>
<p><b>Sort-merge join:</b> sort both, then walk them with two pointers. It suits inputs that are already sorted or too large for memory.</p>
<div class="pic">left:  1  2  2        right: 2  2  3
       ↑                     ↑        1 < 2: move left
          ↑                  ↑        match: pair the runs of 2s</div>
<table><tr><th>Algorithm</th><th>Good for</th><th>Bad for</th></tr>
<tr><td>Index nested loop</td><td>few rows, indexed</td><td>large joins</td></tr>
<tr><td>Hash</td><td>large equality joins</td><td>low memory, ranges</td></tr>
<tr><td>Sort-merge</td><td>huge or sorted data</td><td>sorting cost when not sorted</td></tr></table>
<p><b>Why plans go wrong:</b> the optimiser estimates rows using statistics, multiplying selectivities: 1M × 0.1 × 0.5 = 50,000. But if two columns are correlated, such as city and postal code, the real number is much higher. So stale statistics or correlation can mean a terrible plan. Fix it with <code>ANALYZE</code>.</p>
""", practice=["Nested Loop Join", "Hash Join", "Sort-Merge Join", "Pick a Join Strategy"])


LESSON("Core", "Transactions and ACID", """
<p>Move money: subtract from A, add to B. If it crashes in between, money vanishes. A <b>transaction</b> groups steps so they succeed or fail together.</p>
<table><tr><th>Letter</th><th>Promise</th><th>Example</th></tr>
<tr><td><b>A</b>tomic</td><td>all or nothing</td><td>the second transfer fails, so the first is undone</td></tr>
<tr><td><b>C</b>onsistent</td><td>rules always hold</td><td>a balance can't go negative</td></tr>
<tr><td><b>I</b>solated</td><td>transactions don't interfere</td><td>see below</td></tr>
<tr><td><b>D</b>urable</td><td>committed means safe</td><td>survives a crash</td></tr></table>
<p><b>Durability comes from a write-ahead log.</b> Before changing data, the database appends the change to a log file. After a crash, it replays the log and applies only committed transactions. In our example, transaction 2 never committed, so <code>a = 9</code> is ignored, and a stays 1.</p>
<p><b>Change data capture reads this same log</b> to stream changes out of a database, as you'll see later.</p>
<p><b>Isolation problems.</b> Two people each read a counter of 0, and write 0 + 1. The result's <b>1, not 2</b>: a <b>lost update</b>.</p>
<table><tr><th>Level</th><th>Prevents</th></tr>
<tr><td>Read committed</td><td>seeing uncommitted data</td></tr>
<tr><td>Repeatable read</td><td>a row changing between your reads</td></tr>
<tr><td>Serializable</td><td>all anomalies; safest and slowest</td></tr></table>
<p><b>Locks and deadlocks.</b> If T1 waits for T2 while T2 waits for T1, neither can go on. Databases detect this cycle, and abort one transaction, so your code should be able to retry.</p>
""", practice=["Atomic Transfer", "Recover From a Write-Ahead Log", "Lost Update", "Deadlock Detection"])


LESSON("Advanced", "MVCC, LSM trees and Bloom filters", """
<p><b>MVCC (multi-version concurrency control).</b> Instead of making readers wait, the database keeps several versions of each row. A reader who started at time 12 sees the version committed at time 10, and ignores the one at 20. So <b>readers don't block writers</b>. PostgreSQL works this way, and so do lakehouse table formats, through snapshots.</p>
<p><b>B-trees vs LSM trees.</b> B-trees update in place, which is good for reads. <b>LSM trees</b> make writes very fast:</p>
<ol><li>Writes go to a memory table.</li><li>When it's full, it's flushed to disk as a sorted, unchangeable file.</li><li>Reads check memory, then files from newest to oldest.</li><li>Background <b>compaction</b> merges files.</li></ol>
<table><tr><th></th><th>B-tree</th><th>LSM tree</th></tr><tr><td>Writes</td><td>slower, in place</td><td>very fast, append</td></tr><tr><td>Reads</td><td>predictable</td><td>may check many files</td></tr>
<tr><td>Used in</td><td>PostgreSQL, MySQL</td><td>Cassandra, RocksDB, HBase</td></tr></table>
<p><b>Bloom filters</b> save an LSM tree from reading files that don't have your key. A Bloom filter answers "<b>definitely not here</b>" or "<b>maybe here</b>", using very little memory. It can be wrong in only one direction: it can say maybe when the key's absent, but never no when it's present. Parquet and Spark use them to skip data too.</p>
""", practice=["MVCC: Which Version Do I See?", "A Tiny LSM Tree", "Bloom Filter"])
