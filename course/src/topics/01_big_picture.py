from lib import *
import csv
import io
import json
import math


TOPIC(
    id="big-picture", title="How Data Flows", glyph="→→→",
    blurb="What a data engineer actually does: the data lifecycle, ETL vs ELT, OLTP vs OLAP, batch vs streaming, and how to think about volume, freshness and reliability. No experience needed.",
    theory="""
<h3>Cheat sheet</h3>
<pre><code class="py">Sources → Ingest → Store → Transform → Serve → Users
ETL: transform, then load     ELT: load raw, then transform in the warehouse
OLTP: many small writes       OLAP: few huge reads
Batch: every hour or day      Streaming: within seconds</code></pre>
""")


Q(None, "Extract: Parse CSV Text", "Easy", "The E in ETL",
  "Turn CSV text with a header row into a list of dictionaries, with all values as strings.",
  [(("id,name\n1,Asha\n2,Ben\n",), [{'id': '1', 'name': 'Asha'}, {'id': '2', 'name': 'Ben'}])],
  ("Split lines and commas by hand. It breaks if a value contains a comma.", "O(n)", "O(n)"),
  ("<code>csv.DictReader</code> handles quotes and commas in values.", "O(n)", "O(n)"))


@B
def parse_csv(text):
    lines = text.strip().split("\n")
    header = lines[0].split(",")
    rows = []
    for line in lines[1:]:
        values = line.split(",")
        row = {}
        for name, value in zip(header, values):
            row[name] = value
        rows.append(row)
    return rows


@O
def parse_csv(text):
    return list(csv.DictReader(io.StringIO(text)))


Q(None, "Transform: Clean One Record", "Easy", "The T in ETL",
  "Given a record with name and amount as text: trim and title-case the name, and convert amount to a float. Return None if the amount isn't a number.",
  [(({"name": "  asha ", "amount": "12.50"},), {'name': 'Asha', 'amount': 12.5}), (({"name": "ben", "amount": "oops"},), None)],
  ("Check each character of the amount.", "O(n)", "O(n)"),
  ("<code>try/except ValueError</code> around <code>float()</code>.", "O(n)", "O(n)"))


@B
def clean_record(rec):
    text = rec["amount"]
    if not text or text.count(".") > 1 or not text.replace(".", "").isdigit():
        return None
    return {"name": rec["name"].strip().title(), "amount": float(text)}


@O
def clean_record(rec):
    try:
        return {"name": rec["name"].strip().title(), "amount": float(rec["amount"])}
    except ValueError:
        return None


Q(None, "Load: Good Rows and Bad Rows", "Easy", "Don't lose data silently",
  "Split amounts into good ones (parse as float) and bad ones (kept as they were, to investigate later). Return (good, bad).",
  [((["1.5", "x", "2", ""],), ([1.5, 2.0], ['x', '']))],
  ("A loop with try/except, appending to two lists.", "O(n)", "O(n)"),
  ("The same, with a small helper. A real pipeline writes bad rows to a dead-letter location.", "O(n)", "O(n)"))


@B
def split_rows(values):
    good, bad = [], []
    for v in values:
        try:
            good.append(float(v))
        except ValueError:
            bad.append(v)
    return (good, bad)


@O
def split_rows(values):
    def parse(v):
        try:
            return float(v)
        except ValueError:
            return None
    parsed = [(v, parse(v)) for v in values]
    return ([p for _, p in parsed if p is not None], [v for v, p in parsed if p is None])


Q(None, "A Tiny ETL Pipeline", "Medium", "All three steps together",
  "From CSV text with columns city and amount, keep valid rows and return total amount per city, with cities sorted.",
  [(("city,amount\nPune,10\nDelhi,5\nPune,x\nPune,2.5\n",), {'Delhi': 5.0, 'Pune': 12.5})],
  ("One long loop.", "O(n)", "O(c)"),
  ("Separate extract, transform and load steps, each testable alone.", "O(n)", "O(c)"))


@B
def tiny_etl(text):
    totals = {}
    for line in text.strip().split("\n")[1:]:
        city, amount = line.split(",")
        try:
            totals[city] = totals.get(city, 0) + float(amount)
        except ValueError:
            pass
    return dict(sorted(totals.items()))


@O
def tiny_etl(text):
    def extract(t):
        return csv.DictReader(io.StringIO(t))

    def transform(rows):
        for r in rows:
            try:
                yield r["city"], float(r["amount"])
            except ValueError:
                continue

    def load(pairs):
        out = {}
        for city, amount in pairs:
            out[city] = out.get(city, 0) + amount
        return dict(sorted(out.items()))
    return load(transform(extract(text)))


Q(None, "How Much Data per Day?", "Easy", "Thinking in volume",
  "Given events per second and bytes per event, return GB per day and TB per year (10⁹ and 10¹² bytes), rounded to 2 decimals.",
  [((1000, 500), (43.2, 15.77)), ((50000, 1000), (4320.0, 1576.8))],
  ("Multiply one step at a time.", "O(1)", "O(1)"),
  ("One formula for each.", "O(1)", "O(1)"),
  names=["eps", "size"])


@B
def daily_volume(eps, size):
    per_day = eps * 60 * 60 * 24
    bytes_day = per_day * size
    return (round(bytes_day / 1e9, 2), round(bytes_day * 365 / 1e12, 2))


@O
def daily_volume(eps, size):
    b = eps * size * 86400
    return (round(b / 1e9, 2), round(b * 365 / 1e12, 2))


Q(None, "How Long to Process It?", "Easy", "Will it finish in time?",
  "Given data size in GB and a speed in MB/s per worker, return the minutes to finish with n workers, assuming perfect scaling, rounded to 2 decimals.",
  [((100, 50, 1), 33.33), ((100, 50, 10), 3.33)],
  ("Convert units step by step.", "O(1)", "O(1)"),
  ("One line.", "O(1)", "O(1)"),
  names=["gb", "mb_per_s", "n"])


@B
def process_minutes(gb, mb_per_s, n):
    megabytes = gb * 1000
    seconds = megabytes / mb_per_s / n
    return round(seconds / 60, 2)


@O
def process_minutes(gb, mb_per_s, n):
    return round(gb * 1000 / (mb_per_s * n * 60), 2)


Q(None, "Row Store vs Column Store Cost", "Medium", "Why analytics uses columns",
  "A table has rows rows and cols equal-width columns of 8 bytes. A query reads use_cols columns. Return the MB read by a row store (all columns) and a column store (only those used), with MB = 10⁶ bytes.",
  [((1000000, 50, 2), (400.0, 16.0))],
  ("Compute the total, then the share.", "O(1)", "O(1)"),
  ("Two formulas.", "O(1)", "O(1)"),
  names=["rows", "cols", "use_cols"])


@B
def scan_cost(rows, cols, use_cols):
    row_size = cols * 8
    total = rows * row_size
    columns_only = rows * use_cols * 8
    return (total / 1e6, columns_only / 1e6)


@O
def scan_cost(rows, cols, use_cols):
    return (rows * cols * 8 / 1e6, rows * use_cols * 8 / 1e6)


Q(None, "Data Freshness", "Easy", "How old is the data?",
  "Given the current time and the latest loaded event time (seconds), return the lag in minutes rounded to 1 decimal, and whether it meets the SLA in minutes.",
  [((10000, 9400, 15), (10.0, True)), ((10000, 8000, 15), (33.3, False))],
  ("Subtract, convert, compare.", "O(1)", "O(1)"),
  ("Compact.", "O(1)", "O(1)"),
  names=["now", "latest", "sla"])


@B
def freshness(now, latest, sla):
    seconds = now - latest
    minutes = seconds / 60
    return (round(minutes, 1), minutes <= sla)


@O
def freshness(now, latest, sla):
    lag = (now - latest) / 60
    return (round(lag, 1), lag <= sla)


Q(None, "Batch Size vs Latency", "Easy", "The core trade-off",
  "If events arrive evenly and you process every w minutes, return the average and worst wait in minutes before an event is processed, ignoring run time.",
  [((60,), (30.0, 60)), ((1,), (0.5, 1))],
  ("Reason it through: the worst waits the full window, and the average half.", "O(1)", "O(1)"),
  ("A one-liner.", "O(1)", "O(1)"),
  names=["w"])


@B
def batch_wait(w):
    worst = w
    average = w / 2
    return (average, worst)


@O
def batch_wait(w):
    return (w / 2, w)


Q(None, "Flatten a JSON Event", "Medium", "Nested to tabular",
  "Flatten nested dictionaries, joining keys with a dot. Lists stay as they are.",
  [(({"id": 1, "user": {"name": "A", "geo": {"city": "Pune"}}, "tags": [1]},), {'id': 1, 'tags': [1], 'user.geo.city': 'Pune', 'user.name': 'A'})],
  ("An explicit stack of (prefix, dict).", "O(n)", "O(d)"),
  ("Recursion: a nested dict contributes its flattened keys.", "O(n)", "O(d)"))


@B
def flatten_event(event):
    out = {}
    stack = [("", event)]
    order = []
    while stack:
        prefix, d = stack.pop()
        for k, v in d.items():
            name = prefix + k
            if isinstance(v, dict):
                stack.append((name + ".", v))
            else:
                out[name] = v
    return dict(sorted(out.items()))


@O
def flatten_event(event, prefix=""):
    out = {}
    for k, v in event.items():
        if isinstance(v, dict):
            out.update(flatten_event(v, prefix + k + "."))
        else:
            out[prefix + k] = v
    return dict(sorted(out.items()))


Q(None, "Parse JSON Lines", "Easy", "The standard log format",
  "Text has one JSON object per line. Return (parsed objects, count of invalid lines).",
  [(('{"a": 1}\nnot json\n{"a": 2}\n',), ([{'a': 1}, {'a': 2}], 1))],
  ("A loop with try/except.", "O(n)", "O(n)"),
  ("A helper, so each line is handled the same.", "O(n)", "O(n)"))


@B
def parse_jsonl(text):
    good, bad = [], 0
    for line in text.strip().split("\n"):
        try:
            good.append(json.loads(line))
        except json.JSONDecodeError:
            bad += 1
    return (good, bad)


@O
def parse_jsonl(text):
    def load(line):
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            return None
    parsed = [load(l) for l in text.splitlines() if l.strip()]
    return ([p for p in parsed if p is not None], parsed.count(None))


Q(None, "Remove Exact Duplicates", "Easy", "Sources send things twice",
  "Keep the first copy of each id, preserving order.",
  [(([{"id": 1, "v": "a"}, {"id": 2, "v": "b"}, {"id": 1, "v": "a"}],), [{'id': 1, 'v': 'a'}, {'id': 2, 'v': 'b'}])],
  ("Compare against every kept row.", "O(n²)", "O(n)"),
  ("A set of seen ids.", "O(n)", "O(n)"))


@B
def dedupe_rows(rows):
    kept = []
    for r in rows:
        if not any(k["id"] == r["id"] for k in kept):
            kept.append(r)
    return kept


@O
def dedupe_rows(rows):
    seen, kept = set(), []
    for r in rows:
        if r["id"] not in seen:
            seen.add(r["id"])
            kept.append(r)
    return kept


Q(None, "Which Tool for the Job?", "Easy", "Latency decides",
  "Return 'streaming' if latency needed is under 60 seconds, 'micro-batch' under 15 minutes, otherwise 'batch'. Latencies are in seconds.",
  [(([5, 300, 3600],),  ['streaming', 'micro-batch', 'batch'])],
  ("Ifs in a loop.", "O(n)", "O(n)"),
  ("A helper in a comprehension.", "O(n)", "O(n)"),
  names=["latencies"])


@B
def choose_mode(latencies):
    out = []
    for s in latencies:
        if s < 60:
            out.append("streaming")
        elif s < 900:
            out.append("micro-batch")
        else:
            out.append("batch")
    return out


@O
def choose_mode(latencies):
    return ["streaming" if s < 60 else "micro-batch" if s < 900 else "batch" for s in latencies]


Q(None, "Pipeline Reliability", "Medium", "Chains multiply failures",
  "If a pipeline has steps each succeeding with probability p, return the chance a daily run succeeds, and expected failures per year, rounded to 4 and 1 decimals.",
  [((0.99, 10), (0.9044, 34.9)), ((0.999, 10), (0.99, 3.6))],
  ("Multiply in a loop.", "O(n)", "O(1)"),
  ("A power.", "O(1)", "O(1)"),
  names=["p", "steps"])


@B
def run_success(p, steps):
    chance = 1.0
    for _ in range(steps):
        chance *= p
    return (round(chance, 4), round((1 - chance) * 365, 1))


@O
def run_success(p, steps):
    return (round(p ** steps, 4), round((1 - p ** steps) * 365, 1))


Q(None, "Storage Cost", "Easy", "Everything costs money",
  "Given GB per day, days kept and a made-up monthly price per GB, return stored GB and monthly cost at steady state, rounded to 2 decimals.",
  [((500, 90, 0.02),  (45000, 900.0))],
  ("Stored data, then cost.", "O(1)", "O(1)"),
  ("One line.", "O(1)", "O(1)"),
  names=["gb_day", "days", "price"])


@B
def storage_cost(gb_day, days, price):
    stored = gb_day * days
    cost = stored * price
    return (stored, round(cost, 2))


@O
def storage_cost(gb_day, days, price):
    return (gb_day * days, round(gb_day * days * price, 2))


Q(None, "Compression Savings", "Easy", "Why formats matter",
  "Given raw GB and a compression ratio (raw ÷ compressed), return compressed GB and the percent saved, rounded to 1 decimal.",
  [((1000, 4), (250.0, 75.0)), ((1000, 1.25), (800.0, 20.0))],
  ("Divide, then work out the share.", "O(1)", "O(1)"),
  ("Percent saved is simply 1 − 1/ratio.", "O(1)", "O(1)"),
  names=["raw", "ratio"])


@B
def compression(raw, ratio):
    compressed = raw / ratio
    saved = raw - compressed
    return (round(compressed, 1), round(saved / raw * 100, 1))


@O
def compression(raw, ratio):
    return (round(raw / ratio, 1), round((1 - 1 / ratio) * 100, 1))


Q(None, "Peak vs Average Load", "Easy", "Design for the peak",
  "Given hourly event counts for a day, return average per hour, peak, and the peak-to-average ratio, rounded to 2 decimals.",
  [(([100, 100, 400, 200],),  (200.0, 400, 2.0))],
  ("A loop tracking total and max.", "O(n)", "O(1)"),
  ("Built-ins.", "O(n)", "O(1)"))


@B
def peak_ratio(counts):
    total, peak = 0, counts[0]
    for c in counts:
        total += c
        if c > peak:
            peak = c
    avg = total / len(counts)
    return (round(avg, 2), peak, round(peak / avg, 2))


@O
def peak_ratio(counts):
    avg = sum(counts) / len(counts)
    return (round(avg, 2), max(counts), round(max(counts) / avg, 2))


Q(None, "Lineage: What Breaks Downstream?", "Medium", "Who depends on what",
  "deps maps each table to tables built from it. Return every table affected if table t fails, sorted.",
  [(({"raw": ["clean"], "clean": ["daily", "users"], "daily": ["dashboard"]}, "clean"), ['daily', 'dashboard', 'users'])],
  ("Repeat scanning until nothing new appears.", "O(V·E)", "O(V)"),
  ("Depth-first search with a visited set.", "O(V + E)", "O(V)"),
  names=["deps", "t"])


@B
def downstream(deps, t):
    found = set()
    frontier = [t]
    while frontier:
        new = []
        for x in frontier:
            for y in deps.get(x, []):
                if y not in found:
                    found.add(y)
                    new.append(y)
        frontier = new
    return sorted(found)


@O
def downstream(deps, t):
    seen = set()

    def visit(x):
        for y in deps.get(x, []):
            if y not in seen:
                seen.add(y)
                visit(y)
    visit(t)
    return sorted(seen)


Q(None, "Daily Partition Path", "Easy", "How lakes are organised",
  "Given a table name and date 'YYYY-MM-DD', return its partition path like 'lake/orders/year=2026/month=01/day=05/'.",
  [(("orders", "2026-01-05"), 'lake/orders/year=2026/month=01/day=05/')],
  ("Slice the string.", "O(1)", "O(1)"),
  ("<code>split</code> and an f-string.", "O(1)", "O(1)"),
  names=["table", "date"])


@B
def partition_path(table, date):
    year = date[0:4]
    month = date[5:7]
    day = date[8:10]
    return "lake/" + table + "/year=" + year + "/month=" + month + "/day=" + day + "/"


@O
def partition_path(table, date):
    y, m, d = date.split("-")
    return f"lake/{table}/year={y}/month={m}/day={d}/"


Q(None, "Schema Check on Arrival", "Medium", "Catch changes early",
  "Compare an expected column list with incoming columns. Return (missing, unexpected), each sorted.",
  [((["id", "name", "amount"], ["id", "amount", "currency"]), (['name'], ['currency']))],
  ("Two loops with <code>in</code>.", "O(n·m)", "O(n)"),
  ("Set differences.", "O(n + m)", "O(n)"),
  names=["expected", "incoming"])


@B
def schema_diff(expected, incoming):
    missing = sorted(c for c in expected if c not in incoming)
    extra = sorted(c for c in incoming if c not in expected)
    return (missing, extra)


@O
def schema_diff(expected, incoming):
    e, i = set(expected), set(incoming)
    return (sorted(e - i), sorted(i - e))
