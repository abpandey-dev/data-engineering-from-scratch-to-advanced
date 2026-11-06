from lib import *
import heapq
from collections import defaultdict


TOPIC(
    id="kafka", title="Kafka & Messaging", glyph="▤▤▤",
    blurb="The backbone of streaming: logs, topics and partitions, keys and ordering, consumer groups, offsets and lag, delivery guarantees, replication, retention and compaction, schemas. You'll build a tiny Kafka in Python.",
    theory="""
<h3>Cheat sheet</h3>
<pre><code class="py">Topic: a named log, split into partitions
Partition: ordered, append-only; each record has an offset
Key: the same key always goes to the same partition, keeping order
Consumer group: each partition goes to one member at a time
Offset: how far a group has read; lag = latest − committed
Replication: leader + followers; ISR = in-sync replicas; acks=all</code></pre>
""")


def key_partition(key, n):
    return sum(map(ord, key)) % n


Q(None, "Append to a Log", "Easy", "The core data structure",
  "Append messages to a list log and return their offsets, then read from a given offset.",
  [((["a", "b", "c"], 1), ([0, 1, 2], ['b', 'c']))],
  ("A loop for appends.", "O(n)", "O(n)"),
  ("<code>range</code> and slicing.", "O(n)", "O(n)"),
  names=["messages", "start"])


@B
def log_append(messages, start):
    log, offsets = [], []
    for m in messages:
        offsets.append(len(log))
        log.append(m)
    return (offsets, log[start:])


@O
def log_append(messages, start):
    return (list(range(len(messages))), messages[start:])


Q(None, "Choose a Partition by Key", "Easy", "Same key, same partition",
  "Send (key, value) records to partitions with sum(codes) % n. Return partition contents. Order within each key is preserved.",
  [(([("a", 1), ("b", 2), ("a", 3)], 2), [[2], [1, 3]])],
  ("A list of lists.", "O(k)", "O(k)"),
  ("Same, compactly.", "O(k)", "O(k)"),
  names=["records", "n"])


@B
def produce(records, n):
    parts = []
    for _ in range(n):
        parts.append([])
    for k, v in records:
        total = 0
        for c in k:
            total += ord(c)
        parts[total % n].append(v)
    return parts


@O
def produce(records, n):
    parts = [[] for _ in range(n)]
    for k, v in records:
        parts[sum(map(ord, k)) % n].append(v)
    return parts


Q(None, "Does Order Hold?", "Medium", "Only within a partition",
  "A consumer may read partitions in any interleaving. Given partition contents and an interleaving list of partition ids, return the sequence read.",
  [(([["a1", "a2"], ["b1"]], [1, 0, 0]), ['b1', 'a1', 'a2'])],
  ("Track an offset per partition with a list.", "O(n)", "O(p)"),
  ("Iterators, one per partition.", "O(n)", "O(p)"),
  names=["parts", "order"])


@B
def interleave(parts, order):
    offsets = [0] * len(parts)
    out = []
    for p in order:
        out.append(parts[p][offsets[p]])
        offsets[p] += 1
    return out


@O
def interleave(parts, order):
    its = [iter(p) for p in parts]
    return [next(its[p]) for p in order]


Q(None, "Consumer Group Assignment", "Medium", "Each partition goes to one member",
  "Assign partitions 0..p−1 to sorted consumers in round-robin order. Return {consumer: partitions}. Extra consumers sit idle.",
  [((4, ["c1", "c2"]), {'c1': [0, 2], 'c2': [1, 3]}), ((2, ["c1", "c2", "c3"]), {'c1': [0], 'c2': [1], 'c3': []})],
  ("A loop with an index.", "O(p + c)", "O(p)"),
  ("Slicing with a step.", "O(p + c)", "O(p)"),
  names=["p", "consumers"])


@B
def assign(p, consumers):
    names = sorted(consumers)
    out = {c: [] for c in names}
    for i in range(p):
        out[names[i % len(names)]].append(i)
    return out


@O
def assign(p, consumers):
    names = sorted(consumers)
    return {c: list(range(i, p, len(names))) for i, c in enumerate(names)}


Q(None, "Consumer Lag", "Easy", "The number to alert on",
  "Given latest offsets and committed offsets per partition, return lag per partition and in total.",
  [(({0: 100, 1: 50}, {0: 90, 1: 50}),  ({0: 10, 1: 0}, 10))],
  ("A loop.", "O(p)", "O(p)"),
  ("A comprehension.", "O(p)", "O(p)"),
  names=["latest", "committed"])


@B
def consumer_lag(latest, committed):
    lags, total = {}, 0
    for p in latest:
        lag = latest[p] - committed.get(p, 0)
        lags[p] = lag
        total += lag
    return (lags, total)


@O
def consumer_lag(latest, committed):
    lags = {p: v - committed.get(p, 0) for p, v in latest.items()}
    return (lags, sum(lags.values()))


Q(None, "How Long to Catch Up?", "Medium", "Is the consumer keeping up?",
  "With lag L, producing at in_rate and consuming at out_rate (messages per second), return seconds to catch up rounded to 1 decimal, or None if it never will.",
  [((1000, 100, 200), 10.0), ((1000, 200, 100), None)],
  ("An if, then divide.", "O(1)", "O(1)"),
  ("A conditional expression.", "O(1)", "O(1)"),
  names=["lag", "in_rate", "out_rate"])


@B
def catch_up(lag, in_rate, out_rate):
    net = out_rate - in_rate
    if net <= 0:
        return None
    return round(lag / net, 1)


@O
def catch_up(lag, in_rate, out_rate):
    return round(lag / (out_rate - in_rate), 1) if out_rate > in_rate else None


Q(None, "Partitions Needed", "Easy", "Sizing a topic",
  "Given target throughput and per-partition throughput for producers and consumers, return the partitions needed: the larger of the two, rounded up.",
  [((100, 10, 20), 10), ((100, 50, 5), 20)],
  ("Divide and compare.", "O(1)", "O(1)"),
  ("<code>ceil(max(...))</code>.", "O(1)", "O(1)"),
  names=["target", "produce_each", "consume_each"])


@B
def partitions_needed(target, produce_each, consume_each):
    a = -(-target // produce_each)
    b = -(-target // consume_each)
    return a if a > b else b


@O
def partitions_needed(target, produce_each, consume_each):
    import math
    return math.ceil(max(target / produce_each, target / consume_each))


Q(None, "Commit After Processing", "Medium", "At-least-once",
  "Process messages, committing every c. A crash happens after processing crash_after. On restart, processing resumes from the last commit. Return (all processed values in order, duplicates).",
  [((["a", "b", "c", "d", "e"], 2, 3),  (['a', 'b', 'c', 'c', 'd', 'e'], 1))],
  ("Simulate with loops.", "O(n)", "O(n)"),
  ("Compute the commit point directly.", "O(n)", "O(n)"),
  names=["messages", "c", "crash_after"])


@B
def at_least_once(messages, c, crash_after):
    done, committed = [], 0
    for i in range(crash_after):
        done.append(messages[i])
        if (i + 1) % c == 0:
            committed = i + 1
    for i in range(committed, len(messages)):
        done.append(messages[i])
    return (done, crash_after - committed)


@O
def at_least_once(messages, c, crash_after):
    committed = crash_after // c * c
    return (messages[:crash_after] + messages[committed:], crash_after - committed)


Q(None, "Idempotent Consumer", "Medium", "Exactly-once in effect",
  "Apply messages (id, delta) to a total, ignoring ids already seen. Duplicates from retries don't change the result. Return (total, applied).",
  [(([(1, 10), (2, 5), (1, 10), (3, 1)],), (16, 3))],
  ("A list of seen ids.", "O(n²)", "O(n)"),
  ("A set of ids. In production, store them in the same transaction as the result.", "O(n)", "O(n)"))


@B
def idempotent_consumer(messages):
    seen, total, applied = [], 0, 0
    for i, delta in messages:
        if i not in seen:
            seen.append(i)
            total += delta
            applied += 1
    return (total, applied)


@O
def idempotent_consumer(messages):
    unique = dict(messages)
    return (sum(unique.values()), len(unique))


Q(None, "Producer Retries Reorder", "Medium", "max.in.flight",
  "Two batches are in flight; batch 1 fails, and is retried after batch 2 succeeds. Return the log order without idempotence, and with an idempotent producer preserving order.",
  [((["b1", "b2"],),  (['b2', 'b1'], ['b1', 'b2']))],
  ("Simulate each.", "O(n)", "O(n)"),
  ("Slicing.", "O(n)", "O(n)"))


@B
def retry_order(batches):
    log = []
    log.append(batches[1])
    log.append(batches[0])
    return (log, list(batches))


@O
def retry_order(batches):
    return (batches[::-1], batches)


Q(None, "Log Compaction", "Medium", "Keep the latest per key",
  "Keep only the last record per key, and drop keys whose last value is None (a tombstone). Return remaining (offset, key, value), in offset order.",
  [(([("a", 1), ("b", 2), ("a", 3), ("b", None), ("c", 9)],), [[2, 'a', 3], [4, 'c', 9]])],
  ("For each record, check for a later one.", "O(n²)", "O(n)"),
  ("A dictionary of the last offset.", "O(n)", "O(k)"))


@B
def compact(records):
    out = []
    for i, (k, v) in enumerate(records):
        later = any(records[j][0] == k for j in range(i + 1, len(records)))
        if not later and v is not None:
            out.append([i, k, v])
    return out


@O
def compact(records):
    last = {k: i for i, (k, _) in enumerate(records)}
    return [[i, k, records[i][1]] for k, i in sorted(last.items(), key=lambda x: x[1]) if records[i][1] is not None]


Q(None, "Retention by Time and Size", "Medium", "Old data goes away",
  "Segments are (newest time, MB), oldest first. Delete segments older than retention (now − newest > hours), and then oldest ones until total ≤ max_mb. Return the remaining count and MB.",
  [(([(1, 100), (50, 100), (90, 100), (99, 100)], 100, 60, 250), (2, 200))],
  ("A loop for each rule.", "O(s)", "O(s)"),
  ("A filter, then trim.", "O(s)", "O(s)"),
  names=["segments", "now", "hours", "max_mb"])


@B
def retention(segments, now, hours, max_mb):
    kept = []
    for t, mb in segments:
        if now - t <= hours:
            kept.append((t, mb))
    while sum(m for _, m in kept) > max_mb:
        kept.pop(0)
    return (len(kept), sum(m for _, m in kept))


@O
def retention(segments, now, hours, max_mb):
    from collections import deque
    kept = deque(s for s in segments if now - s[0] <= hours)
    total = sum(m for _, m in kept)
    while total > max_mb:
        total -= kept.popleft()[1]
    return (len(kept), total)


Q(None, "In-Sync Replicas", "Medium", "Durability trade-off",
  "A replica is in sync if within max_lag of the leader's offset. Given offsets, return (ISR), and whether a write with acks=all can proceed under min_isr.",
  [(({"r1": 100, "r2": 99, "r3": 50}, "r1", 5, 2),  (['r1', 'r2'], True)), (({"r1": 100, "r2": 50}, "r1", 5, 2), (['r1'], False))],
  ("A loop.", "O(r log r)", "O(r)"),
  ("A sorted comprehension.", "O(r log r)", "O(r)"),
  names=["offsets", "leader", "max_lag", "min_isr"])


@B
def isr(offsets, leader, max_lag, min_isr):
    top = offsets[leader]
    out = []
    for r, o in offsets.items():
        if top - o <= max_lag:
            out.append(r)
    return (sorted(out), len(out) >= min_isr)


@O
def isr(offsets, leader, max_lag, min_isr):
    s = sorted(r for r, o in offsets.items() if offsets[leader] - o <= max_lag)
    return (s, len(s) >= min_isr)


Q(None, "High Watermark", "Medium", "What consumers can read",
  "Consumers only see messages replicated to all in-sync replicas: the minimum of their offsets. Return it, and how many records the leader has that aren't visible.",
  [(([100, 95, 98],),  (95, 5))],
  ("A loop for the minimum.", "O(r)", "O(1)"),
  ("<code>min</code> and <code>max</code>.", "O(r)", "O(1)"))


@B
def high_watermark(isr_offsets):
    low = isr_offsets[0]
    for o in isr_offsets:
        if o < low:
            low = o
    return (low, isr_offsets[0] - low)


@O
def high_watermark(isr_offsets):
    return (min(isr_offsets), max(isr_offsets) - min(isr_offsets))


Q(None, "Rebalance Movement", "Medium", "Eager vs sticky",
  "Given old assignment and new round-robin (sorted) after a member joins, return partitions that moved with eager (all revoke, so all) and with sticky assignment that keeps as many as possible. Sticky here keeps a partition if its old owner is below its target share.",
  [(({"c1": [0, 1, 2, 3], "c2": [4, 5, 6, 7]}, ["c1", "c2", "c3"]),  (8, 2))],
  ("Simulate with loops.", "O(p)", "O(p)"),
  ("Sticky only moves the excess.", "O(c)", "O(c)"),
  names=["old", "members"])


@B
def rebalance(old, members):
    all_parts = sum(old.values(), [])
    target = len(all_parts) // len(members)
    extra = len(all_parts) % len(members)
    moved = 0
    for i, m in enumerate(sorted(members)):
        share = target + (1 if i < extra else 0)
        have = len(old.get(m, []))
        if have > share:
            moved += have - share
    return (len(all_parts), moved)


@O
def rebalance(old, members):
    total = sum(map(len, old.values()))
    q, r = divmod(total, len(members))
    return (total, sum(max(0, len(old.get(m, [])) - (q + (i < r))) for i, m in enumerate(sorted(members))))


Q(None, "Schema Compatibility", "Medium", "Don't break consumers",
  "Backward compatible: new consumers can read old data, so any added field needs a default, and removing is fine. Fields are {name: has_default}. Return (compatible, problem fields sorted).",
  [(({"id": False}, {"id": False, "x": True}), (True, [])), (({"id": False}, {"id": False, "x": False}), (False, ['x']))],
  ("A loop.", "O(f)", "O(f)"),
  ("A comprehension.", "O(f log f)", "O(f)"),
  names=["old", "new"])


@B
def backward_compatible(old, new):
    problems = []
    for name, has_default in new.items():
        if name not in old and not has_default:
            problems.append(name)
    return (not problems, sorted(problems))


@O
def backward_compatible(old, new):
    bad = sorted(n for n, d in new.items() if n not in old and not d)
    return (not bad, bad)


Q(None, "Batching Trade-off", "Easy", "Latency vs throughput",
  "A producer sends when a batch reaches size or after linger ms. At rate messages per ms, return the time to fill a batch rounded to 2 decimals, and the actual wait.",
  [((1000, 5, 10), (200.0, 10)), ((100, 50, 10), (2.0, 2.0))],
  ("Divide and compare.", "O(1)", "O(1)"),
  ("<code>min</code>.", "O(1)", "O(1)"),
  names=["batch", "rate", "linger"])


@B
def batching(batch, rate, linger):
    fill = batch / rate
    wait = fill if fill < linger else linger
    return (round(fill, 2), wait)


@O
def batching(batch, rate, linger):
    return (round(batch / rate, 2), min(batch / rate, linger))


Q(None, "Kafka Disk Sizing", "Medium", "Capacity planning",
  "Return TB needed for rate MB/s, retention days and replication factor. TB = 10⁶ MB. Round to 2 decimals.",
  [((50, 7, 3),  90.72)],
  ("Step by step.", "O(1)", "O(1)"),
  ("One line.", "O(1)", "O(1)"),
  names=["mb_s", "days", "replicas"])


@B
def kafka_disk(mb_s, days, replicas):
    per_day = mb_s * 86400
    total = per_day * days * replicas
    return round(total / 1e6, 2)


@O
def kafka_disk(mb_s, days, replicas):
    return round(mb_s * 86400 * days * replicas / 1e6, 2)


Q(None, "Find the Hot Partition", "Easy", "A bad key choice",
  "Given partition message counts, return (largest partition, share of all traffic rounded to 2 decimals). Choosing a key like country can overload one partition.",
  [(([100, 900, 50, 50],),  (1, 0.82))],
  ("A loop.", "O(p)", "O(1)"),
  ("<code>max</code>.", "O(p)", "O(1)"))


@B
def hot_partition(counts):
    top, total = 0, 0
    for i, c in enumerate(counts):
        total += c
        if c > counts[top]:
            top = i
    return (top, round(counts[top] / total, 2))


@O
def hot_partition(counts):
    top = counts.index(max(counts))
    return (top, round(max(counts) / sum(counts), 2))


Q(None, "Outbox Pattern", "Hard", "Database and Kafka together",
  "Writing to a database and Kafka separately can fail halfway. Instead, write the row and an outbox event in one transaction, and a relay publishes them. Simulate: for each order, if crash is at 'after_db', compare which rows and events exist with dual writes and with the outbox. Return ((dual rows, dual events), (outbox rows, outbox events)).",
  [((3,),  ((3, 2), (3, 3)))],
  ("Simulate each with lists.", "O(n)", "O(n)"),
  ("Reason it out.", "O(1)", "O(1)"),
  names=["orders"])


@B
def outbox(orders):
    # dual writes: the crash on the last order happens after the DB write, before Kafka
    db, kafka = [], []
    for i in range(orders):
        db.append(i)
        if i < orders - 1:
            kafka.append(i)
    # outbox: the row and event commit together, and the relay publishes them all
    rows, events = [], []
    for i in range(orders):
        rows.append(i)
        events.append(i)
    return ((len(db), len(kafka)), (len(rows), len(events)))


@O
def outbox(orders):
    return ((orders, orders - 1), (orders, orders))
