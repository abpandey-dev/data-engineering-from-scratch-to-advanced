from lib import *
import sqlite3


TOPIC(
    id="sql-foundations", title="SQL Foundations", glyph="SELECT",
    blurb="The most important skill in data engineering, from your very first query: SELECT, WHERE, sorting, aggregates, GROUP BY, HAVING, all the joins, NULLs, CASE and subqueries, on a real database.",
    theory="""
<h3>Cheat sheet</h3>
<pre><code class="py">SELECT city, COUNT(*) AS n, SUM(amount)      -- written first, runs late
FROM orders o
JOIN users u ON u.id = o.user_id
WHERE amount > 0                             -- filters rows
GROUP BY city
HAVING COUNT(*) > 1                          -- filters groups
ORDER BY n DESC
LIMIT 10;</code></pre>
<p>Every question here runs on a real SQLite database through <code>run_sql</code>.</p>
""")

SCHEMA = """
CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, city TEXT, signup TEXT);
INSERT INTO users VALUES (1,'Asha','Pune','2026-01-01'), (2,'Ben','Delhi','2026-01-03'), (3,'Chen','Pune','2026-02-10'),
 (4,'Dara',NULL,'2026-02-11'), (5,'Eli','Goa','2026-03-01');
CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT, category TEXT, price REAL);
INSERT INTO products VALUES (10,'Pen','office',2), (11,'Desk','office',100), (12,'Tea','food',5), (13,'Lamp','home',20);
CREATE TABLE orders (id INTEGER PRIMARY KEY, user_id INTEGER, product_id INTEGER, qty INTEGER, day TEXT, status TEXT);
INSERT INTO orders VALUES (1,1,10,10,'2026-01-05','paid'), (2,1,11,1,'2026-01-06','paid'), (3,2,12,4,'2026-01-06','paid'),
 (4,2,10,1,'2026-02-01','refunded'), (5,3,12,2,'2026-02-15','paid'), (6,1,12,1,'2026-02-20','paid'), (7,4,11,1,'2026-03-02',NULL);
"""


def run_sql(query):
    """Run a query on a fresh database and return the rows as lists."""
    con = sqlite3.connect(":memory:")
    con.executescript(SCHEMA)
    rows = con.execute(query).fetchall()
    con.close()
    return [list(r) for r in rows]


Q(None, "Select Some Columns", "Easy", "SELECT, ORDER BY",
  "Return the name and city of every user, ordered by name.",
  [((), [['Asha', 'Pune'], ['Ben', 'Delhi'], ['Chen', 'Pune'], ['Dara', None], ['Eli', 'Goa']])],
  ("Fetch everything and pick columns in Python.", "O(n log n)", "O(n)"),
  ("Name the columns, and let the database sort.", "O(n log n)", "O(n)"))


@B
def names_cities():
    rows = run_sql("SELECT * FROM users")
    return sorted(([r[1], r[2]] for r in rows), key=lambda r: r[0])


@O
def names_cities():
    return run_sql("SELECT name, city FROM users ORDER BY name")


Q(None, "Filter Rows", "Easy", "WHERE",
  "Return names of products in the office category costing more than 1, cheapest first.",
  [((), ['Pen', 'Desk'])],
  ("A nested filter through a subquery.", "O(n log n)", "O(n)"),
  ("<code>WHERE</code> with <code>AND</code>.", "O(n log n)", "O(n)"))


@B
def office_products():
    rows = run_sql("SELECT name FROM (SELECT * FROM products WHERE category = 'office') WHERE price > 1 ORDER BY price")
    return [r[0] for r in rows]


@O
def office_products():
    return [r[0] for r in run_sql("SELECT name FROM products WHERE category = 'office' AND price > 1 ORDER BY price")]


Q(None, "IN, BETWEEN and LIKE", "Easy", "More filters",
  "Return ids of orders on days from 2026-01-06 to 2026-02-01 inclusive, whose product_id is 10 or 12. Order by id.",
  [((), [3, 4])],
  ("Spell out every comparison.", "O(n)", "O(n)"),
  ("<code>BETWEEN</code> and <code>IN</code> read better.", "O(n)", "O(n)"))


@B
def filtered_orders():
    return [r[0] for r in run_sql("""SELECT id FROM orders
        WHERE day >= '2026-01-06' AND day <= '2026-02-01' AND (product_id = 10 OR product_id = 12) ORDER BY id""")]


@O
def filtered_orders():
    return [r[0] for r in run_sql("""SELECT id FROM orders
        WHERE day BETWEEN '2026-01-06' AND '2026-02-01' AND product_id IN (10, 12) ORDER BY id""")]


Q(None, "Finding NULLs", "Easy", "NULL isn't a value",
  "Return names of users with no city. <code>city = NULL</code> never matches anything.",
  [((), ['Dara'])],
  ("Fetch all and check for None in Python.", "O(n)", "O(n)"),
  ("<code>IS NULL</code>.", "O(n)", "O(n)"))


@B
def no_city():
    return [r[0] for r in run_sql("SELECT name, city FROM users") if r[1] is None]


@O
def no_city():
    return [r[0] for r in run_sql("SELECT name FROM users WHERE city IS NULL")]


Q(None, "Aggregates", "Easy", "COUNT, SUM, AVG, MIN, MAX",
  "Return the product count, cheapest price, highest price and average price rounded to 2 decimals, as one row.",
  [((), [4, 2.0, 100.0, 31.75])],
  ("Fetch prices and compute in Python.", "O(n)", "O(n)"),
  ("Aggregates in one query.", "O(n)", "O(1)"))


@B
def price_stats():
    p = [r[0] for r in run_sql("SELECT price FROM products")]
    return [len(p), min(p), max(p), round(sum(p) / len(p), 2)]


@O
def price_stats():
    return run_sql("SELECT COUNT(*), MIN(price), MAX(price), ROUND(AVG(price), 2) FROM products")[0]


Q(None, "GROUP BY", "Easy", "One row per group",
  "Return each category and its product count, largest count first, then by category.",
  [((), [['office', 2], ['food', 1], ['home', 1]])],
  ("Count in Python.", "O(n)", "O(c)"),
  ("<code>GROUP BY</code>.", "O(n)", "O(c)"))


@B
def category_counts():
    counts = {}
    for r in run_sql("SELECT category FROM products"):
        counts[r[0]] = counts.get(r[0], 0) + 1
    return sorted(([k, v] for k, v in counts.items()), key=lambda x: (-x[1], x[0]))


@O
def category_counts():
    return run_sql("SELECT category, COUNT(*) AS n FROM products GROUP BY category ORDER BY n DESC, category")


Q(None, "HAVING", "Easy", "Filter groups",
  "Return user_ids with 2 or more orders, with their count, ordered by user_id.",
  [((), [[1, 3], [2, 2]])],
  ("Group in a subquery, then use WHERE outside.", "O(n)", "O(u)"),
  ("<code>HAVING</code>.", "O(n)", "O(u)"))


@B
def repeat_buyers():
    return run_sql("SELECT user_id, n FROM (SELECT user_id, COUNT(*) AS n FROM orders GROUP BY user_id) WHERE n >= 2 ORDER BY user_id")


@O
def repeat_buyers():
    return run_sql("SELECT user_id, COUNT(*) FROM orders GROUP BY user_id HAVING COUNT(*) >= 2 ORDER BY user_id")


Q(None, "INNER JOIN", "Easy", "Combine tables",
  "Return order id, user name and product name for each order, ordered by order id.",
  [((), [[1, 'Asha', 'Pen'], [2, 'Asha', 'Desk'], [3, 'Ben', 'Tea'], [4, 'Ben', 'Pen'], [5, 'Chen', 'Tea'], [6, 'Asha', 'Tea'], [7, 'Dara', 'Desk']])],
  ("Scalar subqueries for each name.", "O(n·m)", "O(n)"),
  ("Two joins.", "O(n)", "O(n)"))


@B
def order_details():
    return run_sql("""SELECT id, (SELECT name FROM users u WHERE u.id = o.user_id),
        (SELECT name FROM products p WHERE p.id = o.product_id) FROM orders o ORDER BY id""")


@O
def order_details():
    return run_sql("""SELECT o.id, u.name, p.name FROM orders o
        JOIN users u ON u.id = o.user_id JOIN products p ON p.id = o.product_id ORDER BY o.id""")


Q(None, "LEFT JOIN to Find What's Missing", "Medium", "Users with no orders",
  "Return names of users who have never ordered, and names of products never ordered, as a tuple of two lists.",
  [((), (['Eli'], ['Lamp']))],
  ("<code>NOT IN</code>. Beware of NULLs in the subquery.", "O(n·m)", "O(n)"),
  ("<code>LEFT JOIN ... WHERE right.id IS NULL</code>.", "O(n + m)", "O(n)"))


@B
def never_ordered():
    u = run_sql("SELECT name FROM users WHERE id NOT IN (SELECT user_id FROM orders)")
    p = run_sql("SELECT name FROM products WHERE id NOT IN (SELECT product_id FROM orders)")
    return ([r[0] for r in u], [r[0] for r in p])


@O
def never_ordered():
    u = run_sql("SELECT u.name FROM users u LEFT JOIN orders o ON o.user_id = u.id WHERE o.id IS NULL")
    p = run_sql("SELECT p.name FROM products p LEFT JOIN orders o ON o.product_id = p.id WHERE o.id IS NULL")
    return ([r[0] for r in u], [r[0] for r in p])


Q(None, "Revenue per Category", "Medium", "Join, then aggregate",
  "Return category and revenue (qty × price) from paid orders, highest first.",
  [((), [['office', 120.0], ['food', 35.0]])],
  ("Fetch joined rows and add up in Python.", "O(n)", "O(c)"),
  ("Join, filter, group.", "O(n)", "O(c)"))


@B
def category_revenue():
    totals = {}
    for cat, value in run_sql("""SELECT p.category, o.qty * p.price FROM orders o
            JOIN products p ON p.id = o.product_id WHERE o.status = 'paid'"""):
        totals[cat] = totals.get(cat, 0) + value
    return sorted(([k, v] for k, v in totals.items()), key=lambda x: -x[1])


@O
def category_revenue():
    return run_sql("""SELECT p.category, SUM(o.qty * p.price) AS rev FROM orders o
        JOIN products p ON p.id = o.product_id WHERE o.status = 'paid'
        GROUP BY p.category ORDER BY rev DESC""")


Q(None, "CASE Expressions", "Easy", "If/else in SQL",
  "Label each product 'cheap' (below 10) or 'premium', and return the count per label, ordered by label.",
  [((), [['cheap', 2], ['premium', 2]])],
  ("Two counting queries.", "O(n)", "O(1)"),
  ("Group by a CASE.", "O(n)", "O(1)"))


@B
def price_bands():
    cheap = run_sql("SELECT COUNT(*) FROM products WHERE price < 10")[0][0]
    prem = run_sql("SELECT COUNT(*) FROM products WHERE price >= 10")[0][0]
    return [["cheap", cheap], ["premium", prem]]


@O
def price_bands():
    return run_sql("""SELECT CASE WHEN price < 10 THEN 'cheap' ELSE 'premium' END AS band, COUNT(*)
        FROM products GROUP BY band ORDER BY band""")


Q(None, "COALESCE", "Easy", "Defaults for NULL",
  "Return each user's name with their city, or 'unknown' when NULL, ordered by id.",
  [((), [['Asha', 'Pune'], ['Ben', 'Delhi'], ['Chen', 'Pune'], ['Dara', 'unknown'], ['Eli', 'Goa']])],
  ("Replace in Python.", "O(n)", "O(n)"),
  ("<code>COALESCE(city, 'unknown')</code>.", "O(n)", "O(n)"))


@B
def city_or_unknown():
    return [[r[0], r[1] if r[1] is not None else "unknown"] for r in run_sql("SELECT name, city FROM users ORDER BY id")]


@O
def city_or_unknown():
    return run_sql("SELECT name, COALESCE(city, 'unknown') FROM users ORDER BY id")


Q(None, "COUNT Traps", "Easy", "Rows vs values",
  "Return COUNT(*), COUNT(status) and COUNT(DISTINCT status) from orders, as one row.",
  [((), [7, 6, 2])],
  ("Compute from fetched values.", "O(n)", "O(n)"),
  ("One query. Only <code>COUNT(*)</code> counts NULLs.", "O(n)", "O(d)"))


@B
def count_traps():
    v = [r[0] for r in run_sql("SELECT status FROM orders")]
    known = [x for x in v if x is not None]
    return [len(v), len(known), len(set(known))]


@O
def count_traps():
    return run_sql("SELECT COUNT(*), COUNT(status), COUNT(DISTINCT status) FROM orders")[0]


Q(None, "Joins Multiply Rows", "Medium", "The classic revenue bug",
  "Return (total qty from orders alone, total qty after wrongly joining to a table with two rows per user). Use a CTE as the second table.",
  [((), (20, 40))],
  ("Run each query separately.", "O(n)", "O(1)"),
  ("A single query with a subquery for the correct value shows it side by side.", "O(n)", "O(n)"))


@B
def join_fanout():
    right = run_sql("SELECT SUM(qty) FROM orders")[0][0]
    wrong = run_sql("""WITH tags(user_id, tag) AS (SELECT id, 'a' FROM users UNION ALL SELECT id, 'b' FROM users)
        SELECT SUM(o.qty) FROM orders o JOIN tags t ON t.user_id = o.user_id""")[0][0]
    return (right, wrong)


@O
def join_fanout():
    row = run_sql("""WITH tags(user_id, tag) AS (SELECT id, 'a' FROM users UNION ALL SELECT id, 'b' FROM users)
        SELECT (SELECT SUM(qty) FROM orders), SUM(o.qty) FROM orders o JOIN tags t ON t.user_id = o.user_id""")[0]
    return (row[0], row[1])


Q(None, "Subquery vs Average", "Medium", "Compare against a total",
  "Return names of products priced above the average price, ordered by name.",
  [((), ['Desk'])],
  ("Compute the average first, then filter in Python.", "O(n)", "O(n)"),
  ("A subquery in WHERE.", "O(n)", "O(1)"))


@B
def above_average():
    rows = run_sql("SELECT name, price FROM products")
    avg = sum(r[1] for r in rows) / len(rows)
    return sorted(r[0] for r in rows if r[1] > avg)


@O
def above_average():
    return [r[0] for r in run_sql("SELECT name FROM products WHERE price > (SELECT AVG(price) FROM products) ORDER BY name")]


Q(None, "EXISTS", "Medium", "Is there any?",
  "Return names of users who have at least one refunded order.",
  [((), ['Ben'])],
  ("Join with DISTINCT.", "O(n)", "O(n)"),
  ("<code>EXISTS</code> stops at the first match.", "O(n)", "O(1)"))


@B
def refunded_users():
    return [r[0] for r in run_sql("""SELECT DISTINCT u.name FROM users u JOIN orders o ON o.user_id = u.id
        WHERE o.status = 'refunded'""")]


@O
def refunded_users():
    return [r[0] for r in run_sql("""SELECT name FROM users u
        WHERE EXISTS (SELECT 1 FROM orders o WHERE o.user_id = u.id AND o.status = 'refunded')""")]


Q(None, "Monthly Totals", "Medium", "Grouping by date",
  "Return month (YYYY-MM) and number of paid orders, in month order.",
  [((), [['2026-01', 3], ['2026-02', 2]])],
  ("Slice the date in Python.", "O(n)", "O(m)"),
  ("<code>substr(day, 1, 7)</code>. Real databases have <code>DATE_TRUNC</code>.", "O(n)", "O(m)"))


@B
def monthly_orders():
    counts = {}
    for r in run_sql("SELECT day FROM orders WHERE status = 'paid'"):
        counts[r[0][:7]] = counts.get(r[0][:7], 0) + 1
    return [[k, counts[k]] for k in sorted(counts)]


@O
def monthly_orders():
    return run_sql("SELECT substr(day, 1, 7) AS m, COUNT(*) FROM orders WHERE status = 'paid' GROUP BY m ORDER BY m")


Q(None, "Top Spender", "Medium", "Putting it together",
  "Return the name and total paid spend of the top-spending user.",
  [((), ['Asha', 125.0])],
  ("Sum per user, then find the maximum in Python.", "O(n)", "O(u)"),
  ("Join, group, order, limit.", "O(n log u)", "O(u)"))


@B
def top_spender():
    rows = run_sql("""SELECT u.name, o.qty * p.price FROM orders o JOIN users u ON u.id = o.user_id
        JOIN products p ON p.id = o.product_id WHERE o.status = 'paid'""")
    totals = {}
    for name, value in rows:
        totals[name] = totals.get(name, 0) + value
    best = max(totals, key=totals.get)
    return [best, totals[best]]


@O
def top_spender():
    return run_sql("""SELECT u.name, SUM(o.qty * p.price) AS s FROM orders o
        JOIN users u ON u.id = o.user_id JOIN products p ON p.id = o.product_id
        WHERE o.status = 'paid' GROUP BY u.id ORDER BY s DESC LIMIT 1""")[0]


Q(None, "UNION vs UNION ALL", "Easy", "Stacking rows",
  "Return row counts for stacking user cities with itself, using UNION and UNION ALL, as (union, union_all).",
  [((), (4, 10))],
  ("Two separate queries.", "O(n)", "O(n)"),
  ("Both counts in one query. UNION removes duplicates, including NULL treated as one.", "O(n)", "O(n)"))


@B
def union_counts():
    u = run_sql("SELECT city FROM users UNION SELECT city FROM users")
    a = run_sql("SELECT city FROM users UNION ALL SELECT city FROM users")
    return (len(u), len(a))


@O
def union_counts():
    r = run_sql("""SELECT (SELECT COUNT(*) FROM (SELECT city FROM users UNION SELECT city FROM users)),
                          (SELECT COUNT(*) FROM (SELECT city FROM users UNION ALL SELECT city FROM users))""")[0]
    return (r[0], r[1])


Q(None, "Share of Paid Orders", "Medium", "Conditional aggregation",
  "Return per user_id: total orders, paid orders and the paid percentage rounded to 1 decimal, ordered by user_id.",
  [((), [[1, 3, 3, 100.0], [2, 2, 1, 50.0], [3, 1, 1, 100.0], [4, 1, 0, 0.0]])],
  ("Two grouped queries, joined.", "O(n)", "O(u)"),
  ("<code>SUM(CASE ...)</code>.", "O(n)", "O(u)"))


@B
def paid_share():
    total = dict(map(tuple, run_sql("SELECT user_id, COUNT(*) FROM orders GROUP BY user_id")))
    paid = dict(map(tuple, run_sql("SELECT user_id, COUNT(*) FROM orders WHERE status = 'paid' GROUP BY user_id")))
    return [[u, total[u], paid.get(u, 0), round(100 * paid.get(u, 0) / total[u], 1)] for u in sorted(total)]


@O
def paid_share():
    return run_sql("""SELECT user_id, COUNT(*), SUM(CASE WHEN status = 'paid' THEN 1 ELSE 0 END),
        ROUND(100.0 * SUM(CASE WHEN status = 'paid' THEN 1 ELSE 0 END) / COUNT(*), 1)
        FROM orders GROUP BY user_id ORDER BY user_id""")
