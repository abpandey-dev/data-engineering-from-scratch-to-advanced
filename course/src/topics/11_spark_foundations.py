from lib import *
import math


TOPIC(
    id="spark-foundations", title="Spark Foundations", glyph="⚡",
    blurb="Apache Spark from zero: the driver and executors, lazy evaluation, transformations vs actions, narrow vs wide, DataFrames and PySpark's API. You build a tiny Spark in plain Python to see how it works, then run the real thing in the labs.",
    theory="""
<h3>Cheat sheet</h3>
<pre><code class="py">df = spark.read.parquet("s3://lake/orders/")
out = (df.filter(F.col("amount") > 0)           # transformations: lazy
         .groupBy("city").agg(F.sum("amount").alias("total")))
out.write.mode("overwrite").parquet(path)       # action: runs the job
out.explain()                                   # read the plan</code></pre>
<p>Questions here run a miniature Spark in Python, because PySpark can't run in a browser. Real PySpark code is in the lessons and the labs.</p>
""")


def partitions_of(rows, n):
    return [rows[i::n] for i in range(n)]


Q(None, "Split Data Into Partitions", "Easy", "The unit of parallelism",
  "Split a list into n partitions in turn: item i goes to partition i % n.",
  [(([1, 2, 3, 4, 5], 2), [[1, 3, 5], [2, 4]])],
  ("A list of lists.", "O(k)", "O(k)"),
  ("Slicing with a step.", "O(k)", "O(k)"),
  names=["rows", "n"])


@B
def split_partitions(rows, n):
    parts = [[] for _ in range(n)]
    for i, r in enumerate(rows):
        parts[i % n].append(r)
    return parts


@O
def split_partitions(rows, n):
    return [rows[i::n] for i in range(n)]


Q(None, "Map Over Partitions", "Easy", "Narrow transformation",
  "Double every value in each partition, keeping partitions as they are.",
  [(([[1, 2], [3]],), [[2, 4], [6]])],
  ("Nested loops.", "O(k)", "O(k)"),
  ("A nested comprehension. No data moves between partitions.", "O(k)", "O(k)"))


@B
def map_partitions(parts):
    out = []
    for p in parts:
        new = []
        for x in p:
            new.append(x * 2)
        out.append(new)
    return out


@O
def map_partitions(parts):
    return [[x * 2 for x in p] for p in parts]


Q(None, "Lazy Evaluation", "Medium", "Nothing runs until an action",
  "Build a tiny lazy dataset: map and filter only record the plan, and collect runs it. Return (steps run before collect, result, values processed in total) for mapping ×2 and filtering > 2 on the given rows.",
  [(([1, 2, 3],), (0, [4, 6], 6))],
  ("A class holding a list of operations.", "O(n·s)", "O(s)"),
  ("Generators are lazy by nature, doing the same in fewer lines.", "O(n·s)", "O(1)"))


@B
def lazy_demo(rows):
    class Lazy:
        def __init__(self, data):
            self.data, self.plan, self.ran = data, [], 0

        def map(self, f):
            self.plan.append(("map", f))
            return self

        def filter(self, f):
            self.plan.append(("filter", f))
            return self

        def collect(self):
            out = []
            for x in self.data:
                keep = True
                for kind, f in self.plan:
                    self.ran += 1
                    if kind == "map":
                        x = f(x)
                    elif not f(x):
                        keep = False
                        break
                if keep:
                    out.append(x)
            return out
    d = Lazy(rows).map(lambda x: x * 2).filter(lambda x: x > 2)
    before = d.ran
    result = d.collect()
    return (before, result, d.ran)


@O
def lazy_demo(rows):
    count = [0]

    def double(x):
        count[0] += 1
        return x * 2

    def keep(x):
        count[0] += 1
        return x > 2
    plan = filter(keep, map(double, rows))
    before = count[0]
    result = list(plan)
    return (before, result, count[0])


Q(None, "Predicate Pushdown", "Medium", "Why laziness saves work",
  "Spark can move a filter before an expensive step. Return records processed by the expensive step, with the filter after it, and before it.",
  [(([1, 2, 3, 4, 5, 6], 2),  (6, 3))],
  ("Run both orders, with counters.", "O(n)", "O(n)"),
  ("It's simply n and the number passing the filter.", "O(n)", "O(1)"),
  names=["rows", "modulus"])


@B
def pushdown(rows, modulus):
    after = 0
    for r in rows:
        after += 1
    before = 0
    for r in rows:
        if r % modulus == 0:
            before += 1
    return (after, before)


@O
def pushdown(rows, modulus):
    return (len(rows), sum(r % modulus == 0 for r in rows))


Q(None, "Column Pruning", "Easy", "Read only what you need",
  "Given columns needed downstream and each column's bytes per row, return bytes read for n rows (needed only), and bytes saved compared with all columns.",
  [(({"id": 8, "name": 30, "bio": 500, "amt": 8}, ["id", "amt"], 1000), (16000, 530000))],
  ("A loop.", "O(c)", "O(1)"),
  ("Generators.", "O(c)", "O(1)"),
  names=["sizes", "needed", "n"])


@B
def column_prune(sizes, needed, n):
    used = 0
    for c in needed:
        used += sizes[c]
    total = 0
    for c in sizes:
        total += sizes[c]
    return (used * n, (total - used) * n)


@O
def column_prune(sizes, needed, n):
    used = sum(sizes[c] for c in needed)
    return (used * n, (sum(sizes.values()) - used) * n)


Q(None, "Narrow or Wide?", "Easy", "Does data move?",
  "Classify operations: filter, map, select, withColumn and union are 'narrow'; groupBy, join, distinct, sort and repartition are 'wide'.",
  [((["filter", "groupBy", "select", "join"],), ['narrow', 'wide', 'narrow', 'wide'])],
  ("Ifs.", "O(n)", "O(n)"),
  ("A set.", "O(n)", "O(1)"))


@B
def classify_ops(ops):
    out = []
    for op in ops:
        if op in ("filter", "map", "select", "withColumn", "union"):
            out.append("narrow")
        else:
            out.append("wide")
    return out


@O
def classify_ops(ops):
    wide = {"groupBy", "join", "distinct", "sort", "repartition"}
    return ["wide" if o in wide else "narrow" for o in ops]


Q(None, "Stages From a Plan", "Medium", "Shuffles cut stages",
  "A job's stages are separated by wide operations. Return the number of stages for a list of operations.",
  [((["read", "filter", "groupBy", "select", "join", "write"],), 3), ((["read", "filter", "write"],), 1)],
  ("Count with a loop.", "O(n)", "O(1)"),
  ("A generator.", "O(n)", "O(1)"))


@B
def count_stages(ops):
    stages = 1
    for op in ops:
        if op in ("groupBy", "join", "distinct", "sort", "repartition"):
            stages += 1
    return stages


@O
def count_stages(ops):
    wide = {"groupBy", "join", "distinct", "sort", "repartition"}
    return 1 + sum(o in wide for o in ops)


Q(None, "Shuffle by Key", "Medium", "Bring keys together",
  "Move (key, value) pairs across partitions so that each key lands in partition (sum of char codes) % n. Return partitions, and how many records changed partition.",
  [(([[("a", 1), ("b", 2)], [("a", 3)]], 2), ([[('b', 2)], [('a', 1), ('a', 3)]], 1))],
  ("Loops.", "O(k)", "O(k)"),
  ("A helper for the target partition.", "O(k)", "O(k)"),
  names=["parts", "n"])


@B
def shuffle(parts, n):
    out = [[] for _ in range(n)]
    moved = 0
    for i, p in enumerate(parts):
        for k, v in p:
            target = sum(ord(c) for c in k) % n
            out[target].append((k, v))
            if target != i:
                moved += 1
    return (out, moved)


@O
def shuffle(parts, n):
    target = lambda k: sum(map(ord, k)) % n
    out = [[] for _ in range(n)]
    moved = 0
    for i, p in enumerate(parts):
        for kv in p:
            t = target(kv[0])
            out[t].append(kv)
            moved += t != i
    return (out, moved)


Q(None, "groupBy + sum, Spark Style", "Medium", "Partial, shuffle, final",
  "Each partition first sums per key locally, then those partial results are merged. Return (partial records sent, final dictionary sorted). Partial aggregation is why groupBy shuffles less than the raw data.",
  [(([[("a", 1), ("a", 2), ("b", 3)], [("a", 4)]],), (3, {'a': 7, 'b': 3}))],
  ("Merge everything directly, sending all records.", "O(k)", "O(g)"),
  ("Local dictionaries, then merge.", "O(k)", "O(g)"))


@B
def group_sum(parts):
    sent = 0
    final = {}
    for p in parts:
        local = {}
        for k, v in p:
            local[k] = local.get(k, 0) + v
        sent += len(local)
        for k, v in local.items():
            final[k] = final.get(k, 0) + v
    return (sent, dict(sorted(final.items())))


@O
def group_sum(parts):
    from collections import Counter
    locals_ = []
    for p in parts:
        c = Counter()
        for k, v in p:
            c[k] += v
        locals_.append(c)
    return (sum(map(len, locals_)), dict(sorted(sum(locals_, Counter()).items())))


Q(None, "A Tiny DataFrame", "Medium", "select, filter, withColumn",
  "Implement filter(amt > min), add column tax = amt × 0.1, then select id and tax, on a list of dictionaries. Round tax to 2 decimals.",
  [(([{"id": 1, "amt": 100, "x": "a"}, {"id": 2, "amt": 5, "x": "b"}], 10), [{'id': 1, 'tax': 10.0}])],
  ("One loop with all steps.", "O(n)", "O(n)"),
  ("Chained comprehensions, as in a DataFrame pipeline.", "O(n)", "O(n)"),
  names=["rows", "minimum"])


@B
def tiny_dataframe(rows, minimum):
    out = []
    for r in rows:
        if r["amt"] > minimum:
            out.append({"id": r["id"], "tax": round(r["amt"] * 0.1, 2)})
    return out


@O
def tiny_dataframe(rows, minimum):
    filtered = (r for r in rows if r["amt"] > minimum)
    with_tax = ({**r, "tax": round(r["amt"] * 0.1, 2)} for r in filtered)
    return [{k: r[k] for k in ("id", "tax")} for r in with_tax]


Q(None, "Parallel Time on a Cluster", "Easy", "Tasks and slots",
  "n equal tasks, each t seconds, run on c cores in rounds. Return total seconds.",
  [((10, 60, 4), 180), ((4, 60, 4), 60)],
  ("Simulate rounds.", "O(n/c)", "O(1)"),
  ("<code>ceil(n / c) × t</code>.", "O(1)", "O(1)"),
  names=["n", "t", "c"])


@B
def cluster_time(n, t, c):
    remaining, total = n, 0
    while remaining > 0:
        remaining -= c
        total += t
    return total


@O
def cluster_time(n, t, c):
    return math.ceil(n / c) * t


Q(None, "How Many Partitions?", "Medium", "A common rule of thumb",
  "Target about 128 MB per partition. Return partitions for data_gb, and how many tasks run at a time with executors × cores. GB = 1000 MB.",
  [((100, 10, 4),  (782, 40))],
  ("Step by step.", "O(1)", "O(1)"),
  ("Compact.", "O(1)", "O(1)"),
  names=["data_gb", "executors", "cores"])


@B
def partition_plan(data_gb, executors, cores):
    mb = data_gb * 1000
    parts = mb // 128
    if mb % 128:
        parts += 1
    return (parts, executors * cores)


@O
def partition_plan(data_gb, executors, cores):
    return (math.ceil(data_gb * 1000 / 128), executors * cores)


Q(None, "Sizing an Executor", "Medium", "Memory per core",
  "Reserving 1 core and 1 GB per node for the system, with executors of 5 cores each: return (executors per node, memory per executor rounded down, minus 10% overhead, rounded to 1 decimal).",
  [((16, 64),  (3, 18.9))],
  ("Divide step by step.", "O(1)", "O(1)"),
  ("Compact.", "O(1)", "O(1)"),
  names=["node_cores", "node_gb"])


@B
def size_executor(node_cores, node_gb):
    cores = node_cores - 1
    gb = node_gb - 1
    executors = cores // 5
    each = gb // executors
    return (executors, round(each * 0.9, 1))


@O
def size_executor(node_cores, node_gb):
    n = (node_cores - 1) // 5
    return (n, round((node_gb - 1) // n * 0.9, 1))


Q(None, "Cache or Recompute?", "Medium", "Spend memory to save time",
  "A dataset costs build seconds to compute, and is used n times. Caching adds cache_cost once, with each use then taking read seconds. Return (seconds without, seconds with, whether to cache).",
  [((100, 5, 10, 2), (500, 120, True)), ((100, 1, 10, 2), (100, 112, False))],
  ("Compute both.", "O(1)", "O(1)"),
  ("Compact.", "O(1)", "O(1)"),
  names=["build", "n", "cache_cost", "read"])


@B
def cache_or_not(build, n, cache_cost, read):
    without = build * n
    with_cache = build + cache_cost + read * n
    return (without, with_cache, with_cache < without)


@O
def cache_or_not(build, n, cache_cost, read):
    a, b = build * n, build + cache_cost + read * n
    return (a, b, b < a)


Q(None, "Coalesce vs Repartition", "Medium", "Shrinking without a shuffle",
  "coalesce merges neighbouring partitions without a shuffle; repartition shuffles evenly. Given sizes and target n, return the coalesce result (groups of neighbours, in order, as evenly as possible by count) and the repartition result (even split of the total, remainder to the first).",
  [(([10, 10, 100, 10], 2), ([20, 110], [65, 65]))],
  ("Loops.", "O(p)", "O(n)"),
  ("Slices and divmod.", "O(p)", "O(n)"),
  names=["sizes", "n"])


@B
def coalesce_vs_repartition(sizes, n):
    coalesced = []
    size = len(sizes) // n
    extra = len(sizes) % n
    start = 0
    for i in range(n):
        end = start + size + (1 if i < extra else 0)
        coalesced.append(sum(sizes[start:end]))
        start = end
    total = sum(sizes)
    repart = [total // n + (1 if i < total % n else 0) for i in range(n)]
    return (coalesced, repart)


@O
def coalesce_vs_repartition(sizes, n):
    q, r = divmod(len(sizes), n)
    bounds = [i * q + min(i, r) for i in range(n + 1)]
    Q_, R = divmod(sum(sizes), n)
    return ([sum(sizes[a:b]) for a, b in zip(bounds, bounds[1:])], [Q_ + (i < R) for i in range(n)])


Q(None, "Lineage: Recompute a Lost Partition", "Medium", "Fault tolerance",
  "ops is a list of steps applied to an input. If an executor dies, Spark reapplies them to the lost partition's input. Return (recovered values, recompute count).",
  [(([1, 2], ["double", "inc"]),  ([3, 5], 4))],
  ("Apply with ifs.", "O(n·s)", "O(n)"),
  ("A dictionary of functions.", "O(n·s)", "O(n)"),
  names=["inputs", "ops"])


@B
def recompute(inputs, ops):
    out, count = [], 0
    for x in inputs:
        for op in ops:
            count += 1
            if op == "double":
                x = x * 2
            else:
                x = x + 1
        out.append(x)
    return (out, count)


@O
def recompute(inputs, ops):
    funcs = {"double": lambda x: x * 2, "inc": lambda x: x + 1}
    out = []
    for x in inputs:
        for op in ops:
            x = funcs[op](x)
        out.append(x)
    return (out, len(inputs) * len(ops))


Q(None, "UDF vs Built-in Cost", "Easy", "Why avoid Python UDFs",
  "A Python UDF serialises each row out of the JVM and back. Given rows, built-in ms per million, UDF ms per million, return both times in seconds, and the ratio rounded to 1 decimal.",
  [((10000000, 200, 5000),  (2.0, 50.0, 25.0))],
  ("Step by step.", "O(1)", "O(1)"),
  ("Compact.", "O(1)", "O(1)"),
  names=["rows", "builtin_ms", "udf_ms"])


@B
def udf_cost(rows, builtin_ms, udf_ms):
    millions = rows / 1000000
    a = millions * builtin_ms / 1000
    b = millions * udf_ms / 1000
    return (a, b, round(b / a, 1))


@O
def udf_cost(rows, builtin_ms, udf_ms):
    m = rows / 1e9
    return (m * builtin_ms, m * udf_ms, round(udf_ms / builtin_ms, 1))


Q(None, "Read a Plan", "Medium", "Does it use pushdown?",
  "Given lines of a physical plan, return (number of Exchange (shuffle) steps, whether PushedFilters is non-empty).",
  [((["*(2) HashAggregate", "+- Exchange hashpartitioning(city)", "   +- FileScan parquet PushedFilters: [IsNotNull(amt)]"],), (1, True)), ((["FileScan parquet PushedFilters: []"],), (0, False))],
  ("Search each line.", "O(n)", "O(1)"),
  ("A regular expression.", "O(n)", "O(1)"))


@B
def read_plan(lines):
    exchanges, pushed = 0, False
    for line in lines:
        if "Exchange" in line:
            exchanges += 1
        if "PushedFilters: [" in line and "PushedFilters: []" not in line:
            pushed = True
    return (exchanges, pushed)


@O
def read_plan(lines):
    import re
    text = "\n".join(lines)
    return (text.count("Exchange"), bool(re.search(r"PushedFilters: \[[^\]]+\]", text)))


Q(None, "Explode and Collect", "Easy", "Array columns",
  "Implement explode (one row per array item, dropping empty arrays, as Spark's explode does) on (id, list) rows, then collect_list back by id.",
  [(([(1, ["a", "b"]), (2, []), (3, ["c"])],), ([[1, 'a'], [1, 'b'], [3, 'c']], {1: ['a', 'b'], 3: ['c']}))],
  ("Nested loops.", "O(t)", "O(t)"),
  ("Comprehension, plus a defaultdict.", "O(t)", "O(t)"))


@B
def explode_collect(rows):
    exploded = []
    for i, items in rows:
        for x in items:
            exploded.append([i, x])
    back = {}
    for i, x in exploded:
        back.setdefault(i, []).append(x)
    return (exploded, back)


@O
def explode_collect(rows):
    from collections import defaultdict
    exploded = [[i, x] for i, items in rows for x in items]
    back = defaultdict(list)
    for i, x in exploded:
        back[i].append(x)
    return (exploded, dict(back))


Q(None, "Action or Transformation?", "Easy", "What triggers a job?",
  "count, collect, show, write and first are actions, and they start a job. Given a chain, return how many jobs run.",
  [((["filter", "select", "count", "groupBy", "write"],), 2), ((["filter", "select"],), 0)],
  ("A loop with a tuple check.", "O(n)", "O(1)"),
  ("A set and a sum.", "O(n)", "O(1)"))


@B
def jobs_run(chain):
    jobs = 0
    for op in chain:
        if op in ("count", "collect", "show", "write", "first"):
            jobs += 1
    return jobs


@O
def jobs_run(chain):
    return sum(op in {"count", "collect", "show", "write", "first"} for op in chain)
