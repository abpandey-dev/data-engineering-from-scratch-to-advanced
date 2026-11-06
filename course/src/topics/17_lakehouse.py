from lib import *
import bisect


TOPIC(
    id="lakehouse", title="Lakehouse & Table Formats", glyph="◆",
    blurb="Database features on cheap files: why plain lakes break, how Iceberg and Delta use snapshots and manifests, ACID on object storage, time travel, MERGE, copy-on-write vs merge-on-read, compaction and clustering.",
    theory="""
<h3>Cheat sheet</h3>
<pre><code class="py">Table = data files + metadata that says which files count
Write: add new files, then atomically swap the metadata pointer
Time travel: read an older snapshot
Copy-on-write: rewrite files on update; fast reads
Merge-on-read: write deltas; fast writes, slower reads, needs compaction
Z-order / clustering: keep related rows together for better skipping</code></pre>
""")


Q(None, "Snapshot Commit", "Medium", "ACID on files",
  "A snapshot is a list of data files. Commit adds and removes files, creating a new snapshot. Return the list of snapshots after each commit.",
  [(([(["f1"], []), (["f2"], []), (["f3"], ["f1"])],),  [['f1'], ['f1', 'f2'], ['f2', 'f3']])],
  ("Copy and edit lists.", "O(c·f)", "O(c·f)"),
  ("Sets.", "O(c·f)", "O(c·f)"))


@B
def snapshots(commits):
    current, out = [], []
    for add, remove in commits:
        new = [f for f in current if f not in remove] + add
        out.append(new)
        current = new
    return out


@O
def snapshots(commits):
    out, cur = [], set()
    for add, remove in commits:
        cur = (cur - set(remove)) | set(add)
        out.append(sorted(cur))
    return out


Q(None, "Time Travel", "Medium", "Query the past",
  "Snapshots are (commit_time, files), sorted. Return files for the latest snapshot at or before t, or None.",
  [(([(10, ["a"]), (20, ["a", "b"]), (30, ["c"])], 25), ['a', 'b']), (([(10, ["a"])], 5), None)],
  ("Scan.", "O(s)", "O(1)"),
  ("Binary search.", "O(log s)", "O(s)"),
  names=["snaps", "t"])


@B
def time_travel(snaps, t):
    best = None
    for when, files in snaps:
        if when <= t:
            best = files
    return best


@O
def time_travel(snaps, t):
    i = bisect.bisect_right([s[0] for s in snaps], t)
    return snaps[i - 1][1] if i else None


Q(None, "Optimistic Concurrency", "Hard", "Two writers at once",
  "Each writer read version v and tries to commit. If the table's moved on and they touched the same partition, it fails; else it retries on the new version. Return results for ordered commits (read_version, partition).",
  [(([(0, "d1"), (0, "d2"), (0, "d1")],),  ['v1', 'v2', 'conflict'])],
  ("Scan the history of commits.", "O(n²)", "O(n)"),
  ("A dictionary of the last version per partition.", "O(n)", "O(p)"))


@B
def commit_results(commits):
    history, out = [], []
    for read_version, partition in commits:
        conflict = any(p == partition for v, p in history if v > read_version)
        if conflict:
            out.append("conflict")
        else:
            history.append((len(history) + 1, partition))
            out.append(f"v{len(history)}")
    return out


@O
def commit_results(commits):
    last, version, out = {}, 0, []
    for read_version, partition in commits:
        if last.get(partition, 0) > read_version:
            out.append("conflict")
        else:
            version += 1
            last[partition] = version
            out.append(f"v{version}")
    return out


Q(None, "Copy-on-Write Update", "Medium", "Rewrite the file",
  "Files map to rows {id: value}. To update one id, rewrite the whole file containing it. Return (new files, rows rewritten).",
  [(({"f1": {1: "a", 2: "b"}, "f2": {3: "c"}}, 2, "B"),  ({'f1_v2': {1: 'a', 2: 'B'}, 'f2': {3: 'c'}}, 2))],
  ("Loop through files.", "O(rows)", "O(rows)"),
  ("A comprehension.", "O(rows)", "O(rows)"),
  names=["files", "key", "value"])


@B
def copy_on_write(files, key, value):
    out, rewritten = {}, 0
    for name, rows in files.items():
        if key in rows:
            new = dict(rows)
            new[key] = value
            out[name + "_v2"] = new
            rewritten += len(rows)
        else:
            out[name] = rows
    return (out, rewritten)


@O
def copy_on_write(files, key, value):
    hit = next(n for n, r in files.items() if key in r)
    out = {(n + "_v2" if n == hit else n): ({**r, key: value} if n == hit else r) for n, r in files.items()}
    return (out, len(files[hit]))


Q(None, "Merge-on-Read", "Medium", "Apply deletes at read time",
  "Base rows are {id: value}, and delta logs are applied in order: ('u', id, value) or ('d', id). Return the merged view sorted, and rows the reader had to merge.",
  [(({1: "a", 2: "b"}, [("u", 1, "A"), ("d", 2, None), ("u", 3, "c")]),  ({1: 'A', 3: 'c'}, 3))],
  ("Loop with ifs.", "O(b + d)", "O(b)"),
  ("Dictionary operations.", "O(b + d)", "O(b)"),
  names=["base", "deltas"])


@B
def merge_on_read(base, deltas):
    out = dict(base)
    for op, key, value in deltas:
        if op == "u":
            out[key] = value
        else:
            del out[key]
    return (dict(sorted(out.items())), len(deltas))


@O
def merge_on_read(base, deltas):
    out = dict(base)
    for op, k, v in deltas:
        out.pop(k) if op == "d" else out.update({k: v})
    return (dict(sorted(out.items())), len(deltas))


Q(None, "COW vs MOR Cost", "Medium", "Choosing a strategy",
  "Updates touch u rows per day in files of f rows. Copy-on-write rewrites f rows per update. Merge-on-read adds r reads a day × u delta rows to merge. Return (COW write rows, MOR merge rows).",
  [((10, 1000, 100),  (10000, 1000))],
  ("Compute each.", "O(1)", "O(1)"),
  ("Compact.", "O(1)", "O(1)"),
  names=["u", "f", "r"])


@B
def cow_vs_mor(u, f, r):
    cow = u * f
    mor = r * u
    return (cow, mor)


@O
def cow_vs_mor(u, f, r):
    return (u * f, r * u)


Q(None, "MERGE INTO on a Lake", "Medium", "Upsert with deletes",
  "Apply source rows (id, value, op) to a target {id: value}: op 'D' deletes, otherwise upsert. Return (target sorted, counts of [insert, update, delete]).",
  [(({1: "a", 2: "b"}, [(1, "A", "U"), (2, None, "D"), (3, "c", "U")]),  ({1: 'A', 3: 'c'}, [1, 1, 1]))],
  ("Ifs.", "O(s)", "O(t)"),
  ("Same, with a counter.", "O(s)", "O(t)"),
  names=["target", "source"])


@B
def merge_into(target, source):
    out, ins, upd, dele = dict(target), 0, 0, 0
    for key, value, op in source:
        if op == "D":
            if key in out:
                del out[key]
                dele += 1
        elif key in out:
            out[key] = value
            upd += 1
        else:
            out[key] = value
            ins += 1
    return (dict(sorted(out.items())), [ins, upd, dele])


@O
def merge_into(target, source):
    from collections import Counter
    out, c = dict(target), Counter()
    for k, v, op in source:
        if op == "D":
            c["d"] += out.pop(k, None) is not None
        else:
            c["u" if k in out else "i"] += 1
            out[k] = v
    return (dict(sorted(out.items())), [c["i"], c["u"], c["d"]])


Q(None, "Pick Files From Manifests", "Medium", "Metadata pruning",
  "A manifest lists each file's (name, min, max) for a column. Return files that could contain a value in [lo, hi]. No directory listing is needed.",
  [(([("a", 1, 10), ("b", 11, 20), ("c", 15, 30)], 18, 18),  ['b', 'c'])],
  ("A loop.", "O(f)", "O(m)"),
  ("A comprehension.", "O(f)", "O(m)"),
  names=["manifest", "lo", "hi"])


@B
def manifest_prune(manifest, lo, hi):
    out = []
    for name, a, b in manifest:
        if a <= hi and b >= lo:
            out.append(name)
    return out


@O
def manifest_prune(manifest, lo, hi):
    return [n for n, a, b in manifest if a <= hi and b >= lo]


Q(None, "Effect of Clustering", "Medium", "Sorted files skip better",
  "Compare files scanned for a point lookup before and after sorting values across files of size k. Return the (files containing value v) count for unsorted and sorted data.",
  [(([1, 9, 5, 2, 9, 7, 3, 9, 8], 3, 5),  (3, 1))],
  ("Build file ranges, and test.", "O(n log n)", "O(n)"),
  ("A helper used twice.", "O(n log n)", "O(n)"),
  names=["values", "k", "v"])


@B
def clustering(values, k, v):
    def scanned(vals):
        count = 0
        for i in range(0, len(vals), k):
            part = vals[i:i + k]
            if min(part) <= v <= max(part):
                count += 1
        return count
    return (scanned(values), scanned(sorted(values)))


@O
def clustering(values, k, v):
    scan = lambda x: sum(min(x[i:i + k]) <= v <= max(x[i:i + k]) for i in range(0, len(x), k))
    return (scan(values), scan(sorted(values)))


Q(None, "Z-Order Key", "Hard", "Sort on two columns at once",
  "Interleave the bits of x and y (x's bit first, from the top) to form a Z-order key, for 3-bit values. Sort points by it, and return them.",
  [(([(0, 0), (7, 7), (1, 0), (0, 1)],),  [(0, 0), (0, 1), (1, 0), (7, 7)])],
  ("Loop over bits.", "O(n·b)", "O(n)"),
  ("A comprehension over bits.", "O(n·b)", "O(n)"))


@B
def z_order(points):
    def key(p):
        x, y = p
        out = 0
        for bit in range(2, -1, -1):
            out = out * 2 + ((x >> bit) & 1)
            out = out * 2 + ((y >> bit) & 1)
        return out
    return sorted(points, key=key)


@O
def z_order(points):
    key = lambda p: sum((((p[0] >> b) & 1) << (2 * b + 1)) | (((p[1] >> b) & 1) << (2 * b)) for b in range(3))
    return sorted(points, key=key)


Q(None, "Bin-Pack Compaction", "Medium", "Merge small files",
  "Rewrite files smaller than min_mb into outputs of at most target_mb, greedily in order. Return (untouched files, new file sizes).",
  [(([10, 500, 20, 30, 120, 90], 100, 128),  ([500, 120], [60, 90]))],
  ("Lists and a running total.", "O(f)", "O(f)"),
  ("Same, compactly.", "O(f)", "O(f)"),
  names=["sizes", "min_mb", "target_mb"])


@B
def compaction(sizes, min_mb, target_mb):
    keep = [s for s in sizes if s >= min_mb]
    out, cur = [], 0
    for s in sizes:
        if s < min_mb:
            if cur and cur + s > target_mb:
                out.append(cur)
                cur = 0
            cur += s
    if cur:
        out.append(cur)
    return (keep, out)


@O
def compaction(sizes, min_mb, target_mb):
    out = []
    for s in (x for x in sizes if x < min_mb):
        if out and out[-1] + s <= target_mb:
            out[-1] += s
        else:
            out.append(s)
    return ([s for s in sizes if s >= min_mb], out)


Q(None, "Expire Old Snapshots", "Medium", "Time travel has a cost",
  "Keep snapshots newer than cutoff, plus the latest. A data file can be deleted only if no kept snapshot references it. Return (kept times, files deletable, sorted).",
  [(([(10, ["a"]), (20, ["a", "b"]), (30, ["c"])], 25),  ([30], ['a', 'b']))],
  ("Lists and loops.", "O(s·f)", "O(f)"),
  ("Set operations.", "O(s·f)", "O(f)"),
  names=["snaps", "cutoff"])


@B
def expire(snaps, cutoff):
    kept = [s for s in snaps if s[0] >= cutoff]
    if not kept:
        kept = [snaps[-1]]
    live = []
    for _, files in kept:
        live += files
    every = []
    for _, files in snaps:
        every += files
    return ([s[0] for s in kept], sorted({f for f in every if f not in live}))


@O
def expire(snaps, cutoff):
    kept = [s for s in snaps if s[0] >= cutoff] or snaps[-1:]
    live = {f for _, fs in kept for f in fs}
    return ([s[0] for s in kept], sorted({f for _, fs in snaps for f in fs} - live))


Q(None, "Orphan Files", "Easy", "Failed writes leave debris",
  "Return files on storage that no snapshot references, sorted. Don't delete files newer than a safety age, as a write may be in progress. Files are (name, age_days).",
  [(([("a", 10), ("b", 10), ("tmp", 10), ("new", 0)], ["a", "b"], 3),  ['tmp'])],
  ("A loop.", "O(f)", "O(f)"),
  ("A set.", "O(f)", "O(f)"),
  names=["storage", "referenced", "min_age"])


@B
def orphans(storage, referenced, min_age):
    out = []
    for name, age in storage:
        if name not in referenced and age >= min_age:
            out.append(name)
    return sorted(out)


@O
def orphans(storage, referenced, min_age):
    used = set(referenced)
    return sorted(n for n, a in storage if n not in used and a >= min_age)


Q(None, "Hidden Partitioning", "Medium", "Iceberg's idea",
  "Iceberg derives partitions from a timestamp column: month transform 'YYYY-MM-DD' → 'YYYY-MM'. Given a predicate on days, return which partition months to scan, sorted, and files read.",
  [(({"2026-01": ["a"], "2026-02": ["b", "c"], "2026-03": ["d"]}, "2026-02-10", "2026-03-05"),  (['2026-02', '2026-03'], 3))],
  ("A loop comparing months.", "O(p)", "O(f)"),
  ("A sorted comprehension.", "O(p log p)", "O(f)"),
  names=["partitions", "start", "end"])


@B
def hidden_partition(partitions, start, end):
    months, files = [], 0
    for m in sorted(partitions):
        if start[:7] <= m <= end[:7]:
            months.append(m)
            files += len(partitions[m])
    return (months, files)


@O
def hidden_partition(partitions, start, end):
    months = sorted(m for m in partitions if start[:7] <= m <= end[:7])
    return (months, sum(len(partitions[m]) for m in months))


Q(None, "Schema Evolution by Column ID", "Medium", "Rename safely",
  "Parquet stores column ids. A table maps name to id. Reading old file {1: 'x', 2: 5} after renaming id 1 to 'label' and adding id 3 'new': return the row, with None for missing.",
  [(({1: "x", 2: 5}, {"label": 1, "qty": 2, "new": 3}),  {'label': 'x', 'qty': 5, 'new': None})],
  ("A loop.", "O(c)", "O(c)"),
  ("A comprehension.", "O(c)", "O(c)"),
  names=["file_row", "schema"])


@B
def read_by_id(file_row, schema):
    out = {}
    for name, cid in schema.items():
        if cid in file_row:
            out[name] = file_row[cid]
        else:
            out[name] = None
    return out


@O
def read_by_id(file_row, schema):
    return {n: file_row.get(i) for n, i in schema.items()}


Q(None, "Delete for Privacy", "Medium", "GDPR on immutable files",
  "To delete a user, rewrite only the files holding them. Return (files rewritten, rows rewritten, and whether old snapshots still hold the data until expired).",
  [(({"f1": ["u1", "u2"], "f2": ["u3"], "f3": ["u1", "u4", "u5"]}, "u1"),  (2, 3, True))],
  ("A loop.", "O(rows)", "O(1)"),
  ("Generators.", "O(rows)", "O(1)"),
  names=["files", "user"])


@B
def gdpr_delete(files, user):
    count, rows = 0, 0
    for name, users in files.items():
        if user in users:
            count += 1
            rows += len(users) - 1
    return (count, rows, True)


@O
def gdpr_delete(files, user):
    hit = [u for u in files.values() if user in u]
    return (len(hit), sum(len(u) - 1 for u in hit), True)


Q(None, "Read Delta's Log", "Medium", "The transaction log",
  "Delta's log has actions {'add': f} and {'remove': f} in order. Replay up to version v to get live files, sorted.",
  [(([{"add": "a"}, {"add": "b"}, {"remove": "a"}, {"add": "c"}], 2),  ['b']), (([{"add": "a"}, {"add": "b"}, {"remove": "a"}, {"add": "c"}], 3), ['b', 'c'])],
  ("A list.", "O(v²)", "O(f)"),
  ("A set.", "O(v)", "O(f)"),
  names=["log", "v"])


@B
def replay_log(log, v):
    live = []
    for action in log[:v + 1]:
        if "add" in action:
            live.append(action["add"])
        else:
            live.remove(action["remove"])
    return sorted(live)


@O
def replay_log(log, v):
    live = set()
    for a in log[:v + 1]:
        live.add(a["add"]) if "add" in a else live.discard(a["remove"])
    return sorted(live)


Q(None, "Choose a Table Strategy", "Easy", "COW, MOR or append",
  "Return 'append only' if there are no updates; 'copy-on-write' if reads are at least 10× the update batches per day; otherwise 'merge-on-read'.",
  [((0, 100), 'append only'), ((5, 100), 'copy-on-write'), ((100, 100), 'merge-on-read')],
  ("Ifs.", "O(1)", "O(1)"),
  ("A conditional expression.", "O(1)", "O(1)"),
  names=["updates", "reads"])


@B
def table_strategy(updates, reads):
    if updates == 0:
        return "append only"
    if reads >= 10 * updates:
        return "copy-on-write"
    return "merge-on-read"


@O
def table_strategy(updates, reads):
    return "append only" if not updates else "copy-on-write" if reads >= 10 * updates else "merge-on-read"


Q(None, "Incremental Read Between Snapshots", "Medium", "Read only what changed",
  "Given the file lists of two snapshots, return (files added, files removed), sorted. Downstream jobs can process just the added files.",
  [((["a", "b"], ["b", "c"]), (['c'], ['a']))],
  ("Two loops.", "O(n·m)", "O(n)"),
  ("Set differences.", "O(n + m)", "O(n)"),
  names=["old", "new"])


@B
def snapshot_diff(old, new):
    return (sorted(f for f in new if f not in old), sorted(f for f in old if f not in new))


@O
def snapshot_diff(old, new):
    a, b = set(old), set(new)
    return (sorted(b - a), sorted(a - b))


Q(None, "Does This Table Need Compaction?", "Easy", "Measure small files",
  "Return (share of files under limit MB, average file MB), rounded to 2 decimals.",
  [(([10, 20, 500, 600], 128), (0.5, 282.5))],
  ("A loop.", "O(f)", "O(1)"),
  ("Generators.", "O(f)", "O(1)"),
  names=["sizes", "limit"])


@B
def small_file_stats(sizes, limit):
    small = total = 0
    for s in sizes:
        total += s
        if s < limit:
            small += 1
    return (round(small / len(sizes), 2), round(total / len(sizes), 2))


@O
def small_file_stats(sizes, limit):
    return (round(sum(s < limit for s in sizes) / len(sizes), 2), round(sum(sizes) / len(sizes), 2))
