from lib import *
import hashlib


TOPIC(
    id="pipeline-patterns", title="Pipeline Patterns", glyph="⟲",
    blurb="The heart of the job: idempotent loads, incremental processing, watermarks, merge and upsert, change data capture, backfills, late data, deduplication, dead-letter queues and designing for failure.",
    theory="""
<h3>Cheat sheet</h3>
<pre><code class="py">Idempotent: running it twice gives the same result as once.
Full load:   replace everything; simple, costs grow
Incremental: only what's new, using a high-watermark
Upsert:      update if the key exists, otherwise insert
Overwrite partition: the simplest idempotent batch pattern
CDC:         stream inserts, updates and deletes from the database log</code></pre>
""")


Q(None, "Naive Append Isn't Idempotent", "Easy", "The classic bug",
  "Show the difference: running a load twice with append vs with overwrite-by-day. Return the row counts (append, overwrite). Rows are lists of ids.",
  [(([1, 2, 3], 2), (6, 3))],
  ("Simulate each with a list and a dictionary.", "O(r·n)", "O(r·n)"),
  ("Same simulation, compactly.", "O(r·n)", "O(n)"),
  names=["rows", "runs"])


@B
def append_vs_overwrite(rows, runs):
    table = []
    for _ in range(runs):
        for r in rows:
            table.append(r)
    partition = {}
    for _ in range(runs):
        partition["day"] = list(rows)
    return (len(table), len(partition["day"]))


@O
def append_vs_overwrite(rows, runs):
    return (len(rows) * runs, len(rows))


Q(None, "Overwrite a Partition", "Easy", "The simplest safe pattern",
  "table maps day to rows. Load new rows for a day, replacing any existing ones. Return the table with days sorted.",
  [(({"d1": [1], "d2": [2, 3]}, "d2", [9]), {'d1': [1], 'd2': [9]}), (({"d1": [1]}, "d3", [7]), {'d1': [1], 'd3': [7]})],
  ("Rebuild the dictionary in a loop.", "O(d)", "O(d)"),
  ("Merge with a dictionary union.", "O(d)", "O(d)"),
  names=["table", "day", "rows"])


@B
def overwrite_partition(table, day, rows):
    out = {}
    for d in table:
        if d != day:
            out[d] = table[d]
    out[day] = rows
    return dict(sorted(out.items()))


@O
def overwrite_partition(table, day, rows):
    return dict(sorted((table | {day: rows}).items()))


Q(None, "Upsert (MERGE)", "Medium", "Insert or update by key",
  "Merge incoming rows into target by id: update existing, insert new. Return (rows sorted by id, inserted count, updated count).",
  [(([{"id": 1, "v": "a"}, {"id": 2, "v": "b"}], [{"id": 2, "v": "B"}, {"id": 3, "v": "c"}]), ([{'id': 1, 'v': 'a'}, {'id': 2, 'v': 'B'}, {'id': 3, 'v': 'c'}], 1, 1))],
  ("Search the target for each row.", "O(n·m)", "O(n + m)"),
  ("A dictionary keyed by id.", "O(n + m)", "O(n + m)"),
  names=["target", "incoming"])


@B
def upsert(target, incoming):
    out = [dict(r) for r in target]
    inserted = updated = 0
    for row in incoming:
        for existing in out:
            if existing["id"] == row["id"]:
                existing.update(row)
                updated += 1
                break
        else:
            out.append(dict(row))
            inserted += 1
    return (sorted(out, key=lambda r: r["id"]), inserted, updated)


@O
def upsert(target, incoming):
    table = {r["id"]: r for r in target}
    updated = sum(r["id"] in table for r in incoming)
    table.update({r["id"]: r for r in incoming})
    return ([table[k] for k in sorted(table)], len(incoming) - updated, updated)


Q(None, "Upsert Keeps Only Newer", "Medium", "Out-of-order updates",
  "Rows have id, v and ts. Apply incoming only if its ts is newer than what's stored. Return rows by id.",
  [(([{"id": 1, "v": "new", "ts": 20}], [{"id": 1, "v": "old", "ts": 10}, {"id": 2, "v": "x", "ts": 5}]), [{'id': 1, 'v': 'new', 'ts': 20}, {'id': 2, 'v': 'x', 'ts': 5}])],
  ("Search for each row.", "O(n·m)", "O(n + m)"),
  ("A dictionary with a comparison.", "O(n + m)", "O(n + m)"),
  names=["target", "incoming"])


@B
def upsert_newer(target, incoming):
    out = [dict(r) for r in target]
    for row in incoming:
        for existing in out:
            if existing["id"] == row["id"]:
                if row["ts"] > existing["ts"]:
                    existing.update(row)
                break
        else:
            out.append(dict(row))
    return sorted(out, key=lambda r: r["id"])


@O
def upsert_newer(target, incoming):
    table = {r["id"]: r for r in target}
    for r in incoming:
        if r["id"] not in table or r["ts"] > table[r["id"]]["ts"]:
            table[r["id"]] = r
    return [table[k] for k in sorted(table)]


Q(None, "High-Watermark Incremental Load", "Medium", "Only what's new",
  "Rows have (id, updated). Given the last watermark, return (rows to load, new watermark). Rows with updated > watermark are new. If there are none, the watermark stays.",
  [(([(1, 10), (2, 20), (3, 30)], 15), ([(2, 20), (3, 30)], 30)), (([(1, 10)], 15), ([], 15))],
  ("A loop tracking the maximum.", "O(n)", "O(k)"),
  ("A comprehension, then <code>max</code> with a default.", "O(n)", "O(k)"),
  names=["rows", "watermark"])


@B
def incremental(rows, watermark):
    new, high = [], watermark
    for r in rows:
        if r[1] > watermark:
            new.append(r)
            if r[1] > high:
                high = r[1]
    return (new, high)


@O
def incremental(rows, watermark):
    new = [r for r in rows if r[1] > watermark]
    return (new, max((r[1] for r in new), default=watermark))


Q(None, "Watermark With a Lookback", "Medium", "Don't miss late rows",
  "A strict watermark misses rows committed late with an older timestamp. Re-read with a lookback: rows with updated > watermark − lookback. Then dedupe by id, keeping the latest. Return ids to apply, sorted.",
  [(([(1, 100), (2, 95), (3, 120)], 100, 10, {1: 100}), [2, 3])],
  ("Filter and compare in loops.", "O(n)", "O(n)"),
  ("A comprehension, skipping rows already applied at that version.", "O(n)", "O(n)"),
  names=["rows", "watermark", "lookback", "applied"])


@B
def lookback_ids(rows, watermark, lookback, applied):
    out = []
    for i, ts in rows:
        if ts > watermark - lookback and applied.get(i) != ts:
            out.append(i)
    return sorted(out)


@O
def lookback_ids(rows, watermark, lookback, applied):
    return sorted(i for i, ts in rows if ts > watermark - lookback and applied.get(i) != ts)


Q(None, "Apply Change Data Capture", "Medium", "Replay inserts, updates and deletes",
  "Events are (op, id, value), with op in 'c' create, 'u' update, 'd' delete, in log order. Apply them to a state dictionary. Return it sorted.",
  [(({1: "a"}, [("c", 2, "b"), ("u", 1, "A"), ("d", 2, None), ("c", 3, "c")]), {1: 'A', 3: 'c'})],
  ("Ifs for each operation.", "O(n)", "O(s)"),
  ("Same logic, with a compact conditional.", "O(n)", "O(s)"),
  names=["state", "events"])


@B
def apply_cdc(state, events):
    out = dict(state)
    for op, key, value in events:
        if op == "c" or op == "u":
            out[key] = value
        elif op == "d":
            if key in out:
                del out[key]
    return dict(sorted(out.items()))


@O
def apply_cdc(state, events):
    out = dict(state)
    for op, key, value in events:
        out.pop(key, None) if op == "d" else out.__setitem__(key, value)
    return dict(sorted(out.items()))


Q(None, "Compact a CDC Batch", "Medium", "Last event per key wins",
  "Reduce events to the final operation per id, in id order. A key created then deleted in the same batch still needs a delete in case it existed before.",
  [(([("c", 1, "a"), ("u", 1, "b"), ("c", 2, "x"), ("d", 2, None)],), [['u', 1, 'b'], ['d', 2, None]])],
  ("For each id, scan for its last event.", "O(n²)", "O(k)"),
  ("A dictionary overwrites as it goes.", "O(n)", "O(k)"))


@B
def compact_cdc(events):
    ids = sorted({e[1] for e in events})
    out = []
    for i in ids:
        last = None
        for e in events:
            if e[1] == i:
                last = e
        out.append(list(last))
    return out


@O
def compact_cdc(events):
    last = {e[1]: e for e in events}
    return [list(last[k]) for k in sorted(last)]


Q(None, "Soft Deletes", "Easy", "Keep the history",
  "Mark rows deleted rather than removing them. Return (rows with deleted flags, ids of visible rows).",
  [(([{"id": 1}, {"id": 2}], [2]), ([{'id': 1, 'deleted': False}, {'id': 2, 'deleted': True}], [1]))],
  ("A loop.", "O(n·d)", "O(n)"),
  ("A set for membership.", "O(n + d)", "O(n)"),
  names=["rows", "deleted"])


@B
def soft_delete(rows, deleted):
    out = []
    for r in rows:
        out.append({**r, "deleted": r["id"] in deleted})
    return (out, [r["id"] for r in out if not r["deleted"]])


@O
def soft_delete(rows, deleted):
    gone = set(deleted)
    out = [{**r, "deleted": r["id"] in gone} for r in rows]
    return (out, [r["id"] for r in rows if r["id"] not in gone])


Q(None, "Plan a Backfill", "Medium", "Reprocess history in pieces",
  "Split days from start to end (integers, inclusive) into batches of size at most chunk, as [first, last] pairs.",
  [((1, 10, 4), [[1, 4], [5, 8], [9, 10]]), ((5, 5, 3), [[5, 5]])],
  ("A while loop.", "O(d/c)", "O(d/c)"),
  ("<code>range</code> with a step.", "O(d/c)", "O(d/c)"),
  names=["start", "end", "chunk"])


@B
def backfill_plan(start, end, chunk):
    out = []
    a = start
    while a <= end:
        b = a + chunk - 1
        if b > end:
            b = end
        out.append([a, b])
        a = b + 1
    return out


@O
def backfill_plan(start, end, chunk):
    return [[a, min(a + chunk - 1, end)] for a in range(start, end + 1, chunk)]


Q(None, "Find What's Left to Backfill", "Easy", "Safe to resume",
  "Given days wanted and days done, return remaining days, sorted. A resumable job picks up here after a crash.",
  [(([1, 2, 3, 4], [2, 3]), [1, 4])],
  ("<code>not in</code> on a list.", "O(n·m)", "O(n)"),
  ("Set difference.", "O(n + m)", "O(n)"),
  names=["wanted", "done"])


@B
def remaining_days(wanted, done):
    return sorted(d for d in wanted if d not in done)


@O
def remaining_days(wanted, done):
    return sorted(set(wanted) - set(done))


Q(None, "Write-Audit-Publish", "Medium", "Never show bad data",
  "Write to a staging list, audit with checks, and only publish if all pass. Return (published table, failed checks). Checks here: no null ids, and row count ≥ min_rows.",
  [(([1, 2], [3, 4], 1), ([3, 4], [])), (([1, 2], [3, None], 1), ([1, 2], ['null_id'])), (([1, 2], [], 1), ([1, 2], ['too_few_rows']))],
  ("A sequence of ifs.", "O(n)", "O(n)"),
  ("A dictionary of checks.", "O(n)", "O(n)"),
  names=["current", "staged", "min_rows"])


@B
def write_audit_publish(current, staged, min_rows):
    failed = []
    if None in staged:
        failed.append("null_id")
    if len(staged) < min_rows:
        failed.append("too_few_rows")
    if failed:
        return (current, failed)
    return (staged, failed)


@O
def write_audit_publish(current, staged, min_rows):
    checks = {"null_id": None not in staged, "too_few_rows": len(staged) >= min_rows}
    failed = [n for n, ok in checks.items() if not ok]
    return (current if failed else staged, failed)


Q(None, "Dead-Letter Queue", "Medium", "One bad row shouldn't stop the pipeline",
  "Process messages, sending failures to a dead-letter list with the reason. Stop if the bad share exceeds max_bad. Return (good, dead-letter, status 'ok' or 'halted').",
  [((["1", "x", "3"], 0.5), ([1, 3], [['x', 'not a number']], 'ok')), ((["x", "y", "3"], 0.5), ([3], [['x', 'not a number'], ['y', 'not a number']], 'halted'))],
  ("A loop, then a check.", "O(n)", "O(n)"),
  ("The same, with a small parse helper.", "O(n)", "O(n)"),
  names=["messages", "max_bad"])


@B
def dlq(messages, max_bad):
    good, dead = [], []
    for m in messages:
        try:
            good.append(int(m))
        except ValueError:
            dead.append([m, "not a number"])
    status = "halted" if len(dead) / len(messages) > max_bad else "ok"
    return (good, dead, status)


@O
def dlq(messages, max_bad):
    good = [int(m) for m in messages if m.lstrip("-").isdigit()]
    dead = [[m, "not a number"] for m in messages if not m.lstrip("-").isdigit()]
    return (good, dead, "halted" if len(dead) > max_bad * len(messages) else "ok")


Q(None, "Row Hash for Change Detection", "Medium", "What actually changed?",
  "Compare snapshots keyed by id: hash each row's values with md5 of 'a|b' style. Return (new ids, changed ids, removed ids), sorted.",
  [(({1: ["a", "b"], 2: ["c", "d"]}, {1: ["a", "B"], 3: ["e", "f"], 2: ["c", "d"]}),  ([3], [1], []))],
  ("Compare values directly in loops.", "O(n·c)", "O(n)"),
  ("Hash once, then set operations.", "O(n·c)", "O(n)"),
  names=["old", "new"])


@B
def diff_snapshots(old, new):
    def h(values):
        return hashlib.md5("|".join(values).encode()).hexdigest()
    added, changed, removed = [], [], []
    for k in new:
        if k not in old:
            added.append(k)
        elif h(new[k]) != h(old[k]):
            changed.append(k)
    for k in old:
        if k not in new:
            removed.append(k)
    return (sorted(added), sorted(changed), sorted(removed))


@O
def diff_snapshots(old, new):
    h = lambda v: hashlib.md5("|".join(v).encode()).hexdigest()
    a, b = {k: h(v) for k, v in old.items()}, {k: h(v) for k, v in new.items()}
    return (sorted(b.keys() - a.keys()), sorted(k for k in a.keys() & b.keys() if a[k] != b[k]), sorted(a.keys() - b.keys()))


Q(None, "Dedupe a Stream With a TTL", "Hard", "Don't remember forever",
  "Events are (id, time). Drop an event if the same id was seen within ttl seconds. Return kept events. Memory must stay bounded in a real system, by evicting expired ids.",
  [(([("a", 1), ("b", 2), ("a", 5), ("a", 20)], 10), [['a', 1], ['b', 2], ['a', 20]])],
  ("Scan earlier kept events each time.", "O(n²)", "O(n)"),
  ("A dictionary of last-kept time per id.", "O(n)", "O(k)"),
  names=["events", "ttl"])


@B
def ttl_dedupe(events, ttl):
    kept = []
    for i, t in events:
        recent = [k for k in kept if k[0] == i and t - k[1] <= ttl]
        if not recent:
            kept.append([i, t])
    return kept


@O
def ttl_dedupe(events, ttl):
    last, kept = {}, []
    for i, t in events:
        if i not in last or t - last[i] > ttl:
            kept.append([i, t])
            last[i] = t
    return kept


Q(None, "Which Partitions to Rerun?", "Medium", "Late data",
  "Given late rows with event days, and a table of already-loaded days, return the days to reprocess, sorted, ignoring those older than the retention limit.",
  [(([5, 3, 3, 1], [1, 2, 3, 4, 5], 2),  [3, 5])],
  ("Filter in a loop.", "O(n·d)", "O(n)"),
  ("Set operations.", "O(n + d)", "O(n)"),
  names=["late_days", "loaded", "oldest"])


@B
def rerun_days(late_days, loaded, oldest):
    out = []
    for d in late_days:
        if d in loaded and d >= oldest and d not in out:
            out.append(d)
    return sorted(out)


@O
def rerun_days(late_days, loaded, oldest):
    return sorted(d for d in set(late_days) & set(loaded) if d >= oldest)


Q(None, "Atomic Swap", "Medium", "Readers never see half a load",
  "Simulate: build a new table version, then flip a pointer. If the build fails midway, the pointer doesn't move. Return (current version's data, pointer).",
  [(({"v1": [1, 2]}, "v1", [3, 4], True), ([3, 4], 'v2')), (({"v1": [1, 2]}, "v1", [3, 4], False), ([1, 2], 'v1'))],
  ("Ifs.", "O(n)", "O(n)"),
  ("Compact.", "O(n)", "O(n)"),
  names=["versions", "pointer", "new_rows", "build_ok"])


@B
def atomic_swap(versions, pointer, new_rows, build_ok):
    store = dict(versions)
    if build_ok:
        name = "v" + str(len(store) + 1)
        store[name] = new_rows
        pointer = name
    return (store[pointer], pointer)


@O
def atomic_swap(versions, pointer, new_rows, build_ok):
    return (new_rows, f"v{len(versions) + 1}") if build_ok else (versions[pointer], pointer)


Q(None, "Reconcile Source and Target", "Easy", "Did everything arrive?",
  "Compare per-day counts. Return days where they differ, as [day, source, target], sorted. Missing days count as 0.",
  [(({"d1": 10, "d2": 5}, {"d1": 10, "d3": 2}),  [['d2', 5, 0], ['d3', 0, 2]])],
  ("Union of keys in a loop.", "O(d)", "O(d)"),
  ("A comprehension over the union.", "O(d log d)", "O(d)"),
  names=["source", "target"])


@B
def reconcile(source, target):
    out = []
    for d in sorted(set(source) | set(target)):
        a, b = source.get(d, 0), target.get(d, 0)
        if a != b:
            out.append([d, a, b])
    return out


@O
def reconcile(source, target):
    return [[d, source.get(d, 0), target.get(d, 0)] for d in sorted(source.keys() | target.keys()) if source.get(d, 0) != target.get(d, 0)]


Q(None, "Checkpoint and Resume", "Medium", "Don't start from zero",
  "Process items, saving a checkpoint after each batch. Simulate a crash at crash_at items processed, then resume from the last checkpoint. Return (total item-processings, items reprocessed).",
  [((10, 3, 7), (11, 1)), ((10, 5, 5), (10, 0))],
  ("Simulate in a loop.", "O(n)", "O(1)"),
  ("Reprocessed = crash_at mod batch.", "O(1)", "O(1)"),
  names=["n", "batch", "crash_at"])


@B
def checkpoint_cost(n, batch, crash_at):
    done = checkpoint = 0
    while done < crash_at:
        done += 1
        if done % batch == 0:
            checkpoint = done
    redo = done - checkpoint
    return (done + (n - checkpoint), redo)


@O
def checkpoint_cost(n, batch, crash_at):
    redo = crash_at % batch
    return (n + redo, redo)


Q(None, "Choose Full or Incremental", "Easy", "Simple until it isn't",
  "Compare daily costs: a full load reads total_gb; an incremental load reads changed_gb plus overhead_gb. Return the cheaper option and its GB; on a tie, prefer 'full' for simplicity.",
  [((10, 1, 2), ['incremental', 3]), ((3, 1, 2), ['full', 3])],
  ("Ifs.", "O(1)", "O(1)"),
  ("A conditional expression.", "O(1)", "O(1)"),
  names=["total_gb", "changed_gb", "overhead_gb"], post=list)


@B
def full_or_incremental(total_gb, changed_gb, overhead_gb):
    inc = changed_gb + overhead_gb
    if inc < total_gb:
        return ("incremental", inc)
    return ("full", total_gb)


@O
def full_or_incremental(total_gb, changed_gb, overhead_gb):
    inc = changed_gb + overhead_gb
    return ("incremental", inc) if inc < total_gb else ("full", total_gb)
