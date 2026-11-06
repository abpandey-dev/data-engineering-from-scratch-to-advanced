from lib import *
import heapq
import math
import re
import sqlite3
from collections import defaultdict


TOPIC(
    id="warehouses-dbt", title="Warehouses & dbt", glyph="{{ref}}",
    blurb="Modern analytics engineering: how cloud warehouses store and bill, clustering and distribution keys, views vs tables vs materialized views, and dbt's models, tests, incremental loads and snapshots. You'll build a tiny dbt.",
    theory="""
<h3>Cheat sheet</h3>
<pre><code class="py">-- models/daily_sales.sql
{{ config(materialized='incremental', unique_key='day') }}
SELECT day, SUM(amount) AS total
FROM {{ ref('stg_orders') }}
{% if is_incremental() %}
WHERE day >= (SELECT MAX(day) FROM {{ this }})
{% endif %}
GROUP BY day</code></pre>
<pre><code class="py">dbt run --select daily_sales+     # this model and everything downstream
dbt test                          # run data tests</code></pre>
""")

SCHEMA = """
CREATE TABLE raw_orders (id INT, day TEXT, status TEXT, amount INT);
INSERT INTO raw_orders VALUES (1,'d1','paid',10),(2,'d1','failed',5),(3,'d2','paid',7),(3,'d2','paid',7),(4,'d3','paid',1);
"""


def run_sql(query):
    """Run statements on a fresh database and return the last query's rows as lists."""
    con = sqlite3.connect(":memory:")
    con.executescript(SCHEMA)
    *setup, last = [s for s in query.split(";") if s.strip()]
    for s in setup:
        con.execute(s)
    rows = con.execute(last).fetchall()
    con.close()
    return [list(r) for r in rows]


Q(None, "Find ref() Dependencies", "Easy", "How dbt builds its graph",
  "Return the model names used in {{ ref('x') }} in a SQL string, sorted and unique.",
  [(("SELECT * FROM {{ ref('a') }} JOIN {{ ref( 'b' ) }} USING (id) JOIN {{ ref('a') }} x",), ['a', 'b'])],
  ("Split on 'ref(' and clean each piece.", "O(n)", "O(r)"),
  ("A regular expression.", "O(n)", "O(r)"))


@B
def find_refs(sql):
    out = []
    for piece in sql.split("ref(")[1:]:
        name = piece.split(")")[0].strip().strip("'\"")
        if name not in out:
            out.append(name)
    return sorted(out)


@O
def find_refs(sql):
    return sorted(set(re.findall(r"ref\(\s*['\"](\w+)['\"]\s*\)", sql)))


Q(None, "Build Order of Models", "Medium", "dbt run",
  "models maps a name to its SQL. Return a build order respecting ref() (alphabetical among those ready).",
  [(({"c": "{{ ref('a') }} {{ ref('b') }}", "b": "{{ ref('a') }}", "a": "SELECT 1"},), ['a', 'b', 'c'])],
  ("Repeatedly scan for models whose references are built.", "O(m²)", "O(m)"),
  ("Kahn's algorithm with a heap.", "O(m log m + e)", "O(m + e)"))


@B
def build_order(models):
    deps = {m: set(re.findall(r"ref\('(\w+)'\)", s)) for m, s in models.items()}
    done = []
    while len(done) < len(models):
        ready = sorted(m for m in models if m not in done and deps[m] <= set(done))
        done.append(ready[0])
    return done


@O
def build_order(models):
    after, waiting = defaultdict(list), {}
    for m, s in models.items():
        refs = set(re.findall(r"ref\('(\w+)'\)", s))
        waiting[m] = len(refs)
        for r in refs:
            after[r].append(m)
    heap = sorted(m for m, n in waiting.items() if n == 0)
    order = []
    while heap:
        m = heapq.heappop(heap)
        order.append(m)
        for x in after[m]:
            waiting[x] -= 1
            if not waiting[x]:
                heapq.heappush(heap, x)
    return order


Q(None, "Compile a Model", "Easy", "Jinja to SQL",
  "Replace {{ ref('x') }} with schema.x.",
  [(("SELECT * FROM {{ ref('orders') }}", "prod"), 'SELECT * FROM prod.orders')],
  ("String methods in a loop.", "O(n·r)", "O(n)"),
  ("<code>re.sub</code>.", "O(n)", "O(n)"),
  names=["sql", "schema"])


@B
def compile_model(sql, schema):
    while "{{ ref('" in sql:
        start = sql.index("{{ ref('")
        end = sql.index("}}", start) + 2
        name = sql[start + 8:end - 5]
        sql = sql[:start] + schema + "." + name + sql[end:]
    return sql


@O
def compile_model(sql, schema):
    return re.sub(r"\{\{\s*ref\('(\w+)'\)\s*\}\}", lambda m: f"{schema}.{m.group(1)}", sql)


Q(None, "A Staging Model", "Easy", "One clean version of each source",
  "From raw_orders, return unique orders that are paid: (id, day, amount), by id.",
  [((), [[1, 'd1', 10], [3, 'd2', 7], [4, 'd3', 1]])],
  ("Clean up in Python.", "O(n log n)", "O(n)"),
  ("DISTINCT and a WHERE in a view, which is what a staging model is.", "O(n log n)", "O(n)"))


@B
def stg_orders():
    rows = run_sql("SELECT id, day, status, amount FROM raw_orders")
    out = {}
    for i, d, s, a in rows:
        if s == "paid":
            out[i] = [i, d, a]
    return [out[k] for k in sorted(out)]


@O
def stg_orders():
    return run_sql("""CREATE VIEW stg AS SELECT DISTINCT id, day, amount FROM raw_orders WHERE status = 'paid';
        SELECT * FROM stg ORDER BY id""")


Q(None, "A Mart Built on Staging", "Medium", "Layers of models",
  "Build daily revenue from a staging view. Return (day, total), by day.",
  [((), [['d1', 10], ['d2', 7], ['d3', 1]])],
  ("A CTE, all in one query.", "O(n)", "O(d)"),
  ("Two views, stacked, so the cleaning is reused.", "O(n)", "O(d)"))


@B
def daily_revenue():
    return run_sql("""WITH s AS (SELECT DISTINCT id, day, amount FROM raw_orders WHERE status = 'paid')
        SELECT day, SUM(amount) FROM s GROUP BY day ORDER BY day""")


@O
def daily_revenue():
    return run_sql("""CREATE VIEW stg AS SELECT DISTINCT id, day, amount FROM raw_orders WHERE status = 'paid';
        CREATE VIEW mart AS SELECT day, SUM(amount) AS t FROM stg GROUP BY day;
        SELECT * FROM mart ORDER BY day""")


Q(None, "Incremental Model", "Medium", "Only new days",
  "existing maps day to total. new_rows are (day, amount). Reprocess days ≥ the max existing day, replacing them. Return the table sorted.",
  [(({"d1": 10, "d2": 5}, [("d2", 3), ("d2", 4), ("d3", 1), ("d1", 99)]),  {'d1': 10, 'd2': 7, 'd3': 1})],
  ("Loops.", "O(n)", "O(d)"),
  ("A filter, then group.", "O(n)", "O(d)"),
  names=["existing", "new_rows"])


@B
def incremental_model(existing, new_rows):
    cutoff = max(existing)
    fresh = {}
    for day, amount in new_rows:
        if day >= cutoff:
            fresh[day] = fresh.get(day, 0) + amount
    out = dict(existing)
    out.update(fresh)
    return dict(sorted(out.items()))


@O
def incremental_model(existing, new_rows):
    cut, fresh = max(existing), defaultdict(int)
    for d, a in new_rows:
        if d >= cut:
            fresh[d] += a
    return dict(sorted((existing | fresh).items()))


Q(None, "dbt Snapshot", "Medium", "SCD 2 from a table",
  "Compare current source {id: value} with open snapshot rows (id, value, from). Close changed rows and open new ones at time t. Return (rows closed, rows opened), sorted.",
  [(([(1, "a", 0), (2, "b", 0)], {1: "a", 2: "B", 3: "c"}, 5),  ([2], [[2, 'B', 5], [3, 'c', 5]]))],
  ("Loops over both.", "O(n·m)", "O(n)"),
  ("A dictionary.", "O(n + m)", "O(n)"),
  names=["open_rows", "source", "t"])


@B
def snapshot_step(open_rows, source, t):
    closed, opened = [], []
    for i, v, _ in open_rows:
        if i in source and source[i] != v:
            closed.append(i)
            opened.append([i, source[i], t])
    known = [r[0] for r in open_rows]
    for i in source:
        if i not in known:
            opened.append([i, source[i], t])
    return (sorted(closed), sorted(opened))


@O
def snapshot_step(open_rows, source, t):
    cur = {i: v for i, v, _ in open_rows}
    changed = [i for i, v in cur.items() if i in source and source[i] != v]
    new = [i for i in source if i not in cur]
    return (sorted(changed), sorted([i, source[i], t] for i in changed + new))


Q(None, "dbt run --select", "Medium", "Run part of the graph",
  "Given parent → children edges, return models selected by 'x+' (x and downstream), '+x' (x and upstream) or 'x', sorted.",
  [(({"a": ["b"], "b": ["c"], "d": ["c"]}, "b+"), ['b', 'c']), (({"a": ["b"], "b": ["c"], "d": ["c"]}, "+c"), ['a', 'b', 'c', 'd']), (({"a": ["b"]}, "a"), ['a'])],
  ("Repeat scanning until nothing changes.", "O(V·E)", "O(V)"),
  ("A graph search in the right direction.", "O(V + E)", "O(V)"),
  names=["graph", "selector"])


@B
def select_models(graph, selector):
    name = selector.strip("+")
    out = {name}
    changed = True
    while changed:
        changed = False
        for p, kids in graph.items():
            for k in kids:
                if selector.endswith("+") and p in out and k not in out:
                    out.add(k)
                    changed = True
                if selector.startswith("+") and k in out and p not in out:
                    out.add(p)
                    changed = True
    return sorted(out)


@O
def select_models(graph, selector):
    down, up = defaultdict(list), defaultdict(list)
    for p, kids in graph.items():
        for k in kids:
            down[p].append(k)
            up[k].append(p)
    name = selector.strip("+")
    links = down if selector.endswith("+") else up if selector.startswith("+") else {}
    seen, stack = set(), [name]
    while stack:
        n = stack.pop()
        if n not in seen:
            seen.add(n)
            stack += links.get(n, [])
    return sorted(seen)


Q(None, "View, Table or Materialized View?", "Medium", "Pay at read or at write",
  "A query costs c to run. A view runs it on every read. A table costs c × rebuilds per day. Return the daily cost of each and the cheaper name (a tie goes to 'view').",
  [((10, 100, 1), (1000, 10, 'table')), ((10, 1, 24), (10, 240, 'view'))],
  ("Multiply and compare.", "O(1)", "O(1)"),
  ("Compact.", "O(1)", "O(1)"),
  names=["c", "reads", "rebuilds"])


@B
def materialization(c, reads, rebuilds):
    view = c * reads
    table = c * rebuilds
    if view <= table:
        return (view, table, "view")
    return (view, table, "table")


@O
def materialization(c, reads, rebuilds):
    return (c * reads, c * rebuilds, "view" if reads <= rebuilds else "table")


Q(None, "Pay per Byte Scanned", "Easy", "On-demand pricing",
  "With a made-up price per TB scanned, return query cost for full scan, column pruned and partition pruned too, rounded to 2 decimals.",
  [((10, 0.1, 0.05, 5),  (50, 5.0, 0.25))],
  ("Step by step.", "O(1)", "O(1)"),
  ("Compact.", "O(1)", "O(1)"),
  names=["tb", "col_share", "part_share", "price"])


@B
def scan_cost(tb, col_share, part_share, price):
    full = tb * price
    columns = full * col_share
    both = columns * part_share
    return (round(full, 2), round(columns, 2), round(both, 2))


@O
def scan_cost(tb, col_share, part_share, price):
    f = tb * price
    return (round(f, 2), round(f * col_share, 2), round(f * col_share * part_share, 2))


Q(None, "Warehouse Size vs Time", "Medium", "Pay for compute time",
  "Each size up doubles credits per hour. With perfect scaling, it halves time, so cost stays equal; with an imperfect scale factor it costs more. Return (hours, credits) per size step, rounded to 2 decimals.",
  [((8, 1, [0, 1, 2], 2.0), [[8.0, 8.0], [4.0, 8.0], [2.0, 8.0]]), ((8, 1, [0, 1, 2], 1.5), [[8.0, 8.0], [5.33, 10.67], [3.56, 14.22]])],
  ("A loop with powers.", "O(s)", "O(s)"),
  ("A comprehension.", "O(s)", "O(s)"),
  names=["hours", "credits", "steps", "speedup"])


@B
def size_tradeoff(hours, credits, steps, speedup):
    out = []
    for s in steps:
        h = hours / speedup ** s
        out.append([round(h, 2), round(h * credits * 2 ** s, 2)])
    return out


@O
def size_tradeoff(hours, credits, steps, speedup):
    return [[round(hours / speedup ** s, 2), round(hours / speedup ** s * credits * 2 ** s, 2)] for s in steps]


Q(None, "Auto-Suspend Saves Money", "Easy", "Idle compute costs",
  "A warehouse runs jobs for busy hours a day. Without auto-suspend, it bills 24 hours; with it, busy + idle_after × jobs. Return both and the percent saved, rounded to 1 decimal.",
  [((4, 0.1, 10),  (24, 5.0, 79.2))],
  ("Step by step.", "O(1)", "O(1)"),
  ("Compact.", "O(1)", "O(1)"),
  names=["busy", "idle_after", "jobs"])


@B
def auto_suspend(busy, idle_after, jobs):
    with_it = busy + idle_after * jobs
    saved = (24 - with_it) / 24 * 100
    return (24, round(with_it, 1), round(saved, 1))


@O
def auto_suspend(busy, idle_after, jobs):
    w = busy + idle_after * jobs
    return (24, round(w, 1), round((1 - w / 24) * 100, 1))


Q(None, "Choose a Distribution Key", "Medium", "MPP warehouses",
  "Hash-distributing rows by a key to n nodes: return skew (largest ÷ average, rounded to 2 decimals) for each candidate column, and the best.",
  [(({"country": ["in"] * 8 + ["us"] * 2, "user": list(range(10))}, 2),  ({'country': 1.6, 'user': 1.0}, 'user'))],
  ("Count in loops.", "O(c·r)", "O(n)"),
  ("A helper with <code>Counter</code>.", "O(c·r)", "O(n)"),
  names=["columns", "n"])


@B
def dist_key(columns, n):
    out = {}
    for name, values in columns.items():
        groups = {}
        for v in values:
            distinct = sorted(set(map(str, values)))
            node = distinct.index(str(v)) % n
            groups[node] = groups.get(node, 0) + 1
        out[name] = round(max(groups.values()) / (len(values) / n), 2)
    return (out, min(out, key=out.get))


@O
def dist_key(columns, n):
    from collections import Counter

    def skew(values):
        order = {v: i for i, v in enumerate(sorted(set(map(str, values))))}
        return round(max(Counter(order[str(v)] % n for v in values).values()) * n / len(values), 2)
    out = {k: skew(v) for k, v in columns.items()}
    return (out, min(out, key=out.get))


Q(None, "Sort Key Pruning", "Medium", "Zone maps",
  "Blocks store min and max. Return blocks read for a range filter on the given column. Blocks are (min, max).",
  [(([(1, 10), (11, 20), (21, 30), (31, 40)], 12, 25),  2)],
  ("A loop.", "O(b)", "O(1)"),
  ("A generator.", "O(b)", "O(1)"),
  names=["blocks", "lo", "hi"])


@B
def blocks_read(blocks, lo, hi):
    n = 0
    for a, b in blocks:
        if a <= hi and b >= lo:
            n += 1
    return n


@O
def blocks_read(blocks, lo, hi):
    return sum(a <= hi and b >= lo for a, b in blocks)


Q(None, "Result Cache", "Easy", "Same query, no compute",
  "Warehouses can return a saved result if the query and data haven't changed. Given queries as (text, table_version), return (hits, compute runs).",
  [(([("q1", 1), ("q1", 1), ("q2", 1), ("q1", 2)],),  (1, 3))],
  ("A list of seen pairs.", "O(n²)", "O(n)"),
  ("A set.", "O(n)", "O(n)"))


@B
def result_cache(queries):
    seen, hits = [], 0
    for q in queries:
        if q in seen:
            hits += 1
        else:
            seen.append(q)
    return (hits, len(seen))


@O
def result_cache(queries):
    n = len(set(queries))
    return (len(queries) - n, n)


Q(None, "Cost by Team", "Easy", "Make spending visible",
  "Given query records (team, seconds, credits_per_hour), return credits per team rounded to 2 decimals, largest first.",
  [(([("a", 3600, 2), ("b", 1800, 4), ("a", 1800, 2)],),  [['a', 3.0], ['b', 2.0]])],
  ("A dictionary.", "O(n log t)", "O(t)"),
  ("<code>defaultdict</code> and sorted.", "O(n log t)", "O(t)"))


@B
def cost_by_team(records):
    totals = {}
    for team, seconds, rate in records:
        totals[team] = totals.get(team, 0) + seconds / 3600 * rate
    return [[t, round(v, 2)] for t, v in sorted(totals.items(), key=lambda x: -x[1])]


@O
def cost_by_team(records):
    totals = defaultdict(float)
    for t, s, r in records:
        totals[t] += s * r / 3600
    return sorted(([t, round(v, 2)] for t, v in totals.items()), key=lambda x: -x[1])


Q(None, "Most Expensive Queries", "Easy", "Where to start tuning",
  "Normalise queries by replacing numbers with ?, group the same shape, and return the top k by total bytes.",
  [(([("SELECT * FROM t WHERE id=1", 100), ("SELECT * FROM t WHERE id=2", 100), ("SELECT 1 FROM u", 150)], 1),  [['SELECT * FROM t WHERE id=?', 200]])],
  ("A loop over characters to normalise.", "O(total)", "O(s)"),
  ("A regular expression and a <code>Counter</code>.", "O(total)", "O(s)"),
  names=["queries", "k"])


@B
def top_shapes(queries, k):
    totals = {}
    for q, b in queries:
        shape = re.sub(r"\d+", "?", q)
        totals[shape] = totals.get(shape, 0) + b
    return sorted(([s, v] for s, v in totals.items()), key=lambda x: -x[1])[:k]


@O
def top_shapes(queries, k):
    from collections import Counter
    c = Counter()
    for q, b in queries:
        c[re.sub(r"\d+", "?", q)] += b
    return [[s, v] for s, v in c.most_common(k)]


Q(None, "Queue Wait", "Medium", "Concurrency limits",
  "Queries with durations start in order, with at most c at once. Return each query's wait.",
  [(([10, 10, 10, 5], 2),  [0, 0, 10, 10])],
  ("A list of free times.", "O(n·c)", "O(c)"),
  ("A heap.", "O(n log c)", "O(c)"),
  names=["durations", "c"])


@B
def queue_wait(durations, c):
    free = [0] * c
    out = []
    for d in durations:
        i = free.index(min(free))
        out.append(free[i])
        free[i] += d
    return out


@O
def queue_wait(durations, c):
    heap, out = [0] * c, []
    for d in durations:
        start = heapq.heappop(heap)
        out.append(start)
        heapq.heappush(heap, start + d)
    return out


Q(None, "One Definition of a Metric", "Medium", "The semantic layer",
  "Teams define revenue differently. Given definitions as filters on status, and rows (status, amount), return revenue per definition, and whether they all agree.",
  [(({"sales": ["paid", "shipped"], "finance": ["paid"]}, [("paid", 10), ("shipped", 5), ("failed", 2)]),  ({'sales': 15, 'finance': 10}, False))],
  ("Nested loops.", "O(d·r)", "O(d)"),
  ("A comprehension.", "O(d·r)", "O(d)"),
  names=["definitions", "rows"])


@B
def metric_versions(definitions, rows):
    out = {}
    for team, statuses in definitions.items():
        total = 0
        for s, a in rows:
            if s in statuses:
                total += a
        out[team] = total
    return (out, len(set(out.values())) == 1)


@O
def metric_versions(definitions, rows):
    out = {t: sum(a for s, a in rows if s in st) for t, st in definitions.items()}
    return (out, len(set(out.values())) == 1)


Q(None, "Generate dbt Tests", "Easy", "Tests from a config",
  "Given columns with tests, return the test names as 'test_column', sorted. dbt turns each into a SQL query that should return no rows.",
  [(({"id": ["unique", "not_null"], "status": ["accepted_values"]},), ['accepted_values_status', 'not_null_id', 'unique_id'])],
  ("Nested loops.", "O(t)", "O(t)"),
  ("A sorted comprehension.", "O(t log t)", "O(t)"))


@B
def test_names(config):
    out = []
    for col, tests in config.items():
        for t in tests:
            out.append(t + "_" + col)
    return sorted(out)


@O
def test_names(config):
    return sorted(f"{t}_{c}" for c, ts in config.items() for t in ts)
