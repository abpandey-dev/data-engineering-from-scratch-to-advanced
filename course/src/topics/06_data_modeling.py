from lib import *
import sqlite3


TOPIC(
    id="data-modeling", title="Data Modelling", glyph="★",
    blurb="How to design tables people can trust: grain, keys, normalisation, star schemas, facts and dimensions, slowly changing dimensions, snapshots and surrogate keys. This is what separates senior engineers.",
    theory="""
<h3>Cheat sheet</h3>
<pre><code class="py">Grain: "one row per ___". Decide this first.
Fact: events and measures (orders, amount)
Dimension: descriptive context (customer, product, date)
SCD 1: overwrite   SCD 2: new row with valid_from / valid_to
Star: facts in the middle, dimensions around them</code></pre>
""")

SCHEMA = """
CREATE TABLE dim_customer (customer_key INT, customer_id INT, city TEXT, valid_from TEXT, valid_to TEXT);
INSERT INTO dim_customer VALUES (1,100,'Pune','2026-01-01','2026-02-01'),(2,100,'Delhi','2026-02-01','9999-12-31'),(3,200,'Goa','2026-01-01','9999-12-31');
CREATE TABLE dim_product (product_key INT, name TEXT, category TEXT);
INSERT INTO dim_product VALUES (1,'Pen','office'),(2,'Desk','office'),(3,'Tea','food');
CREATE TABLE fact_orders (order_id INT, customer_id INT, product_key INT, day TEXT, qty INT, amount INT);
INSERT INTO fact_orders VALUES (1,100,1,'2026-01-10',2,20),(2,100,3,'2026-02-10',1,5),(3,200,2,'2026-01-15',1,100),(4,100,2,'2026-03-01',1,100);
"""


def run_sql(query):
    """Run a query on a fresh database and return the rows as lists."""
    con = sqlite3.connect(":memory:")
    con.executescript(SCHEMA)
    rows = con.execute(query).fetchall()
    con.close()
    return [list(r) for r in rows]


Q(None, "Is This Column a Key?", "Easy", "Check before trusting",
  "Return whether a list of rows is unique on the given columns.",
  [(([{"a": 1, "b": 1}, {"a": 1, "b": 2}], ["a"]), False), (([{"a": 1, "b": 1}, {"a": 1, "b": 2}], ["a", "b"]), True)],
  ("Compare every pair.", "O(n²)", "O(1)"),
  ("Build a set of key tuples.", "O(n)", "O(n)"),
  names=["rows", "cols"])


@B
def is_key(rows, cols):
    keys = [[r[c] for c in cols] for r in rows]
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            if keys[i] == keys[j]:
                return False
    return True


@O
def is_key(rows, cols):
    return len({tuple(r[c] for c in cols) for r in rows}) == len(rows)


Q(None, "Find the Grain", "Medium", "One row per what?",
  "Return the smallest list of columns (fewest first, then in the given order) that uniquely identifies rows.",
  [(([{"day": 1, "store": "a", "sku": 1}, {"day": 1, "store": "a", "sku": 2}, {"day": 2, "store": "a", "sku": 1}], ["day", "store", "sku"]), ['day', 'sku'])],
  ("Try combinations by hand, with nested loops.", "O(2ᶜ·n)", "O(n)"),
  ("<code>itertools.combinations</code> by increasing size.", "O(2ᶜ·n)", "O(n)"),
  names=["rows", "cols"])


@B
def find_grain(rows, cols):
    subsets = [[]]
    for c in cols:
        subsets += [s + [c] for s in subsets]
    subsets = sorted(subsets[1:], key=len)
    for s in subsets:
        seen = {tuple(r[c] for c in s) for r in rows}
        if len(seen) == len(rows):
            return s
    return None


@O
def find_grain(rows, cols):
    import itertools
    for size in range(1, len(cols) + 1):
        for combo in itertools.combinations(cols, size):
            if len({tuple(r[c] for c in combo) for r in rows}) == len(rows):
                return list(combo)
    return None


Q(None, "Normalise a Flat Table", "Medium", "Each fact in one place",
  "Rows repeat customer details. Split into (customers, orders): customers is unique by cid with name; orders keeps oid and cid.",
  [(([{"oid": 1, "cid": 7, "name": "A"}, {"oid": 2, "cid": 7, "name": "A"}, {"oid": 3, "cid": 8, "name": "B"}],), ([{'cid': 7, 'name': 'A'}, {'cid': 8, 'name': 'B'}], [{'oid': 1, 'cid': 7}, {'oid': 2, 'cid': 7}, {'oid': 3, 'cid': 8}]))],
  ("Loop and check whether each customer's been seen.", "O(n·c)", "O(n)"),
  ("A dictionary keyed by cid.", "O(n)", "O(n)"))


@B
def normalise(rows):
    customers, orders = [], []
    for r in rows:
        if not any(c["cid"] == r["cid"] for c in customers):
            customers.append({"cid": r["cid"], "name": r["name"]})
        orders.append({"oid": r["oid"], "cid": r["cid"]})
    return (customers, orders)


@O
def normalise(rows):
    customers = {r["cid"]: {"cid": r["cid"], "name": r["name"]} for r in rows}
    return (list(customers.values()), [{"oid": r["oid"], "cid": r["cid"]} for r in rows])


Q(None, "Spot the Update Anomaly", "Easy", "Why normalise?",
  "Return customer ids in a flat table having more than one name, a sign that the same fact was stored inconsistently.",
  [(([{"cid": 7, "name": "A"}, {"cid": 7, "name": "A."}, {"cid": 8, "name": "B"}],), [7])],
  ("Compare names in nested loops.", "O(n²)", "O(1)"),
  ("A dictionary of sets.", "O(n)", "O(n)"))


@B
def inconsistent(rows):
    out = []
    for a in rows:
        for b in rows:
            if a["cid"] == b["cid"] and a["name"] != b["name"] and a["cid"] not in out:
                out.append(a["cid"])
    return sorted(out)


@O
def inconsistent(rows):
    names = {}
    for r in rows:
        names.setdefault(r["cid"], set()).add(r["name"])
    return sorted(c for c, n in names.items() if len(n) > 1)


Q(None, "Star Schema Query", "Easy", "Fact joined to dimensions",
  "Return category and total fact amount, highest first.",
  [((), [['office', 220], ['food', 5]])],
  ("Add up in Python after fetching.", "O(n)", "O(c)"),
  ("Join the fact to the dimension, then group.", "O(n)", "O(c)"))


@B
def category_sales():
    totals = {}
    for cat, a in run_sql("SELECT p.category, f.amount FROM fact_orders f JOIN dim_product p ON p.product_key = f.product_key"):
        totals[cat] = totals.get(cat, 0) + a
    return sorted(([k, v] for k, v in totals.items()), key=lambda x: -x[1])


@O
def category_sales():
    return run_sql("""SELECT p.category, SUM(f.amount) AS t FROM fact_orders f
        JOIN dim_product p ON p.product_key = f.product_key GROUP BY p.category ORDER BY t DESC""")


Q(None, "Point-in-Time Join", "Hard", "SCD 2: what was true then?",
  "Join each order to the customer's city as of the order date, using valid_from and valid_to. Return order_id and city by order_id.",
  [((), [[1, 'Pune'], [2, 'Delhi'], [3, 'Goa'], [4, 'Delhi']])],
  ("A correlated subquery per order.", "O(n·m)", "O(n)"),
  ("A range condition in the join: valid_from ≤ day &lt; valid_to.", "O(n·m) without indexes", "O(n)"))


@B
def city_at_order():
    return run_sql("""SELECT order_id, (SELECT city FROM dim_customer d WHERE d.customer_id = f.customer_id
        AND d.valid_from <= f.day AND f.day < d.valid_to) FROM fact_orders f ORDER BY order_id""")


@O
def city_at_order():
    return run_sql("""SELECT f.order_id, d.city FROM fact_orders f JOIN dim_customer d
        ON d.customer_id = f.customer_id AND f.day >= d.valid_from AND f.day < d.valid_to ORDER BY f.order_id""")


Q(None, "SCD Type 1: Overwrite", "Easy", "No history kept",
  "Apply updates to a dimension keyed by id, overwriting values and adding new ids. Return rows sorted by id.",
  [(([{"id": 1, "city": "Pune"}, {"id": 2, "city": "Goa"}], [{"id": 1, "city": "Delhi"}, {"id": 3, "city": "Agra"}]), [{'id': 1, 'city': 'Delhi'}, {'id': 2, 'city': 'Goa'}, {'id': 3, 'city': 'Agra'}])],
  ("Search the list for each update.", "O(n·u)", "O(n)"),
  ("A dictionary keyed by id.", "O(n + u)", "O(n)"),
  names=["dim", "updates"])


@B
def scd1(dim, updates):
    out = [dict(r) for r in dim]
    for u in updates:
        for r in out:
            if r["id"] == u["id"]:
                r.update(u)
                break
        else:
            out.append(dict(u))
    return sorted(out, key=lambda r: r["id"])


@O
def scd1(dim, updates):
    merged = {r["id"]: r for r in dim}
    merged.update({u["id"]: u for u in updates})
    return [merged[k] for k in sorted(merged)]


Q(None, "SCD Type 2: Keep History", "Hard", "Close the old, open the new",
  "dim rows have id, city, start, end (None = current). For each update (id, city) on day: if the city changed, close the current row and add a new one; new ids get a new row. Return rows sorted by id, start.",
  [(([{"id": 1, "city": "Pune", "start": 1, "end": None}], [{"id": 1, "city": "Delhi"}, {"id": 2, "city": "Goa"}], 5), [{'id': 1, 'city': 'Pune', 'start': 1, 'end': 5}, {'id': 1, 'city': 'Delhi', 'start': 5, 'end': None}, {'id': 2, 'city': 'Goa', 'start': 5, 'end': None}]),
   (([{"id": 1, "city": "Pune", "start": 1, "end": None}], [{"id": 1, "city": "Pune"}], 5), [{'id': 1, 'city': 'Pune', 'start': 1, 'end': None}])],
  ("Search for the current row for each update.", "O(n·u)", "O(n + u)"),
  ("A dictionary of current rows.", "O(n + u)", "O(n + u)"),
  names=["dim", "updates", "day"])


@B
def scd2(dim, updates, day):
    out = [dict(r) for r in dim]
    for u in updates:
        current = None
        for r in out:
            if r["id"] == u["id"] and r["end"] is None:
                current = r
        if current is None:
            out.append({"id": u["id"], "city": u["city"], "start": day, "end": None})
        elif current["city"] != u["city"]:
            current["end"] = day
            out.append({"id": u["id"], "city": u["city"], "start": day, "end": None})
    return sorted(out, key=lambda r: (r["id"], r["start"]))


@O
def scd2(dim, updates, day):
    out = [dict(r) for r in dim]
    current = {r["id"]: r for r in out if r["end"] is None}
    for u in updates:
        row = current.get(u["id"])
        if row is not None and row["city"] == u["city"]:
            continue
        if row is not None:
            row["end"] = day
        new = {"id": u["id"], "city": u["city"], "start": day, "end": None}
        out.append(new)
        current[u["id"]] = new
    return sorted(out, key=lambda r: (r["id"], r["start"]))


Q(None, "Check SCD 2 Integrity", "Medium", "No gaps or overlaps",
  "Rows are (start, end) for one key, with end None for current. Return problems: 'overlap', 'gap' or 'many current', in that order, for those found.",
  [(([(1, 5), (5, None)],), []), (([(1, 5), (4, 8), (9, None), (10, None)],), ['overlap', 'gap', 'many current'])],
  ("Compare each neighbour after sorting, with separate flags.", "O(n log n)", "O(n)"),
  ("Same check, via zip on neighbours.", "O(n log n)", "O(n)"))


@B
def scd_integrity(ranges):
    r = sorted(ranges, key=lambda x: x[0])
    overlap = gap = False
    for i in range(len(r) - 1):
        end = r[i][1]
        if end is None or end > r[i + 1][0]:
            overlap = True
        elif end < r[i + 1][0]:
            gap = True
    many = len([x for x in r if x[1] is None]) > 1
    out = []
    if overlap:
        out.append("overlap")
    if gap:
        out.append("gap")
    if many:
        out.append("many current")
    return out


@O
def scd_integrity(ranges):
    r = sorted(ranges, key=lambda x: x[0])
    pairs = list(zip(r, r[1:]))
    flags = [("overlap", any(a[1] is None or a[1] > b[0] for a, b in pairs)),
             ("gap", any(a[1] is not None and a[1] < b[0] for a, b in pairs)),
             ("many current", sum(x[1] is None for x in r) > 1)]
    return [name for name, hit in flags if hit]


Q(None, "Surrogate Keys", "Easy", "Stable internal ids",
  "Assign integer keys from 1 to natural keys in first-seen order. Return the mapping and the rows as keys.",
  [((["u9", "u3", "u9"],), ({'u9': 1, 'u3': 2}, [1, 2, 1]))],
  ("A list with <code>index</code>.", "O(n²)", "O(n)"),
  ("A dictionary with <code>setdefault</code>.", "O(n)", "O(n)"))


@B
def surrogate(values):
    seen = []
    keys = []
    for v in values:
        if v not in seen:
            seen.append(v)
        keys.append(seen.index(v) + 1)
    return ({v: i + 1 for i, v in enumerate(seen)}, keys)


@O
def surrogate(values):
    mapping = {}
    keys = [mapping.setdefault(v, len(mapping) + 1) for v in values]
    return (mapping, keys)


Q(None, "Hash Key From Several Columns", "Medium", "Deterministic keys",
  "Build a key with md5 of the values joined by '|', treating None as an empty string, and keep the first 8 hex characters.",
  [(([1, "Pune", None],), '6461e899')],
  ("Build the text in a loop.", "O(k)", "O(k)"),
  ("<code>join</code> with a generator.", "O(k)", "O(k)"))


@B
def hash_key(values):
    import hashlib
    text = ""
    for i, v in enumerate(values):
        if i:
            text += "|"
        text += "" if v is None else str(v)
    return hashlib.md5(text.encode()).hexdigest()[:8]


@O
def hash_key(values):
    import hashlib
    return hashlib.md5("|".join("" if v is None else str(v) for v in values).encode()).hexdigest()[:8]


Q(None, "Build a Date Dimension", "Easy", "Every warehouse has one",
  "For each date string, return key (YYYYMMDD as int), year, month, weekday name, and whether it's a weekend.",
  [((["2026-01-03", "2026-01-05"],), [{'key': 20260103, 'year': 2026, 'month': 1, 'weekday': 'Saturday', 'weekend': True}, {'key': 20260105, 'year': 2026, 'month': 1, 'weekday': 'Monday', 'weekend': False}])],
  ("Parse parts by hand and use the datetime weekday.", "O(n)", "O(n)"),
  ("<code>date.fromisoformat</code> and <code>strftime</code>.", "O(n)", "O(n)"))


@B
def date_dim(days):
    from datetime import date
    names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    out = []
    for d in days:
        y, m, dd = map(int, d.split("-"))
        wd = date(y, m, dd).weekday()
        out.append({"key": y * 10000 + m * 100 + dd, "year": y, "month": m, "weekday": names[wd], "weekend": wd >= 5})
    return out


@O
def date_dim(days):
    from datetime import date
    parsed = [date.fromisoformat(d) for d in days]
    return [{"key": int(d.strftime("%Y%m%d")), "year": d.year, "month": d.month, "weekday": d.strftime("%A"), "weekend": d.weekday() >= 5} for d in parsed]


Q(None, "Additive or Not?", "Medium", "Which measures can you SUM?",
  "Given daily balance snapshots (a semi-additive measure), return (the wrong sum across days, the correct closing balance at the last day).",
  [(([("d1", 100), ("d2", 120), ("d3", 90)],), (310, 90))],
  ("A loop tracking the sum and the last day.", "O(n)", "O(1)"),
  ("<code>sum</code> and <code>max</code>.", "O(n)", "O(1)"))


@B
def closing_balance(rows):
    total = 0
    last_day, last_value = None, None
    for day, value in rows:
        total += value
        if last_day is None or day > last_day:
            last_day, last_value = day, value
    return (total, last_value)


@O
def closing_balance(rows):
    return (sum(v for _, v in rows), max(rows)[1])


Q(None, "Daily Snapshot From Events", "Medium", "Accumulate to a state",
  "Given deposits and withdrawals as (day, delta), return the balance at the end of each day from first to last, including days with no events.",
  [(([(1, 100), (3, -30), (3, 10), (5, 5)],), [[1, 100], [2, 100], [3, 80], [4, 80], [5, 85]])],
  ("For each day, sum all events up to it.", "O(d·n)", "O(d)"),
  ("A dictionary per day, then a running sum.", "O(d + n)", "O(d)"))


@B
def daily_balance(events):
    days = [e[0] for e in events]
    return [[d, sum(v for day, v in events if day <= d)] for d in range(min(days), max(days) + 1)]


@O
def daily_balance(events):
    import itertools
    per_day = {}
    for d, v in events:
        per_day[d] = per_day.get(d, 0) + v
    lo, hi = min(per_day), max(per_day)
    running = itertools.accumulate(per_day.get(d, 0) for d in range(lo, hi + 1))
    return [[d, b] for d, b in zip(range(lo, hi + 1), running)]


Q(None, "Bridge Table: Avoid Double Counting", "Hard", "Many-to-many",
  "An order can have several tags. Return (revenue by naive join, true revenue, revenue per tag).",
  [(([(1, 100), (2, 50)], [(1, "sale"), (1, "gift"), (2, "sale")]), (250, 150, {'gift': 100, 'sale': 150}))],
  ("Loops over both lists.", "O(n·m)", "O(t)"),
  ("A dictionary for amounts. Each tag's total is valid, but they don't add up to the true total.", "O(n + m)", "O(t)"),
  names=["orders", "tags"])


@B
def bridge_revenue(orders, tags):
    naive = 0
    per = {}
    for oid, amt in orders:
        for t_oid, tag in tags:
            if oid == t_oid:
                naive += amt
                per[tag] = per.get(tag, 0) + amt
    return (naive, sum(a for _, a in orders), dict(sorted(per.items())))


@O
def bridge_revenue(orders, tags):
    amt = dict(orders)
    per = {}
    for oid, tag in tags:
        per[tag] = per.get(tag, 0) + amt[oid]
    return (sum(amt[o] for o, _ in tags), sum(amt.values()), dict(sorted(per.items())))


Q(None, "Unknown Dimension Member", "Medium", "Don't drop facts",
  "Facts refer to dimension keys. Replace missing keys with −1 ('unknown'), so an inner join won't lose them. Return (facts with fixed keys, count fixed).",
  [(([{"id": 1, "k": 10}, {"id": 2, "k": 99}], [10, 20]),  ([{'id': 1, 'k': 10}, {'id': 2, 'k': -1}], 1))],
  ("Search the list for each fact.", "O(f·d)", "O(f)"),
  ("A set for membership.", "O(f + d)", "O(d)"),
  names=["facts", "keys"])


@B
def unknown_member(facts, keys):
    out, fixed = [], 0
    for f in facts:
        if f["k"] in keys:
            out.append(dict(f))
        else:
            out.append({**f, "k": -1})
            fixed += 1
    return (out, fixed)


@O
def unknown_member(facts, keys):
    known = set(keys)
    out = [{**f, "k": f["k"] if f["k"] in known else -1} for f in facts]
    return (out, sum(f["k"] == -1 for f in out))


Q(None, "Wide Table or Star?", "Easy", "Storage trade-offs",
  "A fact has n rows. Repeating a text attribute of s bytes on each row costs n × s. A dimension stores d distinct values and an 8-byte key per fact. Return (wide MB, star MB) with MB = 10⁶ bytes, before compression.",
  [((10000000, 30, 1000),  (300.0, 80.038))],
  ("Compute each part.", "O(1)", "O(1)"),
  ("Two formulas.", "O(1)", "O(1)"),
  names=["n", "s", "d"])


@B
def wide_vs_star(n, s, d):
    wide = n * s
    keys = n * 8
    dimension = d * (s + 8)
    return (wide / 1e6, (keys + dimension) / 1e6)


@O
def wide_vs_star(n, s, d):
    return (n * s / 1e6, (n * 8 + d * (s + 8)) / 1e6)


Q(None, "Late-Arriving Fact", "Hard", "Which dimension row applies?",
  "versions are (key, start) sorted by start. For each fact date, return the key active on that date, or −1 if before all of them.",
  [(([(1, 10), (2, 20), (3, 30)], [5, 10, 25, 99]), [-1, 1, 2, 3])],
  ("Scan versions for each fact.", "O(f·v)", "O(f)"),
  ("Binary search on the start dates.", "O(f log v)", "O(f)"),
  names=["versions", "dates"])


@B
def active_key(versions, dates):
    out = []
    for d in dates:
        key = -1
        for k, start in versions:
            if start <= d:
                key = k
        out.append(key)
    return out


@O
def active_key(versions, dates):
    import bisect
    starts = [s for _, s in versions]
    return [versions[bisect.bisect_right(starts, d) - 1][0] if d >= starts[0] else -1 for d in dates]


Q(None, "Check Foreign Keys", "Easy", "Referential integrity",
  "Warehouses often don't enforce foreign keys, so you check. Return fact keys missing from the dimension, sorted and unique.",
  [(([1, 2, 2, 9, 7], [1, 2, 3]),  [7, 9])],
  ("Search for each.", "O(f·d)", "O(f)"),
  ("Set difference.", "O(f + d)", "O(d)"),
  names=["fact_keys", "dim_keys"])


@B
def orphan_keys(fact_keys, dim_keys):
    out = []
    for k in fact_keys:
        if k not in dim_keys and k not in out:
            out.append(k)
    return sorted(out)


@O
def orphan_keys(fact_keys, dim_keys):
    return sorted(set(fact_keys) - set(dim_keys))


Q(None, "Rollup Must Reconcile", "Easy", "Trust but verify",
  "Daily totals must add up to the fact table's total per month. Return months where they don't, sorted. Rows are (month, amount).",
  [(([("01", 10), ("01", 5), ("02", 7)], {"01": 15, "02": 8}),  ['02'])],
  ("Add up in a loop, and compare.", "O(n)", "O(m)"),
  ("A <code>defaultdict</code>.", "O(n)", "O(m)"),
  names=["facts", "rollup"])


@B
def bad_months(facts, rollup):
    totals = {}
    for m, a in facts:
        totals[m] = totals.get(m, 0) + a
    return sorted(m for m in rollup if totals.get(m, 0) != rollup[m])


@O
def bad_months(facts, rollup):
    from collections import defaultdict
    totals = defaultdict(int)
    for m, a in facts:
        totals[m] += a
    return sorted(m for m, v in rollup.items() if totals[m] != v)
