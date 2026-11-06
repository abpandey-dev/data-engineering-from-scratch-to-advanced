from lib import *
import math


TOPIC(
    id="system-design", title="Data System Design", glyph="▣",
    blurb="How senior engineers think: a repeatable design framework, sizing, choosing tools and walkthroughs of clickstream analytics, CDC to a lake, real-time dashboards and data platforms, with the trade-offs interviewers want to hear.",
    theory="""
<h3>The framework</h3>
<ol><li><b>Requirements:</b> who uses it, what questions, how fresh, how correct?</li>
<li><b>Size it:</b> events per second, GB per day, retention, peak.</li>
<li><b>Data model:</b> grain, keys, partitions.</li>
<li><b>Architecture:</b> ingest, store, process, serve.</li>
<li><b>Failure:</b> reruns, late data, duplicates, bad data.</li>
<li><b>Operate:</b> monitoring, cost, security, growth.</li></ol>
""")


Q(None, "Size the Ingest", "Easy", "Start with numbers",
  "From daily users and events per user, return (average events per second, peak at the multiple, GB per day at size bytes), rounded to 1 decimal.",
  [((10000000, 50, 3, 1000), (5787.0, 17361.1, 500.0))],
  ("Step by step.", "O(1)", "O(1)"),
  ("Compact.", "O(1)", "O(1)"),
  names=["users", "per_user", "peak", "size"])


@B
def size_ingest(users, per_user, peak, size):
    per_day = users * per_user
    avg = per_day / 86400
    gb = per_day * size / 1e9
    return (round(avg, 1), round(avg * peak, 1), round(gb, 1))


@O
def size_ingest(users, per_user, peak, size):
    d = users * per_user
    return (round(d / 86400, 1), round(d / 86400 * peak, 1), round(d * size / 1e9, 1))


Q(None, "Storage Over Time", "Easy", "Layers and retention",
  "Given raw GB per day, Parquet compression ratio and retention days for raw and clean, return TB for each, rounded to 2 decimals.",
  [((500, 5, 30, 365),  (15.0, 36.5))],
  ("Step by step.", "O(1)", "O(1)"),
  ("Compact.", "O(1)", "O(1)"),
  names=["gb_day", "ratio", "raw_days", "clean_days"])


@B
def storage_plan(gb_day, ratio, raw_days, clean_days):
    raw = gb_day * raw_days / 1000
    clean = gb_day / ratio * clean_days / 1000
    return (round(raw, 2), round(clean, 2))


@O
def storage_plan(gb_day, ratio, raw_days, clean_days):
    return (round(gb_day * raw_days / 1e3, 2), round(gb_day * clean_days / ratio / 1e3, 2))


Q(None, "Kafka Partitions for the Peak", "Easy", "Handle bursts",
  "Given peak events per second, event bytes and MB/s per partition, return partitions, rounded up, with a headroom multiple.",
  [((17000, 1000, 10, 2),  4)],
  ("Step by step.", "O(1)", "O(1)"),
  ("Compact.", "O(1)", "O(1)"),
  names=["peak_eps", "size", "mb_each", "headroom"])


@B
def kafka_partitions(peak_eps, size, mb_each, headroom):
    mb = peak_eps * size / 1e6
    need = mb * headroom / mb_each
    return math.ceil(need)


@O
def kafka_partitions(peak_eps, size, mb_each, headroom):
    return math.ceil(peak_eps * size * headroom / 1e6 / mb_each)


Q(None, "Will the Batch Finish in Time?", "Medium", "Check the window",
  "A job must process gb within window hours. With MB/s per core and an efficiency share, return cores needed, rounded up.",
  [((5000, 2, 20, 0.7),  50)],
  ("Convert units step by step.", "O(1)", "O(1)"),
  ("One formula.", "O(1)", "O(1)"),
  names=["gb", "window", "mb_core", "efficiency"])


@B
def cores_needed(gb, window, mb_core, efficiency):
    mb = gb * 1000
    seconds = window * 3600
    rate = mb / seconds
    return math.ceil(rate / (mb_core * efficiency))


@O
def cores_needed(gb, window, mb_core, efficiency):
    return math.ceil(gb * 1000 / (window * 3600) / (mb_core * efficiency))


Q(None, "Batch, Micro-Batch or Streaming?", "Easy", "Match the need",
  "Given freshness needed in seconds: under 10 is 'streaming', up to 900 'micro-batch', otherwise 'batch'. Also return the design's rough complexity, 3, 2 or 1.",
  [((5,), ('streaming', 3)), ((300,), ('micro-batch', 2)), ((86400,), ('batch', 1))],
  ("Ifs.", "O(1)", "O(1)"),
  ("Conditional expression.", "O(1)", "O(1)"))


@B
def processing_mode(seconds):
    if seconds < 10:
        return ("streaming", 3)
    if seconds <= 900:
        return ("micro-batch", 2)
    return ("batch", 1)


@O
def processing_mode(seconds):
    return ("streaming", 3) if seconds < 10 else ("micro-batch", 2) if seconds <= 900 else ("batch", 1)


Q(None, "Pick a Serving Store", "Medium", "It depends on the query",
  "Given latency in ms and whether queries are by key: key lookups under 50 ms → 'key-value store'; aggregates under 1000 ms → 'real-time OLAP'; otherwise 'warehouse'.",
  [((10, True), 'key-value store'), ((500, False), 'real-time OLAP'), ((30000, False), 'warehouse')],
  ("Ifs.", "O(1)", "O(1)"),
  ("Conditional expression.", "O(1)", "O(1)"),
  names=["latency_ms", "by_key"])


@B
def serving_store(latency_ms, by_key):
    if by_key and latency_ms < 50:
        return "key-value store"
    if latency_ms < 1000:
        return "real-time OLAP"
    return "warehouse"


@O
def serving_store(latency_ms, by_key):
    return "key-value store" if by_key and latency_ms < 50 else "real-time OLAP" if latency_ms < 1000 else "warehouse"


Q(None, "End-to-End Latency Budget", "Easy", "Add up the hops",
  "Given stage latencies in seconds, return the total, whether it meets the target, and the largest stage.",
  [(({"ingest": 2, "process": 30, "load": 10, "query": 1}, 60),  (43, True, 'process'))],
  ("A loop.", "O(s)", "O(1)"),
  ("Built-ins.", "O(s)", "O(1)"),
  names=["stages", "target"])


@B
def latency_budget(stages, target):
    total, big = 0, None
    for name, s in stages.items():
        total += s
        if big is None or s > stages[big]:
            big = name
    return (total, total <= target, big)


@O
def latency_budget(stages, target):
    t = sum(stages.values())
    return (t, t <= target, max(stages, key=stages.get))


Q(None, "Clickstream: Bot Filter", "Medium", "Clean before counting",
  "Drop users with more than limit events in the data. Return (kept events, bots sorted).",
  [(([("a", 1), ("b", 1), ("b", 2), ("b", 3), ("c", 1)], 2),  ([('a', 1), ('c', 1)], ['b']))],
  ("A dictionary, then filter.", "O(n)", "O(u)"),
  ("<code>Counter</code>.", "O(n)", "O(u)"),
  names=["events", "limit"])


@B
def bot_filter(events, limit):
    counts = {}
    for u, _ in events:
        counts[u] = counts.get(u, 0) + 1
    bots = sorted(u for u, c in counts.items() if c > limit)
    return ([e for e in events if e[0] not in bots], bots)


@O
def bot_filter(events, limit):
    from collections import Counter
    c = Counter(u for u, _ in events)
    bots = {u for u, n in c.items() if n > limit}
    return ([e for e in events if e[0] not in bots], sorted(bots))


Q(None, "Daily Active Users From Events", "Easy", "A core metric",
  "Given (day, user) events, return distinct users per day, sorted. Reprocessing should give the same answer, however many duplicates.",
  [(([("d1", "a"), ("d1", "a"), ("d1", "b"), ("d2", "a")],),  {'d1': 2, 'd2': 1})],
  ("A dictionary of sets.", "O(n)", "O(n)"),
  ("Set of pairs, then count.", "O(n)", "O(n)"))


@B
def dau(events):
    days = {}
    for day, user in events:
        days.setdefault(day, set()).add(user)
    return {d: len(days[d]) for d in sorted(days)}


@O
def dau(events):
    from collections import Counter
    return dict(sorted(Counter(d for d, _ in set(events)).items()))


Q(None, "CDC Into a Lake: Plan the Merge", "Medium", "Compact, then merge",
  "Given a target, and CDC events (seq, op, id, value) possibly out of order, keep the highest seq per id, then apply. Return the target sorted.",
  [(({1: "a"}, [(2, "u", 1, "B"), (1, "u", 1, "OLD"), (3, "c", 2, "x"), (4, "d", 2, None)]),  {1: 'B'})],
  ("Sort by seq, then replay all.", "O(n log n)", "O(t)"),
  ("A dictionary of the highest seq per id, then one pass.", "O(n)", "O(k)"),
  names=["target", "events"])


@B
def cdc_merge(target, events):
    out = dict(target)
    for seq, op, key, value in sorted(events):
        if op == "d":
            out.pop(key, None)
        else:
            out[key] = value
    return dict(sorted(out.items()))


@O
def cdc_merge(target, events):
    latest = {}
    for e in events:
        if e[2] not in latest or e[0] > latest[e[2]][0]:
            latest[e[2]] = e
    out = dict(target)
    for _, op, key, value in latest.values():
        if op == "d":
            out.pop(key, None)
        else:
            out[key] = value
    return dict(sorted(out.items()))


Q(None, "Real-Time Counter With Rollups", "Medium", "Fast dashboards",
  "Keep per-minute counts, and roll them up to hours for faster reads. Given (minute, n) rows, return {hour: total}, sorted.",
  [(([(0, 5), (59, 5), (60, 1), (125, 2)],),  {0: 10, 1: 1, 2: 2})],
  ("A dictionary.", "O(n)", "O(h)"),
  ("<code>defaultdict</code>.", "O(n)", "O(h)"))


@B
def rollup(rows):
    out = {}
    for minute, n in rows:
        h = minute // 60
        out[h] = out.get(h, 0) + n
    return dict(sorted(out.items()))


@O
def rollup(rows):
    from collections import defaultdict
    out = defaultdict(int)
    for m, n in rows:
        out[m // 60] += n
    return dict(sorted(out.items()))


Q(None, "Fan-Out to Many Consumers", "Easy", "Kafka vs point-to-point",
  "With p producers and c consumers, return direct connections needed, and connections through a central log.",
  [((5, 10),  (50, 15))],
  ("Multiply and add.", "O(1)", "O(1)"),
  ("Compact.", "O(1)", "O(1)"),
  names=["p", "c"])


@B
def connections(p, c):
    direct = p * c
    via_log = p + c
    return (direct, via_log)


@O
def connections(p, c):
    return (p * c, p + c)


Q(None, "Tenant Quotas", "Medium", "One customer shouldn't starve the rest",
  "Share capacity fairly: each tenant gets up to its demand, and leftovers go to those still wanting more (max-min fairness). Return allocations sorted by name.",
  [(({"a": 10, "b": 50, "c": 100}, 90),  {'a': 10, 'b': 40.0, 'c': 40.0})],
  ("Repeatedly give an equal share.", "O(t²)", "O(t)"),
  ("Sort by demand, then fill smallest first.", "O(t log t)", "O(t)"),
  names=["demand", "capacity"])


@B
def fair_share(demand, capacity):
    alloc = {t: 0 for t in demand}
    left = capacity
    active = [t for t in demand if demand[t] > 0]
    while left > 1e-9 and active:
        share = left / len(active)
        for t in list(active):
            give = min(share, demand[t] - alloc[t])
            alloc[t] += give
            left -= give
            if demand[t] - alloc[t] <= 1e-9:
                active.remove(t)
    return {t: round(alloc[t], 2) for t in sorted(alloc)}


@O
def fair_share(demand, capacity):
    out, left = {}, capacity
    order = sorted(demand, key=demand.get)
    for i, t in enumerate(order):
        out[t] = round(min(demand[t], left / (len(order) - i)), 2)
        left -= out[t]
    return dict(sorted(out.items()))


Q(None, "How Long Can You Replay?", "Medium", "Retention vs recovery",
  "After an outage of h hours, can you recover from Kafka? Return (can recover, hours to catch up at speed × input, rounded to 2 decimals).",
  [((6, 168, 3), (True, 3.0)), ((200, 168, 3), (False, 100.0))],
  ("Ifs and a division.", "O(1)", "O(1)"),
  ("Compact.", "O(1)", "O(1)"),
  names=["outage", "retention", "speed"])


@B
def can_replay(outage, retention, speed):
    ok = outage <= retention
    hours = outage / (speed - 1)
    return (ok, round(hours, 2))


@O
def can_replay(outage, retention, speed):
    return (outage <= retention, round(outage / (speed - 1), 2))


Q(None, "Monthly Cost Estimate", "Medium", "Every design has a price",
  "With made-up unit prices, return the monthly total: storage_tb × 23, compute_hours × 0.5 × nodes, streaming_mb × 0.04 × 730. Round to 2 decimals, and return the largest part.",
  [((100, 300, 10, 50),  (5260.0, 'storage'))],
  ("Compute each.", "O(1)", "O(1)"),
  ("A dictionary.", "O(1)", "O(1)"),
  names=["storage_tb", "hours", "nodes", "streaming_mb"])


@B
def monthly_cost(storage_tb, hours, nodes, streaming_mb):
    storage = storage_tb * 23
    compute = hours * 0.5 * nodes
    stream = streaming_mb * 0.04 * 730
    total = storage + compute + stream
    if storage >= compute and storage >= stream:
        big = "storage"
    elif compute >= stream:
        big = "compute"
    else:
        big = "streaming"
    return (round(total, 2), big)


@O
def monthly_cost(storage_tb, hours, nodes, streaming_mb):
    parts = {"storage": storage_tb * 23, "compute": hours * 0.5 * nodes, "streaming": streaming_mb * 0.04 * 730}
    return (round(sum(parts.values()), 2), max(parts, key=parts.get))


Q(None, "Design a Partition Layout", "Medium", "Year, month, day or hour?",
  "Choose the coarsest of 'month', 'day' or 'hour' so each partition stays at or below max_gb. Given GB per day, return the choice and its GB, rounded to 2 decimals. If even an hour's too big, return 'hour' anyway.",
  [((10, 500), ('month', 300)), ((500, 100), ('hour', 20.83)), ((5000, 100), ('hour', 208.33))],
  ("Ifs.", "O(1)", "O(1)"),
  ("A loop over options.", "O(1)", "O(1)"),
  names=["gb_day", "max_gb"])


@B
def partition_grain(gb_day, max_gb):
    if gb_day * 30 <= max_gb:
        return ("month", round(gb_day * 30, 2))
    if gb_day <= max_gb:
        return ("day", round(gb_day, 2))
    return ("hour", round(gb_day / 24, 2))


@O
def partition_grain(gb_day, max_gb):
    for name, factor in (("month", 30), ("day", 1)):
        if gb_day * factor <= max_gb:
            return (name, round(gb_day * factor, 2))
    return ("hour", round(gb_day / 24, 2))


Q(None, "Rank the Risks", "Easy", "Likelihood × impact",
  "Given risks as (name, likelihood 1-5, impact 1-5), return names ordered by score descending, ties alphabetical.",
  [(([("late data", 5, 2), ("source outage", 2, 5), ("schema change", 4, 4)],),  ['schema change', 'late data', 'source outage'])],
  ("Compute, then sort pairs.", "O(n log n)", "O(n)"),
  ("A sort key.", "O(n log n)", "O(n)"))


@B
def rank_risks(risks):
    scored = []
    for name, l, i in risks:
        scored.append((-l * i, name))
    scored.sort()
    return [n for _, n in scored]


@O
def rank_risks(risks):
    return [r[0] for r in sorted(risks, key=lambda r: (-r[1] * r[2], r[0]))]


Q(None, "Sharding a Key-Value Table", "Medium", "Scale reads and writes",
  "Return shards needed for read and write rates, and for data size, taking the largest and rounding up. Each shard handles reads_each, writes_each and gb_each.",
  [((100000, 10000, 2000, 10000, 2000, 500),  10)],
  ("Three divisions.", "O(1)", "O(1)"),
  ("<code>max</code> of them.", "O(1)", "O(1)"),
  names=["reads", "writes", "gb", "reads_each", "writes_each", "gb_each"])


@B
def shards(reads, writes, gb, reads_each, writes_each, gb_each):
    a = math.ceil(reads / reads_each)
    b = math.ceil(writes / writes_each)
    c = math.ceil(gb / gb_each)
    return max(a, b, c)


@O
def shards(reads, writes, gb, reads_each, writes_each, gb_each):
    return math.ceil(max(reads / reads_each, writes / writes_each, gb / gb_each))


Q(None, "Data Mesh Ownership", "Medium", "Who owns which data?",
  "Given datasets with owners, return datasets with no owner, and owners with more than limit datasets (a sign that one team's a bottleneck), both sorted.",
  [(({"a": "x", "b": "x", "c": "x", "d": None, "e": "y"}, 2),  (['d'], ['x']))],
  ("Loops.", "O(d)", "O(o)"),
  ("<code>Counter</code>.", "O(d)", "O(o)"),
  names=["datasets", "limit"])


@B
def ownership(datasets, limit):
    orphans, counts = [], {}
    for name, owner in datasets.items():
        if owner is None:
            orphans.append(name)
        else:
            counts[owner] = counts.get(owner, 0) + 1
    return (sorted(orphans), sorted(o for o, c in counts.items() if c > limit))


@O
def ownership(datasets, limit):
    from collections import Counter
    c = Counter(o for o in datasets.values() if o)
    return (sorted(n for n, o in datasets.items() if o is None), sorted(o for o, n in c.items() if n > limit))


Q(None, "Growth Headroom", "Easy", "When will it break?",
  "Data grows by a monthly rate. Given current load, capacity and growth rate, return whole months until load exceeds capacity.",
  [((100, 400, 0.1),  15), ((100, 100, 0.1), 1)],
  ("Compound in a loop.", "O(m)", "O(1)"),
  ("A logarithm, with care for exact boundaries.", "O(1)", "O(1)"),
  names=["load", "capacity", "rate"])


@B
def months_left(load, capacity, rate):
    months = 0
    while load <= capacity:
        load *= 1 + rate
        months += 1
    return months


@O
def months_left(load, capacity, rate):
    return math.floor(math.log(capacity / load) / math.log(1 + rate)) + 1
