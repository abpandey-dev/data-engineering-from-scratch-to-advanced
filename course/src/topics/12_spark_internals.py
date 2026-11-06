from lib import *
import math


TOPIC(
    id="spark-internals", title="Spark Tuning & Internals", glyph="⚙",
    blurb="Make Spark fast and stop it crashing: join strategies, broadcast, skew and salting, shuffle tuning, adaptive execution, memory, out-of-memory errors, file sizes, reading the Spark UI, and real debugging.",
    theory="""
<h3>Cheat sheet</h3>
<pre><code class="py">F.broadcast(small)                         # avoid a shuffle
spark.conf.set("spark.sql.shuffle.partitions", 400)
spark.conf.set("spark.sql.adaptive.enabled", True)  # AQE, on by default in recent versions
df.repartition(200, "key")   # even out, with a shuffle
df.coalesce(10)              # fewer files, no shuffle
df.cache() ... df.unpersist()</code></pre>
""")


Q(None, "Pick a Join Strategy", "Medium", "What Spark chooses",
  "Return 'broadcast' if the smaller side (MB) is at or below threshold (default 10 MB in Spark), 'bucketed' if both are bucketed the same, otherwise 'sort-merge'.",
  [((5, 1000000, 10, False), 'broadcast'), ((500, 1000000, 10, True), 'bucketed'), ((500, 1000000, 10, False), 'sort-merge')],
  ("Ifs.", "O(1)", "O(1)"),
  ("A conditional expression.", "O(1)", "O(1)"),
  names=["a_mb", "b_mb", "threshold", "bucketed"])


@B
def spark_join(a_mb, b_mb, threshold, bucketed):
    if min(a_mb, b_mb) <= threshold:
        return "broadcast"
    if bucketed:
        return "bucketed"
    return "sort-merge"


@O
def spark_join(a_mb, b_mb, threshold, bucketed):
    return "broadcast" if min(a_mb, b_mb) <= threshold else "bucketed" if bucketed else "sort-merge"


Q(None, "Broadcast Join Simulation", "Medium", "Each partition joins locally",
  "Each partition of the big table joins a small dictionary, with no shuffle. Return the joined rows per partition, dropping unmatched.",
  [(([[(1, "x"), (2, "y")], [(1, "z"), (9, "q")]], {1: "A", 2: "B"}), [[[1, 'x', 'A'], [2, 'y', 'B']], [[1, 'z', 'A']]])],
  ("Nested loops scanning the small table.", "O(k·s)", "O(k)"),
  ("A dictionary lookup for each row.", "O(k)", "O(k)"),
  names=["parts", "small"])


@B
def broadcast_join(parts, small):
    out = []
    for p in parts:
        joined = []
        for k, v in p:
            for sk in small:
                if sk == k:
                    joined.append([k, v, small[sk]])
        out.append(joined)
    return out


@O
def broadcast_join(parts, small):
    return [[[k, v, small[k]] for k, v in p if k in small] for p in parts]


Q(None, "Find the Skewed Partitions", "Medium", "Spark's AQE rule",
  "A partition is skewed if it's larger than factor × median and larger than min_mb. Return the skewed indexes.",
  [(([100, 120, 110, 5000, 90], 5, 256), [3]), (([10, 10, 100], 5, 256), [])],
  ("Sort for the median, then a loop.", "O(n log n)", "O(n)"),
  ("<code>statistics.median</code>.", "O(n log n)", "O(n)"),
  names=["sizes", "factor", "min_mb"])


@B
def skewed(sizes, factor, min_mb):
    s = sorted(sizes)
    n = len(s)
    median = s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2
    return [i for i, v in enumerate(sizes) if v > factor * median and v > min_mb]


@O
def skewed(sizes, factor, min_mb):
    import statistics
    m = statistics.median(sizes)
    return [i for i, v in enumerate(sizes) if v > max(factor * m, min_mb)]


Q(None, "Salted Join", "Hard", "Fix a hot key",
  "Salt the big side's keys with i % s, and replicate each small-side row s times with each salt. Return (joined rows sorted, largest group size before and after, for a key appearing n times).",
  [(([("us", 1), ("us", 2), ("us", 3), ("in", 4)], {"us": "A", "in": "B"}, 2),  ([['in', 4, 'B'], ['us', 1, 'A'], ['us', 2, 'A'], ['us', 3, 'A']], 3, 2))],
  ("Build salted keys, and loop over both sides.", "O(b·s·m)", "O(b)"),
  ("A dictionary of salted small rows.", "O(b + s·m)", "O(s·m)"),
  names=["big", "small", "s"])


@B
def salted_join(big, small, s):
    salted_small = []
    for k, v in small.items():
        for i in range(s):
            salted_small.append((f"{k}#{i}", v))
    groups, joined = {}, []
    for i, (k, v) in enumerate(big):
        key = f"{k}#{i % s}"
        groups[key] = groups.get(key, 0) + 1
        for sk, sv in salted_small:
            if sk == key:
                joined.append([k, v, sv])
    before = {}
    for k, _ in big:
        before[k] = before.get(k, 0) + 1
    return (sorted(joined), max(before.values()), max(groups.values()))


@O
def salted_join(big, small, s):
    from collections import Counter
    table = {f"{k}#{i}": v for k, v in small.items() for i in range(s)}
    keys = [f"{k}#{i % s}" for i, (k, _) in enumerate(big)]
    joined = [[k, v, table[sk]] for (k, v), sk in zip(big, keys)]
    return (sorted(joined), max(Counter(k for k, _ in big).values()), max(Counter(keys).values()))


Q(None, "Isolate the Hot Key", "Medium", "Another fix for skew",
  "Keys with over limit rows are 'hot': broadcast-join them, and shuffle-join the rest. Return (hot keys sorted, rows in the normal path).",
  [(([("a", 1)] * 5 + [("b", 1)] + [("c", 1)] * 2, 3),  (['a'], 3))],
  ("Count in a dictionary.", "O(n)", "O(k)"),
  ("<code>Counter</code>.", "O(n)", "O(k)"),
  names=["rows", "limit"])


@B
def hot_keys(rows, limit):
    counts = {}
    for k, _ in rows:
        counts[k] = counts.get(k, 0) + 1
    hot = sorted(k for k, c in counts.items() if c > limit)
    normal = 0
    for k, _ in rows:
        if k not in hot:
            normal += 1
    return (hot, normal)


@O
def hot_keys(rows, limit):
    from collections import Counter
    c = Counter(k for k, _ in rows)
    hot = sorted(k for k, n in c.items() if n > limit)
    return (hot, sum(n for k, n in c.items() if k not in hot))


Q(None, "Null Keys Cause Skew", "Easy", "The classic surprise",
  "Return the share of rows with a NULL join key, rounded to 4 decimals. Those rows hash to one partition and never match in an inner join, so filter them first.",
  [(([1, None, None, 2, None],),  0.6)],
  ("A loop.", "O(n)", "O(1)"),
  ("<code>count</code>.", "O(n)", "O(1)"))


@B
def null_share(keys):
    nulls = 0
    for k in keys:
        if k is None:
            nulls += 1
    return round(nulls / len(keys), 4)


@O
def null_share(keys):
    return round(keys.count(None) / len(keys), 4)


Q(None, "Shuffle Partitions Setting", "Medium", "The default is rarely right",
  "Target partition_mb after a shuffle. Return the partition count (rounded up) for shuffle_gb, and the average MB with the default of 200 partitions. GB = 1000 MB.",
  [((1000, 128), (7813, 5000.0)), ((2, 128), (16, 10.0))],
  ("Step by step.", "O(1)", "O(1)"),
  ("Compact.", "O(1)", "O(1)"),
  names=["shuffle_gb", "partition_mb"])


@B
def shuffle_setting(shuffle_gb, partition_mb):
    mb = shuffle_gb * 1000
    needed = math.ceil(mb / partition_mb)
    with_default = mb / 200
    return (needed, with_default)


@O
def shuffle_setting(shuffle_gb, partition_mb):
    return (math.ceil(shuffle_gb * 1000 / partition_mb), shuffle_gb * 5.0)


Q(None, "AQE: Coalesce Small Partitions", "Medium", "Adaptive execution",
  "Adaptive Query Execution merges neighbouring small shuffle partitions up to target MB. Return the merged sizes.",
  [(([10, 20, 30, 100, 5, 5], 64), [60, 100, 10])],
  ("A running total.", "O(n)", "O(m)"),
  ("Same algorithm, compactly.", "O(n)", "O(m)"),
  names=["sizes", "target"])


@B
def aqe_coalesce(sizes, target):
    out, current = [], 0
    for s in sizes:
        if current and current + s > target:
            out.append(current)
            current = 0
        current += s
    if current:
        out.append(current)
    return out


@O
def aqe_coalesce(sizes, target):
    out = []
    for s in sizes:
        if out and out[-1] + s <= target:
            out[-1] += s
        else:
            out.append(s)
    return out


Q(None, "Executor Memory Breakdown", "Medium", "Where does memory go?",
  "Given executor GB: 300 MB reserved; of the rest, a fraction 0.6 is unified (execution + storage), half of which is initially storage. Return (unified GB, storage GB, user GB), rounded to 2 decimals. GB = 1024 MB.",
  [((8,),  (4.62, 2.31, 3.08))],
  ("Step by step.", "O(1)", "O(1)"),
  ("Compact.", "O(1)", "O(1)"))


@B
def memory_split(gb):
    usable = gb - 300 / 1024
    unified = usable * 0.6
    storage = unified * 0.5
    user = usable - unified
    return (round(unified, 2), round(storage, 2), round(user, 2))


@O
def memory_split(gb):
    u = gb - 300 / 1024
    return (round(u * 0.6, 2), round(u * 0.3, 2), round(u * 0.4, 2))


Q(None, "Diagnose an Out-of-Memory", "Medium", "Driver or executor?",
  "Given symptoms, return the likely fix. 'collect' → 'avoid collect; write out instead'. 'broadcast' → 'lower the broadcast threshold'. 'skew' → 'fix skew with salting or AQE'. 'many_small_tasks' → 'fewer partitions'. Otherwise 'increase memory only after finding the cause'.",
  [(("collect",), 'avoid collect; write out instead'), (("skew",), 'fix skew with salting or AQE'), (("mystery",), 'increase memory only after finding the cause')],
  ("Ifs.", "O(1)", "O(1)"),
  ("A dictionary with a default.", "O(1)", "O(1)"))


@B
def oom_fix(symptom):
    if symptom == "collect":
        return "avoid collect; write out instead"
    if symptom == "broadcast":
        return "lower the broadcast threshold"
    if symptom == "skew":
        return "fix skew with salting or AQE"
    if symptom == "many_small_tasks":
        return "fewer partitions"
    return "increase memory only after finding the cause"


@O
def oom_fix(symptom):
    return {"collect": "avoid collect; write out instead", "broadcast": "lower the broadcast threshold",
            "skew": "fix skew with salting or AQE", "many_small_tasks": "fewer partitions"}.get(symptom, "increase memory only after finding the cause")


Q(None, "Files Written per Partition", "Medium", "How jobs make small files",
  "Writing with partitionBy: each task writes one file per partition value it holds. With t tasks and v values spread across all tasks, return the file count, and with repartition by that column first (one task per value).",
  [((200, 30),  (6000, 30))],
  ("Multiply.", "O(1)", "O(1)"),
  ("Compact.", "O(1)", "O(1)"),
  names=["t", "v"])


@B
def files_written(t, v):
    naive = t * v
    fixed = v
    return (naive, fixed)


@O
def files_written(t, v):
    return (t * v, v)


Q(None, "Spot the Straggler Task", "Easy", "Read the Spark UI",
  "Tasks have (duration, input MB). Return indexes of tasks slower than 2 × median duration, labelled 'skew' if input is also over 2 × median input, else 'slow node'.",
  [(([(10, 100), (11, 110), (9, 90), (60, 900), (50, 100)],),  [[3, 'skew'], [4, 'slow node']])],
  ("Sort for medians, then a loop.", "O(n log n)", "O(n)"),
  ("<code>statistics.median</code>.", "O(n log n)", "O(n)"))


@B
def stragglers(tasks):
    d = sorted(t[0] for t in tasks)
    i = sorted(t[1] for t in tasks)
    med_d, med_i = d[len(d) // 2], i[len(i) // 2]
    out = []
    for n, (dur, mb) in enumerate(tasks):
        if dur > 2 * med_d:
            out.append([n, "skew" if mb > 2 * med_i else "slow node"])
    return out


@O
def stragglers(tasks):
    import statistics
    md, mi = statistics.median(t[0] for t in tasks), statistics.median(t[1] for t in tasks)
    return [[n, "skew" if mb > 2 * mi else "slow node"] for n, (dur, mb) in enumerate(tasks) if dur > 2 * md]


Q(None, "Dynamic Allocation", "Medium", "Scale to the backlog",
  "Pending tasks and cores per executor give the executors wanted, rounded up and capped by max. Remove idle ones down to min. Return the target.",
  [((100, 4, 2, 10), 10), ((0, 4, 2, 10), 2), ((20, 4, 2, 10), 5)],
  ("Ifs.", "O(1)", "O(1)"),
  ("<code>min</code> and <code>max</code>.", "O(1)", "O(1)"),
  names=["pending", "cores", "min_e", "max_e"])


@B
def target_executors(pending, cores, min_e, max_e):
    want = pending // cores
    if pending % cores:
        want += 1
    if want > max_e:
        want = max_e
    if want < min_e:
        want = min_e
    return want


@O
def target_executors(pending, cores, min_e, max_e):
    return max(min_e, min(max_e, math.ceil(pending / cores)))


Q(None, "Cost of a Cluster Run", "Easy", "Time × machines",
  "Return the cost of nodes × hours × a made-up hourly price, rounded to 2 decimals, for two options, and the cheaper's name. More nodes finishing faster can cost the same.",
  [((10, 2, 0.5, 20, 1, 0.5), (10.0, 10.0, 'first')), ((10, 2, 0.5, 20, 1.5, 0.5), (10.0, 15.0, 'first'))],
  ("Compute both, then compare.", "O(1)", "O(1)"),
  ("Compact.", "O(1)", "O(1)"),
  names=["n1", "h1", "p1", "n2", "h2", "p2"])


@B
def cluster_cost(n1, h1, p1, n2, h2, p2):
    a = n1 * h1 * p1
    b = n2 * h2 * p2
    if a <= b:
        name = "first"
    else:
        name = "second"
    return (round(a, 2), round(b, 2), name)


@O
def cluster_cost(n1, h1, p1, n2, h2, p2):
    a, b = n1 * h1 * p1, n2 * h2 * p2
    return (round(a, 2), round(b, 2), "first" if a <= b else "second")


Q(None, "Bucketed Join Avoids Shuffle", "Medium", "Pay once at write time",
  "Two tables bucketed the same way need no shuffle at join. Return shuffle GB for r runs without buckets (both tables each run), and with buckets (only once for writing).",
  [((100, 900, 30), (30000, 1000))],
  ("Compute each.", "O(1)", "O(1)"),
  ("Compact.", "O(1)", "O(1)"),
  names=["a", "b", "runs"])


@B
def bucket_savings(a, b, runs):
    without = (a + b) * runs
    with_buckets = a + b
    return (without, with_buckets)


@O
def bucket_savings(a, b, runs):
    return ((a + b) * runs, a + b)


Q(None, "Dynamic Partition Pruning", "Medium", "Filter via the join",
  "A fact table is partitioned by day. A dimension filter keeps days. Return (partitions read without DPP, partitions read with DPP, sorted).",
  [(([1, 2, 3, 4, 5], {1: "wk", 2: "wk", 3: "wk", 4: "wk", 5: "we"}, "we"),  (5, [5]))],
  ("A loop.", "O(n)", "O(k)"),
  ("A comprehension.", "O(n)", "O(k)"),
  names=["fact_days", "dim", "label"])


@B
def dpp(fact_days, dim, label):
    keep = []
    for d in fact_days:
        if dim.get(d) == label:
            keep.append(d)
    return (len(fact_days), sorted(keep))


@O
def dpp(fact_days, dim, label):
    return (len(fact_days), sorted(d for d in fact_days if dim.get(d) == label))


Q(None, "Sort-Merge Spill", "Medium", "Memory runs out, disk takes over",
  "Sorting data_mb in memory_mb requires spilling if it doesn't fit. Return (number of sorted runs on disk, whether it spilled).",
  [((1000, 300), (4, True)), ((100, 300), (1, False))],
  ("Divide with a remainder check.", "O(1)", "O(1)"),
  ("<code>ceil</code>.", "O(1)", "O(1)"),
  names=["data_mb", "memory_mb"])


@B
def spill(data_mb, memory_mb):
    if data_mb <= memory_mb:
        return (1, False)
    runs = data_mb // memory_mb
    if data_mb % memory_mb:
        runs += 1
    return (runs, True)


@O
def spill(data_mb, memory_mb):
    return (math.ceil(data_mb / memory_mb), data_mb > memory_mb)


Q(None, "Window With No Partition", "Medium", "A hidden single-task trap",
  "A window with no PARTITION BY puts all rows on one task. Return (max rows on a task with partitioning by key, and without). Rows are keys.",
  [((["a", "a", "b", "c"],),  (2, 4))],
  ("Count in a dictionary.", "O(n)", "O(k)"),
  ("<code>Counter</code>.", "O(n)", "O(k)"))


@B
def window_task(keys):
    counts = {}
    for k in keys:
        counts[k] = counts.get(k, 0) + 1
    return (max(counts.values()), len(keys))


@O
def window_task(keys):
    from collections import Counter
    return (max(Counter(keys).values()), len(keys))


Q(None, "Debug a Slow Job", "Hard", "Find the real bottleneck",
  "Given stage (name, seconds), return the slowest stage's name and its share of total time rounded to 1 decimal, and 'Amdahl limit' speedup if only that stage gets infinitely faster, rounded to 2 decimals.",
  [(([("read", 10), ("shuffle", 80), ("write", 10)],),  ('shuffle', 80.0, 5.0))],
  ("A loop.", "O(n)", "O(1)"),
  ("<code>max</code> and <code>sum</code>.", "O(n)", "O(1)"))


@B
def bottleneck(stages):
    total, name, worst = 0, None, -1
    for n, s in stages:
        total += s
        if s > worst:
            name, worst = n, s
    return (name, round(100 * worst / total, 1), round(total / (total - worst), 2))


@O
def bottleneck(stages):
    name, worst = max(stages, key=lambda x: x[1])
    total = sum(s for _, s in stages)
    return (name, round(100 * worst / total, 1), round(total / (total - worst), 2))


Q(None, "Parquet Target File Count", "Easy", "repartition before write",
  "Return repartition(n) for writing data_gb at target_mb per file, assuming compression shrinks by ratio. GB = 1000 MB.",
  [((100, 256, 4), 98)],
  ("Step by step.", "O(1)", "O(1)"),
  ("Compact.", "O(1)", "O(1)"),
  names=["data_gb", "target_mb", "ratio"])


@B
def write_partitions(data_gb, target_mb, ratio):
    on_disk = data_gb * 1000 / ratio
    return math.ceil(on_disk / target_mb)


@O
def write_partitions(data_gb, target_mb, ratio):
    return math.ceil(data_gb * 1000 / ratio / target_mb)
