from lib import *
from collections import defaultdict


TOPIC(
    id="streaming", title="Stream Processing", glyph="∿",
    blurb="Processing data that never ends: event time vs processing time, tumbling, sliding and session windows, watermarks and late data, stateful processing, stream joins, checkpoints and exactly-once, with Spark and Flink in mind.",
    theory="""
<h3>Cheat sheet</h3>
<pre><code class="py">events.withWatermark("ts", "10 minutes") \\
      .groupBy(F.window("ts", "5 minutes"), "user").count()
Tumbling: fixed, no overlap   Sliding: fixed, overlap   Session: gap-based
Watermark = max event time seen − allowed lateness
Checkpoint: saved offsets + state, so a restart resumes</code></pre>
""")


Q(None, "Tumbling Windows", "Easy", "Fixed buckets",
  "Count events by window of size w: window start = t − t % w. Return {start: count}, sorted.",
  [(([1, 2, 61, 62, 130], 60), {0: 2, 60: 2, 120: 1})],
  ("A dictionary in a loop.", "O(n)", "O(w)"),
  ("<code>Counter</code>.", "O(n)", "O(w)"),
  names=["times", "w"])


@B
def tumbling(times, w):
    counts = {}
    for t in times:
        start = t - t % w
        counts[start] = counts.get(start, 0) + 1
    return dict(sorted(counts.items()))


@O
def tumbling(times, w):
    from collections import Counter
    return dict(sorted(Counter(t - t % w for t in times).items()))


Q(None, "Sliding Windows", "Medium", "One event, many windows",
  "With size s and slide d, an event belongs to each window [k·d, k·d + s) containing it. Return {start: count}, sorted.",
  [(([5, 12], 10, 5), {0: 1, 5: 2, 10: 1})],
  ("Check each candidate window.", "O(n·w)", "O(w)"),
  ("Compute the starting points directly.", "O(n·s/d)", "O(w)"),
  names=["times", "s", "d"])


@B
def sliding(times, s, d):
    last = max(times)
    counts = {}
    k = 0
    while k * d <= last:
        n = sum(1 for t in times if k * d <= t < k * d + s)
        if n:
            counts[k * d] = n
        k += 1
    return counts


@O
def sliding(times, s, d):
    counts = defaultdict(int)
    for t in times:
        start = t - t % d
        while start > t - s and start >= 0:
            counts[start] += 1
            start -= d
    return dict(sorted(counts.items()))


Q(None, "Session Windows", "Medium", "Activity bursts",
  "Sessions end after a gap larger than g. Given sorted times, return [start, end, count] per session.",
  [(([1, 2, 10, 11, 12, 30], 5), [[1, 2, 2], [10, 12, 3], [30, 30, 1]])],
  ("A loop tracking the current session.", "O(n)", "O(s)"),
  ("Same loop, with lists.", "O(n)", "O(s)"),
  names=["times", "g"])


@B
def sessions(times, g):
    out = []
    for t in times:
        if out and t - out[-1][1] <= g:
            out[-1][1] = t
            out[-1][2] += 1
        else:
            out.append([t, t, 1])
    return out


@O
def sessions(times, g):
    import itertools
    breaks = [0] + [t - p > g for p, t in zip(times, times[1:])]
    ids = itertools.accumulate(map(int, breaks))
    groups = itertools.groupby(zip(ids, times), key=lambda x: x[0])
    out = []
    for _, g_ in groups:
        ts = [t for _, t in g_]
        out.append([ts[0], ts[-1], len(ts)])
    return out


Q(None, "Event Time vs Processing Time", "Easy", "Which bucket?",
  "Events are (event_time, arrival_time). Return per-window counts by event time and by arrival time, for window w.",
  [(([(55, 62), (58, 59), (61, 65)], 60),  ({0: 2, 1: 1}, {0: 1, 1: 2}))],
  ("Two dictionaries.", "O(n)", "O(w)"),
  ("A helper used twice.", "O(n)", "O(w)"),
  names=["events", "w"])


@B
def time_buckets(events, w):
    by_event, by_arrival = {}, {}
    for e, a in events:
        by_event[e // w] = by_event.get(e // w, 0) + 1
        by_arrival[a // w] = by_arrival.get(a // w, 0) + 1
    return (dict(sorted(by_event.items())), dict(sorted(by_arrival.items())))


@O
def time_buckets(events, w):
    from collections import Counter
    count = lambda i: dict(sorted(Counter(x[i] // w for x in events).items()))
    return (count(0), count(1))


Q(None, "Compute the Watermark", "Easy", "How late is too late?",
  "Watermark = largest event time seen so far − lateness. Return the watermark after each event.",
  [(([10, 20, 15, 30], 5), [5, 15, 15, 25])],
  ("Track a maximum.", "O(n)", "O(n)"),
  ("<code>itertools.accumulate(max)</code>.", "O(n)", "O(n)"),
  names=["times", "lateness"])


@B
def watermarks(times, lateness):
    out, top = [], times[0]
    for t in times:
        if t > top:
            top = t
        out.append(top - lateness)
    return out


@O
def watermarks(times, lateness):
    import itertools
    return [m - lateness for m in itertools.accumulate(times, max)]


Q(None, "Drop Late Events", "Medium", "Watermarks in action",
  "Process events in arrival order. An event whose window has closed (window end ≤ current watermark) is dropped. Return (counts per window start, dropped count) for window w and lateness l.",
  [(([10, 70, 15, 130, 65], 60, 5), ({0: 1, 60: 1, 120: 1}, 2))],
  ("Track watermark in a loop.", "O(n)", "O(w)"),
  ("Same, with defaultdict.", "O(n)", "O(w)"),
  names=["times", "w", "l"])


@B
def late_filter(times, w, l):
    top, counts, dropped = -10**9, {}, 0
    for t in times:
        start = t - t % w
        if start + w <= top - l:
            dropped += 1
            continue
        counts[start] = counts.get(start, 0) + 1
        top = max(top, t)
    return (dict(sorted(counts.items())), dropped)


@O
def late_filter(times, w, l):
    counts, dropped, wm = defaultdict(int), 0, float("-inf")
    for t in times:
        start = t - t % w
        if start + w <= wm:
            dropped += 1
        else:
            counts[start] += 1
            wm = max(wm, t - l)
    return (dict(sorted(counts.items())), dropped)


Q(None, "When Does a Window Fire?", "Medium", "Output mode: append",
  "A window [s, s + w) emits when the watermark reaches s + w. Given arrival-ordered event times and lateness, return the event index at which window s closes, or None.",
  [(([10, 70, 200], 0, 60, 10), 1), (([10, 20], 0, 60, 10), None)],
  ("Track the maximum.", "O(n)", "O(1)"),
  ("<code>next</code> over accumulated maximums.", "O(n)", "O(n)"),
  names=["times", "s", "w", "lateness"])


@B
def window_fires(times, s, w, lateness):
    top = None
    for i, t in enumerate(times):
        top = t if top is None or t > top else top
        if top - lateness >= s + w:
            return i
    return None


@O
def window_fires(times, s, w, lateness):
    import itertools
    return next((i for i, m in enumerate(itertools.accumulate(times, max)) if m - lateness >= s + w), None)


Q(None, "Running Count With State", "Easy", "Stateful processing",
  "For a stream of keys, return the running count per key after each event.",
  [((["a", "b", "a"],), [1, 1, 2])],
  ("A dictionary.", "O(n)", "O(k)"),
  ("<code>defaultdict(int)</code>.", "O(n)", "O(k)"))


@B
def running_counts(keys):
    state, out = {}, []
    for k in keys:
        state[k] = state.get(k, 0) + 1
        out.append(state[k])
    return out


@O
def running_counts(keys):
    state = defaultdict(int)
    out = []
    for k in keys:
        state[k] += 1
        out.append(state[k])
    return out


Q(None, "State Growth", "Medium", "State can blow up",
  "Without eviction, state grows with distinct keys. With a TTL, keys expire. Given (key, time) events in order and ttl, return (keys kept forever, keys in state at the end).",
  [(([("a", 1), ("b", 2), ("c", 50), ("a", 60)], 30),  (3, 2))],
  ("A dictionary, then filter.", "O(n)", "O(k)"),
  ("Same, compactly.", "O(n)", "O(k)"),
  names=["events", "ttl"])


@B
def state_size(events, ttl):
    last = {}
    now = 0
    for k, t in events:
        last[k] = t
        now = t
    live = 0
    for k in last:
        if now - last[k] <= ttl:
            live += 1
    return (len(last), live)


@O
def state_size(events, ttl):
    last = dict(events)
    now = events[-1][1]
    return (len(last), sum(now - t <= ttl for t in last.values()))


Q(None, "Stream-Static Join", "Easy", "Enrich events",
  "Join each event (id, user) with a user table to add a country, using 'unknown' if not found.",
  [(([(1, "u1"), (2, "u9")], {"u1": "IN"}),  [[1, 'u1', 'IN'], [2, 'u9', 'unknown']])],
  ("Search a list of pairs.", "O(n·m)", "O(n)"),
  ("A dictionary lookup.", "O(n)", "O(n)"),
  names=["events", "users"])


@B
def enrich(events, users):
    out = []
    for i, u in events:
        country = "unknown"
        for name in users:
            if name == u:
                country = users[name]
        out.append([i, u, country])
    return out


@O
def enrich(events, users):
    return [[i, u, users.get(u, "unknown")] for i, u in events]


Q(None, "Stream-Stream Join", "Hard", "Both sides arrive over time",
  "Join clicks and impressions by ad id if click time is within w seconds after the impression. Events arrive together, in time order, as (kind, id, time). Return matched [id, impression_time, click_time].",
  [(([("imp", 1, 10), ("click", 1, 15), ("imp", 2, 20), ("click", 2, 90), ("click", 3, 95)], 30),  [[1, 10, 15]])],
  ("Scan all previous impressions for each click.", "O(n²)", "O(n)"),
  ("Buffer impressions in a dictionary, dropping old ones, which is what stream state does.", "O(n)", "O(k)"),
  names=["events", "w"])


@B
def stream_join(events, w):
    seen, out = [], []
    for kind, i, t in events:
        if kind == "imp":
            seen.append((i, t))
        else:
            for sid, st in seen:
                if sid == i and 0 <= t - st <= w:
                    out.append([i, st, t])
    return out


@O
def stream_join(events, w):
    buffer, out = {}, []
    for kind, i, t in events:
        if kind == "imp":
            buffer[i] = t
        elif i in buffer:
            if t - buffer[i] <= w:
                out.append([i, buffer[i], t])
            else:
                del buffer[i]
    return out


Q(None, "Checkpoint and Replay", "Medium", "Fault tolerance",
  "A stream job checkpoints state and offset every k events. A crash happens after event c. Return (restored count from the checkpoint, events replayed, final total, all events counted once).",
  [((10, 4, 7),  (4, 3, 10))],
  ("Simulate it.", "O(n)", "O(1)"),
  ("Arithmetic.", "O(1)", "O(1)"),
  names=["n", "k", "c"])


@B
def stream_recover(n, k, c):
    count = saved = 0
    for i in range(1, c + 1):
        count += 1
        if i % k == 0:
            saved = count
    replayed = c - saved
    total = saved
    for _ in range(saved, n):
        total += 1
    return (saved, replayed, total)


@O
def stream_recover(n, k, c):
    saved = c // k * k
    return (saved, c - saved, n)


Q(None, "Micro-Batch Latency", "Easy", "Spark's model",
  "With trigger interval t seconds and batch run time r, return the average and worst latency: wait for the batch, plus processing. Stable only if r ≤ t.",
  [((10, 2), (7.0, 12, True)), ((10, 15), (20.0, 25, False))],
  ("Add up.", "O(1)", "O(1)"),
  ("Compact.", "O(1)", "O(1)"),
  names=["t", "r"])


@B
def micro_batch(t, r):
    average = t / 2 + r
    worst = t + r
    stable = r <= t
    return (average, worst, stable)


@O
def micro_batch(t, r):
    return (t / 2 + r, t + r, r <= t)


Q(None, "Approximate Distinct Counts", "Hard", "HyperLogLog's idea",
  "Hash each item with md5. Keep the maximum number of leading zero bits seen. Estimate distinct ≈ 2^max. Compare with the truth on a small set, returning (estimate, truth). This shows the idea; real HLL averages many buckets.",
  [(([f"u{i}" for i in range(1000)],),  (2048, 1000))],
  ("Loop with bit counting.", "O(n)", "O(1)"),
  ("Same, with <code>bin</code>.", "O(n)", "O(1)"))


@B
def hll_idea(items):
    import hashlib
    best = 0
    for x in items:
        h = int(hashlib.md5(x.encode()).hexdigest(), 16)
        zeros = 128
        while h:
            h >>= 1
            zeros -= 1
        best = max(best, zeros)
    return (2 ** best, len(set(items)))


@O
def hll_idea(items):
    import hashlib
    z = lambda x: 128 - int(hashlib.md5(x.encode()).hexdigest(), 16).bit_length()
    return (2 ** max(map(z, items)), len(set(items)))


Q(None, "Count-Min Sketch", "Hard", "Frequencies with little memory",
  "Use a d × w table. Hash i of x is md5(f'{i}{x}') mod w. Add items, then estimate a count as the minimum of its cells. It can overestimate but never underestimate.",
  [((["a", "b", "a", "c", "a"], "a", 3, 10), 3), ((["a", "b", "a"], "z", 3, 10), 0)],
  ("Lists of lists.", "O(n·d)", "O(d·w)"),
  ("A NumPy table.", "O(n·d)", "O(d·w)"),
  names=["items", "query", "d", "w"])


@B
def count_min(items, query, d, w):
    import hashlib
    h = lambda i, x: int(hashlib.md5(f"{i}{x}".encode()).hexdigest(), 16) % w
    table = [[0] * w for _ in range(d)]
    for x in items:
        for i in range(d):
            table[i][h(i, x)] += 1
    return min(table[i][h(i, query)] for i in range(d))


@O
def count_min(items, query, d, w):
    import hashlib
    import numpy as np
    h = lambda i, x: int(hashlib.md5(f"{i}{x}".encode()).hexdigest(), 16) % w
    table = np.zeros((d, w), dtype=int)
    for x in items:
        for i in range(d):
            table[i, h(i, x)] += 1
    return int(min(table[i, h(i, query)] for i in range(d)))


Q(None, "Backpressure", "Medium", "When input outruns output",
  "Given per-second input counts and a capacity, return the queue length after each second.",
  [(([5, 20, 5, 5], 10),  [0, 10, 5, 0])],
  ("A running queue.", "O(n)", "O(n)"),
  ("<code>itertools.accumulate</code> with a function.", "O(n)", "O(n)"),
  names=["arrivals", "capacity"])


@B
def backlog(arrivals, capacity):
    queue, out = 0, []
    for a in arrivals:
        queue = max(0, queue + a - capacity)
        out.append(queue)
    return out


@O
def backlog(arrivals, capacity):
    import itertools
    return list(itertools.accumulate(arrivals, lambda q, a: max(0, q + a - capacity), initial=0))[1:]


Q(None, "Deduplicate With a Watermark", "Medium", "Bound the state",
  "Drop repeated ids within the window. Keep state only for ids newer than watermark = max time − w. Return (kept ids, final state size).",
  [(([("a", 1), ("a", 2), ("b", 50), ("a", 60)], 10),  (['a', 'b', 'a'], 2))],
  ("A dictionary with eviction in a loop.", "O(n·k)", "O(k)"),
  ("Same with a comprehension.", "O(n·k)", "O(k)"),
  names=["events", "w"])


@B
def watermark_dedupe(events, w):
    state, kept, top = {}, [], 0
    for i, t in events:
        top = max(top, t)
        if i not in state:
            kept.append(i)
        state[i] = t
        for k in list(state):
            if state[k] < top - w:
                del state[k]
    return (kept, len(state))


@O
def watermark_dedupe(events, w):
    state, kept, top = {}, [], 0
    for i, t in events:
        top = max(top, t)
        if i not in state:
            kept.append(i)
        state[i] = t
        state = {k: v for k, v in state.items() if v >= top - w}
    return (kept, len(state))


Q(None, "Lambda or Kappa?", "Easy", "Two architectures",
  "Lambda runs batch and streaming code paths; Kappa uses only a stream with replay. Return the number of code paths and, for a change, the deployments needed.",
  [(("lambda",), (2, 2)), (("kappa",), (1, 1))],
  ("Ifs.", "O(1)", "O(1)"),
  ("A dictionary.", "O(1)", "O(1)"))


@B
def architecture(name):
    if name == "lambda":
        return (2, 2)
    return (1, 1)


@O
def architecture(name):
    return {"lambda": (2, 2), "kappa": (1, 1)}[name]


Q(None, "Top K per Window", "Medium", "Trending items",
  "Given (time, item) events and window w, return the top item per window (ties alphabetical), sorted by window start.",
  [(([(1, "a"), (2, "b"), (3, "b"), (61, "c")], 60),  [[0, 'b'], [60, 'c']])],
  ("Nested dictionaries.", "O(n log k)", "O(w·k)"),
  ("<code>defaultdict(Counter)</code>.", "O(n log k)", "O(w·k)"),
  names=["events", "w"])


@B
def top_per_window(events, w):
    windows = {}
    for t, item in events:
        start = t - t % w
        windows.setdefault(start, {})
        windows[start][item] = windows[start].get(item, 0) + 1
    out = []
    for s in sorted(windows):
        best = sorted(windows[s].items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
        out.append([s, best])
    return out


@O
def top_per_window(events, w):
    from collections import Counter
    wins = defaultdict(Counter)
    for t, item in events:
        wins[t - t % w][item] += 1
    return [[s, min(c, key=lambda i: (-c[i], i))] for s, c in sorted(wins.items())]


Q(None, "Replays Need an Idempotent Sink", "Medium", "Exactly-once in effect",
  "A stream replays after a crash, so a record can arrive twice. Return (rows in an append sink, rows in an upsert sink keyed by id).",
  [(([(1, "a"), (2, "b"), (1, "a")],), (3, 2))],
  ("Simulate both sinks.", "O(n)", "O(n)"),
  ("A list length and a dictionary.", "O(n)", "O(k)"))


@B
def sink_rows(records):
    append, upsert = [], {}
    for key, value in records:
        append.append((key, value))
        upsert[key] = value
    return (len(append), len(upsert))


@O
def sink_rows(records):
    return (len(records), len(dict(records)))
