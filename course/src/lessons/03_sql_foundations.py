from lib import *
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import sqlite3

DEMO = """
CREATE TABLE orders (id INT, user TEXT, amount INT);
INSERT INTO orders VALUES (1,'Asha',10), (2,'Asha',20), (3,'Ben',5);
CREATE TABLE users (name TEXT, city TEXT);
INSERT INTO users VALUES ('Asha','Pune'), ('Ben','Delhi'), ('Eli','Goa');
"""


def sql(query):
    con = sqlite3.connect(":memory:")
    con.executescript(DEMO)
    return con.execute(query).fetchall()


LESSON("Basics", "Your first queries", """
<p>A database table is a spreadsheet with rules: each column has a type, and every row has the same columns. <b>SQL is how you ask it questions.</b> It's the most important skill in this course, and you'll use it daily for the rest of your career.</p>
<p>You describe <i>what</i> you want, and the database works out <i>how</i>:</p>
<pre><code class="py">SELECT name, price       -- which columns
FROM products            -- from which table
WHERE price > 1          -- which rows
ORDER BY price           -- in what order
LIMIT 10;                -- how many</code></pre>
<table><tr><th>Filter</th><th>Example</th></tr>
<tr><td>Comparison</td><td><code>price &gt; 1</code>, <code>status = 'paid'</code></td></tr>
<tr><td>Combine</td><td><code>a AND b</code>, <code>a OR b</code></td></tr>
<tr><td>A list</td><td><code>product_id IN (10, 12)</code></td></tr>
<tr><td>A range</td><td><code>day BETWEEN '2026-01-06' AND '2026-02-01'</code> (inclusive)</td></tr>
<tr><td>Pattern</td><td><code>name LIKE 'A%'</code> means "starts with A"</td></tr></table>
<p><b>NULL means unknown</b>, and it's not zero or empty. Anything compared to unknown is unknown, so <code>city = NULL</code> finds nothing. Use <code>IS NULL</code>. For a default, use <code>COALESCE(city, 'unknown')</code>.</p>
<p><b>Practise as you read:</b> the <a href="../ide/sql.html">SQL IDE</a> runs real SQL in your browser, with sample databases and questions that check your answer. Keep it open in another tab, and try each example.</p>
<p><b>Good habits from day one:</b> name your columns rather than using <code>SELECT *</code>, because tables change and scans cost money. Format queries over several lines, as you'll read them more often than you write them.</p>
""", practice=["Select Some Columns", "Filter Rows", "IN, BETWEEN and LIKE", "Finding NULLs", "COALESCE"])


LESSON("Basics", "Summarising: GROUP BY and HAVING", """
<p><b>Aggregates</b> squeeze many rows into one number: COUNT, SUM, AVG, MIN, MAX. Prices 2, 100, 5, 20 give a count of 4, a minimum of 2, a maximum of 100 and an average of 31.75.</p>
<p><b>GROUP BY</b> makes one result per group. Picture sorting receipts into piles, then totalling each pile.</p>
<p><b>The order SQL actually runs in explains nearly every beginner error:</b></p>
<table><tr><th>Order</th><th>Clause</th><th>Does</th></tr>
<tr><td>1</td><td>FROM, JOIN</td><td>gather rows</td></tr><tr><td>2</td><td>WHERE</td><td>keep rows</td></tr>
<tr><td>3</td><td>GROUP BY</td><td>make piles</td></tr><tr><td>4</td><td>HAVING</td><td>keep piles</td></tr>
<tr><td>5</td><td>SELECT</td><td>pick and compute columns</td></tr><tr><td>6</td><td>ORDER BY</td><td>sort</td></tr><tr><td>7</td><td>LIMIT</td><td>cut off</td></tr></table>
<p>So <code>WHERE COUNT(*) &gt; 1</code> fails, because counts don't exist yet at step 2. That's what <code>HAVING</code> is for.</p>
<p><b>COUNT trap:</b> with 7 orders where one status is NULL, <code>COUNT(*)</code> is 7, <code>COUNT(status)</code> is 6, and <code>COUNT(DISTINCT status)</code> is 2.</p>
<p><b>Conditional aggregation</b> is very useful, as it counts several things in one pass:</p>
<pre><code class="py">SELECT user_id,
       COUNT(*) AS total,
       SUM(CASE WHEN status = 'paid' THEN 1 ELSE 0 END) AS paid
FROM orders GROUP BY user_id;</code></pre>
<p>User 2 has 2 orders, with 1 paid, so 50%.</p>
""", practice=["Aggregates", "GROUP BY", "HAVING", "CASE Expressions", "COUNT Traps", "Monthly Totals", "Share of Paid Orders"])


LESSON("Core", "Joins, and why totals go wrong", """
<p>Good databases store each fact once, in separate tables, so you join them to answer questions. Our demo has orders for Asha and Ben, plus users Asha, Ben and Eli.</p>
<table><tr><th>Join</th><th>Keeps</th><th>Eli (no orders)?</th></tr>
<tr><td>INNER</td><td>only matching rows</td><td>gone</td></tr>
<tr><td>LEFT (users first)</td><td>every user</td><td>kept, with NULL for order columns</td></tr>
<tr><td>FULL</td><td>all rows from both</td><td>kept</td></tr>
<tr><td>CROSS</td><td>every combination</td><td>n × m rows</td></tr></table>
<p>Run the demo and see for yourself.</p>
<p><b>Finding what's missing</b> is a classic: LEFT JOIN, then keep rows where the right side is NULL. Why not <code>NOT IN</code>? Because <code>x NOT IN (1, NULL)</code> is never true, so one NULL makes it return nothing.</p>
<p><b>The most expensive beginner mistake: joins multiply rows.</b> If a user has 2 rows on the right, each of their orders appears twice. In our practice data, the true total quantity is 20, but joining to a table with 2 rows per user gives <b>40</b>. Nothing errors, and the report's simply wrong by double.</p>
<p><b>Always ask: what's one row of each table?</b> And check counts before and after a join. A common fix is to aggregate first, then join, or to deduplicate the other side.</p>
<p><b>Filtering a LEFT JOIN trap:</b> a <code>WHERE</code> on the right table removes the NULL rows, silently turning it into an INNER JOIN. Move that condition into <code>ON</code>.</p>
""", practice=["INNER JOIN", "LEFT JOIN to Find What's Missing", "Revenue per Category", "Joins Multiply Rows", "Top Spender"])


@LD
def joins_side_by_side():
    print("INNER:", sql("SELECT u.name, o.amount FROM users u JOIN orders o ON o.user = u.name ORDER BY 1, 2"))
    print("LEFT: ", sql("SELECT u.name, o.amount FROM users u LEFT JOIN orders o ON o.user = u.name ORDER BY 1, 2"))
    print("Missing:", sql("SELECT u.name FROM users u LEFT JOIN orders o ON o.user = u.name WHERE o.id IS NULL"))


LESSON("Core", "Subqueries, EXISTS and UNION", """
<p>A <b>subquery</b> is a query inside a query:</p>
<pre><code class="py">SELECT name FROM products
WHERE price > (SELECT AVG(price) FROM products);</code></pre>
<p>The average of 2, 100, 5, 20 is 31.75, so only Desk qualifies.</p>
<p><b>EXISTS</b> asks "is there at least one?", and stops at the first match. It's often the clearest way of writing "users who have a refunded order", and it can't accidentally multiply rows the way a join can.</p>
<p><b>UNION</b> stacks results, and removes duplicates. <b>UNION ALL</b> keeps everything, and it's faster because there's no duplicate check. Use UNION ALL unless you need deduplication. Cities Pune, Delhi, Pune, NULL, Goa stacked twice give 10 rows with UNION ALL, and 4 with UNION.</p>
<p><b>Dates.</b> Group by month with <code>substr(day, 1, 7)</code> in SQLite, or <code>DATE_TRUNC('month', day)</code> in PostgreSQL and most warehouses.</p>
<p><b>Next:</b> window functions, which is where SQL starts being really powerful.</p>
""", practice=["Subquery vs Average", "EXISTS", "UNION vs UNION ALL"])
