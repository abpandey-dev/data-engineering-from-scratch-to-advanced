from lib import *
import bisect
import math


TOPIC(
    id="database-internals", title="How Databases Work", glyph="B-tree",
    blurb="What's inside a database: pages, B-trees and indexes, query plans and join algorithms, transactions and isolation levels, write-ahead logs, locks, MVCC and LSM trees. You'll build each one in miniature.",
    theory="""
<h3>Cheat sheet</h3>
<pre><code class="py">Index lookup: O(log n), full scan: O(n)
Hash join: O(n + m), needs memory    Merge join: sorted inputs
Nested loop: O(n·m) unless the inner side has an index
ACID: atomic, consistent, isolated, durable
Isolation: read uncommitted < read committed < repeatable read < serializable</code></pre>
""")


Q(None, "Scan vs Index: Comparisons", "Easy", "Why indexes exist",
  "Return (worst-case comparisons for a full scan, comparisons for binary search) on n rows.",
  [((1000000,), (1000000, 20)), ((1000000000,), (1000000000, 30))],
  ("Halve in a loop to count the steps.", "O(log n)", "O(1)"),
  ("<code>ceil(log2(n + 1))</code>.", "O(1)", "O(1)"))


@B
def scan_vs_index(n):
    steps, size = 0, n
    while size > 0:
        size //= 2
        steps += 1
    return (n, steps)


@O
def scan_vs_index(n):
    return (n, math.ceil(math.log2(n + 1)))


Q(None, "Index Lookup in a Sorted List", "Easy", "The core idea",
  "keys is sorted, and rows parallel to it. Return the row for a key, or None.",
  [(([1, 3, 7], ["a", "b", "c"], 3), 'b'), (([1, 3, 7], ["a", "b", "c"], 4), None)],
  ("Scan.", "O(n)", "O(1)"),
  ("<code>bisect</code>.", "O(log n)", "O(1)"),
  names=["keys", "rows", "key"])


@B
def index_lookup(keys, rows, key):
    for k, r in zip(keys, rows):
        if k == key:
            return r
    return None


@O
def index_lookup(keys, rows, key):
    i = bisect.bisect_left(keys, key)
    return rows[i] if i < len(keys) and keys[i] == key else None


Q(None, "B-Tree Height", "Medium", "Why so few disk reads?",
  "A B-tree node holds fanout children. Return how many levels are needed for n rows: the smallest h with fanout^h ≥ n.",
  [((1000000000, 500), 4), ((1000000, 2), 20)],
  ("Multiply until it's big enough.", "O(h)", "O(1)"),
  ("A logarithm can have rounding error, so integer multiplication is safer; shown with a compact loop.", "O(h)", "O(1)"),
  names=["n", "fanout"])


@B
def btree_height(n, fanout):
    height, capacity = 0, 1
    while capacity < n:
        capacity *= fanout
        height += 1
    return height


@O
def btree_height(n, fanout):
    h = 0
    while fanout ** h < n:
        h += 1
    return h


Q(None, "Range Scan With an Index", "Easy", "Sorted data helps ranges",
  "Return values in sorted keys with lo ≤ key ≤ hi, and how many rows were examined after finding the start.",
  [(([1, 3, 5, 7, 9, 11], 4, 9), ([5, 7, 9], 3))],
  ("Scan everything: examined = n.", "O(n)", "O(k)"),
  ("Binary search for the start and end.", "O(log n + k)", "O(k)"),
  names=["keys", "lo", "hi"])


@B
def range_scan(keys, lo, hi):
    out = []
    for k in keys:
        if lo <= k <= hi:
            out.append(k)
    return (out, len(out))


@O
def range_scan(keys, lo, hi):
    a, b = bisect.bisect_left(keys, lo), bisect.bisect_right(keys, hi)
    return (keys[a:b], b - a)


Q(None, "Composite Index: Leftmost Rule", "Medium", "Column order matters",
  "An index on columns index_cols can use a query's equality columns only as a leftmost run. Return how many index columns are usable.",
  [((["a", "b", "c"], ["a", "b"]), 2), ((["a", "b", "c"], ["b", "c"]), 0), ((["a", "b", "c"], ["a", "c"]), 1)],
  ("Walk the index columns until one is missing.", "O(i·q)", "O(1)"),
  ("A set for the query's columns.", "O(i + q)", "O(q)"),
  names=["index_cols", "query_cols"])


@B
def usable_prefix(index_cols, query_cols):
    n = 0
    for col in index_cols:
        if col in query_cols:
            n += 1
        else:
            break
    return n


@O
def usable_prefix(index_cols, query_cols):
    wanted = set(query_cols)
    import itertools
    return len(list(itertools.takewhile(wanted.__contains__, index_cols)))


Q(None, "Selectivity", "Easy", "Is the index worth using?",
  "Selectivity = distinct values ÷ rows. Return it, rounded to 4 decimals, and 'index' if at least 0.01, otherwise 'scan'.",
  [((1000000, 900000), (0.9, 'index')), ((1000000, 2), (0.0, 'scan'))],
  ("Compute, then compare.", "O(1)", "O(1)"),
  ("A conditional expression.", "O(1)", "O(1)"),
  names=["rows", "distinct"])


@B
def selectivity(rows, distinct):
    s = distinct / rows
    if s >= 0.01:
        choice = "index"
    else:
        choice = "scan"
    return (round(s, 4), choice)


@O
def selectivity(rows, distinct):
    s = distinct / rows
    return (round(s, 4), "index" if s >= 0.01 else "scan")


Q(None, "Nested Loop Join", "Easy", "The simplest join",
  "Join lists of (key, value) on key. Return (rows as [key, left, right], comparisons made).",
  [(([(1, "a"), (2, "b")], [(2, "x"), (2, "y"), (3, "z")]), ([[2, 'b', 'x'], [2, 'b', 'y']], 6))],
  ("Two nested loops.", "O(n·m)", "O(r)"),
  ("A comprehension, with comparisons being n × m.", "O(n·m)", "O(r)"),
  names=["left", "right"])


@B
def nested_loop(left, right):
    out, comparisons = [], 0
    for lk, lv in left:
        for rk, rv in right:
            comparisons += 1
            if lk == rk:
                out.append([lk, lv, rv])
    return (out, comparisons)


@O
def nested_loop(left, right):
    return ([[lk, lv, rv] for lk, lv in left for rk, rv in right if lk == rk], len(left) * len(right))


Q(None, "Hash Join", "Medium", "The workhorse",
  "Build a hash table on the right list, then probe with the left. Return rows as [key, left, right], in probe order. It should give the same rows as a nested loop.",
  [(([(1, "a"), (2, "b")], [(2, "x"), (2, "y"), (3, "z")]),  [[2, 'b', 'x'], [2, 'b', 'y']])],
  ("Nested loops.", "O(n·m)", "O(r)"),
  ("Build, then probe. Build on the smaller side to save memory.", "O(n + m)", "O(m)"),
  names=["left", "right"])


@B
def hash_join(left, right):
    return [[lk, lv, rv] for lk, lv in left for rk, rv in right if lk == rk]


@O
def hash_join(left, right):
    table = {}
    for k, v in right:
        table.setdefault(k, []).append(v)
    return [[k, v, r] for k, v in left for r in table.get(k, [])]


Q(None, "Sort-Merge Join", "Hard", "When both sides are sorted",
  "Both lists are sorted by key. Merge-join them, handling duplicates.",
  [(([(1, "a"), (2, "b"), (2, "c")], [(2, "x"), (2, "y"), (3, "z")]), [[2, 'b', 'x'], [2, 'b', 'y'], [2, 'c', 'x'], [2, 'c', 'y']])],
  ("Nested loops ignore that it's sorted.", "O(n·m)", "O(r)"),
  ("Two pointers: advance the smaller side; on a match, pair up the runs.", "O(n + m + r)", "O(r)"),
  names=["left", "right"])


@B
def merge_join(left, right):
    return [[lk, lv, rv] for lk, lv in left for rk, rv in right if lk == rk]


@O
def merge_join(left, right):
    out, i, j = [], 0, 0
    while i < len(left) and j < len(right):
        if left[i][0] < right[j][0]:
            i += 1
        elif left[i][0] > right[j][0]:
            j += 1
        else:
            key, end = left[i][0], j
            while end < len(right) and right[end][0] == key:
                end += 1
            while i < len(left) and left[i][0] == key:
                out += [[key, left[i][1], right[k][1]] for k in range(j, end)]
                i += 1
            j = end
    return out


Q(None, "Rows per Page", "Easy", "Disk works in pages",
  "With 8,000-byte pages, return (rows per page, pages needed, MB on disk with MB = 10⁶ bytes) for n rows of a given size.",
  [((1000000, 100),  (80, 12500, 100.0))],
  ("Divide step by step.", "O(1)", "O(1)"),
  ("Compact, with <code>ceil</code>.", "O(1)", "O(1)"),
  names=["n", "row_size"])


@B
def pages_needed(n, row_size):
    per_page = 8000 // row_size
    pages = n // per_page
    if n % per_page:
        pages += 1
    return (per_page, pages, pages * 8000 / 1e6)


@O
def pages_needed(n, row_size):
    per = 8000 // row_size
    p = math.ceil(n / per)
    return (per, p, p * 8000 / 1e6)


Q(None, "Atomic Transfer", "Medium", "All or nothing",
  "Apply transfers (from, to, amount) as a transaction on a balances dictionary: if any would go negative, roll back everything. Return (committed, final balances).",
  [(({"a": 10, "b": 0}, [("a", "b", 5), ("a", "b", 4)]), (True, {'a': 1, 'b': 9})), (({"a": 10, "b": 0}, [("a", "b", 5), ("a", "b", 6)]), (False, {'a': 10, 'b': 0}))],
  ("Work on a copy, replacing the original only if all succeed.", "O(k + t)", "O(k)"),
  ("Keep an undo log and reverse it on failure, as real databases do.", "O(t)", "O(t)"),
  names=["balances", "transfers"])


@B
def atomic_transfer(balances, transfers):
    work = dict(balances)
    for src, dst, amount in transfers:
        if work[src] < amount:
            return (False, balances)
        work[src] -= amount
        work[dst] += amount
    return (True, work)


@O
def atomic_transfer(balances, transfers):
    undo = []
    for src, dst, amount in transfers:
        if balances[src] < amount:
            for s, d, a in reversed(undo):
                balances[s] += a
                balances[d] -= a
            return (False, balances)
        balances[src] -= amount
        balances[dst] += amount
        undo.append((src, dst, amount))
    return (True, balances)


Q(None, "Recover From a Write-Ahead Log", "Medium", "Durability",
  "After a crash, replay the log: ('set', txn, key, value) and ('commit', txn). Only committed transactions count. Return the final state.",
  [(([("set", 1, "a", 1), ("commit", 1), ("set", 2, "a", 9), ("set", 3, "b", 2), ("commit", 3)],), {'a': 1, 'b': 2})],
  ("Two passes: find the committed ones, then apply.", "O(n)", "O(n)"),
  ("One pass, buffering each transaction until it commits.", "O(n)", "O(n)"))


@B
def recover(log):
    committed = {e[1] for e in log if e[0] == "commit"}
    state = {}
    for e in log:
        if e[0] == "set" and e[1] in committed:
            state[e[2]] = e[3]
    return dict(sorted(state.items()))


@O
def recover(log):
    pending, state = {}, {}
    for e in log:
        if e[0] == "set":
            pending.setdefault(e[1], []).append(e[2:])
        else:
            state.update(pending.pop(e[1], []))
    return dict(sorted(state.items()))


Q(None, "Lost Update", "Medium", "Why isolation matters",
  "Two transactions each read a counter, then write read + 1. Given an order such as ['r1', 'r2', 'w1', 'w2'], return the final value starting from 0.",
  [((["r1", "w1", "r2", "w2"],), 2), ((["r1", "r2", "w1", "w2"],), 1)],
  ("Track each transaction's read in variables.", "O(n)", "O(1)"),
  ("A dictionary of reads.", "O(n)", "O(1)"))


@B
def lost_update(order):
    value = 0
    read1 = read2 = None
    for op in order:
        if op == "r1":
            read1 = value
        elif op == "r2":
            read2 = value
        elif op == "w1":
            value = read1 + 1
        else:
            value = read2 + 1
    return value


@O
def lost_update(order):
    value, reads = 0, {}
    for op in order:
        if op[0] == "r":
            reads[op[1]] = value
        else:
            value = reads[op[1]] + 1
    return value


Q(None, "MVCC: Which Version Do I See?", "Hard", "Readers don't block writers",
  "versions is a list of (value, commit_time). A reader started at time t sees the latest version committed at or before t, or None.",
  [(([("a", 5), ("b", 10), ("c", 20)], 12), 'b'), (([("a", 5)], 1), None)],
  ("Scan all versions.", "O(n)", "O(1)"),
  ("Versions are in time order, so binary search.", "O(log n)", "O(n)"),
  names=["versions", "t"])


@B
def visible_version(versions, t):
    best = None
    for value, commit in versions:
        if commit <= t:
            best = value
    return best


@O
def visible_version(versions, t):
    i = bisect.bisect_right([c for _, c in versions], t)
    return versions[i - 1][0] if i else None


Q(None, "Deadlock Detection", "Hard", "A cycle in who waits for whom",
  "waits maps a transaction to the ones it's waiting for. Return whether there's a deadlock.",
  [(({"t1": ["t2"], "t2": ["t1"]},), True), (({"t1": ["t2"], "t2": ["t3"]},), False)],
  ("From each transaction, search for a path back to itself.", "O(V·(V + E))", "O(V)"),
  ("DFS with three colours: finding a grey node means a cycle.", "O(V + E)", "O(V)"))


@B
def has_deadlock(waits):
    for start in waits:
        stack, seen = list(waits.get(start, [])), set()
        while stack:
            x = stack.pop()
            if x == start:
                return True
            if x not in seen:
                seen.add(x)
                stack += waits.get(x, [])
    return False


@O
def has_deadlock(waits):
    state = {}

    def visit(x):
        if state.get(x) == 1:
            return True
        if state.get(x) == 2:
            return False
        state[x] = 1
        found = any(visit(y) for y in waits.get(x, []))
        state[x] = 2
        return found
    return any(visit(x) for x in waits)


Q(None, "A Tiny LSM Tree", "Hard", "Write-optimised storage",
  "Writes go to a memtable; when it holds cap keys it's flushed as a new sorted run. Reads check the memtable, then runs from newest to oldest. Apply writes, and return (value of key, number of runs).",
  [(([("a", 1), ("b", 2), ("a", 3), ("c", 4), ("d", 5)], 2, "a"), (3, 2))],
  ("Follow the rules with lists of pairs.", "O(n)", "O(n)"),
  ("Dictionaries for memtable and runs.", "O(n)", "O(n)"),
  names=["writes", "cap", "key"])


@B
def lsm(writes, cap, key):
    mem, runs = [], []
    for k, v in writes:
        mem = [p for p in mem if p[0] != k] + [(k, v)]
        if len(mem) == cap:
            runs.append(sorted(mem))
            mem = []
    for k, v in mem:
        if k == key:
            return (v, len(runs))
    for run in reversed(runs):
        for k, v in run:
            if k == key:
                return (v, len(runs))
    return (None, len(runs))


@O
def lsm(writes, cap, key):
    mem, runs = {}, []
    for k, v in writes:
        mem[k] = v
        if len(mem) == cap:
            runs.append(mem)
            mem = {}
    for layer in [mem] + runs[::-1]:
        if key in layer:
            return (layer[key], len(runs))
    return (None, len(runs))


Q(None, "Bloom Filter", "Hard", "Definitely not, or maybe",
  "Use m bits and two hashes, sum(codes) % m and sum(i × code) % m (i from 1). Add words, then return for each query 'no' if any bit is unset, else 'maybe'.",
  [((["cat", "dog"], ["cat", "bird"], 64), ['maybe', 'no'])],
  ("A list of booleans.", "O(w)", "O(m)"),
  ("A single integer as a bitset.", "O(w)", "O(m/64)"),
  names=["words", "queries", "m"])


@B
def bloom(words, queries, m):
    def hashes(w):
        return (sum(map(ord, w)) % m, sum((i + 1) * ord(c) for i, c in enumerate(w)) % m)
    bits = [False] * m
    for w in words:
        for h in hashes(w):
            bits[h] = True
    return ["maybe" if all(bits[h] for h in hashes(q)) else "no" for q in queries]


@O
def bloom(words, queries, m):
    def hashes(w):
        return (sum(map(ord, w)) % m, sum((i + 1) * ord(c) for i, c in enumerate(w)) % m)
    bits = 0
    for w in words:
        for h in hashes(w):
            bits |= 1 << h
    return ["maybe" if all(bits >> h & 1 for h in hashes(q)) else "no" for q in queries]


Q(None, "Estimate Rows After a Filter", "Medium", "What the planner guesses",
  "With independent filters of given selectivities on n rows, return estimated rows, rounded to the nearest whole number. Correlated columns make this estimate wrong.",
  [((1000000, [0.1, 0.5]), 50000)],
  ("Multiply in a loop.", "O(k)", "O(1)"),
  ("<code>math.prod</code>.", "O(k)", "O(1)"),
  names=["n", "selectivities"])


@B
def estimate_rows(n, selectivities):
    value = n
    for s in selectivities:
        value *= s
    return round(value)


@O
def estimate_rows(n, selectivities):
    return round(n * math.prod(selectivities))


Q(None, "Pick a Join Strategy", "Medium", "The optimizer's choice",
  "Given rows on each side, whether the larger side has an index on the key, and memory in rows: return 'index nested loop' if the smaller side ≤ 1,000 and there's an index; 'hash' if the smaller side fits in memory; otherwise 'sort-merge'.",
  [((100, 1000000, True, 10000), 'index nested loop'), ((5000, 1000000, False, 10000), 'hash'), ((500000, 1000000, False, 10000), 'sort-merge')],
  ("Ifs.", "O(1)", "O(1)"),
  ("Same logic with an expression.", "O(1)", "O(1)"),
  names=["a", "b", "indexed", "memory"])


@B
def join_strategy(a, b, indexed, memory):
    small = a if a < b else b
    if small <= 1000 and indexed:
        return "index nested loop"
    if small <= memory:
        return "hash"
    return "sort-merge"


@O
def join_strategy(a, b, indexed, memory):
    small = min(a, b)
    return "index nested loop" if small <= 1000 and indexed else "hash" if small <= memory else "sort-merge"


Q(None, "Write Amplification", "Medium", "Indexes aren't free",
  "Each insert writes the row plus one entry per index. Return the writes for n inserts with k indexes, and how many times more than with none.",
  [((1000, 4), (5000, 5.0))],
  ("Count in steps.", "O(1)", "O(1)"),
  ("A formula.", "O(1)", "O(1)"),
  names=["n", "k"])


@B
def write_amp(n, k):
    per_insert = 1 + k
    total = per_insert * n
    return (total, total / n)


@O
def write_amp(n, k):
    return ((1 + k) * n, float(1 + k))
