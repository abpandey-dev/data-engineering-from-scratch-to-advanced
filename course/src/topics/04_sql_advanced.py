from lib import *
import sqlite3


TOPIC(
    id="sql-advanced", title="Advanced SQL", glyph="OVER()",
    blurb="The SQL that separates beginners from professionals: CTEs, every window function, top-N per group, running totals, sessionisation, gaps and islands, deduplication, retention, funnels and recursive queries.",
    theory="""
<h3>Cheat sheet</h3>
<pre><code class="py">WITH step AS (SELECT ...)                     -- name a step
ROW_NUMBER() OVER (PARTITION BY u ORDER BY t) -- 1, 2, 3 per user
LAG(x) OVER (PARTITION BY u ORDER BY t)       -- the previous row
SUM(x) OVER (ORDER BY t ROWS UNBOUNDED PRECEDING)   -- running total
AVG(x) OVER (ORDER BY t ROWS 2 PRECEDING)     -- moving average</code></pre>
""")

SCHEMA = """
CREATE TABLE events (user_id INT, ts INT, page TEXT);
INSERT INTO events VALUES (1,100,'home'),(1,160,'cart'),(1,2000,'home'),(1,2050,'buy'),(2,300,'home'),(2,4000,'home'),(3,500,'cart');
CREATE TABLE sales (id INT, region TEXT, rep TEXT, day TEXT, amount INT);
INSERT INTO sales VALUES (1,'N','a','2026-01-01',100),(2,'N','b','2026-01-02',300),(3,'N','a','2026-01-03',200),
 (4,'S','c','2026-01-01',50),(5,'S','d','2026-01-02',50),(6,'S','c','2026-01-04',400);
CREATE TABLE customer_updates (id INT, customer INT, email TEXT, updated INT);
INSERT INTO customer_updates VALUES (1,1,'a@x',10),(2,1,'a2@x',20),(3,2,'b@x',15),(4,2,'b@x',15),(5,3,'c@x',5);
CREATE TABLE logins (user_id INT, day INT);
INSERT INTO logins VALUES (1,1),(1,2),(1,3),(1,5),(1,6),(2,2),(2,4),(3,1),(3,2),(3,8);
CREATE TABLE tree (id INT, parent INT, name TEXT);
INSERT INTO tree VALUES (1,NULL,'all'),(2,1,'food'),(3,1,'home'),(4,2,'tea'),(5,4,'green');
CREATE TABLE signups (user_id INT, week INT);
INSERT INTO signups VALUES (1,0),(2,0),(3,0),(4,1),(5,1);
CREATE TABLE activity (user_id INT, week INT);
INSERT INTO activity VALUES (1,0),(1,1),(2,0),(2,2),(3,0),(4,1),(4,2),(5,1);
CREATE TABLE seats (seat INT, taken INT);
INSERT INTO seats VALUES (1,1),(2,1),(3,0),(4,0),(5,0),(6,1),(7,0),(8,0);
"""


def run_sql(query):
    """Run a query on a fresh database and return the rows as lists."""
    con = sqlite3.connect(":memory:")
    con.executescript(SCHEMA)
    rows = con.execute(query).fetchall()
    con.close()
    return [list(r) for r in rows]


Q(None, "Readable Steps With a CTE", "Easy", "WITH",
  "Using a CTE of each region's total, return regions whose total exceeds 500.",
  [((), [['N', 600]])],
  ("A nested subquery. It works, but reads inside out.", "O(n)", "O(r)"),
  ("Name the step with WITH, so it reads top to bottom.", "O(n)", "O(r)"))


@B
def big_regions():
    return run_sql("SELECT region, t FROM (SELECT region, SUM(amount) AS t FROM sales GROUP BY region) WHERE t > 500")


@O
def big_regions():
    return run_sql("""WITH totals AS (SELECT region, SUM(amount) AS t FROM sales GROUP BY region)
        SELECT region, t FROM totals WHERE t > 500""")


Q(None, "Number the Rows", "Easy", "ROW_NUMBER",
  "Return id and its order by amount (highest first) within each region, ordered by region, then that number. Ties by id.",
  [((), [['N', 2, 1], ['N', 3, 2], ['N', 1, 3], ['S', 6, 1], ['S', 4, 2], ['S', 5, 3]])],
  ("Count how many rows rank higher, using a correlated subquery.", "O(n²)", "O(n)"),
  ("<code>ROW_NUMBER() OVER (PARTITION BY ...)</code>.", "O(n log n)", "O(n)"))


@B
def numbered():
    return run_sql("""SELECT region, id, (SELECT COUNT(*) FROM sales b WHERE b.region = a.region AND
        (b.amount > a.amount OR (b.amount = a.amount AND b.id <= a.id))) AS rn
        FROM sales a ORDER BY region, rn""")


@O
def numbered():
    return run_sql("""SELECT region, id, ROW_NUMBER() OVER (PARTITION BY region ORDER BY amount DESC, id) AS rn
        FROM sales ORDER BY region, rn""")


Q(None, "RANK vs DENSE_RANK", "Medium", "Ties",
  "For region S ordered by amount descending, return id, RANK and DENSE_RANK, ordered by rank, then id.",
  [((), [[6, 1, 1], [4, 2, 2], [5, 2, 2]])],
  ("Counting subqueries.", "O(n²)", "O(n)"),
  ("Window functions. RANK leaves gaps after ties; DENSE_RANK doesn't.", "O(n log n)", "O(n)"))


@B
def ranks():
    return run_sql("""SELECT id,
        (SELECT COUNT(*) + 1 FROM sales b WHERE b.region = 'S' AND b.amount > a.amount) AS r,
        (SELECT COUNT(DISTINCT amount) + 1 FROM sales b WHERE b.region = 'S' AND b.amount > a.amount) AS d
        FROM sales a WHERE region = 'S' ORDER BY r, id""")


@O
def ranks():
    return run_sql("""SELECT id, RANK() OVER w, DENSE_RANK() OVER w FROM sales WHERE region = 'S'
        WINDOW w AS (ORDER BY amount DESC) ORDER BY 2, id""")


Q(None, "Top Sale per Region", "Medium", "Top N per group",
  "Return region, id and amount of each region's largest sale.",
  [((), [['N', 2, 300], ['S', 6, 400]])],
  ("Join to a grouped MAX subquery.", "O(n)", "O(r)"),
  ("ROW_NUMBER in a CTE, keeping number 1. Change 1 to any N.", "O(n log n)", "O(n)"))


@B
def top_sale():
    return run_sql("""SELECT s.region, s.id, s.amount FROM sales s
        JOIN (SELECT region, MAX(amount) AS m FROM sales GROUP BY region) t
        ON t.region = s.region AND t.m = s.amount ORDER BY s.region""")


@O
def top_sale():
    return run_sql("""WITH r AS (SELECT *, ROW_NUMBER() OVER (PARTITION BY region ORDER BY amount DESC) AS rn FROM sales)
        SELECT region, id, amount FROM r WHERE rn = 1 ORDER BY region""")


Q(None, "Running Total", "Medium", "SUM OVER",
  "Return day, amount and running total within region N, by day.",
  [((), [['2026-01-01', 100, 100], ['2026-01-02', 300, 400], ['2026-01-03', 200, 600]])],
  ("A subquery summing all earlier rows.", "O(n²)", "O(1)"),
  ("<code>SUM(...) OVER (ORDER BY day)</code>.", "O(n log n)", "O(n)"))


@B
def running_total():
    return run_sql("""SELECT day, amount, (SELECT SUM(amount) FROM sales b WHERE b.region = 'N' AND b.day <= a.day)
        FROM sales a WHERE region = 'N' ORDER BY day""")


@O
def running_total():
    return run_sql("""SELECT day, amount, SUM(amount) OVER (ORDER BY day ROWS UNBOUNDED PRECEDING)
        FROM sales WHERE region = 'N' ORDER BY day""")


Q(None, "Moving Average", "Medium", "Frames",
  "For region S ordered by day, return id and the average of this row and the one before it, as a float.",
  [((), [[4, 50.0], [5, 50.0], [6, 225.0]])],
  ("Self join to the previous row with ROW_NUMBER.", "O(n log n)", "O(n)"),
  ("A frame: <code>ROWS 1 PRECEDING</code>.", "O(n log n)", "O(n)"))


@B
def moving_average():
    return run_sql("""WITH t AS (SELECT id, amount, ROW_NUMBER() OVER (ORDER BY day) AS rn FROM sales WHERE region = 'S')
        SELECT a.id, CASE WHEN b.id IS NULL THEN a.amount * 1.0 ELSE (a.amount + b.amount) / 2.0 END
        FROM t a LEFT JOIN t b ON b.rn = a.rn - 1 ORDER BY a.rn""")


@O
def moving_average():
    return run_sql("""SELECT id, AVG(amount) OVER (ORDER BY day ROWS 1 PRECEDING) FROM sales
        WHERE region = 'S' ORDER BY day""")


Q(None, "Compare With the Previous Row", "Medium", "LAG",
  "For region N by day, return id and change from the previous sale (NULL for the first).",
  [((), [[1, None], [2, 200], [3, -100]])],
  ("A correlated subquery for the previous day's row.", "O(n²)", "O(1)"),
  ("<code>LAG</code>.", "O(n log n)", "O(n)"))


@B
def change_from_previous():
    return run_sql("""SELECT id, amount - (SELECT b.amount FROM sales b WHERE b.region = 'N' AND b.day < a.day
        ORDER BY b.day DESC LIMIT 1) FROM sales a WHERE region = 'N' ORDER BY day""")


@O
def change_from_previous():
    return run_sql("""SELECT id, amount - LAG(amount) OVER (ORDER BY day) FROM sales WHERE region = 'N' ORDER BY day""")


Q(None, "Share Within a Group", "Medium", "Window without collapsing",
  "Return id and its percentage of its region's total, rounded to 1 decimal, ordered by id.",
  [((), [[1, 16.7], [2, 50.0], [3, 33.3], [4, 10.0], [5, 10.0], [6, 80.0]])],
  ("Join to grouped totals.", "O(n)", "O(r)"),
  ("<code>SUM(...) OVER (PARTITION BY ...)</code> keeps every row.", "O(n log n)", "O(n)"))


@B
def share_of_region():
    return run_sql("""SELECT s.id, ROUND(100.0 * s.amount / t.total, 1) FROM sales s
        JOIN (SELECT region, SUM(amount) AS total FROM sales GROUP BY region) t ON t.region = s.region ORDER BY s.id""")


@O
def share_of_region():
    return run_sql("""SELECT id, ROUND(100.0 * amount / SUM(amount) OVER (PARTITION BY region), 1) FROM sales ORDER BY id""")


Q(None, "Latest Row per Key", "Medium", "The most-used dedupe",
  "From customer_updates, return customer and email of the newest row per customer (ties: highest id), ordered by customer.",
  [((), [[1, 'a2@x'], [2, 'b@x'], [3, 'c@x']])],
  ("NOT EXISTS a newer row.", "O(n²)", "O(1)"),
  ("ROW_NUMBER ordered newest first, keeping 1.", "O(n log n)", "O(n)"))


@B
def latest_row():
    return run_sql("""SELECT customer, email FROM customer_updates a WHERE NOT EXISTS (
        SELECT 1 FROM customer_updates b WHERE b.customer = a.customer
        AND (b.updated > a.updated OR (b.updated = a.updated AND b.id > a.id))) ORDER BY customer""")


@O
def latest_row():
    return run_sql("""WITH r AS (SELECT *, ROW_NUMBER() OVER (PARTITION BY customer ORDER BY updated DESC, id DESC) AS rn
        FROM customer_updates) SELECT customer, email FROM r WHERE rn = 1 ORDER BY customer""")


Q(None, "Find Exact Duplicates", "Easy", "Data quality",
  "Return (customer, email, updated) combinations appearing more than once.",
  [((), [[2, 'b@x', 15]])],
  ("Self join on all the columns.", "O(n²)", "O(n)"),
  ("Group by all of them, with HAVING.", "O(n)", "O(n)"))


@B
def exact_dupes():
    return run_sql("""SELECT DISTINCT a.customer, a.email, a.updated FROM customer_updates a JOIN customer_updates b
        ON a.customer = b.customer AND a.email = b.email AND a.updated = b.updated AND a.id < b.id""")


@O
def exact_dupes():
    return run_sql("SELECT customer, email, updated FROM customer_updates GROUP BY 1, 2, 3 HAVING COUNT(*) > 1")


Q(None, "Sessionise Clicks", "Hard", "New session after 30 minutes",
  "Give each event a session number per user, where a gap above 1800 seconds starts a new session. Return user_id, ts and session, ordered by user and time.",
  [((), [[1, 100, 1], [1, 160, 1], [1, 2000, 2], [1, 2050, 2], [2, 300, 1], [2, 4000, 2], [3, 500, 1]])],
  ("Fetch rows and walk them in Python.", "O(n log n)", "O(n)"),
  ("LAG finds gaps; a running SUM of 'is new session' numbers them.", "O(n log n)", "O(n)"))


@B
def sessions():
    out, last_user, last_ts, session = [], None, None, 0
    for user, ts in run_sql("SELECT user_id, ts FROM events ORDER BY user_id, ts"):
        if user != last_user:
            session = 1
        elif ts - last_ts > 1800:
            session += 1
        out.append([user, ts, session])
        last_user, last_ts = user, ts
    return out


@O
def sessions():
    return run_sql("""WITH g AS (
            SELECT user_id, ts, CASE WHEN ts - LAG(ts) OVER w > 1800 THEN 1 ELSE 0 END AS new
            FROM events WINDOW w AS (PARTITION BY user_id ORDER BY ts))
        SELECT user_id, ts, 1 + SUM(new) OVER (PARTITION BY user_id ORDER BY ts) FROM g ORDER BY user_id, ts""")


Q(None, "Longest Login Streak", "Hard", "Gaps and islands",
  "Return each user's longest run of consecutive days, ordered by user.",
  [((), [[1, 3], [2, 1], [3, 2]])],
  ("Walk the rows in Python.", "O(n log n)", "O(n)"),
  ("Day minus ROW_NUMBER stays constant within a streak.", "O(n log n)", "O(n)"))


@B
def longest_streak():
    best, prev_user, prev_day, run = {}, None, None, 0
    for user, day in run_sql("SELECT user_id, day FROM logins ORDER BY user_id, day"):
        run = run + 1 if user == prev_user and day == prev_day + 1 else 1
        best[user] = max(best.get(user, 0), run)
        prev_user, prev_day = user, day
    return [[u, best[u]] for u in sorted(best)]


@O
def longest_streak():
    return run_sql("""WITH g AS (SELECT user_id, day - ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY day) AS grp FROM logins),
        s AS (SELECT user_id, COUNT(*) AS n FROM g GROUP BY user_id, grp)
        SELECT user_id, MAX(n) FROM s GROUP BY user_id ORDER BY user_id""")


Q(None, "Find Gaps in a Sequence", "Medium", "Missing ranges",
  "From seats, return the start and end of each run of free seats (taken = 0), in order.",
  [((), [[3, 5], [7, 8]])],
  ("Walk the rows in Python.", "O(n)", "O(g)"),
  ("Islands: seat − ROW_NUMBER among free seats.", "O(n log n)", "O(n)"))


@B
def free_runs():
    out = []
    for seat, taken in run_sql("SELECT seat, taken FROM seats ORDER BY seat"):
        if taken:
            continue
        if out and out[-1][1] == seat - 1:
            out[-1][1] = seat
        else:
            out.append([seat, seat])
    return out


@O
def free_runs():
    return run_sql("""WITH f AS (SELECT seat, seat - ROW_NUMBER() OVER (ORDER BY seat) AS grp FROM seats WHERE taken = 0)
        SELECT MIN(seat), MAX(seat) FROM f GROUP BY grp ORDER BY 1""")


Q(None, "Funnel Conversion", "Medium", "Who reached each step?",
  "Return distinct users who viewed 'home', and of those how many reached 'cart', then 'buy', as one row.",
  [((), [2, 1, 1])],
  ("Three queries, using sets in Python.", "O(n)", "O(u)"),
  ("Conditional aggregation per user, then sum.", "O(n)", "O(u)"))


@B
def funnel():
    pages = {}
    for u, p in run_sql("SELECT user_id, page FROM events"):
        pages.setdefault(p, set()).add(u)
    home = pages.get("home", set())
    cart = home & pages.get("cart", set())
    return [len(home), len(cart), len(cart & pages.get("buy", set()))]


@O
def funnel():
    return run_sql("""WITH f AS (SELECT user_id, MAX(page = 'home') AS h, MAX(page = 'cart') AS c, MAX(page = 'buy') AS b
        FROM events GROUP BY user_id)
        SELECT SUM(h), SUM(h AND c), SUM(h AND c AND b) FROM f""")[0]


Q(None, "Weekly Retention", "Hard", "Cohorts",
  "For each signup week and weeks since signup, return the number of active users. Order by cohort, then offset.",
  [((), [[0, 0, 3], [0, 1, 1], [0, 2, 1], [1, 0, 2], [1, 1, 1]])],
  ("Dictionaries of sets in Python.", "O(n)", "O(n)"),
  ("Join activity to signups, and group by cohort and offset.", "O(n)", "O(c·w)"))


@B
def retention():
    signup = dict(map(tuple, run_sql("SELECT user_id, week FROM signups")))
    groups = {}
    for user, week in run_sql("SELECT user_id, week FROM activity"):
        groups.setdefault((signup[user], week - signup[user]), set()).add(user)
    return [[c, o, len(groups[(c, o)])] for c, o in sorted(groups)]


@O
def retention():
    return run_sql("""SELECT s.week, a.week - s.week AS offset, COUNT(DISTINCT a.user_id)
        FROM activity a JOIN signups s ON s.user_id = a.user_id GROUP BY 1, 2 ORDER BY 1, 2""")


Q(None, "Pivot Rows to Columns", "Medium", "Reports",
  "For each rep, return amount in region N and region S as separate columns, ordered by rep.",
  [((), [['a', 300, 0], ['b', 300, 0], ['c', 0, 450], ['d', 0, 50]])],
  ("Two scalar subqueries per rep.", "O(r·n)", "O(r)"),
  ("Conditional aggregation.", "O(n)", "O(r)"))


@B
def pivot_regions():
    return run_sql("""SELECT DISTINCT rep,
        (SELECT COALESCE(SUM(amount),0) FROM sales b WHERE b.rep = a.rep AND b.region = 'N'),
        (SELECT COALESCE(SUM(amount),0) FROM sales b WHERE b.rep = a.rep AND b.region = 'S') FROM sales a ORDER BY rep""")


@O
def pivot_regions():
    return run_sql("""SELECT rep, SUM(CASE WHEN region = 'N' THEN amount ELSE 0 END),
        SUM(CASE WHEN region = 'S' THEN amount ELSE 0 END) FROM sales GROUP BY rep ORDER BY rep""")


Q(None, "Walk a Hierarchy", "Hard", "Recursive CTE",
  "Return each category's name and depth (root = 0), ordered by depth, then name.",
  [((), [['all', 0], ['food', 1], ['home', 1], ['tea', 2], ['green', 3]])],
  ("Search level by level in Python.", "O(n·d)", "O(n)"),
  ("A recursive CTE.", "O(n)", "O(n)"))


@B
def depths():
    rows = run_sql("SELECT id, parent, name FROM tree")
    out, level, frontier = [], 0, [r for r in rows if r[1] is None]
    while frontier:
        out += [[r[2], level] for r in frontier]
        ids = {r[0] for r in frontier}
        frontier = [r for r in rows if r[1] in ids]
        level += 1
    return sorted(out, key=lambda x: (x[1], x[0]))


@O
def depths():
    return run_sql("""WITH RECURSIVE t(id, name, d) AS (
            SELECT id, name, 0 FROM tree WHERE parent IS NULL
            UNION ALL SELECT c.id, c.name, t.d + 1 FROM tree c JOIN t ON c.parent = t.id)
        SELECT name, d FROM t ORDER BY d, name""")


Q(None, "Generate a Date Spine", "Medium", "Fill the missing days",
  "Return every day from 2026-01-01 to 2026-01-04 with region S's total, showing 0 for days without sales.",
  [((), [['2026-01-01', 50], ['2026-01-02', 50], ['2026-01-03', 0], ['2026-01-04', 400]])],
  ("Fill in missing days in Python.", "O(d)", "O(d)"),
  ("A recursive CTE of dates, LEFT JOINed to the sales.", "O(d + n)", "O(d)"))


@B
def daily_with_zeros():
    have = dict(map(tuple, run_sql("SELECT day, SUM(amount) FROM sales WHERE region = 'S' GROUP BY day")))
    return [[d, have.get(d, 0)] for d in ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"]]


@O
def daily_with_zeros():
    return run_sql("""WITH RECURSIVE d(day) AS (SELECT '2026-01-01' UNION ALL
            SELECT date(day, '+1 day') FROM d WHERE day < '2026-01-04')
        SELECT d.day, COALESCE(SUM(s.amount), 0) FROM d LEFT JOIN sales s ON s.day = d.day AND s.region = 'S'
        GROUP BY d.day ORDER BY d.day""")


Q(None, "First and Last in a Group", "Medium", "FIRST_VALUE",
  "For each user in events, return the first and last page visited, ordered by user.",
  [((), [[1, 'home', 'buy'], [2, 'home', 'home'], [3, 'cart', 'cart']])],
  ("Two ROW_NUMBER lookups joined together.", "O(n log n)", "O(n)"),
  ("<code>FIRST_VALUE</code>, with a full frame for the last.", "O(n log n)", "O(n)"))


@B
def first_last_page():
    rows = run_sql("SELECT user_id, page FROM events ORDER BY user_id, ts")
    first, last = {}, {}
    for u, p in rows:
        first.setdefault(u, p)
        last[u] = p
    return [[u, first[u], last[u]] for u in sorted(first)]


@O
def first_last_page():
    return run_sql("""SELECT DISTINCT user_id,
        FIRST_VALUE(page) OVER (PARTITION BY user_id ORDER BY ts),
        FIRST_VALUE(page) OVER (PARTITION BY user_id ORDER BY ts DESC) FROM events ORDER BY user_id""")


Q(None, "Split Into Buckets", "Medium", "NTILE",
  "Split all sales by amount into 3 equal buckets (ties by id), returning id and bucket, ordered by id.",
  [((), [[1, 2], [2, 3], [3, 2], [4, 1], [5, 1], [6, 3]])],
  ("Number the rows, then compute the bucket.", "O(n log n)", "O(n)"),
  ("<code>NTILE(3)</code>.", "O(n log n)", "O(n)"))


@B
def buckets():
    rows = run_sql("SELECT id, ROW_NUMBER() OVER (ORDER BY amount, id) FROM sales")
    n = len(rows)
    return sorted([[i, (r - 1) * 3 // n + 1] for i, r in rows])


@O
def buckets():
    return run_sql("SELECT id, NTILE(3) OVER (ORDER BY amount, id) FROM sales ORDER BY id")
