from lib import *

THEORY("Picking the tool", """
<table><tr><th>Question sounds like</th><th>Reach for</th></tr>
<tr><td>"latest for each…", "keep one per…"</td><td>ROW_NUMBER = 1</td></tr>
<tr><td>"top N per…"</td><td>RANK / DENSE_RANK in a CTE</td></tr>
<tr><td>"running…", "cumulative…"</td><td>SUM() OVER (ORDER BY)</td></tr>
<tr><td>"compared to previous…"</td><td>LAG</td></tr>
<tr><td>"moving average"</td><td>AVG() OVER (ROWS n PRECEDING)</td></tr>
<tr><td>"consecutive…"</td><td>value − ROW_NUMBER</td></tr>
<tr><td>"sessions"</td><td>LAG, then a running SUM of new-session flags</td></tr>
<tr><td>"share of total"</td><td>x / SUM(x) OVER (PARTITION BY g)</td></tr>
<tr><td>"hierarchy", "reports to"</td><td>recursive CTE</td></tr></table>
""")
FAQ("ROW_NUMBER vs RANK vs DENSE_RANK?", "<p>On ties, ROW_NUMBER still gives different numbers, RANK shares and leaves a gap, and DENSE_RANK shares with no gap.</p>")
FAQ("GROUP BY vs window function?", "<p>GROUP BY collapses rows to one per group. A window computes across rows while keeping them all.</p>")
FAQ("ROWS vs RANGE in a frame?", "<p>ROWS counts physical rows. RANGE groups rows with equal ORDER BY values, so ties share a result. The default with ORDER BY is usually RANGE.</p>")
FAQ("Why can't you use a window function in WHERE?", "<p>WHERE runs before windows are computed. Wrap the query in a CTE or subquery, and filter outside it.</p>")
FAQ("CTE vs subquery vs temp table?", "<p>CTEs and subqueries are logical, and CTEs read better. A temp table actually stores results, which helps when a step's used several times or the optimiser needs real statistics.</p>")
FAQ("Scenario: a dedupe query gives different results on each run. Why?", "<p>The ROW_NUMBER ordering has ties, so which row wins is arbitrary. Add a deterministic tiebreaker, such as an id or ingestion time.</p>")
FAQ("Scenario: a daily report misses days with no sales. How do you fix it?", "<p>Build a date spine, using a calendar table or generated series, and LEFT JOIN the facts, using COALESCE to show 0.</p>")
FAQ("Scenario: a window query is very slow on a huge table. What do you try?", "<p>Filter first, reduce the columns, make sure partition sizes are sensible, and check for skew. Possibly pre-aggregate. Windows need sorting, which is costly at scale.</p>")
