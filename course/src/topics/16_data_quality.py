from lib import *
import math
import statistics


TOPIC(
    id="data-quality", title="Data Quality & Observability", glyph="✓",
    blurb="Trustworthy data: the dimensions of quality, tests for nulls, uniqueness, ranges and freshness, anomaly detection, reconciliation, data contracts, lineage and running incidents. This is where a QA background becomes a superpower.",
    theory="""
<h3>Cheat sheet</h3>
<pre><code class="py">Completeness: not null        Uniqueness: no duplicate keys
Validity: in range, in a set  Consistency: tables agree
Timeliness: fresh enough      Accuracy: matches reality
Volume check: rows today vs recent days
Contract: an agreed schema and guarantees from the source team</code></pre>
""")


Q(None, "Null Rate per Column", "Easy", "Completeness",
  "Return the share of None per column, rounded to 4 decimals, sorted by column.",
  [(([{"a": 1, "b": None}, {"a": None, "b": None}],),  {'a': 0.5, 'b': 1.0})],
  ("Nested loops.", "O(n·c)", "O(c)"),
  ("A comprehension per column.", "O(n·c)", "O(c)"))


@B
def null_rates(rows):
    counts = {}
    for r in rows:
        for k, v in r.items():
            counts[k] = counts.get(k, 0) + (1 if v is None else 0)
    return {k: round(counts[k] / len(rows), 4) for k in sorted(counts)}


@O
def null_rates(rows):
    return {c: round(sum(r[c] is None for r in rows) / len(rows), 4) for c in sorted(rows[0])}


Q(None, "Uniqueness Check", "Easy", "Primary keys",
  "Return (is unique, duplicate key values sorted).",
  [(([1, 2, 2, 3, 3, 3],), (False, [2, 3])), (([1, 2],), (True, []))],
  ("Count with a dictionary.", "O(n)", "O(n)"),
  ("<code>Counter</code>.", "O(n log n)", "O(n)"))


@B
def uniqueness(keys):
    counts = {}
    for k in keys:
        counts[k] = counts.get(k, 0) + 1
    dupes = sorted(k for k, c in counts.items() if c > 1)
    return (not dupes, dupes)


@O
def uniqueness(keys):
    from collections import Counter
    d = sorted(k for k, c in Counter(keys).items() if c > 1)
    return (not d, d)


Q(None, "Accepted Values", "Easy", "Validity",
  "Return values not in the allowed set, with their counts, sorted by value. None is ignored.",
  [((["paid", "PAID", "paid", None, "lost"], ["paid", "refunded"]),  {'PAID': 1, 'lost': 1})],
  ("A dictionary and a loop.", "O(n)", "O(d)"),
  ("<code>Counter</code>.", "O(n)", "O(d)"),
  names=["values", "allowed"])


@B
def bad_values(values, allowed):
    out = {}
    for v in values:
        if v is not None and v not in allowed:
            out[v] = out.get(v, 0) + 1
    return dict(sorted(out.items()))


@O
def bad_values(values, allowed):
    from collections import Counter
    ok = set(allowed) | {None}
    return dict(sorted(Counter(v for v in values if v not in ok).items()))


Q(None, "Range Check", "Easy", "Impossible values",
  "Return indexes of values outside [lo, hi].",
  [(([5, -1, 200, 50], 0, 120),  [1, 2])],
  ("A loop.", "O(n)", "O(m)"),
  ("A comprehension.", "O(n)", "O(m)"),
  names=["values", "lo", "hi"])


@B
def out_of_range(values, lo, hi):
    out = []
    for i, v in enumerate(values):
        if v < lo or v > hi:
            out.append(i)
    return out


@O
def out_of_range(values, lo, hi):
    return [i for i, v in enumerate(values) if not lo <= v <= hi]


Q(None, "Referential Integrity", "Easy", "Do the keys exist?",
  "Return the share of foreign keys without a match, rounded to 4 decimals, plus the unmatched values sorted.",
  [(([1, 2, 9, 9], [1, 2, 3]),  (0.5, [9]))],
  ("Check a list for each key.", "O(n·m)", "O(1)"),
  ("A set.", "O(n + m)", "O(m)"),
  names=["fks", "pks"])


@B
def ref_integrity(fks, pks):
    missing = []
    for k in fks:
        if k not in pks:
            missing.append(k)
    return (round(len(missing) / len(fks), 4), sorted(set(missing)))


@O
def ref_integrity(fks, pks):
    known = set(pks)
    bad = [k for k in fks if k not in known]
    return (round(len(bad) / len(fks), 4), sorted(set(bad)))


Q(None, "Volume Anomaly", "Medium", "Is today's row count normal?",
  "Flag today's count if it's beyond 3 standard deviations from the recent mean. Return (flagged, z score rounded to 2 decimals). Use sample standard deviation.",
  [(([100, 102, 98, 101, 99], 50), (True, -31.62)), (([100, 102, 98, 101, 99], 103), (False, 1.9))],
  ("Compute mean and deviation by hand.", "O(n)", "O(1)"),
  ("The <code>statistics</code> module.", "O(n)", "O(1)"),
  names=["history", "today"])


@B
def volume_check(history, today):
    mean = sum(history) / len(history)
    var = sum((x - mean) ** 2 for x in history) / (len(history) - 1)
    z = (today - mean) / math.sqrt(var)
    return (abs(z) > 3, round(z, 2))


@O
def volume_check(history, today):
    z = (today - statistics.mean(history)) / statistics.stdev(history)
    return (abs(z) > 3, round(z, 2))


Q(None, "Weekly Seasonality", "Medium", "Don't alert every Sunday",
  "Compare today to the same weekday's past counts instead. Given history (oldest first, daily) and today, return the expected value as the mean of the same weekday in prior weeks, and percent difference, rounded to 1 decimal.",
  [(([100, 100, 100, 100, 100, 20, 20, 100, 100, 100, 100, 100, 20, 20], 21), (100.0, -79.0))],
  ("A loop stepping back 7 days.", "O(n/7)", "O(1)"),
  ("Slicing with a step.", "O(n/7)", "O(n/7)"),
  names=["history", "today"])


@B
def seasonal(history, today):
    values, i = [], len(history) - 7
    while i >= 0:
        values.append(history[i])
        i -= 7
    expected = sum(values) / len(values)
    return (expected, round(100 * (today - expected) / expected, 1))


@O
def seasonal(history, today):
    same = history[-7::-7]
    expected = sum(same) / len(same)
    return (expected, round(100 * (today - expected) / expected, 1))


Q(None, "Distribution Drift", "Medium", "PSI",
  "Compare two distributions over bins: PSI = Σ (a − e)·ln(a/e), adding 0.001 to avoid zero. Return PSI rounded to 4 decimals, and 'stable' under 0.1, 'watch' under 0.25, otherwise 'drift'.",
  [(([0.5, 0.5], [0.5, 0.5]), (0.0, 'stable')), (([0.8, 0.2], [0.2, 0.8]), (1.6591, 'drift'))],
  ("A loop.", "O(b)", "O(1)"),
  ("A generator.", "O(b)", "O(1)"),
  names=["expected", "actual"])


@B
def psi(expected, actual):
    total = 0.0
    for e, a in zip(expected, actual):
        e, a = e + 0.001, a + 0.001
        total += (a - e) * math.log(a / e)
    verdict = "stable"
    if total >= 0.25:
        verdict = "drift"
    elif total >= 0.1:
        verdict = "watch"
    return (round(total, 4), verdict)


@O
def psi(expected, actual):
    p = sum((a - e) * math.log((a + 0.001) / (e + 0.001)) for e, a in zip(expected, actual))
    return (round(p, 4), "stable" if p < 0.1 else "watch" if p < 0.25 else "drift")


Q(None, "Freshness per Table", "Easy", "SLA dashboards",
  "Given tables' last load time, an SLA in minutes and now, return stale tables with minutes late, sorted by name.",
  [(({"a": 100, "b": 40}, 30, 120),  [['b', 50]])],
  ("A loop.", "O(t log t)", "O(t)"),
  ("A sorted comprehension.", "O(t log t)", "O(t)"),
  names=["last", "sla", "now"])


@B
def stale_tables(last, sla, now):
    out = []
    for t in sorted(last):
        age = now - last[t]
        if age > sla:
            out.append([t, age - sla])
    return out


@O
def stale_tables(last, sla, now):
    return [[t, now - v - sla] for t, v in sorted(last.items()) if now - v > sla]


Q(None, "A Small Test Framework", "Medium", "How dbt tests work",
  "Run named checks on rows: not_null(col), unique(col). Tests are (name, col). Return failing test descriptions, such as 'not_null(id)', sorted.",
  [(([{"id": 1, "e": None}, {"id": 1, "e": "x"}], [("not_null", "id"), ("not_null", "e"), ("unique", "id"), ("unique", "e")]),  ['not_null(e)', 'unique(id)'])],
  ("Ifs in a loop.", "O(t·n)", "O(n)"),
  ("A dictionary of test functions.", "O(t·n)", "O(n)"),
  names=["rows", "tests"])


@B
def run_checks(rows, tests):
    failed = []
    for name, col in tests:
        values = [r[col] for r in rows]
        if name == "not_null" and None in values:
            failed.append(f"{name}({col})")
        if name == "unique" and len(set(values)) != len(values):
            failed.append(f"{name}({col})")
    return sorted(failed)


@O
def run_checks(rows, tests):
    checks = {"not_null": lambda v: None not in v, "unique": lambda v: len(set(v)) == len(v)}
    return sorted(f"{n}({c})" for n, c in tests if not checks[n]([r[c] for r in rows]))


Q(None, "Severity: Warn or Stop?", "Medium", "Not all failures are equal",
  "Each check has (name, failure_rate, warn_limit, error_limit). Return (status: 'pass', 'warn' or 'error' for the worst, names at error sorted).",
  [(([("nulls", 0.02, 0.01, 0.1), ("dupes", 0.0, 0.0, 0.01)],), ('warn', [])), (([("nulls", 0.5, 0.01, 0.1)],), ('error', ['nulls']))],
  ("Loop with flags.", "O(c)", "O(c)"),
  ("Comprehensions.", "O(c)", "O(c)"))


@B
def severity(checks):
    errors, warned = [], False
    for name, rate, warn, err in checks:
        if rate > err:
            errors.append(name)
        elif rate > warn:
            warned = True
    status = "error" if errors else "warn" if warned else "pass"
    return (status, sorted(errors))


@O
def severity(checks):
    errors = sorted(n for n, r, _, e in checks if r > e)
    warned = any(r > w for _, r, w, _ in checks)
    return ("error" if errors else "warn" if warned else "pass", errors)


Q(None, "Quarantine Bad Rows", "Medium", "Don't block the good ones",
  "Split rows into good and quarantined, with reasons. Rules: id not None, amount ≥ 0. Return (good ids, [id, reasons]).",
  [(([{"id": 1, "amount": 5}, {"id": None, "amount": -1}, {"id": 3, "amount": -2}],),  ([1], [[None, ['null_id', 'negative']], [3, ['negative']]]))],
  ("Ifs.", "O(n)", "O(n)"),
  ("A rule table.", "O(n·r)", "O(n)"))


@B
def quarantine(rows):
    good, bad = [], []
    for r in rows:
        reasons = []
        if r["id"] is None:
            reasons.append("null_id")
        if r["amount"] < 0:
            reasons.append("negative")
        if reasons:
            bad.append([r["id"], reasons])
        else:
            good.append(r["id"])
    return (good, bad)


@O
def quarantine(rows):
    rules = {"null_id": lambda r: r["id"] is None, "negative": lambda r: r["amount"] < 0}
    checked = [(r, [n for n, bad in rules.items() if bad(r)]) for r in rows]
    return ([r["id"] for r, why in checked if not why], [[r["id"], why] for r, why in checked if why])


Q(None, "Reconcile Totals", "Easy", "Do the sums agree?",
  "Return whether two totals match within a relative tolerance, and the percent difference rounded to 2 decimals.",
  [((1000, 1001, 0.01), (True, 0.1)), ((1000, 900, 0.01), (False, 10.0))],
  ("Step by step.", "O(1)", "O(1)"),
  ("Compact.", "O(1)", "O(1)"),
  names=["source", "target", "tol"])


@B
def reconcile_totals(source, target, tol):
    diff = abs(source - target) / source
    return (diff <= tol, round(diff * 100, 2))


@O
def reconcile_totals(source, target, tol):
    d = abs(source - target) / source
    return (d <= tol, round(d * 100, 2))


Q(None, "Check a Data Contract", "Medium", "Promises between teams",
  "A contract lists columns with type and nullable. Given a sample row, return violations, sorted: 'missing:x', 'type:x', 'null:x'.",
  [(({"id": ("int", False), "name": ("str", True), "age": ("int", False)}, {"id": "7", "name": None, "age": None}),  ['null:age', 'type:id'])],
  ("Ifs.", "O(c)", "O(c)"),
  ("A dictionary of types.", "O(c log c)", "O(c)"),
  names=["contract", "row"])


@B
def contract_violations(contract, row):
    out = []
    for col, (kind, nullable) in contract.items():
        if col not in row:
            out.append("missing:" + col)
        elif row[col] is None:
            if not nullable:
                out.append("null:" + col)
        elif (kind == "int" and not isinstance(row[col], int)) or (kind == "str" and not isinstance(row[col], str)):
            out.append("type:" + col)
    return sorted(out)


@O
def contract_violations(contract, row):
    types = {"int": int, "str": str}
    out = []
    for col, (kind, nullable) in contract.items():
        if col not in row:
            out.append(f"missing:{col}")
        elif row[col] is None and not nullable:
            out.append(f"null:{col}")
        elif row[col] is not None and not isinstance(row[col], types[kind]):
            out.append(f"type:{col}")
    return sorted(out)


Q(None, "Impact Analysis", "Medium", "Who's affected?",
  "lineage maps a table to its direct consumers. consumers_of maps a table to teams. Return teams affected if a table is broken, sorted.",
  [(({"a": ["b", "c"], "b": ["d"]}, {"d": ["finance"], "c": ["growth"], "a": []}, "a"),  ['finance', 'growth'])],
  ("Repeat until no change.", "O(V·E)", "O(V)"),
  ("A graph search.", "O(V + E)", "O(V)"),
  names=["lineage", "owners", "table"])


@B
def impacted(lineage, owners, table):
    found = {table}
    changed = True
    while changed:
        changed = False
        for t in list(found):
            for c in lineage.get(t, []):
                if c not in found:
                    found.add(c)
                    changed = True
    teams = set()
    for t in found:
        teams |= set(owners.get(t, []))
    return sorted(teams)


@O
def impacted(lineage, owners, table):
    seen, stack = set(), [table]
    while stack:
        t = stack.pop()
        if t not in seen:
            seen.add(t)
            stack += lineage.get(t, [])
    return sorted({team for t in seen for team in owners.get(t, [])})


Q(None, "Find Where Rows Were Lost", "Medium", "Debug by layer",
  "Given counts by pipeline step in order, return the step with the biggest drop, and the drop percentage, rounded to 1 decimal.",
  [(([("raw", 1000), ("clean", 990), ("joined", 400), ("final", 395)],),  ('joined', 59.6))],
  ("Compare neighbours in a loop.", "O(n)", "O(1)"),
  ("<code>max</code> over pairs.", "O(n)", "O(n)"))


@B
def biggest_drop(steps):
    best, drop = None, -1.0
    for i in range(1, len(steps)):
        d = (steps[i - 1][1] - steps[i][1]) / steps[i - 1][1]
        if d > drop:
            best, drop = steps[i][0], d
    return (best, round(drop * 100, 1))


@O
def biggest_drop(steps):
    name, d = max(((b[0], (a[1] - b[1]) / a[1]) for a, b in zip(steps, steps[1:])), key=lambda x: x[1])
    return (name, round(d * 100, 1))


Q(None, "Alert Fatigue", "Easy", "Measure your alerts",
  "Given (alert, was_real) records, return precision per alert name, rounded to 2 decimals, sorted. Noisy alerts get ignored, so fix or remove them.",
  [(([("vol", True), ("vol", False), ("null", False), ("null", False)],),  {'null': 0.0, 'vol': 0.5})],
  ("Two dictionaries.", "O(n)", "O(a)"),
  ("A grouped comprehension.", "O(n)", "O(a)"))


@B
def alert_precision(records):
    real, total = {}, {}
    for name, ok in records:
        total[name] = total.get(name, 0) + 1
        real[name] = real.get(name, 0) + (1 if ok else 0)
    return {n: round(real[n] / total[n], 2) for n in sorted(total)}


@O
def alert_precision(records):
    from collections import defaultdict
    groups = defaultdict(list)
    for name, ok in records:
        groups[name].append(ok)
    return {n: round(sum(v) / len(v), 2) for n, v in sorted(groups.items())}


Q(None, "Incident Metrics", "Easy", "Learn from failures",
  "Given incidents as (started, detected, resolved) minutes, return mean time to detect and to resolve, rounded to 1 decimal.",
  [(([(0, 30, 90), (100, 110, 150)],),  (20, 70))],
  ("A loop.", "O(n)", "O(1)"),
  ("Generators.", "O(n)", "O(1)"))


@B
def incident_metrics(incidents):
    detect = resolve = 0
    for s, d, r in incidents:
        detect += d - s
        resolve += r - s
    n = len(incidents)
    return (round(detect / n, 1), round(resolve / n, 1))


@O
def incident_metrics(incidents):
    return (round(statistics.mean(d - s for s, d, _ in incidents), 1), round(statistics.mean(r - s for s, _, r in incidents), 1))


Q(None, "Compare Two Versions of a Table", "Medium", "Test your change safely",
  "Compare old and new tables keyed by id: return (only in old, only in new, changed), all sorted. Do this before releasing a logic change.",
  [(({1: "a", 2: "b", 3: "c"}, {2: "b", 3: "C", 4: "d"}),  ([1], [4], [3]))],
  ("Loops.", "O(n)", "O(n)"),
  ("Dictionary views.", "O(n log n)", "O(n)"),
  names=["old", "new"])


@B
def table_diff(old, new):
    only_old, only_new, changed = [], [], []
    for k in old:
        if k not in new:
            only_old.append(k)
        elif old[k] != new[k]:
            changed.append(k)
    for k in new:
        if k not in old:
            only_new.append(k)
    return (sorted(only_old), sorted(only_new), sorted(changed))


@O
def table_diff(old, new):
    return (sorted(old.keys() - new.keys()), sorted(new.keys() - old.keys()), sorted(k for k in old.keys() & new.keys() if old[k] != new[k]))


Q(None, "Profile a Column", "Easy", "Know your data first",
  "Return (count, nulls, distinct non-null values, min, max) for a list of numbers with None.",
  [(([1, None, 3, 3],), (4, 1, 2, 1, 3))],
  ("A loop tracking everything.", "O(n)", "O(d)"),
  ("Filter out None, then use built-ins.", "O(n)", "O(d)"))


@B
def profile(values):
    nulls, seen, low, high = 0, [], None, None
    for v in values:
        if v is None:
            nulls += 1
            continue
        if v not in seen:
            seen.append(v)
        low = v if low is None or v < low else low
        high = v if high is None or v > high else high
    return (len(values), nulls, len(seen), low, high)


@O
def profile(values):
    known = [v for v in values if v is not None]
    return (len(values), len(values) - len(known), len(set(known)), min(known), max(known))
