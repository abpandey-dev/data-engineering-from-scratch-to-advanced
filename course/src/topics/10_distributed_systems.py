from lib import *
import hashlib
import bisect
import math


TOPIC(
    id="distributed-systems", title="Distributed Systems", glyph="⬡⬡⬡",
    blurb="Why big data tools work the way they do: partitioning, MapReduce, replication, quorums, consistent hashing, CAP, failures, Amdahl's law and exactly-once. Understand this and Spark and Kafka make sense.",
    theory="""
<h3>Cheat sheet</h3>
<pre><code class="py">Scale up: bigger machine       Scale out: more machines
Partition: split data          Replicate: copy data
Quorum: R + W > N means reads see the latest write
CAP: during a network partition, choose consistency or availability
Amdahl: speedup is limited by the part that can't run in parallel</code></pre>
""")


def h(key):
    return int(hashlib.md5(str(key).encode()).hexdigest(), 16)


Q(None, "Word Count With MapReduce", "Easy", "The original big data idea",
  "Implement map (emit (word, 1)), shuffle (group by word) and reduce (sum). Return counts with sorted keys.",
  [((["a b a", "b c"],), {'a': 2, 'b': 2, 'c': 1})],
  ("Three explicit phases.", "O(w)", "O(k)"),
  ("<code>Counter</code> on one machine; the phases matter when data's spread over many.", "O(w)", "O(k)"))


@B
def word_count(lines):
    mapped = []
    for line in lines:
        for word in line.split():
            mapped.append((word, 1))
    groups = {}
    for word, one in mapped:
        groups.setdefault(word, []).append(one)
    return {word: sum(groups[word]) for word in sorted(groups)}


@O
def word_count(lines):
    from collections import Counter
    return dict(sorted(Counter(w for l in lines for w in l.split()).items()))


Q(None, "Hash Partitioning", "Easy", "Where does each key live?",
  "Send each key to partition (sum of character codes) mod n. Return lists of keys per partition.",
  [((["a", "b", "c", "a"], 2), [['b'], ['a', 'c', 'a']])],
  ("A list of lists.", "O(k)", "O(k)"),
  ("Same, with a comprehension for the setup.", "O(k)", "O(k)"),
  names=["keys", "n"])


@B
def hash_partition(keys, n):
    parts = []
    for _ in range(n):
        parts.append([])
    for k in keys:
        total = 0
        for ch in k:
            total += ord(ch)
        parts[total % n].append(k)
    return parts


@O
def hash_partition(keys, n):
    parts = [[] for _ in range(n)]
    for k in keys:
        parts[sum(map(ord, k)) % n].append(k)
    return parts


Q(None, "Range Partitioning", "Medium", "Sorted across machines",
  "Split boundaries define partitions: x goes to the first partition whose upper bound is greater than x. Return partition index for each value.",
  [(([5, 15, 25, 10], [10, 20]), [0, 1, 2, 1])],
  ("Scan the boundaries.", "O(n·b)", "O(n)"),
  ("<code>bisect</code>.", "O(n log b)", "O(n)"),
  names=["values", "bounds"])


@B
def range_partition(values, bounds):
    out = []
    for v in values:
        i = 0
        while i < len(bounds) and v >= bounds[i]:
            i += 1
        out.append(i)
    return out


@O
def range_partition(values, bounds):
    return [bisect.bisect_right(bounds, v) for v in values]


Q(None, "Measure Skew", "Medium", "One slow partition slows everything",
  "Given partition sizes, return (largest ÷ average, rounded to 2 decimals; the job time as the largest, in seconds at rate rows per second).",
  [(([100, 100, 100, 100], 10), (1.0, 10.0)), (([10, 10, 10, 370], 10), (3.7, 37.0))],
  ("Compute by hand.", "O(p)", "O(1)"),
  ("Built-ins.", "O(p)", "O(1)"),
  names=["sizes", "rate"])


@B
def skew(sizes, rate):
    total = big = 0
    for s in sizes:
        total += s
        if s > big:
            big = s
    return (round(big / (total / len(sizes)), 2), big / rate)


@O
def skew(sizes, rate):
    return (round(max(sizes) * len(sizes) / sum(sizes), 2), max(sizes) / rate)


Q(None, "Salting a Hot Key", "Medium", "Break up skew",
  "Split a hot key's rows across s sub-keys in turn ('key#0', 'key#1', …). Return row counts per sub-key, sorted by name.",
  [((["us"] * 7, 3), {'us#0': 3, 'us#1': 2, 'us#2': 2})],
  ("A dictionary with a counter.", "O(n)", "O(s)"),
  ("<code>Counter</code>.", "O(n)", "O(s)"),
  names=["rows", "s"])


@B
def salt(rows, s):
    counts = {}
    for i, r in enumerate(rows):
        key = f"{r}#{i % s}"
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


@O
def salt(rows, s):
    from collections import Counter
    return dict(sorted(Counter(f"{r}#{i % s}" for i, r in enumerate(rows)).items()))


Q(None, "Rehash Cost: Mod vs Consistent", "Hard", "Adding a machine",
  "Keys are 0 to n−1. Return the share that move when going from a to b machines with id % machines, rounded to 4 decimals.",
  [((1000, 4, 5), 0.8), ((1000, 100, 101), 0.9)],
  ("Count in a loop.", "O(n)", "O(1)"),
  ("A generator with sum.", "O(n)", "O(1)"),
  names=["n", "a", "b"])


@B
def moved_share(n, a, b):
    moved = 0
    for k in range(n):
        if k % a != k % b:
            moved += 1
    return round(moved / n, 4)


@O
def moved_share(n, a, b):
    return round(sum(k % a != k % b for k in range(n)) / n, 4)


Q(None, "Consistent Hashing", "Hard", "Move little when machines change",
  "Place nodes on a ring at hash(node) % 360 (hash = md5 as an integer). A key belongs to the first node clockwise. Return the share of keys 'k0'..'k{n−1}' that move when a node is added, rounded to 2 decimals.",
  [((["a", "b", "c", "d"], "e", 1000), 0.38)],
  ("Scan nodes for each key.", "O(n·m)", "O(m)"),
  ("Sort the ring, and use binary search.", "O((n + m) log m)", "O(m)"),
  names=["nodes", "new", "n"])


@B
def ring_moved(nodes, new, n):
    def h2(s):
        return int(hashlib.md5(s.encode()).hexdigest(), 16) % 360

    def owner(key, members):
        pos = h2(key)
        best, best_d = None, 999
        for m in members:
            d = (h2(m) - pos) % 360
            if d < best_d or (d == best_d and m < best):
                best, best_d = m, d
        return best
    moved = sum(owner(f"k{i}", nodes) != owner(f"k{i}", nodes + [new]) for i in range(n))
    return round(moved / n, 2)


@O
def ring_moved(nodes, new, n):
    def h2(s):
        return int(hashlib.md5(s.encode()).hexdigest(), 16) % 360

    def ring(members):
        return sorted((h2(m), m) for m in members)

    def owner(key, r):
        i = bisect.bisect_left(r, (h2(key), ""))
        return r[i % len(r)][1]
    a, b = ring(nodes), ring(nodes + [new])
    return round(sum(owner(f"k{i}", a) != owner(f"k{i}", b) for i in range(n)) / n, 2)


Q(None, "Quorum Reads and Writes", "Medium", "R + W > N",
  "With N replicas, W write acks and R read acks: return whether reads must see the latest write, and how many failures writes and reads each tolerate.",
  [((3, 2, 2), (True, 1, 1)), ((3, 1, 1), (False, 2, 2)), ((5, 3, 3), (True, 2, 2))],
  ("Check by reasoning.", "O(1)", "O(1)"),
  ("A one-line formula.", "O(1)", "O(1)"),
  names=["n", "w", "r"])


@B
def quorum(n, w, r):
    overlap = r + w > n
    write_fail = n - w
    read_fail = n - r
    return (overlap, write_fail, read_fail)


@O
def quorum(n, w, r):
    return (r + w > n, n - w, n - r)


Q(None, "Replication Lag: Stale Read?", "Easy", "Eventually consistent",
  "A write happened at t_write and reached a replica after lag. Return whether a read at t_read sees it.",
  [((10, 5, 14), False), ((10, 5, 15), True)],
  ("Compute when it arrives.", "O(1)", "O(1)"),
  ("One comparison.", "O(1)", "O(1)"),
  names=["t_write", "lag", "t_read"])


@B
def sees_write(t_write, lag, t_read):
    arrives = t_write + lag
    return t_read >= arrives


@O
def sees_write(t_write, lag, t_read):
    return t_read - t_write >= lag


Q(None, "Amdahl's Law", "Medium", "Why more machines stop helping",
  "With parallel share p and n workers, speedup = 1 / ((1 − p) + p/n). Return it rounded to 2 decimals.",
  [((0.95, 10), 6.9), ((0.95, 1000), 19.63), ((0.5, 1000), 2.0)],
  ("Compute the serial and parallel parts.", "O(1)", "O(1)"),
  ("One formula.", "O(1)", "O(1)"),
  names=["p", "n"])


@B
def amdahl(p, n):
    serial = 1 - p
    parallel = p / n
    return round(1 / (serial + parallel), 2)


@O
def amdahl(p, n):
    return round(1 / ((1 - p) + p / n), 2)


Q(None, "Chance of Failure at Scale", "Easy", "Failure is normal",
  "If a machine fails with probability p per day, return the chance at least one of n fails, and expected failures a day, rounded to 4 decimals.",
  [((0.001, 1000), (0.6323, 1.0)), ((0.001, 10), (0.01, 0.01))],
  ("Multiply survival in a loop.", "O(n)", "O(1)"),
  ("A power.", "O(1)", "O(1)"),
  names=["p", "n"])


@B
def failure_chance(p, n):
    survive = 1.0
    for _ in range(n):
        survive *= 1 - p
    return (round(1 - survive, 4), round(p * n, 4))


@O
def failure_chance(p, n):
    return (round(1 - (1 - p) ** n, 4), round(p * n, 4))


Q(None, "Retries Without Double Effects", "Medium", "Idempotency keys",
  "Requests are (key, amount); retries repeat a key. Apply each key once, and return (total, duplicates ignored).",
  [(([("a", 10), ("b", 5), ("a", 10)],), (15, 1))],
  ("A list of seen keys.", "O(n²)", "O(n)"),
  ("A set.", "O(n)", "O(n)"))


@B
def idempotent_total(requests):
    seen, total, dupes = [], 0, 0
    for key, amount in requests:
        if key in seen:
            dupes += 1
        else:
            seen.append(key)
            total += amount
    return (total, dupes)


@O
def idempotent_total(requests):
    first = {}
    for key, amount in requests:
        first.setdefault(key, amount)
    return (sum(first.values()), len(requests) - len(first))


Q(None, "Delivery Semantics", "Medium", "At most, at least, exactly once",
  "A consumer handles messages 1 to n and crashes around message c. Committing before processing loses the next message; committing after processing repeats message c. Return (messages processed at least once with commit-before, total processings with commit-after).",
  [((5, 3),  (4, 6))],
  ("Simulate each order.", "O(n)", "O(n)"),
  ("Reason it out: at-most-once loses none of the done ones here, and at-least-once does one extra.", "O(1)", "O(1)"),
  names=["n", "c"])


@B
def delivery(n, c):
    # commit-after: crash before committing c, so c is read and processed again
    after = 0
    committed = 0
    for m in range(1, c + 1):
        after += 1
        if m < c:
            committed = m
    for m in range(committed + 1, n + 1):
        after += 1
    # commit-before: message c+1 was committed but never processed
    before = set(range(1, c + 1)) | set(range(c + 2, n + 1))
    return (len(before), after)


@O
def delivery(n, c):
    return (n - 1, n + 1)


Q(None, "Vector Clocks: Which Came First?", "Hard", "No shared clock",
  "Compare two vector clocks (lists). Return 'before', 'after', 'equal' or 'concurrent'.",
  [(([1, 2], [1, 3]), 'before'), (([2, 1], [1, 2]), 'concurrent'), (([1, 1], [1, 1]), 'equal')],
  ("Track flags in a loop.", "O(n)", "O(1)"),
  ("<code>all</code> twice.", "O(n)", "O(1)"),
  names=["a", "b"])


@B
def clock_order(a, b):
    smaller = bigger = False
    for x, y in zip(a, b):
        if x < y:
            smaller = True
        if x > y:
            bigger = True
    if smaller and bigger:
        return "concurrent"
    if smaller:
        return "before"
    if bigger:
        return "after"
    return "equal"


@O
def clock_order(a, b):
    le, ge = all(x <= y for x, y in zip(a, b)), all(x >= y for x, y in zip(a, b))
    return "equal" if le and ge else "before" if le else "after" if ge else "concurrent"


Q(None, "Leader Election by Majority", "Medium", "Who's in charge?",
  "Given votes per candidate and total nodes, return the winner with a strict majority, else None. A majority prevents two leaders in a split.",
  [(({"a": 3, "b": 2}, 5), 'a'), (({"a": 2, "b": 2}, 5), None)],
  ("A loop.", "O(c)", "O(1)"),
  ("<code>next</code> with a generator.", "O(c)", "O(1)"),
  names=["votes", "nodes"])


@B
def leader(votes, nodes):
    for name, count in votes.items():
        if count > nodes / 2:
            return name
    return None


@O
def leader(votes, nodes):
    return next((c for c, v in votes.items() if 2 * v > nodes), None)


Q(None, "Heartbeats: Who's Dead?", "Easy", "Detecting failures",
  "last maps a worker to its last heartbeat time. Return workers silent for longer than timeout at now, sorted.",
  [(({"a": 100, "b": 50, "c": 91}, 110, 30), ['b'])],
  ("A loop.", "O(w log w)", "O(w)"),
  ("A sorted comprehension.", "O(w log w)", "O(w)"),
  names=["last", "now", "timeout"])


@B
def dead_workers(last, now, timeout):
    out = []
    for worker, t in last.items():
        if now - t > timeout:
            out.append(worker)
    return sorted(out)


@O
def dead_workers(last, now, timeout):
    return sorted(w for w, t in last.items() if now - t > timeout)


Q(None, "Reassign Tasks After a Failure", "Medium", "Lineage rebuilds work",
  "tasks maps a task to its worker. When a worker dies, reassign its tasks to the least-loaded workers in turn. Return the new mapping, sorted.",
  [(({"t1": "a", "t2": "a", "t3": "b", "t4": "c"}, "a"),  {'t1': 'b', 't2': 'c', 't3': 'b', 't4': 'c'})],
  ("Recount the load each time.", "O(t²)", "O(t)"),
  ("A heap of (load, worker).", "O(t log w)", "O(w)"),
  names=["tasks", "dead"])


@B
def reassign(tasks, dead):
    out = dict(tasks)
    alive = sorted({w for w in tasks.values() if w != dead})
    for t in sorted(tasks):
        if tasks[t] == dead:
            loads = {w: sum(1 for x in out.values() if x == w) for w in alive}
            out[t] = min(alive, key=lambda w: (loads[w], w))
    return dict(sorted(out.items()))


@O
def reassign(tasks, dead):
    import heapq
    from collections import Counter
    loads = Counter(w for w in tasks.values() if w != dead)
    heap = [(n, w) for w, n in loads.items()]
    heapq.heapify(heap)
    out = dict(tasks)
    for t in sorted(k for k, w in tasks.items() if w == dead):
        n, w = heapq.heappop(heap)
        out[t] = w
        heapq.heappush(heap, (n + 1, w))
    return dict(sorted(out.items()))


Q(None, "Speculative Execution", "Medium", "Beat the stragglers",
  "Tasks have run times. The job takes the longest. If tasks above limit are re-run on a fresh worker taking backup seconds, the finish is the smaller. Return (time before, time after), with each task's new time min(t, limit + backup).",
  [(([10, 11, 100], 20, 12),  (100, 32))],
  ("Loop, computing each task's time.", "O(n)", "O(1)"),
  ("A generator with <code>max</code>.", "O(n)", "O(1)"),
  names=["times", "limit", "backup"])


@B
def speculative(times, limit, backup):
    before = after = 0
    for t in times:
        before = max(before, t)
        new = t if t <= limit else min(t, limit + backup)
        after = max(after, new)
    return (before, after)


@O
def speculative(times, limit, backup):
    return (max(times), max(t if t <= limit else min(t, limit + backup) for t in times))


Q(None, "Shuffle Volume", "Medium", "Network is the bottleneck",
  "With hash partitioning over m machines, a share of (m − 1)/m of the data must cross the network. Return GB moved and minutes at gbps gigabits per second in total, rounded to 2 decimals.",
  [((1000, 10, 10),  (900.0, 12.0))],
  ("Step by step, watching bits vs bytes.", "O(1)", "O(1)"),
  ("Formulas.", "O(1)", "O(1)"),
  names=["gb", "m", "gbps"])


@B
def shuffle_cost(gb, m, gbps):
    moved = gb * (m - 1) / m
    gigabits = moved * 8
    seconds = gigabits / gbps
    return (round(moved, 2), round(seconds / 60, 2))


@O
def shuffle_cost(gb, m, gbps):
    moved = gb * (m - 1) / m
    return (round(moved, 2), round(moved * 8 / gbps / 60, 2))


Q(None, "Broadcast or Shuffle?", "Medium", "The cost of a join",
  "Broadcasting copies the small table to each of m machines: small × m. Shuffling moves (m − 1)/m of both tables. Return the cheaper strategy and its GB moved, rounded to 2 decimals.",
  [((1, 1000, 10), ['broadcast', 10]), ((800, 1000, 10), ['shuffle', 1620.0])],
  ("Compute both, then compare.", "O(1)", "O(1)"),
  ("<code>min</code> over pairs.", "O(1)", "O(1)"),
  names=["small", "large", "m"], post=list)


@B
def join_network(small, large, m):
    broadcast = small * m
    shuffle = (small + large) * (m - 1) / m
    if broadcast < shuffle:
        return ("broadcast", round(broadcast, 2))
    return ("shuffle", round(shuffle, 2))


@O
def join_network(small, large, m):
    return min([("broadcast", round(small * m, 2)), ("shuffle", round((small + large) * (m - 1) / m, 2))], key=lambda x: x[1])
