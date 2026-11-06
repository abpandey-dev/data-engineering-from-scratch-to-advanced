from lib import *
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np



LESSON("Basics", "Idempotency: the most important word in pipelines", """
<p>Pipelines fail and get rerun. Sometimes a scheduler even runs one twice. <b>Idempotent</b> means running it twice gives the same result as running it once.</p>
<p>Imagine a light switch labelled "turn on": pressing it again changes nothing. A switch labelled "toggle" isn't idempotent.</p>
<table><tr><th>Pattern</th><th>3 rows, run twice</th><th>Idempotent?</th></tr>
<tr><td>Plain append</td><td><b>6 rows: every total doubled</b></td><td>no</td></tr>
<tr><td>Overwrite the day's partition</td><td>3 rows</td><td>yes</td></tr>
<tr><td>Upsert by key</td><td>3 rows</td><td>yes</td></tr></table>
<p>This one idea prevents many of the data incidents you'll meet. If a teammate says "just rerun it", your first thought should be: is that safe?</p>
<p><b>Overwrite a partition</b> is the simplest safe batch pattern. A job for 5 January deletes and rewrites only that day's data, and leaves others alone. Rerun it as many times as you like.</p>
<pre><code class="py">INSERT OVERWRITE TABLE orders PARTITION (day = '2026-01-05')
SELECT ... WHERE day = '2026-01-05';</code></pre>
<p><b>Design rule:</b> make each run a pure function of its input and its date, and pass the date in as a parameter. Never use "today" in the logic, or reruns of old days will read the wrong data.</p>
""", practice=["Naive Append Isn't Idempotent", "Overwrite a Partition"])


LESSON("Core", "Incremental loads: only what's new", """
<p>Copying a 10 TB table every day is slow and expensive. If 1 TB changes, load just that.</p>
<table><tr><th>Approach</th><th>How</th><th>Trade-off</th></tr>
<tr><td>Full load</td><td>replace everything</td><td>simple; catches deletes; gets expensive</td></tr>
<tr><td>Incremental</td><td>only new or changed rows</td><td>cheap; more logic; can miss things</td></tr>
<tr><td>CDC</td><td>read the database's log</td><td>complete and fresh; more infrastructure</td></tr></table>
<p>Don't optimise too early. A 3 GB table where incremental would still cost 3 GB should simply be fully reloaded.</p>
<p><b>The high-watermark pattern:</b> remember the largest <code>updated_at</code> you've loaded, then ask for rows after it.</p>
<p>Rows at times 10, 20, 30, with watermark 15: load 20 and 30, and the new watermark is 30. If there are no new rows, keep the old one. Save it only <b>after</b> the load succeeds, or a crash would skip data.</p>
<p><b>The trap: long transactions.</b> A row stamped time 95 might commit after you've already read up to 100, so a strict watermark misses it forever. So re-read with a <b>lookback window</b>: read from 90. You'll see some rows twice, which is fine, as long as you <b>apply with an idempotent upsert</b>.</p>
<p><b>Upsert (MERGE)</b> updates existing keys and inserts new ones:</p>
<pre><code class="py">MERGE INTO target t USING updates u ON t.id = u.id
WHEN MATCHED AND u.ts > t.ts THEN UPDATE SET ...
WHEN NOT MATCHED THEN INSERT ...;</code></pre>
<p>The <code>u.ts &gt; t.ts</code> condition matters. Updates can arrive out of order, and an old update mustn't overwrite a newer one.</p>
""", practice=["Choose Full or Incremental", "High-Watermark Incremental Load", "Watermark With a Lookback", "Upsert (MERGE)", "Upsert Keeps Only Newer"])


LESSON("Core", "Change data capture", """
<p>Watermarks can't see <b>deleted</b> rows: a row that's gone doesn't show up in "changed since". And they miss intermediate changes.</p>
<p><b>Change data capture (CDC)</b> reads the database's own log, which records every insert, update and delete, with little load on the source. Debezium is the best-known tool, usually writing to Kafka.</p>
<div class="pic">App → Postgres → WAL → Debezium → Kafka → Consumer → Lake table</div>
<p><b>Replaying events by hand,</b> starting from {1: a}:</p>
<table><tr><th>Event</th><th>State</th></tr>
<tr><td>create 2 = b</td><td>{1: a, 2: b}</td></tr>
<tr><td>update 1 = A</td><td>{1: A, 2: b}</td></tr>
<tr><td>delete 2</td><td>{1: A}</td></tr>
<tr><td>create 3 = c</td><td>{1: A, 3: c}</td></tr></table>
<p><b>Order matters per key,</b> so messages for one key must stay in order. In Kafka, you ensure this by using the primary key as the message key.</p>
<p><b>Compaction before merging.</b> If a batch has several events per key, only the last matters: create then update becomes the update. A create then delete still needs the delete, in case that row existed before the batch.</p>
<p><b>Soft deletes</b> mark a row as deleted rather than removing it, so downstream systems can see it went away. Hard deletes remain important for privacy laws, which you'll see later.</p>
<p><b>No CDC available?</b> Compare snapshots by hashing rows, which is expensive but works: new ids, changed hashes, missing ids.</p>
""", practice=["Apply Change Data Capture", "Compact a CDC Batch", "Soft Deletes", "Row Hash for Change Detection"])


LESSON("Core", "Late data and backfills", """
<p><b>Late data is normal.</b> A phone offline for two days sends events from two days ago. If you've already closed that day, what do you do?</p>
<ol><li><b>Reprocess affected partitions:</b> find the event days among late rows, and rerun those days, which is easy if runs are idempotent.</li>
<li><b>Set a limit:</b> after, say, 7 days, close the books. Older data goes to a separate table.</li>
<li><b>Tell people:</b> numbers for recent days may still change.</li></ol>
<p><b>Backfills</b> reprocess history, because of a bug fix or a new column. Run them in pieces:</p>
<p>10 days in chunks of 4 gives [1–4], [5–8], [9–10].</p>
<ul><li>Small chunks mean failures lose little. Track what's finished, and <b>resume</b> where you stopped.</li>
<li>Limit how many run at once, so you don't starve daily jobs or the source database.</li>
<li>Write to a new location, compare with the old data, and then switch.</li></ul>
<p><b>Checkpoints.</b> With a batch of 3 and a crash after item 7, the last checkpoint is at 6, so only item 7 is redone: 11 processings for 10 items. Checkpoint more often and you redo less, but pay more overhead.</p>
<p>The chart shows the trade-off between how often you checkpoint and the work you'd lose.</p>
""", practice=["Plan a Backfill", "Find What's Left to Backfill", "Which Partitions to Rerun?", "Checkpoint and Resume"])


@LD
def checkpoint_tradeoff():
    n, crash = 100000, 73217
    sizes = np.array([10, 100, 1000, 10000, 50000])
    lost = crash % sizes
    overhead = n // sizes
    print("work lost per checkpoint size:", dict(zip(sizes.tolist(), lost.tolist())))
    fig, ax = plt.subplots(figsize=(4.6, 2.7))
    ax.loglog(sizes, np.maximum(lost, 1), "o-", label="rows redone after this crash")
    ax.loglog(sizes, overhead, "s-", label="checkpoints written")
    ax.set_xlabel("rows between checkpoints")
    ax.legend(fontsize=7)


LESSON("Advanced", "Designing so that failure doesn't hurt users", """
<p><b>Dead-letter queues.</b> One corrupt message shouldn't stop a pipeline, so set it aside with its reason and carry on. But if a <i>large share</i> is bad, something's badly wrong, so halt. With a 50% limit, 1 bad in 3 continues, and 2 bad in 3 stops.</p>
<p><b>Write-audit-publish (WAP).</b> Don't let users see data you haven't checked:</p>
<ol><li><b>Write</b> to a staging location.</li><li><b>Audit:</b> run the quality checks.</li><li><b>Publish</b> atomically, only if they pass.</li></ol>
<p>If staged data contains a NULL id, users keep seeing yesterday's table, which is stale but correct. That's nearly always better than fresh but wrong.</p>
<p><b>Atomic swap.</b> Readers must never see half a load. Build the new version off to the side, and then flip one pointer, such as a view or a table format's metadata. If the build fails, the pointer doesn't move.</p>
<p><b>Dedupe in streams.</b> You can't remember every id forever, so keep ids for a time window (TTL). Event "a" at time 5 is a duplicate of time 1, with a 10-second TTL. At time 20 it's treated as new. Choose a TTL longer than the realistic delay of retries.</p>
<p><b>Always reconcile</b> source and target per day. If source has d2 = 5 and target has d2 = 0, you've found the problem before your users do.</p>
<table><tr><th>Question for any pipeline</th><th>Good answer</th></tr>
<tr><td>Run it twice?</td><td>same result</td></tr>
<tr><td>Fails halfway?</td><td>rerun from the start or a checkpoint</td></tr>
<tr><td>Data arrives late?</td><td>affected days get reprocessed</td></tr>
<tr><td>Source sends garbage?</td><td>caught at the door, and doesn't reach users</td></tr>
<tr><td>How will I know?</td><td>alerts, not a user's email</td></tr></table>
""", practice=["Write-Audit-Publish", "Dead-Letter Queue", "Dedupe a Stream With a TTL", "Atomic Swap", "Reconcile Source and Target"])
