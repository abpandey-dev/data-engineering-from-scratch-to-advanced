from lib import *

THEORY("Slow query checklist", """
<ol><li>Run EXPLAIN ANALYZE, and find the most expensive step.</li>
<li>Look for full scans of large tables and large row estimate errors.</li>
<li>Check that indexes match the filter and join columns, in the right order.</li>
<li>Avoid functions on indexed columns.</li>
<li>Update statistics with ANALYZE.</li>
<li>Select fewer columns, and filter earlier.</li>
<li>Consider partitioning or a summary table.</li></ol>
""")
FAQ("What is an index? What does it cost?", "<p>A sorted structure, usually a B-tree, that makes lookups O(log n). It costs storage and slows every write.</p>")
FAQ("Clustered vs non-clustered index?", "<p>A clustered index decides how rows are physically stored, so a table has one. Non-clustered indexes are separate structures pointing at rows.</p>")
FAQ("Why is a B-tree better than a binary tree on disk?", "<p>Each node fills a page with hundreds of keys, so the tree is only a few levels deep, and few disk reads are needed.</p>")
FAQ("Explain ACID.", "<p>Atomic: all or nothing. Consistent: rules hold. Isolated: transactions don't interfere. Durable: committed data survives a crash.</p>")
FAQ("Explain isolation levels.", "<p>Read committed avoids dirty reads. Repeatable read keeps a row stable during a transaction. Serializable behaves as if transactions ran one at a time, at the highest cost.</p>")
FAQ("What is a write-ahead log?", "<p>Changes are appended to a log before data files change. After a crash, committed changes are replayed. CDC tools read this log too.</p>")
FAQ("Hash join vs sort-merge join?", "<p>Hash join builds a table on the smaller side, and is fast for equality but needs memory. Sort-merge sorts both sides, and handles huge inputs or already-sorted data.</p>")
FAQ("B-tree vs LSM tree?", "<p>B-trees update in place and read predictably. LSM trees append and compact, giving very fast writes but potentially slower reads.</p>")
FAQ("Scenario: a query was fast yesterday and is slow today, with no code change. Why?", "<p>Likely data growth, stale statistics giving a new bad plan, lock contention, or a change in skew. Compare the plans and check ANALYZE.</p>")
FAQ("Scenario: you added an index but the query still does a full scan. Why?", "<p>The column may be wrapped in a function, the type may mismatch, the leading column may be missing from the filter, or the filter isn't selective enough for the index to be worth it.</p>")
FAQ("Scenario: a bulk load became very slow. What can you do?", "<p>Too many indexes are often the cause. Load in batches, use bulk copy, and consider dropping and rebuilding non-essential indexes around large loads.</p>")
