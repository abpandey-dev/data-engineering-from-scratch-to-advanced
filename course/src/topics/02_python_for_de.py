from lib import *
import itertools
import json
import re
from collections import Counter, defaultdict, deque
from datetime import date, datetime, timedelta


TOPIC(
    id="python-for-de", title="Python for Pipelines", glyph="py",
    blurb="The Python a data engineer uses every day: dates and time zones, processing files too big for memory with generators, batching, retries, validation, logging and writing code you can test.",
    theory="""
<h3>Cheat sheet</h3>
<pre><code class="py">for line in open(path):             # streams; doesn't load the whole file
    ...
def read(path):                     # a generator pipeline
    with open(path) as f:
        yield from f
datetime.fromisoformat("2026-01-05T10:00:00+00:00")
logging.getLogger(__name__).info("loaded %d rows", n)</code></pre>
""")


Q(None, "Chunk a Stream", "Easy", "Write in batches",
  "Yield lists of at most size items from any iterable.",
  [((range(7), 3), [[0, 1, 2], [3, 4, 5], [6]]), (([], 3), [])],
  ("Build up a list; yield when full.", "O(n)", "O(s)"),
  ("<code>itertools.islice</code> repeatedly.", "O(n)", "O(s)"),
  names=["items", "size"], post=list)


@B
def chunks(items, size):
    batch = []
    for x in items:
        batch.append(x)
        if len(batch) == size:
            yield batch
            batch = []
    if batch:
        yield batch


@O
def chunks(items, size):
    it = iter(items)
    while batch := list(itertools.islice(it, size)):
        yield batch


Q(None, "Generator Pipeline", "Medium", "Process more than fits in memory",
  "Using generators, parse lines 'user,amount', skip bad ones, keep amounts over minimum, and return the total. Nothing should build a full list.",
  [((["a,10", "bad", "b,x", "c,3", "d,20"], 5), 30.0)],
  ("One loop doing everything.", "O(n)", "O(1)"),
  ("Chain small generators, so each step is reusable and testable.", "O(n)", "O(1)"),
  names=["lines", "minimum"])


@B
def total_over(lines, minimum):
    total = 0.0
    for line in lines:
        parts = line.split(",")
        if len(parts) != 2:
            continue
        try:
            amount = float(parts[1])
        except ValueError:
            continue
        if amount > minimum:
            total += amount
    return total


@O
def total_over(lines, minimum):
    def parse(rows):
        for r in rows:
            try:
                yield float(r.split(",")[1])
            except (IndexError, ValueError):
                continue
    return sum(a for a in parse(lines) if a > minimum)


Q(None, "Dates in a Range", "Easy", "Every backfill needs this",
  "Return every date from start to end, inclusive, as 'YYYY-MM-DD'.",
  [(("2026-02-27", "2026-03-02"), ['2026-02-27', '2026-02-28', '2026-03-01', '2026-03-02'])],
  ("A while loop adding a timedelta.", "O(d)", "O(d)"),
  ("A comprehension over day offsets.", "O(d)", "O(d)"),
  names=["start", "end"])


@B
def date_range(start, end):
    current = date.fromisoformat(start)
    last = date.fromisoformat(end)
    out = []
    while current <= last:
        out.append(current.isoformat())
        current += timedelta(days=1)
    return out


@O
def date_range(start, end):
    a, b = date.fromisoformat(start), date.fromisoformat(end)
    return [(a + timedelta(days=i)).isoformat() for i in range((b - a).days + 1)]


Q(None, "Convert to UTC", "Medium", "Store times in UTC",
  "Parse an ISO timestamp with an offset, and return it in UTC as 'YYYY-MM-DD HH:MM'.",
  [(("2026-01-05T01:30:00+05:30",), '2026-01-04 20:00'), (("2026-03-01T22:00:00-05:00",), '2026-03-02 03:00')],
  ("Parse the offset by hand, then subtract it.", "O(1)", "O(1)"),
  ("<code>datetime.fromisoformat</code> and <code>astimezone</code>.", "O(1)", "O(1)"))


@B
def to_utc(text):
    base, sign_offset = text[:19], text[19:]
    sign = 1 if sign_offset[0] == "+" else -1
    hours, minutes = sign_offset[1:].split(":")
    delta = timedelta(hours=int(hours), minutes=int(minutes))
    return (datetime.fromisoformat(base) - sign * delta).strftime("%Y-%m-%d %H:%M")


@O
def to_utc(text):
    from datetime import timezone
    return datetime.fromisoformat(text).astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M")


Q(None, "Find Missing Days", "Medium", "Gaps in a partition list",
  "Given loaded dates, return the missing ones between the first and last.",
  [((["2026-01-01", "2026-01-02", "2026-01-05"],), ['2026-01-03', '2026-01-04']), ((["2026-01-01"],), [])],
  ("For each possible day, scan the list.", "O(d·n)", "O(d)"),
  ("Put them in a set, then walk the calendar.", "O(d + n)", "O(n)"))


@B
def missing_days(days):
    parsed = sorted(date.fromisoformat(d) for d in days)
    out = []
    current = parsed[0]
    while current < parsed[-1]:
        if current not in parsed:
            out.append(current.isoformat())
        current += timedelta(days=1)
    return out


@O
def missing_days(days):
    have = {date.fromisoformat(d) for d in days}
    first, last = min(have), max(have)
    every = (first + timedelta(days=i) for i in range((last - first).days))
    return [d.isoformat() for d in every if d not in have]


Q(None, "Retry With Backoff", "Medium", "Networks fail",
  "Given results of attempts (True is success), retry up to max_tries total with delays 1, 2, 4… Return (succeeded, attempts, seconds waited).",
  [(([False, False, True], 5), (True, 3, 3)), (([False, False, False], 2), (False, 2, 1))],
  ("A loop with a doubling delay.", "O(t)", "O(1)"),
  ("Find the first success; the wait is a geometric sum.", "O(t)", "O(1)"),
  names=["results", "max_tries"])


@B
def retry(results, max_tries):
    waited, delay = 0, 1
    for attempt in range(max_tries):
        if results[attempt]:
            return (True, attempt + 1, waited)
        if attempt < max_tries - 1:
            waited += delay
            delay *= 2
    return (False, max_tries, waited)


@O
def retry(results, max_tries):
    tries = results[:max_tries]
    if True in tries:
        n = tries.index(True) + 1
        return (True, n, 2 ** (n - 1) - 1)
    return (False, max_tries, 2 ** (max_tries - 1) - 1)


Q(None, "Parse a Log Line", "Easy", "Regex for logs",
  "Parse '2026-01-05 10:00:00 ERROR payment failed' into date, level and message. Return None if it doesn't fit.",
  [(("2026-01-05 10:00:00 ERROR payment failed",), {'date': '2026-01-05', 'level': 'ERROR', 'message': 'payment failed'}), (("garbage",), None)],
  ("Split with a limit, then check the parts.", "O(n)", "O(n)"),
  ("A regular expression with named groups.", "O(n)", "O(n)"))


@B
def parse_log(line):
    parts = line.split(" ", 3)
    if len(parts) < 4 or parts[2] not in ("INFO", "WARN", "ERROR"):
        return None
    return {"date": parts[0], "level": parts[2], "message": parts[3]}


@O
def parse_log(line):
    m = re.match(r"(?P<date>\d{4}-\d\d-\d\d) \S+ (?P<level>INFO|WARN|ERROR) (?P<message>.*)", line)
    return m.groupdict() if m else None


Q(None, "Count Errors by Level", "Easy", "Log aggregation",
  "Given log lines, count each level (third word). Return a dictionary sorted by level.",
  [((["d t ERROR a", "d t INFO b", "d t ERROR c"],), {'ERROR': 2, 'INFO': 1})],
  ("A dictionary and a loop.", "O(n)", "O(k)"),
  ("<code>Counter</code>.", "O(n)", "O(k)"))


@B
def count_levels(lines):
    counts = {}
    for line in lines:
        level = line.split()[2]
        counts[level] = counts.get(level, 0) + 1
    return dict(sorted(counts.items()))


@O
def count_levels(lines):
    return dict(sorted(Counter(l.split()[2] for l in lines).items()))


Q(None, "Validate a Record", "Medium", "Reject bad data with reasons",
  "Rules: id must be a positive int, email must contain '@', age must be between 0 and 120 if present. Return a sorted list of problems.",
  [(({"id": 1, "email": "a@b", "age": 30},), []), (({"id": -1, "email": "x", "age": 200},), ['age', 'email', 'id']), (({"email": "a@b"},), ['id'])],
  ("Ifs, one rule at a time.", "O(1)", "O(1)"),
  ("A table of rules, so adding one needs no new code.", "O(r)", "O(r)"))


@B
def validate(rec):
    problems = []
    if not isinstance(rec.get("id"), int) or rec.get("id") <= 0:
        problems.append("id")
    if "@" not in str(rec.get("email", "")):
        problems.append("email")
    if "age" in rec and not 0 <= rec["age"] <= 120:
        problems.append("age")
    return sorted(problems)


@O
def validate(rec):
    rules = {
        "id": lambda r: isinstance(r.get("id"), int) and r["id"] > 0,
        "email": lambda r: "@" in str(r.get("email", "")),
        "age": lambda r: "age" not in r or 0 <= r["age"] <= 120,
    }
    return sorted(name for name, ok in rules.items() if not ok(rec))


Q(None, "Group Into Files by Key", "Easy", "Partitioning by hand",
  "Group rows by the given key, keeping order within each group. Return a dictionary with sorted keys.",
  [(([{"d": "b", "v": 1}, {"d": "a", "v": 2}, {"d": "b", "v": 3}], "d"), {'a': [{'d': 'a', 'v': 2}], 'b': [{'d': 'b', 'v': 1}, {'d': 'b', 'v': 3}]})],
  ("Check for the key each time.", "O(n)", "O(n)"),
  ("<code>defaultdict(list)</code>.", "O(n)", "O(n)"),
  names=["rows", "key"])


@B
def group_rows(rows, key):
    groups = {}
    for r in rows:
        if r[key] not in groups:
            groups[r[key]] = []
        groups[r[key]].append(r)
    return dict(sorted(groups.items()))


@O
def group_rows(rows, key):
    groups = defaultdict(list)
    for r in rows:
        groups[r[key]].append(r)
    return dict(sorted(groups.items()))


Q(None, "Sliding Time Window Count", "Medium", "Rate per minute",
  "Given sorted event times in seconds, return the largest number of events in any window of w seconds.",
  [(([1, 2, 3, 10, 11, 30], 5), 3), (([1, 100], 5), 1)],
  ("For each start, count those within w.", "O(n²)", "O(1)"),
  ("A deque drops events that have left the window.", "O(n)", "O(n)"),
  names=["times", "w"])


@B
def busiest_window(times, w):
    best = 0
    for start in times:
        best = max(best, sum(1 for t in times if start <= t < start + w))
    return best


@O
def busiest_window(times, w):
    window, best = deque(), 0
    for t in times:
        window.append(t)
        while window[0] <= t - w:
            window.popleft()
        best = max(best, len(window))
    return best


Q(None, "Merge Sorted Files", "Medium", "External sorting",
  "Merge several already sorted lists into one, lazily, as you would huge sorted files.",
  [(([[1, 4], [2, 3], [0, 9]],), [0, 1, 2, 3, 4, 9])],
  ("Join everything and sort. It needs everything in memory.", "O(n log n)", "O(n)"),
  ("<code>heapq.merge</code> keeps one item per file in memory.", "O(n log k)", "O(k)"))


@B
def merge_files(files):
    out = []
    for f in files:
        out.extend(f)
    return sorted(out)


@O
def merge_files(files):
    import heapq
    return list(heapq.merge(*files))


Q(None, "Top K From a Huge Stream", "Medium", "Don't sort everything",
  "Return the k largest values, descending, while keeping only k in memory.",
  [(([5, 1, 9, 3, 7], 2), [9, 7])],
  ("Sort it all.", "O(n log n)", "O(n)"),
  ("A min-heap of size k.", "O(n log k)", "O(k)"),
  names=["stream", "k"])


@B
def top_k(stream, k):
    return sorted(stream, reverse=True)[:k]


@O
def top_k(stream, k):
    import heapq
    heap = []
    for x in stream:
        if len(heap) < k:
            heapq.heappush(heap, x)
        elif x > heap[0]:
            heapq.heapreplace(heap, x)
    return sorted(heap, reverse=True)


Q(None, "Reservoir Sampling", "Hard", "A fair sample of an unknown length",
  "Keep k items from a stream. The i-th item (0-based, i ≥ k) replaces a random slot if the draw r[i−k] is below k; draws are given as integers from 0 to i. Return the sample.",
  [(([10, 20, 30, 40, 50], 2, [0, 3, 1]), [30, 50])],
  ("Follow the rule in a loop with an index.", "O(n)", "O(k)"),
  ("Same algorithm, with <code>enumerate</code>. Every item ends up with chance k/n.", "O(n)", "O(k)"),
  names=["stream", "k", "draws"])


@B
def reservoir(stream, k, draws):
    sample = stream[:k]
    i = k
    while i < len(stream):
        r = draws[i - k]
        if r < k:
            sample[r] = stream[i]
        i += 1
    return sample


@O
def reservoir(stream, k, draws):
    sample = list(stream[:k])
    for x, r in zip(stream[k:], draws):
        if r < k:
            sample[r] = x
    return sample


Q(None, "Stable Hash Bucket", "Medium", "Same key, same place",
  "Assign a key to one of n buckets with a stable hash: md5 of the key, read as hex, mod n. Python's own hash() differs between runs, so it isn't safe here.",
  [(("user-1", 8), 4), (("user-2", 8), 3)],
  ("Step by step.", "O(len)", "O(1)"),
  ("One expression.", "O(len)", "O(1)"),
  names=["key", "n"])


@B
def bucket(key, n):
    import hashlib
    digest = hashlib.md5(key.encode()).hexdigest()
    value = int(digest, 16)
    return value % n


@O
def bucket(key, n):
    import hashlib
    return int(hashlib.md5(key.encode()).hexdigest(), 16) % n


Q(None, "Coerce Types With a Schema", "Medium", "Text in, typed out",
  "schema maps a column to 'int', 'float' or 'str'. Convert a row's values. Return (row, list of failed columns), with failed values set to None.",
  [(({"id": "7", "amt": "x", "n": "A"}, {"id": "int", "amt": "float", "n": "str"}), ({'id': 7, 'amt': None, 'n': 'A'}, ['amt']))],
  ("Ifs per type.", "O(c)", "O(c)"),
  ("A mapping from type name to a function.", "O(c)", "O(c)"),
  names=["row", "schema"])


@B
def coerce(row, schema):
    out, failed = {}, []
    for col, kind in schema.items():
        try:
            if kind == "int":
                out[col] = int(row[col])
            elif kind == "float":
                out[col] = float(row[col])
            else:
                out[col] = str(row[col])
        except (ValueError, KeyError):
            out[col] = None
            failed.append(col)
    return (out, failed)


@O
def coerce(row, schema):
    types = {"int": int, "float": float, "str": str}
    out, failed = {}, []
    for col, kind in schema.items():
        try:
            out[col] = types[kind](row[col])
        except (ValueError, KeyError):
            out[col], _ = None, failed.append(col)
    return (out, failed)


Q(None, "Mask Personal Data", "Easy", "Never log it raw",
  "Replace all but the first letter of an email's name with '*', keeping the domain.",
  [(("asha@example.com",), 'a***@example.com'), (("b@x.io",), 'b@x.io')],
  ("Split on @ and rebuild.", "O(n)", "O(n)"),
  ("<code>partition</code> and string multiplication.", "O(n)", "O(n)"))


@B
def mask_email(email):
    parts = email.split("@")
    name = parts[0]
    stars = ""
    for _ in name[1:]:
        stars += "*"
    return name[0] + stars + "@" + parts[1]


@O
def mask_email(email):
    name, _, domain = email.partition("@")
    return f"{name[0]}{'*' * (len(name) - 1)}@{domain}"


Q(None, "Read Config With Defaults", "Easy", "Same code, every environment",
  "Merge defaults, then an environment's settings, then overrides; later ones win, and nested dictionaries merge too.",
  [(({"db": {"host": "x", "port": 1}, "n": 1}, {"db": {"host": "prod"}}, {"n": 2}),  {'db': {'host': 'prod', 'port': 1}, 'n': 2})],
  ("Handle nested keys with explicit loops.", "O(k)", "O(k)"),
  ("A recursive merge helper.", "O(k)", "O(k)"),
  names=["defaults", "env", "override"])


@B
def merge_config(defaults, env, override):
    out = json.loads(json.dumps(defaults))
    for layer in (env, override):
        for k, v in layer.items():
            if isinstance(v, dict) and isinstance(out.get(k), dict):
                out[k].update(v)
            else:
                out[k] = v
    return out


@O
def merge_config(defaults, env, override):
    def merge(a, b):
        return {**a, **{k: merge(a[k], v) if isinstance(v, dict) and isinstance(a.get(k), dict) else v for k, v in b.items()}}
    return merge(merge(defaults, env), override)


Q(None, "Run Summary Metrics", "Medium", "Every run should report",
  "Given rows read, written and rejected, and start and end seconds, return rows per second rounded to 1 decimal, and whether counts reconcile (read = written + rejected).",
  [((1000, 990, 10, 100, 110), (100.0, True)), ((1000, 980, 10, 100, 110), (100.0, False))],
  ("Compute each field.", "O(1)", "O(1)"),
  ("Compact.", "O(1)", "O(1)"),
  names=["read", "written", "rejected", "start", "end"])


@B
def run_metrics(read, written, rejected, start, end):
    seconds = end - start
    rate = read / seconds
    balanced = read == written + rejected
    return (round(rate, 1), balanced)


@O
def run_metrics(read, written, rejected, start, end):
    return (round(read / (end - start), 1), read == written + rejected)


Q(None, "Testable Transform", "Easy", "Pure functions",
  "Write a pure function adding tax to a list of order dictionaries, returning new dictionaries and leaving the input unchanged. Return (new list, whether the input stayed the same).",
  [(([{"id": 1, "amt": 100}], 0.18),  ([{'id': 1, 'amt': 100, 'total': 118.0}], True))],
  ("Copy each dictionary by hand.", "O(n)", "O(n)"),
  ("A comprehension with <code>{**row, ...}</code>.", "O(n)", "O(n)"),
  names=["orders", "rate"])


@B
def add_tax(orders, rate):
    before = json.dumps(orders)
    out = []
    for row in orders:
        new = dict(row)
        new["total"] = round(row["amt"] * (1 + rate), 2)
        out.append(new)
    return (out, json.dumps(orders) == before)


@O
def add_tax(orders, rate):
    before = json.dumps(orders)
    out = [{**r, "total": round(r["amt"] * (1 + rate), 2)} for r in orders]
    return (out, json.dumps(orders) == before)
