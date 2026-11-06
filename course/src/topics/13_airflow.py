from lib import *
import heapq
from collections import defaultdict, deque
from datetime import date, datetime, timedelta


TOPIC(
    id="airflow", title="Orchestration With Airflow", glyph="DAG",
    blurb="Running pipelines reliably: DAGs and topological order, schedules and data intervals, catchup and backfills, retries, sensors, XComs, pools and common mistakes. You'll build a tiny scheduler to see how it works.",
    theory="""
<h3>Cheat sheet</h3>
<pre><code class="py">from airflow.decorators import dag, task
from datetime import datetime

@dag(schedule="@daily", start_date=datetime(2026, 1, 1), catchup=False)
def orders():
    @task(retries=3)
    def extract(ds=None): ...     # ds is the logical date
    @task
    def load(path): ...
    load(extract())

orders()</code></pre>
""")


Q(None, "Is This a Valid DAG?", "Medium", "No cycles allowed",
  "edges are (before, after). Return whether the graph has no cycle.",
  [(([("a", "b"), ("b", "c")],), True), (([("a", "b"), ("b", "a")],), False)],
  ("Repeatedly remove nodes with no incoming edges.", "O(V·E)", "O(V)"),
  ("Kahn's algorithm with indegree counts.", "O(V + E)", "O(V + E)"))


@B
def is_dag(edges):
    remaining = list(edges)
    nodes = {n for e in edges for n in e}
    while nodes:
        free = {n for n in nodes if not any(b == n for _, b in remaining)}
        if not free:
            return False
        nodes -= free
        remaining = [e for e in remaining if e[0] not in free]
    return True


@O
def is_dag(edges):
    after, indeg = defaultdict(list), defaultdict(int)
    nodes = set()
    for a, b in edges:
        after[a].append(b)
        indeg[b] += 1
        nodes |= {a, b}
    ready = deque(n for n in nodes if indeg[n] == 0)
    seen = 0
    while ready:
        n = ready.popleft()
        seen += 1
        for m in after[n]:
            indeg[m] -= 1
            if indeg[m] == 0:
                ready.append(m)
    return seen == len(nodes)


Q(None, "Run Order", "Medium", "Topological sort",
  "Return tasks in an order that respects dependencies; when several are ready, choose alphabetically.",
  [(([("extract", "transform"), ("transform", "load"), ("extract", "audit")],), ['extract', 'audit', 'transform', 'load'])],
  ("Repeatedly scan for ready tasks.", "O(V²)", "O(V)"),
  ("Kahn's algorithm with a heap.", "O((V + E) log V)", "O(V)"))


@B
def run_order(edges):
    nodes = {n for e in edges for n in e}
    order = []
    while nodes:
        ready = sorted(n for n in nodes if not any(b == n and a in nodes for a, b in edges))
        order.append(ready[0])
        nodes.remove(ready[0])
    return order


@O
def run_order(edges):
    after, indeg = defaultdict(list), defaultdict(int)
    nodes = set()
    for a, b in edges:
        after[a].append(b)
        indeg[b] += 1
        nodes |= {a, b}
    heap = sorted(n for n in nodes if indeg[n] == 0)
    order = []
    while heap:
        n = heapq.heappop(heap)
        order.append(n)
        for m in after[n]:
            indeg[m] -= 1
            if not indeg[m]:
                heapq.heappush(heap, m)
    return order


Q(None, "Parallel Levels", "Medium", "What can run at once?",
  "Group tasks into levels: each runs after all its dependencies. Return levels, each sorted.",
  [(([("a", "c"), ("b", "c"), ("c", "d"), ("c", "e")],), [['a', 'b'], ['c'], ['d', 'e']])],
  ("Repeatedly take all ready tasks.", "O(V²)", "O(V)"),
  ("Kahn's algorithm, one level at a time.", "O(V + E)", "O(V)"))


@B
def levels(edges):
    nodes = {n for e in edges for n in e}
    done, out = set(), []
    while nodes - done:
        level = sorted(n for n in nodes - done if all(a in done for a, b in edges if b == n))
        out.append(level)
        done |= set(level)
    return out


@O
def levels(edges):
    after, indeg = defaultdict(list), defaultdict(int)
    nodes = set()
    for a, b in edges:
        after[a].append(b)
        indeg[b] += 1
        nodes |= {a, b}
    level, out = sorted(n for n in nodes if not indeg[n]), []
    while level:
        out.append(level)
        nxt = []
        for n in level:
            for m in after[n]:
                indeg[m] -= 1
                if not indeg[m]:
                    nxt.append(m)
        level = sorted(nxt)
    return out


Q(None, "Critical Path", "Hard", "The minimum time for a DAG",
  "durations maps task to seconds. Return the total time with unlimited parallelism: the longest path through the graph.",
  [(([("a", "b"), ("a", "c"), ("b", "d"), ("c", "d")], {"a": 1, "b": 5, "c": 2, "d": 1}),  7)],
  ("Try every path recursively.", "exponential worst case", "O(V)"),
  ("Dynamic programming in topological order.", "O(V + E)", "O(V)"),
  names=["edges", "durations"])


@B
def critical_path(edges, durations):
    def longest(n):
        before = [a for a, b in edges if b == n]
        return durations[n] + max((longest(p) for p in before), default=0)
    return max(longest(n) for n in durations)


@O
def critical_path(edges, durations):
    import functools
    before = defaultdict(list)
    for a, b in edges:
        before[b].append(a)

    @functools.lru_cache(maxsize=None)
    def finish(n):
        return durations[n] + max(map(finish, before[n]), default=0)
    return max(map(finish, durations))


Q(None, "Daily Data Intervals", "Medium", "Airflow's most confusing idea",
  "A daily DAG's run for an interval starts after the interval ends. Given the logical date, return (interval start, interval end, when it actually runs). Times are days.",
  [(("2026-01-05",), ('2026-01-05', '2026-01-06', '2026-01-06'))],
  ("Add one day by hand.", "O(1)", "O(1)"),
  ("Compact.", "O(1)", "O(1)"))


@B
def data_interval(logical):
    d = date.fromisoformat(logical)
    end = d + timedelta(days=1)
    return (d.isoformat(), end.isoformat(), end.isoformat())


@O
def data_interval(logical):
    d = date.fromisoformat(logical)
    e = (d + timedelta(days=1)).isoformat()
    return (logical, e, e)


Q(None, "How Many Runs Will Catchup Create?", "Easy", "A classic surprise",
  "With a daily DAG and catchup on, return the runs created from start_date up to today (the interval must have ended). With catchup off, it's at most 1.",
  [(("2026-01-01", "2026-01-11", True), 10), (("2026-01-01", "2026-01-11", False), 1), (("2026-01-11", "2026-01-11", True), 0)],
  ("Loop through dates.", "O(d)", "O(1)"),
  ("Date subtraction.", "O(1)", "O(1)"),
  names=["start", "today", "catchup"])


@B
def catchup_runs(start, today, catchup):
    d = date.fromisoformat(start)
    end = date.fromisoformat(today)
    count = 0
    while d + timedelta(days=1) <= end:
        count += 1
        d += timedelta(days=1)
    return count if catchup else min(count, 1)


@O
def catchup_runs(start, today, catchup):
    n = max(0, (date.fromisoformat(today) - date.fromisoformat(start)).days)
    return n if catchup else min(n, 1)


Q(None, "Retries With Exponential Delay", "Easy", "When does each retry happen?",
  "Return the retry times in seconds after failing at t0: delay, 2×delay, 4×delay… added cumulatively, capped at max per wait.",
  [((0, 60, 4, 300), [60, 180, 420, 720])],
  ("A loop.", "O(n)", "O(n)"),
  ("<code>itertools.accumulate</code>.", "O(n)", "O(n)"),
  names=["t0", "delay", "retries", "cap"])


@B
def retry_times(t0, delay, retries, cap):
    out, t = [], t0
    for i in range(retries):
        t += min(delay * 2 ** i, cap)
        out.append(t)
    return out


@O
def retry_times(t0, delay, retries, cap):
    import itertools
    return list(itertools.accumulate((min(delay * 2 ** i, cap) for i in range(retries)), initial=t0))[1:]


Q(None, "Task State After Attempts", "Easy", "Success, retry or failed",
  "attempts are True or False. With retries r, return the final state: 'success', or 'failed' if all r + 1 attempts fail, and attempts used.",
  [(([False, True], 3), ('success', 2)), (([False, False, False], 2), ('failed', 3))],
  ("A loop.", "O(r)", "O(1)"),
  ("Slice, then <code>index</code>.", "O(r)", "O(1)"),
  names=["attempts", "r"])


@B
def task_state(attempts, r):
    used = 0
    for ok in attempts[:r + 1]:
        used += 1
        if ok:
            return ("success", used)
    return ("failed", used)


@O
def task_state(attempts, r):
    tries = attempts[:r + 1]
    return ("success", tries.index(True) + 1) if True in tries else ("failed", len(tries))


Q(None, "Upstream Failed", "Medium", "Trigger rules",
  "Given each task's upstream states, return whether it runs. Rules: 'all_success', 'all_done', 'one_failed'.",
  [((["success", "failed"], "all_success"), False), ((["success", "failed"], "all_done"), True), ((["success", "success"], "one_failed"), False)],
  ("Ifs.", "O(n)", "O(1)"),
  ("A dictionary of rules.", "O(n)", "O(1)"),
  names=["upstream", "rule"])


@B
def should_run(upstream, rule):
    if rule == "all_success":
        return all(s == "success" for s in upstream)
    if rule == "one_failed":
        return "failed" in upstream
    return True


@O
def should_run(upstream, rule):
    return {"all_success": set(upstream) <= {"success"}, "one_failed": "failed" in upstream, "all_done": True}[rule]


Q(None, "What Needs Rerunning?", "Medium", "Clear downstream",
  "If a task is cleared, it and all downstream tasks rerun. Return them, sorted.",
  [(([("a", "b"), ("b", "c"), ("a", "d")], "b"), ['b', 'c'])],
  ("Repeat until no change.", "O(V·E)", "O(V)"),
  ("Breadth-first search.", "O(V + E)", "O(V)"),
  names=["edges", "task"])


@B
def to_rerun(edges, task):
    found = {task}
    changed = True
    while changed:
        changed = False
        for a, b in edges:
            if a in found and b not in found:
                found.add(b)
                changed = True
    return sorted(found)


@O
def to_rerun(edges, task):
    after = defaultdict(list)
    for a, b in edges:
        after[a].append(b)
    seen, todo = {task}, deque([task])
    while todo:
        for m in after[todo.popleft()]:
            if m not in seen:
                seen.add(m)
                todo.append(m)
    return sorted(seen)


Q(None, "Sensor: Wait for a File", "Easy", "Poke until ready",
  "A sensor checks every interval until the file exists at ready_at, or fails after timeout. Return ('success' or 'timeout', number of pokes). Checks start at 0.",
  [((90, 30, 300), ('success', 4)), ((1000, 30, 90), ('timeout', 4))],
  ("Simulate the checks.", "O(t/i)", "O(1)"),
  ("Integer arithmetic.", "O(1)", "O(1)"),
  names=["ready_at", "interval", "timeout"])


@B
def sensor(ready_at, interval, timeout):
    t, pokes = 0, 0
    while t <= timeout:
        pokes += 1
        if t >= ready_at:
            return ("success", pokes)
        t += interval
    return ("timeout", pokes)


@O
def sensor(ready_at, interval, timeout):
    needed = -(-ready_at // interval)
    if needed * interval <= timeout:
        return ("success", needed + 1)
    return ("timeout", timeout // interval + 1)


Q(None, "Pool Scheduling", "Hard", "Limit concurrency",
  "Tasks have durations and run in order, using at most slots at once. Return the finish time.",
  [(([4, 2, 8, 3], 2), 10), (([1, 1, 1], 5), 1)],
  ("Track each slot's free time, and scan for the earliest.", "O(n·s)", "O(s)"),
  ("A heap of finish times.", "O(n log s)", "O(s)"),
  names=["tasks", "slots"])


@B
def pool_finish(tasks, slots):
    free = [0] * slots
    for t in tasks:
        i = free.index(min(free))
        free[i] += t
    return max(free)


@O
def pool_finish(tasks, slots):
    heap = [0] * slots
    for t in tasks:
        heapq.heappush(heap, heapq.heappop(heap) + t)
    return max(heap)


Q(None, "Is the SLA Met?", "Easy", "Alert before anyone complains",
  "Given a task's start and duration and an SLA time, return (finish, minutes late, or 0).",
  [((360, 90, 480), (450, 0)), ((360, 150, 480), (510, 30))],
  ("Compute and compare.", "O(1)", "O(1)"),
  ("<code>max</code>.", "O(1)", "O(1)"),
  names=["start", "duration", "sla"])


@B
def sla_check(start, duration, sla):
    finish = start + duration
    late = 0
    if finish > sla:
        late = finish - sla
    return (finish, late)


@O
def sla_check(start, duration, sla):
    return (start + duration, max(0, start + duration - sla))


Q(None, "Don't Pass Data Through XCom", "Easy", "Pass a reference",
  "XCom stores small values in the metadata database. Return whether a payload in KB is acceptable under a limit, and otherwise suggest 'write to storage and pass the path'.",
  [((2, 48), 'ok'), ((5000, 48), 'write to storage and pass the path')],
  ("An if.", "O(1)", "O(1)"),
  ("A conditional expression.", "O(1)", "O(1)"),
  names=["size_kb", "limit_kb"])


@B
def xcom_ok(size_kb, limit_kb):
    if size_kb <= limit_kb:
        return "ok"
    return "write to storage and pass the path"


@O
def xcom_ok(size_kb, limit_kb):
    return "ok" if size_kb <= limit_kb else "write to storage and pass the path"


Q(None, "Find Top-Level Work in a DAG File", "Medium", "The scheduler parses it constantly",
  "Top-level code runs on every parse. Given a DAG file's lines, return unindented lines that call a function other than dag(...) or a decorator, using a simple test: not import/from/def/@/#, and contains '('.",
  [((["import x", "rows = fetch_all()", "@dag()", "def d():", "    y = fetch()", "d()"],), ['rows = fetch_all()', 'd()'])],
  ("Checks in a loop.", "O(n)", "O(m)"),
  ("A regular expression.", "O(n)", "O(m)"))


@B
def top_level_calls(lines):
    out = []
    for line in lines:
        if line[:1] in (" ", "\t", "") or "(" not in line:
            continue
        if line.startswith(("import", "from", "def", "@", "#")):
            continue
        out.append(line)
    return out


@O
def top_level_calls(lines):
    import re
    return [l for l in lines if re.match(r"(?!import|from|def|@|#)\S.*\(", l)]


Q(None, "Render a Date Template", "Easy", "Jinja in Airflow",
  "Replace {{ ds }} with the logical date, and {{ ds_nodash }} with it without dashes.",
  [(("s3://lake/dt={{ ds }}/part-{{ ds_nodash }}.parquet", "2026-01-05"), 's3://lake/dt=2026-01-05/part-20260105.parquet')],
  ("Two replaces.", "O(n)", "O(n)"),
  ("A regular expression with a dictionary.", "O(n)", "O(n)"),
  names=["template", "ds"])


@B
def render(template, ds):
    return template.replace("{{ ds }}", ds).replace("{{ ds_nodash }}", ds.replace("-", ""))


@O
def render(template, ds):
    import re
    values = {"ds": ds, "ds_nodash": ds.replace("-", "")}
    return re.sub(r"\{\{\s*(\w+)\s*\}\}", lambda m: values[m.group(1)], template)


Q(None, "Backfill With a Concurrency Limit", "Medium", "Don't overload",
  "Backfill d days, each taking m minutes, with at most c at once. Return total minutes.",
  [((30, 10, 5), 60), ((31, 10, 5), 70)],
  ("Simulate rounds.", "O(d/c)", "O(1)"),
  ("Round up.", "O(1)", "O(1)"),
  names=["d", "m", "c"])


@B
def backfill_minutes(d, m, c):
    left, total = d, 0
    while left > 0:
        left -= c
        total += m
    return total


@O
def backfill_minutes(d, m, c):
    return -(-d // c) * m


Q(None, "A Tiny Scheduler", "Hard", "Put it all together",
  "Run a DAG given task results (True or False). Failed tasks block their downstream tasks ('upstream_failed'); others run. Return state per task, sorted by name.",
  [(([("a", "b"), ("b", "c"), ("a", "d")], {"a": True, "b": False, "c": True, "d": True}),  {'a': 'success', 'b': 'failed', 'c': 'upstream_failed', 'd': 'success'})],
  ("Repeat scanning for tasks with finished upstream.", "O(V²)", "O(V)"),
  ("Kahn's order, tracking state.", "O(V + E)", "O(V)"),
  names=["edges", "results"])


@B
def scheduler(edges, results):
    state = {}
    while len(state) < len(results):
        for t in sorted(results):
            if t in state:
                continue
            ups = [a for a, b in edges if b == t]
            if all(u in state for u in ups):
                if any(state[u] != "success" for u in ups):
                    state[t] = "upstream_failed"
                else:
                    state[t] = "success" if results[t] else "failed"
    return dict(sorted(state.items()))


@O
def scheduler(edges, results):
    before, after = defaultdict(list), defaultdict(list)
    for a, b in edges:
        before[b].append(a)
        after[a].append(b)
    waiting = {t: len(before[t]) for t in results}
    ready = deque(t for t, n in waiting.items() if n == 0)
    state = {}
    while ready:
        t = ready.popleft()
        blocked = any(state[u] != "success" for u in before[t])
        state[t] = "upstream_failed" if blocked else ("success" if results[t] else "failed")
        for m in after[t]:
            waiting[m] -= 1
            if not waiting[m]:
                ready.append(m)
    return dict(sorted(state.items()))


Q(None, "Duration Anomaly", "Medium", "Spot slowdowns early",
  "Given past durations and today's, return whether today exceeds mean + 3 standard deviations (population), and the threshold, rounded to 2 decimals.",
  [(([100, 110, 90, 100], 200), (True, 121.21)), (([100, 110, 90, 100], 105), (False, 121.21))],
  ("Compute the mean and deviation by hand.", "O(n)", "O(1)"),
  ("<code>statistics.pstdev</code>.", "O(n)", "O(1)"),
  names=["history", "today"])


@B
def duration_alert(history, today):
    mean = sum(history) / len(history)
    variance = sum((x - mean) ** 2 for x in history) / len(history)
    limit = mean + 3 * variance ** 0.5
    return (today > limit, round(limit, 2))


@O
def duration_alert(history, today):
    import statistics
    limit = statistics.mean(history) + 3 * statistics.pstdev(history)
    return (today > limit, round(limit, 2))


Q(None, "Which Tasks Are Ready?", "Easy", "The scheduler's core loop",
  "Given dependencies and finished tasks, return tasks not done whose upstream are all done, sorted.",
  [(([("a", "b"), ("a", "c"), ("b", "d")], ["a", "b", "c", "d"], ["a"]), ['b', 'c'])],
  ("A loop over tasks and edges.", "O(V·E)", "O(V)"),
  ("A set of finished tasks.", "O(V + E)", "O(V)"),
  names=["edges", "tasks", "done"])


@B
def ready_tasks(edges, tasks, done):
    out = []
    for t in tasks:
        if t not in done and all(a in done for a, b in edges if b == t):
            out.append(t)
    return sorted(out)


@O
def ready_tasks(edges, tasks, done):
    d = set(done)
    blocked = {b for a, b in edges if a not in d}
    return sorted(set(tasks) - d - blocked)
