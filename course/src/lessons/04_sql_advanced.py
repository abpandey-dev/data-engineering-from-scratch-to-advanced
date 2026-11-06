from lib import *
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import sqlite3

DEMO = """
CREATE TABLE sales (name TEXT, region TEXT, amount INT);
INSERT INTO sales VALUES ('a','N',100),('b','N',300),('c','N',300),('d','N',200),('e','S',50);
"""


def sql(query):
    con = sqlite3.connect(":memory:")
    con.executescript(DEMO)
    return con.execute(query).fetchall()


LESSON("Basics", "CTEs: write SQL you can read", """
<p>Long nested queries read inside out. A <b>CTE</b> (common table expression) names each step, so a query reads top to bottom like a recipe:</p>
<pre><code class="py">WITH totals AS (                 -- step 1: revenue per region
    SELECT region, SUM(amount) AS t FROM sales GROUP BY region
),
big AS (                         -- step 2: only the big ones
    SELECT * FROM totals WHERE t > 500
)
SELECT * FROM big;</code></pre>
<p>Regions N and S total 600 and 500, so only N remains.</p>
<p>Professional SQL is mostly chains of CTEs: import the data, clean it, join it, aggregate it. Each step can be checked on its own by selecting from it, which makes debugging far easier.</p>
""", practice=["Readable Steps With a CTE"])


LESSON("Core", "Window functions: the big idea", """
<p>GROUP BY squashes each group into one row. A <b>window function</b> computes across related rows, but <b>every row stays</b>.</p>
<pre><code class="py">function() OVER (PARTITION BY region ORDER BY amount DESC)
                 └── separate groups ┘ └── order inside ─┘</code></pre>
<p><b>The three rankings differ only on ties.</b> Amounts 300, 300, 200, 100:</p>
<table><tr><th>Amount</th><th>ROW_NUMBER</th><th>RANK</th><th>DENSE_RANK</th></tr>
<tr><td>300</td><td>1</td><td>1</td><td>1</td></tr><tr><td>300</td><td>2</td><td>1</td><td>1</td></tr>
<tr><td>200</td><td>3</td><td><b>3</b></td><td><b>2</b></td></tr><tr><td>100</td><td>4</td><td>4</td><td>3</td></tr></table>
<ul><li><b>ROW_NUMBER:</b> always unique. Use it to keep exactly one row per group.</li>
<li><b>RANK:</b> ties share a rank, then there's a gap.</li>
<li><b>DENSE_RANK:</b> no gap. Use it for "top 2 distinct values".</li></ul>
<p><b>You can't filter on a window function in WHERE,</b> because windows run after WHERE. Wrap it in a CTE, as in the top-N pattern you'll write hundreds of times:</p>
<pre><code class="py">WITH r AS (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY region ORDER BY amount DESC) AS rn
  FROM sales)
SELECT * FROM r WHERE rn = 1;</code></pre>
<p><b>The most used pattern in data engineering is "latest row per key".</b> Sources resend and update records, and you keep the newest. Order by updated time descending, and add a tiebreaker so reruns give identical results.</p>
<p>The demo prints all three rankings. Change the data and predict the output first.</p>
""", practice=["Number the Rows", "RANK vs DENSE_RANK", "Top Sale per Region", "Latest Row per Key", "Find Exact Duplicates", "Split Into Buckets"])


@LD
def rank_demo():
    for row in sql("""SELECT name, amount, ROW_NUMBER() OVER w, RANK() OVER w, DENSE_RANK() OVER w
                      FROM sales WHERE region = 'N' WINDOW w AS (ORDER BY amount DESC)"""):
        print(row)


LESSON("Core", "Running totals, moving averages and LAG", """
<p><b>Running total:</b> <code>SUM(x) OVER (ORDER BY day)</code>. For 100, 300, 200 it gives 100, 400, 600.</p>
<p><b>Frames</b> choose which rows the window includes:</p>
<table><tr><th>Frame</th><th>Meaning</th></tr>
<tr><td><code>ROWS UNBOUNDED PRECEDING</code></td><td>from the start to here</td></tr>
<tr><td><code>ROWS 1 PRECEDING</code></td><td>this row and the one before</td></tr>
<tr><td><code>ROWS BETWEEN 3 PRECEDING AND CURRENT ROW</code></td><td>a 4-row window</td></tr></table>
<p>For 50, 50, 400, a 2-row average gives 50, 50, 225. The first row only has itself.</p>
<p><b>A trap:</b> with ORDER BY and no frame, the default is <code>RANGE</code>, and tied rows are treated as one. Rows with equal keys get the same running total. Use <code>ROWS</code> and a unique ordering when you want row by row.</p>
<p><b>LAG and LEAD</b> read the previous and next row. For 100, 300, 200, the change is NULL, +200, −100. <code>FIRST_VALUE</code> gets the first in the window.</p>
<p><b>Share of total without collapsing:</b> <code>amount / SUM(amount) OVER (PARTITION BY region)</code>. Region N of 100, 300, 200 gives 16.7%, 50%, 33.3%.</p>
""", practice=["Running Total", "Moving Average", "Compare With the Previous Row", "Share Within a Group", "First and Last in a Group"])


LESSON("Advanced", "Sessions, streaks and gaps", """
<p>These look hard, and they're asked a lot. Learn the two tricks and they become routine.</p>
<p><b>Trick 1: sessionisation.</b> A new session starts after a gap of over 30 minutes (1800 seconds). Mark where gaps occur, then take a running sum of those marks.</p>
<table><tr><th>ts</th><th>gap</th><th>new?</th><th>running sum + 1 = session</th></tr>
<tr><td>100</td><td>none</td><td>0</td><td>1</td></tr><tr><td>160</td><td>60</td><td>0</td><td>1</td></tr>
<tr><td>2000</td><td>1840</td><td><b>1</b></td><td>2</td></tr><tr><td>2050</td><td>50</td><td>0</td><td>2</td></tr></table>
<p><b>Trick 2: gaps and islands.</b> Find consecutive runs by subtracting a row number. Logins on days 1, 2, 3, 5, 6:</p>
<table><tr><th>Day</th><th>Row number</th><th>Day − row</th></tr>
<tr><td>1</td><td>1</td><td><b>0</b></td></tr><tr><td>2</td><td>2</td><td><b>0</b></td></tr><tr><td>3</td><td>3</td><td><b>0</b></td></tr>
<tr><td>5</td><td>4</td><td><b>1</b></td></tr><tr><td>6</td><td>5</td><td><b>1</b></td></tr></table>
<p>Within a run, both rise by 1, so the difference stays constant. Group by it and count: runs of 3 and 2, so the longest is <b>3</b>. The same trick finds free seat ranges: 3–5 and 7–8.</p>
<p><b>Date spines.</b> A report with no sales on a day should show 0, not skip it. Generate all dates, then LEFT JOIN the facts.</p>
""", practice=["Sessionise Clicks", "Longest Login Streak", "Find Gaps in a Sequence", "Generate a Date Spine"])


LESSON("Advanced", "Funnels, retention, pivots and hierarchies", """
<p><b>Funnel:</b> how many users reached each step? Make one row per user with a flag for each step, and then sum.</p>
<pre><code class="py">SELECT user_id, MAX(page = 'home') AS h, MAX(page = 'cart') AS c ...</code></pre>
<p><b>Cohort retention.</b> Group users by signup week, and count who's active N weeks later. Join activity to signups, and compute <code>activity_week − signup_week</code>. Cohort 0 has 3 users: 3 active in week 0, 1 in week 1, 1 in week 2. Count <i>distinct</i> users, since one person can have many events.</p>
<p><b>Pivot:</b> <code>SUM(CASE WHEN region = 'N' THEN amount ELSE 0 END)</code> turns rows into columns.</p>
<p><b>Recursive CTE:</b> walks trees and graphs. A starting row, then a step that joins back to itself, until no new rows appear:</p>
<pre><code class="py">WITH RECURSIVE t(id, name, d) AS (
    SELECT id, name, 0 FROM tree WHERE parent IS NULL
    UNION ALL
    SELECT c.id, c.name, t.d + 1 FROM tree c JOIN t ON c.parent = t.id)
SELECT * FROM t;</code></pre>
<p>Beware of cycles in the data, which would make it loop forever. Add a depth limit.</p>
""", practice=["Funnel Conversion", "Weekly Retention", "Pivot Rows to Columns", "Walk a Hierarchy"])
