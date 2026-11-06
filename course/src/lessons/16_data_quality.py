from lib import *
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np



LESSON("Basics", "Bad data is worse than no data", """
<p>A broken dashboard gets noticed. A dashboard quietly showing wrong numbers gets used to make decisions. <b>Trust is the real product of a data team.</b></p>
<table><tr><th>Dimension</th><th>Question</th><th>Example test</th></tr>
<tr><td>Completeness</td><td>is anything missing?</td><td>null rate of 0.5 in a column</td></tr>
<tr><td>Uniqueness</td><td>any duplicates?</td><td>keys 1, 2, 2, 3 fail on 2</td></tr>
<tr><td>Validity</td><td>are values allowed?</td><td>"PAID" isn't in paid, refunded</td></tr>
<tr><td>Range</td><td>are values possible?</td><td>age 200</td></tr>
<tr><td>Consistency</td><td>do tables agree?</td><td>half the foreign keys have no match</td></tr>
<tr><td>Timeliness</td><td>is it fresh?</td><td>50 minutes past the SLA</td></tr></table>
<p><b>Your QA background is a real advantage here.</b> Most data engineers learned testing late. Boundary values, equivalence classes and "how could this break?" are exactly the right instincts.</p>
<p><b>Start by profiling:</b> for [1, None, 3, 3], the count is 4, nulls 1, distinct 2, min 1, max 3. Profile any new source before writing rules, because you'll be surprised.</p>
<p><b>Tests as configuration,</b> as in dbt or Great Expectations:</p>
<pre><code class="py">models:
  - name: orders
    columns:
      - name: order_id
        tests: [not_null, unique]
      - name: status
        tests:
          - accepted_values: {values: [paid, refunded]}</code></pre>
""", practice=["Profile a Column", "Null Rate per Column", "Uniqueness Check", "Accepted Values", "Range Check", "Referential Integrity", "Freshness per Table", "A Small Test Framework"])


LESSON("Core", "Catching problems nobody wrote a rule for", """
<p>Rules catch known problems. <b>Anomaly detection</b> catches surprises: a source sends half its usual rows, with every value still valid.</p>
<p><b>Volume check.</b> Past counts 100, 102, 98, 101, 99 have mean 100 and standard deviation 1.58. Today's 50 has z = (50 − 100) / 1.58 = <b>−31.6</b>, so raise an alert. 103 has z = 1.9, which is fine.</p>
<p><b>Seasonality.</b> If weekends are always low, comparing to the last few days alerts every Saturday. Compare with the <b>same weekday</b> instead. The chart shows why.</p>
<p><b>Distribution drift.</b> Row counts can be perfect while the mix changes. Bins 0.8/0.2 shifting to 0.2/0.8 give a PSI of 1.66, a large shift. A common rule: below 0.1 is stable, above 0.25 is drift. These cut-offs are conventions.</p>
<p><b>Alert fatigue.</b> If an alert is right only half the time, people stop reading it. Track each alert's precision, and fix or delete the noisy ones. An alert nobody acts on is worse than none.</p>
<table><tr><th>Severity</th><th>Example</th><th>Action</th></tr>
<tr><td>Warn</td><td>2% nulls, limit 1%</td><td>notify, continue</td></tr>
<tr><td>Error</td><td>50% nulls, limit 10%</td><td>stop publishing</td></tr></table>
""", practice=["Volume Anomaly", "Weekly Seasonality", "Distribution Drift", "Severity: Warn or Stop?", "Alert Fatigue"])


@LD
def seasonality_chart():
    rng = np.random.default_rng(1)
    days = np.arange(56)
    counts = np.where(days % 7 >= 5, 20, 100) + rng.normal(0, 3, 56)
    recent = np.array([counts[max(0, d - 7):d].mean() if d else counts[0] for d in days])
    fig, ax = plt.subplots(figsize=(4.8, 2.7))
    ax.plot(days, counts, label="daily rows")
    ax.plot(days, recent, label="last 7 days' average")
    ax.set_xlabel("day")
    ax.set_ylabel("rows (thousands)")
    ax.legend(fontsize=7)


LESSON("Core", "Handling failures: quarantine, contracts and debugging", """
<p><b>Quarantine rows, don't lose them.</b> Split good rows from bad ones, recording why: id None and amount −1 gets reasons null_id and negative. Good rows flow on, and bad ones wait to be looked at.</p>
<p><b>Data contracts.</b> Most breakages begin upstream, when a team changes a column without knowing who depends on it. A contract is an agreement, checked in code, on schema, meaning and freshness:</p>
<pre><code class="py">{"id": ("int", not null), "name": ("str", nullable), "age": ("int", not null)}
row {"id": "7", "name": None, "age": None}  →  null:age, type:id</code></pre>
<p>Run contract checks in the <b>producer's CI</b>, so a breaking change fails before it ships.</p>
<p><b>Debug by layer.</b> Count rows at every step: raw 1000, clean 990, joined 400, final 395. The join lost 59.6%, so look there, likely at a key mismatch.</p>
<p><b>Test logic changes safely.</b> Before releasing a change, build both versions and compare them. Keys only in old: 1. Only in new: 4. Changed: 3. Then explain each difference, because every difference is either intended or a bug.</p>
<p><b>Reconcile with the source.</b> A total of 1000 vs 1001 is within a 1% tolerance, and 1000 vs 900 isn't.</p>
""", practice=["Quarantine Bad Rows", "Check a Data Contract", "Find Where Rows Were Lost", "Compare Two Versions of a Table", "Reconcile Totals"])


LESSON("Advanced", "Observability and incidents", """
<p><b>Five things to watch on every important table:</b> freshness, volume, schema, distribution and lineage.</p>
<p><b>Lineage turns panic into a plan.</b> If table a breaks, following its consumers shows finance and growth are affected, so you can tell them before they find out.</p>
<p><b>When an incident happens:</b></p>
<ol><li><b>Detect:</b> ideally by your alert, not a stakeholder.</li>
<li><b>Communicate:</b> say what's affected and when you'll update again.</li>
<li><b>Stop the damage:</b> pause publishing, or roll back.</li>
<li><b>Fix and backfill.</b></li>
<li><b>Review without blame:</b> ask what would have caught this sooner, and add that test.</li></ol>
<p><b>Measure yourself.</b> Two incidents, detected after 30 and 10 minutes, resolved after 90 and 50: mean time to detect is 20 minutes, and to resolve 70. If detection is slow, invest in monitoring.</p>
<p><b>Tools you'll hear about:</b> dbt tests, Great Expectations, Soda, Monte Carlo, OpenLineage. Learn the ideas above, and the tools are easy to pick up.</p>
""", practice=["Impact Analysis", "Incident Metrics"])
