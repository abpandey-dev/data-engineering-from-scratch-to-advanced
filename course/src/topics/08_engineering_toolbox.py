from lib import *
import re
from datetime import datetime, timedelta


TOPIC(
    id="engineering-toolbox", title="Engineering Toolbox", glyph="$_",
    blurb="The everyday skills around the data: Linux commands, Git, Docker, cron, testing, CI/CD and environments. Each idea is modelled in Python, so you understand what the tools are really doing.",
    theory="""
<h3>Cheat sheet</h3>
<pre><code class="py">grep ERROR app.log | wc -l            # count errors
sort file | uniq -c | sort -rn | head # top values
awk -F, '{print $2}' data.csv         # second column
git switch -c fix && git commit       # branch, commit, then open a PR
docker build -t job . && docker run job
0 2 * * *                             # cron: daily at 02:00</code></pre>
""")


Q(None, "Build grep in Python", "Easy", "Search lines",
  "Return lines containing a word, ignoring case if asked, with their line numbers from 1.",
  [((["ok", "ERROR x", "error y"], "error", True), [[2, 'ERROR x'], [3, 'error y']]), ((["ok", "ERROR x"], "error", False), [])],
  ("A loop with a counter.", "O(n)", "O(m)"),
  ("A comprehension with <code>enumerate</code>.", "O(n)", "O(m)"),
  names=["lines", "word", "ignore_case"])


@B
def grep(lines, word, ignore_case):
    out, n = [], 0
    for line in lines:
        n += 1
        a, b = (line.lower(), word.lower()) if ignore_case else (line, word)
        if b in a:
            out.append([n, line])
    return out


@O
def grep(lines, word, ignore_case):
    pattern = re.compile(re.escape(word), re.I if ignore_case else 0)
    return [[i, l] for i, l in enumerate(lines, 1) if pattern.search(l)]


Q(None, "sort | uniq -c | sort -rn", "Easy", "The most useful one-liner",
  "Return the top k values as [count, value], most frequent first, ties alphabetical.",
  [((["b", "a", "b", "c", "a", "b"], 2), [[3, 'b'], [2, 'a']])],
  ("Sort, then count neighbouring runs, as uniq does.", "O(n log n)", "O(n)"),
  ("<code>Counter</code>.", "O(n log n)", "O(d)"),
  names=["lines", "k"])


@B
def top_values(lines, k):
    s = sorted(lines)
    runs = []
    for v in s:
        if runs and runs[-1][1] == v:
            runs[-1][0] += 1
        else:
            runs.append([1, v])
    return sorted(runs, key=lambda r: (-r[0], r[1]))[:k]


@O
def top_values(lines, k):
    from collections import Counter
    return sorted(([c, v] for v, c in Counter(lines).items()), key=lambda r: (-r[0], r[1]))[:k]


Q(None, "awk: Pick a Column", "Easy", "Field extraction",
  "Sum column index col (0-based) of comma-separated lines, skipping non-numbers.",
  [((["a,1", "b,2", "c,x"], 1), 3.0)],
  ("Split and try to convert.", "O(n)", "O(1)"),
  ("A generator with a regular expression test.", "O(n)", "O(1)"),
  names=["lines", "col"])


@B
def sum_column(lines, col):
    total = 0.0
    for line in lines:
        try:
            total += float(line.split(",")[col])
        except (ValueError, IndexError):
            pass
    return total


@O
def sum_column(lines, col):
    number = re.compile(r"-?\d+(\.\d+)?$")
    values = (l.split(",")[col] for l in lines)
    return float(sum(float(v) for v in values if number.match(v)))


Q(None, "tail -n", "Easy", "Last lines without loading everything",
  "Return the last n lines of a stream while keeping only n in memory.",
  [((["a", "b", "c", "d"], 2), ['c', 'd'])],
  ("Keep a list, trimming it.", "O(l·n)", "O(n)"),
  ("<code>deque(maxlen=n)</code>.", "O(l)", "O(n)"),
  names=["lines", "n"])


@B
def tail(lines, n):
    keep = []
    for l in lines:
        keep.append(l)
        if len(keep) > n:
            keep.pop(0)
    return keep


@O
def tail(lines, n):
    from collections import deque
    return list(deque(lines, maxlen=n))


Q(None, "Does Cron Match This Time?", "Medium", "Scheduling basics",
  "Given fields 'minute hour day month weekday' with numbers, * or */n, return whether a time matches (weekday 0 = Sunday).",
  [(("0 2 * * *", 0, 2, 5, 1, 3), True), (("*/15 * * * *", 30, 9, 5, 1, 3), True), (("0 2 * * 1", 0, 2, 5, 1, 3), False)],
  ("A loop with ifs.", "O(1)", "O(1)"),
  ("A small field-matching helper.", "O(1)", "O(1)"),
  names=["expr", "minute", "hour", "day", "month", "weekday"])


@B
def cron_match(expr, minute, hour, day, month, weekday):
    values = [minute, hour, day, month, weekday]
    for field, v in zip(expr.split(), values):
        if field == "*":
            continue
        if field.startswith("*/"):
            if v % int(field[2:]) != 0:
                return False
        elif int(field) != v:
            return False
    return True


@O
def cron_match(expr, minute, hour, day, month, weekday):
    def ok(f, v):
        return f == "*" or (v % int(f[2:]) == 0 if f.startswith("*/") else int(f) == v)
    return all(ok(f, v) for f, v in zip(expr.split(), (minute, hour, day, month, weekday)))


Q(None, "Next Cron Runs", "Medium", "When will it fire?",
  "For 'minute hour * * *', return the next n run times after a timestamp, as 'YYYY-MM-DD HH:MM'.",
  [((30, 2, "2026-01-05 03:00", 2), ['2026-01-06 02:30', '2026-01-07 02:30']), ((30, 2, "2026-01-05 01:00", 1), ['2026-01-05 02:30'])],
  ("Step minute by minute. It's simple, but slow.", "O(1440·n)", "O(n)"),
  ("Jump: today's run if it's still ahead, otherwise tomorrow's.", "O(n)", "O(n)"),
  names=["minute", "hour", "after", "n"])


@B
def next_runs(minute, hour, after, n):
    t = datetime.strptime(after, "%Y-%m-%d %H:%M") + timedelta(minutes=1)
    out = []
    while len(out) < n:
        if t.minute == minute and t.hour == hour:
            out.append(t.strftime("%Y-%m-%d %H:%M"))
        t += timedelta(minutes=1)
    return out


@O
def next_runs(minute, hour, after, n):
    now = datetime.strptime(after, "%Y-%m-%d %H:%M")
    first = now.replace(hour=hour, minute=minute)
    if first <= now:
        first += timedelta(days=1)
    return [(first + timedelta(days=i)).strftime("%Y-%m-%d %H:%M") for i in range(n)]


Q(None, "Git: Which Commits Are New?", "Medium", "Commits form a graph",
  "parents maps a commit to its parents. Return commits reachable from branch but not from main, sorted.",
  [(({"a": [], "b": ["a"], "c": ["b"], "d": ["b"], "e": ["d"]}, "c", "e"), ['d', 'e'])],
  ("Build both ancestor lists, then compare.", "O(c²)", "O(c)"),
  ("Two graph walks with sets.", "O(c)", "O(c)"),
  names=["parents", "main", "branch"])


@B
def new_commits(parents, main, branch):
    def ancestors(x):
        out, todo = [], [x]
        while todo:
            c = todo.pop()
            if c not in out:
                out.append(c)
                todo += parents[c]
        return out
    base = ancestors(main)
    return sorted(c for c in ancestors(branch) if c not in base)


@O
def new_commits(parents, main, branch):
    def reach(x, seen=None):
        seen = set() if seen is None else seen
        if x not in seen:
            seen.add(x)
            for p in parents[x]:
                reach(p, seen)
        return seen
    return sorted(reach(branch) - reach(main))


Q(None, "Semantic Version Bump", "Easy", "Releases",
  "Bump 'major.minor.patch' for a 'breaking', 'feature' or 'fix' change.",
  [(("1.4.2", "fix"), '1.4.3'), (("1.4.2", "feature"), '1.5.0'), (("1.4.2", "breaking"), '2.0.0')],
  ("Ifs.", "O(1)", "O(1)"),
  ("A compact conditional.", "O(1)", "O(1)"),
  names=["version", "change"])


@B
def bump(version, change):
    major, minor, patch = map(int, version.split("."))
    if change == "breaking":
        major += 1
        minor = 0
        patch = 0
    elif change == "feature":
        minor += 1
        patch = 0
    else:
        patch += 1
    return f"{major}.{minor}.{patch}"


@O
def bump(version, change):
    a, b, c = map(int, version.split("."))
    return {"breaking": f"{a + 1}.0.0", "feature": f"{a}.{b + 1}.0"}.get(change, f"{a}.{b}.{c + 1}")


Q(None, "Docker Layer Cache", "Medium", "Why order matters",
  "Each step is rebuilt if it or any earlier step changed. Given steps with seconds, and the index of the first changed step, return the rebuild seconds. Compare copying code before or after installing packages.",
  [(([5, 100, 2], 2), 2), (([5, 2, 100], 1), 102)],
  ("Add up in a loop.", "O(n)", "O(1)"),
  ("A slice.", "O(n)", "O(1)"),
  names=["steps", "first_changed"])


@B
def rebuild_time(steps, first_changed):
    total = 0
    for i, s in enumerate(steps):
        if i >= first_changed:
            total += s
    return total


@O
def rebuild_time(steps, first_changed):
    return sum(steps[first_changed:])


Q(None, "Environment Variables With Defaults", "Easy", "Twelve-factor config",
  "Given an environment dictionary and required and optional settings, return (config, missing required, sorted).",
  [(({"DB": "x"}, ["DB", "KEY"], {"PORT": "5432"}), ({'DB': 'x', 'PORT': '5432'}, ['KEY']))],
  ("Loops.", "O(k)", "O(k)"),
  ("Comprehensions.", "O(k)", "O(k)"),
  names=["env", "required", "optional"])


@B
def read_env(env, required, optional):
    config, missing = {}, []
    for k in required:
        if k in env:
            config[k] = env[k]
        else:
            missing.append(k)
    for k, default in optional.items():
        config[k] = env.get(k, default)
    return (config, sorted(missing))


@O
def read_env(env, required, optional):
    config = {k: env[k] for k in required if k in env} | {k: env.get(k, d) for k, d in optional.items()}
    return (config, sorted(set(required) - env.keys()))


Q(None, "Find Secrets Before Committing", "Medium", "Never commit a key",
  "Return line numbers (from 1) that look like secrets: a name containing key, secret, token or password assigned a non-empty value.",
  [((['name = "x"', 'API_KEY = "abc"', "password=hunter2", "key_count = 3", "token = ''"],), [2, 3])],
  ("Split on = and check words.", "O(n)", "O(m)"),
  ("A regular expression. Real teams use a tool like gitleaks.", "O(n)", "O(m)"))


@B
def find_secrets(lines):
    out = []
    for i, line in enumerate(lines, 1):
        if "=" not in line:
            continue
        name, value = line.split("=", 1)
        name = name.strip().lower()
        value = value.strip().strip("'\"")
        if value and name.split("_")[-1] in ("key", "secret", "token", "password"):
            out.append(i)
    return out


@O
def find_secrets(lines):
    p = re.compile(r"^\s*\w*(key|secret|token|password)\s*=\s*['\"]?[^'\"\s]+", re.I)
    return [i for i, l in enumerate(lines, 1) if p.match(l)]


Q(None, "Unit Test Runner", "Medium", "What pytest does",
  "Given a function and cases (args, expected), return (passed count, failing case indexes). An exception counts as a failure.",
  [(([((1, 2), 3), ((1, 1), 3), ((1, "x"), 0)],), (1, [1, 2]))],
  ("A loop with try/except, testing addition.", "O(n)", "O(n)"),
  ("The same, with enumerate and a helper.", "O(n)", "O(n)"),
  names=["cases"])


@B
def run_tests(cases):
    def add(a, b):
        return a + b
    passed, failed = 0, []
    for i, (args, want) in enumerate(cases):
        try:
            if add(*args) == want:
                passed += 1
            else:
                failed.append(i)
        except TypeError:
            failed.append(i)
    return (passed, failed)


@O
def run_tests(cases):
    def add(a, b):
        return a + b

    def ok(args, want):
        try:
            return add(*args) == want
        except TypeError:
            return False
    results = [ok(*c) for c in cases]
    return (sum(results), [i for i, r in enumerate(results) if not r])


Q(None, "Mock an External Call", "Medium", "Test without the network",
  "A load function takes a fetch function. Pass a fake fetch returning rows, and return the rows it loads with amount above 0. Injecting dependencies makes code testable.",
  [(([{"a": 1}, {"a": -1}],), [{'a': 1}])],
  ("A fake function in the test.", "O(n)", "O(n)"),
  ("A lambda as the stub.", "O(n)", "O(n)"),
  names=["fake_rows"])


@B
def load_with_fake(fake_rows):
    def fake_fetch():
        return fake_rows

    def load(fetch):
        return [r for r in fetch() if r["a"] > 0]
    return load(fake_fetch)


@O
def load_with_fake(fake_rows):
    load = lambda fetch: [r for r in fetch() if r["a"] > 0]
    return load(lambda: fake_rows)


Q(None, "CI Pipeline Order", "Medium", "Fail fast",
  "Given stages with (name, seconds, failure chance), order by seconds ascending and return the order and the expected seconds until stopping, rounded to 2 decimals. Each stage runs only if earlier ones passed.",
  [(([("tests", 60, 0.2), ("lint", 5, 0.1)],), (['lint', 'tests'], 59.0))],
  ("A loop tracking the chance of reaching each stage.", "O(n log n)", "O(n)"),
  ("Same, compactly.", "O(n log n)", "O(n)"))


@B
def ci_order(stages):
    ordered = sorted(stages, key=lambda s: s[1])
    reach, expected = 1.0, 0.0
    for name, seconds, fail in ordered:
        expected += reach * seconds
        reach *= 1 - fail
    return ([s[0] for s in ordered], round(expected, 2))


@O
def ci_order(stages):
    ordered = sorted(stages, key=lambda s: s[1])
    reach, cost = 1.0, 0.0
    for _, sec, fail in ordered:
        cost, reach = cost + reach * sec, reach * (1 - fail)
    return ([s[0] for s in ordered], round(cost, 2))


Q(None, "Disk Usage Report", "Easy", "du in Python",
  "paths map a file path to bytes. Return total bytes per top-level folder, sorted by folder.",
  [(({"a/x.log": 10, "a/b/y.log": 5, "c/z.log": 7},), {'a': 15, 'c': 7})],
  ("Split on / and add up.", "O(n)", "O(d)"),
  ("A <code>defaultdict</code>.", "O(n)", "O(d)"))


@B
def disk_usage(paths):
    totals = {}
    for p, size in paths.items():
        top = p.split("/")[0]
        totals[top] = totals.get(top, 0) + size
    return dict(sorted(totals.items()))


@O
def disk_usage(paths):
    from collections import defaultdict
    totals = defaultdict(int)
    for p, s in paths.items():
        totals[p.partition("/")[0]] += s
    return dict(sorted(totals.items()))


Q(None, "Merge Conflict Check", "Medium", "Three-way merge",
  "Given base, ours and theirs for lines at the same positions: take whichever changed; if both changed differently, it's a conflict. Return (merged with 'CONFLICT' where needed, number of conflicts).",
  [((["a", "b", "c"], ["a", "B", "c"], ["a", "b", "C"]), (['a', 'B', 'C'], 0)), ((["a"], ["x"], ["y"]), (['CONFLICT'], 1))],
  ("Ifs per line.", "O(n)", "O(n)"),
  ("A helper in a comprehension.", "O(n)", "O(n)"),
  names=["base", "ours", "theirs"])


@B
def merge3(base, ours, theirs):
    out, conflicts = [], 0
    for b, o, t in zip(base, ours, theirs):
        if o == t or t == b:
            out.append(o)
        elif o == b:
            out.append(t)
        else:
            out.append("CONFLICT")
            conflicts += 1
    return (out, conflicts)


@O
def merge3(base, ours, theirs):
    pick = lambda b, o, t: o if o == t or t == b else t if o == b else "CONFLICT"
    out = [pick(*x) for x in zip(base, ours, theirs)]
    return (out, out.count("CONFLICT"))


Q(None, "Log Rotation", "Easy", "Don't fill the disk",
  "Keep files of a pattern 'app.YYYY-MM-DD.log' newer than or equal to keep_from. Return (kept, deleted), sorted.",
  [((["app.2026-01-01.log", "app.2026-01-09.log", "app.2026-01-05.log"], "2026-01-05"), (['app.2026-01-05.log', 'app.2026-01-09.log'], ['app.2026-01-01.log']))],
  ("Slice the date from the name.", "O(n log n)", "O(n)"),
  ("A regular expression, then split.", "O(n log n)", "O(n)"),
  names=["files", "keep_from"])


@B
def rotate(files, keep_from):
    kept, deleted = [], []
    for f in files:
        if f[4:14] >= keep_from:
            kept.append(f)
        else:
            deleted.append(f)
    return (sorted(kept), sorted(deleted))


@O
def rotate(files, keep_from):
    day = lambda f: re.search(r"\d{4}-\d\d-\d\d", f).group()
    return (sorted(f for f in files if day(f) >= keep_from), sorted(f for f in files if day(f) < keep_from))


Q(None, "Dependency Pin Check", "Easy", "Reproducible builds",
  "Return requirement lines not pinned with '=='. Comments and blanks are ignored.",
  [((["pandas==2.2.0", "# note", "", "requests>=2", "numpy"],), ['requests>=2', 'numpy'])],
  ("Loop with checks.", "O(n)", "O(m)"),
  ("A comprehension.", "O(n)", "O(m)"))


@B
def unpinned(lines):
    out = []
    for l in lines:
        s = l.strip()
        if s and not s.startswith("#") and "==" not in s:
            out.append(s)
    return out


@O
def unpinned(lines):
    return [s for s in map(str.strip, lines) if s and s[0] != "#" and "==" not in s]


Q(None, "Parse Exit Codes", "Easy", "Did the job really succeed?",
  "Given a list of (command, exit code), return first failing command or None. In a shell script, set -e stops at the first failure.",
  [(([("extract", 0), ("load", 1), ("notify", 0)],), 'load'), (([("a", 0)],), None)],
  ("A loop.", "O(n)", "O(1)"),
  ("<code>next</code> with a default.", "O(n)", "O(1)"))


@B
def first_failure(results):
    for cmd, code in results:
        if code != 0:
            return cmd
    return None


@O
def first_failure(results):
    return next((c for c, code in results if code), None)


Q(None, "File Permissions", "Easy", "chmod 640",
  "Convert an octal permission string such as '640' to 'rw-r-----'.",
  [(("640",), 'rw-r-----'), (("755",), 'rwxr-xr-x')],
  ("Check each bit with ifs.", "O(1)", "O(1)"),
  ("A comprehension over the bits.", "O(1)", "O(1)"))


@B
def perms(octal):
    out = ""
    for digit in octal:
        d = int(digit)
        out += "r" if d & 4 else "-"
        out += "w" if d & 2 else "-"
        out += "x" if d & 1 else "-"
    return out


@O
def perms(octal):
    return "".join(c if int(d) & b else "-" for d in octal for c, b in zip("rwx", (4, 2, 1)))
