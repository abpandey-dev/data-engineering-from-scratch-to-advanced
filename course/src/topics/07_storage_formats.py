from lib import *
import gzip
import json
import math
import numpy as np


TOPIC(
    id="storage-formats", title="Files, Formats & Storage", glyph="▦",
    blurb="How data is laid out on disk and why it decides your speed and bill: CSV vs JSON vs Parquet, columnar storage, compression, run-length and dictionary encoding, partitioning, the small-file problem and object storage.",
    theory="""
<h3>Cheat sheet</h3>
<table><tr><th>Format</th><th>Layout</th><th>Best for</th></tr>
<tr><td>CSV</td><td>text rows</td><td>exchange with people</td></tr>
<tr><td>JSON Lines</td><td>text rows</td><td>raw events, nested data</td></tr>
<tr><td>Avro</td><td>binary rows</td><td>Kafka, schema evolution</td></tr>
<tr><td>Parquet / ORC</td><td>binary columns</td><td>analytics</td></tr></table>
""")


Q(None, "Rows to Columns", "Easy", "The columnar idea",
  "Convert a list of dictionaries into a dictionary of column lists.",
  [(([{"a": 1, "b": "x"}, {"a": 2, "b": "y"}],), {'a': [1, 2], 'b': ['x', 'y']})],
  ("Nested loops.", "O(n·c)", "O(n·c)"),
  ("A comprehension per column.", "O(n·c)", "O(n·c)"))


@B
def to_columns(rows):
    out = {}
    for r in rows:
        for k, v in r.items():
            out.setdefault(k, []).append(v)
    return out


@O
def to_columns(rows):
    return {k: [r[k] for r in rows] for k in rows[0]}


Q(None, "Run-Length Encoding", "Easy", "Repeated values shrink",
  "Encode a list into [value, count] pairs for consecutive runs.",
  [((["a", "a", "a", "b", "a"],), [['a', 3], ['b', 1], ['a', 1]]), (([],), [])],
  ("Track the current run.", "O(n)", "O(r)"),
  ("<code>itertools.groupby</code>.", "O(n)", "O(r)"))


@B
def rle(values):
    out = []
    for v in values:
        if out and out[-1][0] == v:
            out[-1][1] += 1
        else:
            out.append([v, 1])
    return out


@O
def rle(values):
    import itertools
    return [[k, len(list(g))] for k, g in itertools.groupby(values)]


Q(None, "Dictionary Encoding", "Easy", "Few distinct values",
  "Return (dictionary of distinct values in first-seen order, list of indices).",
  [((["IN", "US", "IN", "IN"],), (['IN', 'US'], [0, 1, 0, 0]))],
  ("<code>list.index</code>.", "O(n·d)", "O(d)"),
  ("A dictionary for lookups.", "O(n)", "O(d)"))


@B
def dict_encode(values):
    d = []
    ids = []
    for v in values:
        if v not in d:
            d.append(v)
        ids.append(d.index(v))
    return (d, ids)


@O
def dict_encode(values):
    index = {}
    ids = [index.setdefault(v, len(index)) for v in values]
    return (list(index), ids)


Q(None, "Delta Encoding", "Easy", "Timestamps compress well",
  "Store the first value, then differences. Return encoded values, and decode to confirm the round trip.",
  [(([1000, 1001, 1003, 1003],), ([1000, 1, 2, 0], True))],
  ("Loops both ways.", "O(n)", "O(n)"),
  ("<code>np.diff</code> and <code>np.cumsum</code>.", "O(n)", "O(n)"))


@B
def delta(values):
    enc = [values[0]]
    for i in range(1, len(values)):
        enc.append(values[i] - values[i - 1])
    dec, total = [], 0
    for d in enc:
        total += d
        dec.append(total)
    return (enc, dec == values)


@O
def delta(values):
    enc = np.concatenate([values[:1], np.diff(values)])
    return (enc, np.cumsum(enc).tolist() == values)


Q(None, "Encoded Size Comparison", "Medium", "Which encoding wins?",
  "With ints at 4 bytes and strings at their length, return bytes for plain storage, dictionary encoding (strings once, 4 per index) and RLE (string + 4 per run).",
  [((["IN"] * 1000 + ["US"] * 1000,), (4000, 8004, 12)), ((["a", "b"] * 1000,), (2000, 8002, 10000))],
  ("Compute each in a loop.", "O(n)", "O(d)"),
  ("Built-ins, and groupby.", "O(n)", "O(d)"))


@B
def encoding_sizes(values):
    plain = 0
    for v in values:
        plain += len(v)
    distinct = []
    for v in values:
        if v not in distinct:
            distinct.append(v)
    dictionary = sum(len(v) for v in distinct) + 4 * len(values)
    rle_size, prev = 0, None
    for v in values:
        if v != prev:
            rle_size += len(v) + 4
            prev = v
    return (plain, dictionary, rle_size)


@O
def encoding_sizes(values):
    import itertools
    runs = [k for k, _ in itertools.groupby(values)]
    return (sum(map(len, values)), sum(map(len, set(values))) + 4 * len(values), sum(len(r) + 4 for r in runs))


Q(None, "Sorted Data Compresses Better", "Medium", "Order matters",
  "Return whether gzip output is smaller when the values are sorted first, using a fixed level and no timestamp.",
  [(([str(i * 7919 % 1000) for i in range(5000)],), True)],
  ("Compress both, comparing the lengths.", "O(n log n)", "O(n)"),
  ("A helper used twice.", "O(n log n)", "O(n)"))


@B
def sorted_is_smaller(values):
    original = gzip.compress(",".join(values).encode(), 6, mtime=0)
    ordered = gzip.compress(",".join(sorted(values)).encode(), 6, mtime=0)
    return len(ordered) < len(original)


@O
def sorted_is_smaller(values):
    size = lambda v: len(gzip.compress(",".join(v).encode(), 6, mtime=0))
    return size(sorted(values)) < size(values)


Q(None, "Partition Pruning", "Easy", "Skip whole folders",
  "partitions maps a date to file bytes. Return (bytes scanned for a date range, bytes saved vs reading all).",
  [(({"d1": 100, "d2": 200, "d3": 300}, "d2", "d3"), (500, 100))],
  ("A loop with a comparison.", "O(p)", "O(1)"),
  ("A generator.", "O(p)", "O(1)"),
  names=["partitions", "lo", "hi"])


@B
def pruning(partitions, lo, hi):
    scanned = total = 0
    for day, size in partitions.items():
        total += size
        if lo <= day <= hi:
            scanned += size
    return (scanned, total - scanned)


@O
def pruning(partitions, lo, hi):
    scanned = sum(s for d, s in partitions.items() if lo <= d <= hi)
    return (scanned, sum(partitions.values()) - scanned)


Q(None, "Min/Max Skipping", "Medium", "Row group statistics",
  "Each row group has min and max for a column. Return indices of groups that could contain values in [lo, hi]. Parquet readers do this.",
  [(([(1, 10), (11, 20), (21, 30)], 15, 22), [1, 2]), (([(1, 5)], 9, 10), [])],
  ("Compare in a loop.", "O(g)", "O(g)"),
  ("A comprehension.", "O(g)", "O(g)"),
  names=["groups", "lo", "hi"])


@B
def skip_groups(groups, lo, hi):
    out = []
    for i, (a, b) in enumerate(groups):
        if not (b < lo or a > hi):
            out.append(i)
    return out


@O
def skip_groups(groups, lo, hi):
    return [i for i, (a, b) in enumerate(groups) if a <= hi and b >= lo]


Q(None, "Choosing a Partition Column", "Medium", "Too few or too many",
  "Given total GB and the distinct values of a column, return average GB per partition rounded to 3 decimals, and 'good' if between 0.1 and 100, 'too many' if below, 'too few' if above.",
  [((1000, 365), (2.74, 'good')), ((1000, 2), (500.0, 'too few')), ((1000, 10000000), (0.0, 'too many'))],
  ("Ifs.", "O(1)", "O(1)"),
  ("Compact.", "O(1)", "O(1)"),
  names=["gb", "distinct"])


@B
def partition_check(gb, distinct):
    avg = gb / distinct
    if avg < 0.1:
        verdict = "too many"
    elif avg > 100:
        verdict = "too few"
    else:
        verdict = "good"
    return (round(avg, 3), verdict)


@O
def partition_check(gb, distinct):
    avg = gb / distinct
    return (round(avg, 3), "too many" if avg < 0.1 else "too few" if avg > 100 else "good")


Q(None, "The Small File Problem", "Medium", "Metadata overhead",
  "Each file costs a fixed open time in ms plus reading at mb_per_ms. Return total ms for total_mb split into n files, rounded to 1 decimal.",
  [((1000, 10000, 2, 1), 21000.0), ((1000, 4, 2, 1), 1008.0)],
  ("Step by step.", "O(1)", "O(1)"),
  ("One line.", "O(1)", "O(1)"),
  names=["total_mb", "n", "open_ms", "mb_per_ms"])


@B
def read_time(total_mb, n, open_ms, mb_per_ms):
    opening = n * open_ms
    reading = total_mb / mb_per_ms
    return round(opening + reading, 1)


@O
def read_time(total_mb, n, open_ms, mb_per_ms):
    return round(n * open_ms + total_mb / mb_per_ms, 1)


Q(None, "Compact Small Files", "Medium", "Merge into target size",
  "Greedily group file sizes in order into outputs of at most target MB. Return group sizes.",
  [(([10, 40, 80, 20, 100, 5], 128),  [50, 100, 105])],
  ("Build lists, then sum.", "O(n)", "O(n)"),
  ("A running total.", "O(n)", "O(g)"),
  names=["sizes", "target"])


@B
def compact(sizes, target):
    groups, current = [], []
    for s in sizes:
        if current and sum(current) + s > target:
            groups.append(sum(current))
            current = []
        current.append(s)
    if current:
        groups.append(sum(current))
    return groups


@O
def compact(sizes, target):
    out, cur = [], 0
    for s in sizes:
        if cur and cur + s > target:
            out.append(cur)
            cur = 0
        cur += s
    return out + [cur] if cur else out


Q(None, "How Many Output Files?", "Easy", "Sizing a write",
  "Return files needed for data_gb at target_mb per file (GB = 1000 MB), rounded up.",
  [((10, 128), 79), ((1, 1000), 1)],
  ("Integer arithmetic with a remainder check.", "O(1)", "O(1)"),
  ("<code>math.ceil</code>.", "O(1)", "O(1)"),
  names=["data_gb", "target_mb"])


@B
def file_count(data_gb, target_mb):
    total = data_gb * 1000
    n = total // target_mb
    return n + 1 if total % target_mb else n


@O
def file_count(data_gb, target_mb):
    return math.ceil(data_gb * 1000 / target_mb)


Q(None, "Hive-Style Partition Paths", "Easy", "Parse them back",
  "Parse 'lake/t/year=2026/month=01/part-0.parquet' into a dictionary of partition values, in order.",
  [(("lake/t/year=2026/month=01/part-0.parquet",), {'year': '2026', 'month': '01'})],
  ("Split on / and check for =.", "O(n)", "O(p)"),
  ("A regular expression.", "O(n)", "O(p)"))


@B
def parse_partitions(path):
    out = {}
    for part in path.split("/"):
        if "=" in part:
            key, value = part.split("=", 1)
            out[key] = value
    return out


@O
def parse_partitions(path):
    import re
    return dict(re.findall(r"([^/=]+)=([^/]+)", path))


Q(None, "Schema Evolution: What's Safe?", "Medium", "Change without breaking readers",
  "Compare old and new schemas (column → type). Return (added, removed, changed types), each sorted, and whether it's safe: no removed or changed columns.",
  [(({"id": "int", "a": "str"}, {"id": "int", "a": "str", "b": "int"}), (['b'], [], [], True)), (({"id": "int", "a": "str"}, {"id": "str"}), ([], ['a'], ['id'], False))],
  ("Loops over both.", "O(c)", "O(c)"),
  ("Set operations.", "O(c)", "O(c)"),
  names=["old", "new"])


@B
def schema_change(old, new):
    added, removed, changed = [], [], []
    for c in new:
        if c not in old:
            added.append(c)
    for c in old:
        if c not in new:
            removed.append(c)
        elif old[c] != new[c]:
            changed.append(c)
    return (sorted(added), sorted(removed), sorted(changed), not removed and not changed)


@O
def schema_change(old, new):
    added, removed = sorted(new.keys() - old.keys()), sorted(old.keys() - new.keys())
    changed = sorted(c for c in old.keys() & new.keys() if old[c] != new[c])
    return (added, removed, changed, not removed and not changed)


Q(None, "Bucket for Sampling and Joins", "Medium", "Hash partitioning",
  "Assign ids to n buckets as id % n, and return the size of each bucket.",
  [(([1, 2, 3, 4, 5, 6, 7], 3), [2, 3, 2])],
  ("A list of counters.", "O(k)", "O(n)"),
  ("<code>np.bincount</code>.", "O(k)", "O(n)"),
  names=["ids", "n"])


@B
def bucket_sizes(ids, n):
    counts = [0] * n
    for i in ids:
        counts[i % n] += 1
    return counts


@O
def bucket_sizes(ids, n):
    return np.bincount(np.array(ids) % n, minlength=n)


Q(None, "Compare Query Cost by Format", "Medium", "Priced per byte scanned",
  "A query reads use_cols of cols on data_gb. CSV scans everything; Parquet reads the used share, then compression ratio applies. Return the GB scanned in each, rounded to 2 decimals.",
  [((1000, 50, 5, 4),  (1000, 25.0))],
  ("Compute each.", "O(1)", "O(1)"),
  ("Formulas.", "O(1)", "O(1)"),
  names=["data_gb", "cols", "use_cols", "ratio"])


@B
def scan_by_format(data_gb, cols, use_cols, ratio):
    csv_scan = data_gb
    share = use_cols / cols
    parquet = data_gb * share
    parquet = parquet / ratio
    return (round(csv_scan, 2), round(parquet, 2))


@O
def scan_by_format(data_gb, cols, use_cols, ratio):
    return (round(data_gb, 2), round(data_gb * use_cols / cols / ratio, 2))


Q(None, "Storage Tier Choice", "Medium", "Hot, warm, cold",
  "Given days since last access, return 'hot' under 30, 'warm' under 180, otherwise 'cold'. Then return total cost, with made-up per-GB prices hot 0.023, warm 0.0125, cold 0.004. Items are (days, gb); round to 3 decimals.",
  [(([(5, 100), (60, 200), (400, 1000)],), (['hot', 'warm', 'cold'], 8.8))],
  ("Ifs in a loop.", "O(n)", "O(n)"),
  ("A helper.", "O(n)", "O(n)"))


@B
def tier_cost(items):
    tiers, cost = [], 0.0
    for days, gb in items:
        if days < 30:
            tiers.append("hot")
            cost += gb * 0.023
        elif days < 180:
            tiers.append("warm")
            cost += gb * 0.0125
        else:
            tiers.append("cold")
            cost += gb * 0.004
    return (tiers, round(cost, 3))


@O
def tier_cost(items):
    price = {"hot": 0.023, "warm": 0.0125, "cold": 0.004}
    tier = lambda d: "hot" if d < 30 else "warm" if d < 180 else "cold"
    tiers = [tier(d) for d, _ in items]
    return (tiers, round(sum(price[t] * g for t, (_, g) in zip(tiers, items)), 3))


Q(None, "Nested to Parquet-Friendly", "Medium", "Explode arrays",
  "Rows have an id and a list of items. Return one row per item (explode), and rows with empty lists keep one row with item None.",
  [(([{"id": 1, "items": ["a", "b"]}, {"id": 2, "items": []}],), [{'id': 1, 'item': 'a'}, {'id': 1, 'item': 'b'}, {'id': 2, 'item': None}])],
  ("Nested loops with an if.", "O(total)", "O(total)"),
  ("A comprehension using <code>or [None]</code>.", "O(total)", "O(total)"))


@B
def explode(rows):
    out = []
    for r in rows:
        if r["items"]:
            for item in r["items"]:
                out.append({"id": r["id"], "item": item})
        else:
            out.append({"id": r["id"], "item": None})
    return out


@O
def explode(rows):
    return [{"id": r["id"], "item": i} for r in rows for i in (r["items"] or [None])]


Q(None, "Checksums Catch Corruption", "Medium", "Trust, but verify",
  "manifest maps a file name to its expected md5. Return names whose content doesn't match, sorted.",
  [(({"a.csv": "1,2", "b.csv": "3,4"}, {"a.csv": "05cf281c050be3da4eecf3bc6e8aac1b", "b.csv": "x"}), ['b.csv'])],
  ("A loop.", "O(bytes)", "O(f)"),
  ("A comprehension.", "O(bytes)", "O(f)"),
  names=["files", "manifest"])


@B
def corrupt_files(files, manifest):
    import hashlib
    bad = []
    for name, text in files.items():
        if hashlib.md5(text.encode()).hexdigest() != manifest[name]:
            bad.append(name)
    return sorted(bad)


@O
def corrupt_files(files, manifest):
    import hashlib
    return sorted(n for n, t in files.items() if hashlib.md5(t.encode()).hexdigest() != manifest[n])


Q(None, "Bit-Width of a Dictionary", "Medium", "Why real encodings are tiny",
  "Dictionary indices need ⌈log₂(d)⌉ bits (at least 1). Return bits per value, and bytes for n values, rounded up.",
  [((2, 1000), [1, 125]), ((200, 1000), [8, 1000]), ((1, 10), [1, 2])],
  ("Double in a loop until d fits.", "O(log d)", "O(1)"),
  ("A logarithm.", "O(1)", "O(1)"),
  names=["d", "n"], post=list)


@B
def bit_width(d, n):
    bits, capacity = 1, 2
    while capacity < d:
        capacity *= 2
        bits += 1
    return (bits, math.ceil(n * bits / 8))


@O
def bit_width(d, n):
    bits = max(1, math.ceil(math.log2(d))) if d > 1 else 1
    return (bits, math.ceil(n * bits / 8))
