from lib import *
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np



LESSON("Basics", "The terminal: your daily tool", """
<p>Servers have no mouse. When a job fails at 3 am, you'll log in and read logs. Commands do one small thing each, and a pipe <code>|</code> joins them, passing one's output to the next.</p>
<table><tr><th>Command</th><th>Does</th></tr>
<tr><td><code>ls -lh</code>, <code>cd</code>, <code>pwd</code></td><td>look around</td></tr>
<tr><td><code>head</code>, <code>tail -f app.log</code></td><td>see the start or end; -f follows live</td></tr>
<tr><td><code>grep -i error app.log</code></td><td>find lines</td></tr>
<tr><td><code>wc -l</code></td><td>count lines</td></tr>
<tr><td><code>cut -d, -f2</code>, <code>awk</code></td><td>pick columns</td></tr>
<tr><td><code>sort | uniq -c | sort -rn</code></td><td>count and rank values</td></tr>
<tr><td><code>du -sh *</code>, <code>df -h</code></td><td>what's using disk space?</td></tr>
<tr><td><code>ps</code>, <code>top</code>, <code>kill</code></td><td>what's running?</td></tr>
<tr><td><code>chmod</code>, <code>chown</code></td><td>permissions</td></tr>
<tr><td><code>ssh</code>, <code>scp</code></td><td>connect, and copy to servers</td></tr></table>
<p><b>A real example:</b> which errors are most common today?</p>
<pre><code class="py">grep ERROR app.log | cut -d' ' -f4 | sort | uniq -c | sort -rn | head -5</code></pre>
<p>You can answer that in 10 seconds without writing a script. In this topic you rebuild these tools in Python, to see what they do.</p>
<p><b>Shell scripts:</b> always start with <code>set -euo pipefail</code>. Otherwise a failed step gets ignored and the script carries on, reporting success. Check <b>exit codes</b>: 0 means success, and anything else means failure.</p>
<p><b>Permissions:</b> 640 means rw- r-- ---: the owner reads and writes, the group reads, others get nothing. Each digit adds read 4, write 2 and execute 1.</p>
""", practice=["Build grep in Python", "sort | uniq -c | sort -rn", "awk: Pick a Column", "tail -n", "Disk Usage Report", "Log Rotation", "File Permissions", "Parse Exit Codes"])


LESSON("Basics", "Scheduling with cron", """
<p>Cron runs commands on a schedule, written as five fields:</p>
<div class="pic">┌ minute (0-59)
│ ┌ hour (0-23)
│ │ ┌ day of month
│ │ │ ┌ month
│ │ │ │ ┌ day of week (0 = Sunday)
0 2 * * *    every day at 02:00
*/15 * * * * every 15 minutes
0 2 * * 1    Mondays at 02:00</div>
<p>A job with schedule 02:30, checked at 03:00, next runs tomorrow at 02:30.</p>
<p><b>Cron is enough for one simple job, but it isn't an orchestrator.</b> It knows nothing about dependencies, retries, backfills or whether the job succeeded. That's why teams move to Airflow, which comes later in this course.</p>
<p>Remember that cron usually runs in the server's time zone, so check it, or set it to UTC.</p>
""", practice=["Does Cron Match This Time?", "Next Cron Runs"])


LESSON("Core", "Git: how teams work on code", """
<p>Git keeps every version of your code. <b>Each commit is a snapshot pointing to its parent</b>, so history is a graph.</p>
<div class="pic">a ─ b ─ c          main
     └─ d ─ e      my-feature</div>
<p>The commits new on <code>my-feature</code> are those reachable from e, but not from c: d and e.</p>
<pre><code class="py">git switch -c fix-dedupe       # new branch
git add transform.py
git commit -m "Keep latest row per customer"
git push -u origin fix-dedupe  # then open a pull request
git pull --rebase origin main  # catch up with main</code></pre>
<p><b>A pull request</b> lets teammates review your change, and lets automated tests run, before it reaches main.</p>
<p><b>Merge conflicts</b> are less scary once you see the logic. Git compares three versions: the shared base, yours and theirs. If only one side changed a line, take that change. If both changed it differently, a person has to decide.</p>
<p><b>Rules that keep you out of trouble:</b></p>
<ul><li>Small commits with clear messages.</li>
<li><b>Never commit secrets.</b> Git history keeps them even after you delete the line, so a leaked key must be rotated. Use tools like gitleaks, which catch <code>API_KEY = "abc"</code> before it lands.</li>
<li>Use <code>.gitignore</code> for data files and environments.</li>
<li>Pin dependency versions, so builds can be reproduced.</li></ul>
<p><b>Versions:</b> in 1.4.2, a bug fix gives 1.4.3, a new feature 1.5.0 and a breaking change 2.0.0.</p>
""", practice=["Git: Which Commits Are New?", "Merge Conflict Check", "Semantic Version Bump", "Find Secrets Before Committing", "Dependency Pin Check"])


LESSON("Core", "Docker: the same everywhere", """
<p>"It works on my machine" stops being a problem with <b>containers</b>. A container bundles your code with its exact dependencies, and it runs the same on a laptop or in production. It's lighter than a virtual machine, as it shares the host's kernel.</p>
<pre><code class="py">FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .          # dependencies first
RUN pip install -r requirements.txt
COPY src/ ./src                  # code last
CMD ["python", "-m", "src.main"]</code></pre>
<pre><code class="py">docker build -t my-job .
docker run --rm -e DB_URL=... my-job</code></pre>
<p><b>Why that order?</b> Each line is a cached layer, and changing one rebuilds it and everything after it. With steps of 5 s (base), 100 s (install) and 2 s (code):</p>
<table><tr><th>Order</th><th>Change code, rebuild takes</th></tr>
<tr><td>install, then code</td><td><b>2 s</b></td></tr><tr><td>code, then install</td><td>102 s</td></tr></table>
<p><b>Configuration comes from the environment,</b> so one image runs in dev and production. Fail immediately when something required is missing, rather than halfway through a run. <b>Never bake secrets into an image.</b></p>
<p><b>Kubernetes</b> runs many containers across machines, restarting failed ones and scaling them. You should understand pods, and resource requests and limits, as many Spark and Airflow platforms run on it.</p>
""", practice=["Docker Layer Cache", "Environment Variables With Defaults"])


LESSON("Core", "Testing and CI/CD", """
<p>Data code is often untested, which is why data is often wrong. Your QA background is a real advantage here.</p>
<table><tr><th>Test</th><th>Checks</th><th>Speed</th></tr>
<tr><td>Unit</td><td>one transform on tiny input</td><td>milliseconds</td></tr>
<tr><td>Integration</td><td>steps together, on a test database</td><td>seconds to minutes</td></tr>
<tr><td>Data quality</td><td>real data in production</td><td>each run</td></tr></table>
<pre><code class="py">import pytest

@pytest.mark.parametrize("rows,expected", [
    ([], 0),                          # empty input!
    ([{"amt": 1}, {"amt": 2}], 3),
])
def test_total(rows, expected):
    assert total(rows) == expected</code></pre>
<p><b>Make code testable by injecting dependencies.</b> A load function that accepts a <code>fetch</code> function can be tested with a fake one, with no network at all.</p>
<p><b>CI (continuous integration)</b> runs checks on every pull request. <b>CD</b> deploys when they pass. <b>Put cheap checks first.</b> Lint takes 5 s and fails 10% of the time; tests take 60 s and fail 20%. Running lint first costs an expected 5 + 0.9 × 60 = <b>59 s</b> until you stop. Running tests first costs 60 + 0.8 × 5 = 64 s.</p>
<pre><code class="py"># .github/workflows/ci.yml
on: pull_request
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install -r requirements.txt
      - run: ruff check . && pytest</code></pre>
""", practice=["Unit Test Runner", "Mock an External Call", "CI Pipeline Order"])
