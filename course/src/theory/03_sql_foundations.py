from lib import *

THEORY("NULL rules", """
<ul><li><code>x = NULL</code> is never true; use <code>IS NULL</code>.</li>
<li><code>COUNT(*)</code> counts rows, and <code>COUNT(col)</code> skips NULLs.</li>
<li>SUM and AVG ignore NULLs, so an average divides only by non-NULL rows.</li>
<li><code>NOT IN</code> with a NULL in the list returns nothing.</li>
<li>In GROUP BY, NULLs form one group.</li></ul>
""")
FAQ("WHERE vs HAVING?", "<p>WHERE filters rows before grouping. HAVING filters groups after grouping, so it can use aggregates.</p>")
FAQ("What's the logical order of a SQL query?", "<p>FROM and JOIN, WHERE, GROUP BY, HAVING, SELECT, ORDER BY, LIMIT.</p>")
FAQ("INNER vs LEFT JOIN?", "<p>INNER keeps matches only. LEFT keeps all left rows, and fills in NULL where there's no match.</p>")
FAQ("Two tables of 3 rows are joined. How many rows can you get?", "<p>From 0 to 9, depending on matches. Duplicate keys multiply.</p>")
FAQ("UNION vs UNION ALL?", "<p>UNION removes duplicates, which costs extra work. UNION ALL keeps everything, and is faster.</p>")
FAQ("EXISTS vs IN vs JOIN?", "<p>EXISTS checks for any match and is safe with NULLs. IN checks a list, but NOT IN breaks on NULLs. JOIN brings in columns, and can multiply rows.</p>")
FAQ("Scenario: after adding a join, revenue doubled. What happened?", "<p>The join key isn't unique on one side, so rows multiplied. Check row counts before and after, and check key uniqueness, then aggregate or deduplicate before joining.</p>")
FAQ("Scenario: your LEFT JOIN returns the same as an INNER JOIN. Why?", "<p>Probably a WHERE condition on the right table is removing NULL rows. Move it into the ON clause.</p>")
FAQ("Scenario: NOT IN returns zero rows, though you're sure there are matches. Why?", "<p>The subquery has a NULL. Use NOT EXISTS, or a LEFT JOIN with IS NULL.</p>")
