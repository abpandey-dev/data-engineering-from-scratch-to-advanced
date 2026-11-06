from lib import *

THEORY("Output modes in Structured Streaming", """
<table><tr><th>Mode</th><th>Emits</th><th>Needs</th></tr>
<tr><td>Append</td><td>final rows once a window closes</td><td>a watermark for aggregates</td></tr>
<tr><td>Update</td><td>rows that changed this trigger</td><td>a sink that can update</td></tr>
<tr><td>Complete</td><td>the whole result each time</td><td>memory for everything</td></tr></table>
""")
FAQ("Event time vs processing time?", "<p>Event time is when it happened. Processing time is when it was handled. Use event time for correct results, because data can arrive late.</p>")
FAQ("What is a watermark?", "<p>The maximum event time seen minus allowed lateness. It decides when windows close, when state is freed, and which late events get dropped.</p>")
FAQ("Tumbling vs sliding vs session windows?", "<p>Tumbling are fixed and non-overlapping. Sliding are fixed and overlapping. Session windows close after a gap in activity.</p>")
FAQ("How do you get exactly-once?", "<p>A replayable source, checkpointed offsets and state, and an idempotent or transactional sink.</p>")
FAQ("Micro-batch vs continuous processing?", "<p>Micro-batch groups records into small jobs, which is simple with latency in seconds. Continuous handles each record, for lower latency and more complexity.</p>")
FAQ("Lambda vs Kappa?", "<p>Lambda maintains batch and streaming paths. Kappa uses a single streaming path, and reprocesses by replaying the log.</p>")
FAQ("Scenario: your streaming job's state keeps growing until it crashes. What do you do?", "<p>Add a watermark or TTL so old state is evicted. Check for high-cardinality keys, and use RocksDB for large state.</p>")
FAQ("Scenario: batch duration exceeds the trigger interval. What happens, and what do you do?", "<p>Lag grows without limit. Add resources or partitions, fix slow sinks, limit input per trigger, or lengthen the interval if latency allows it.</p>")
FAQ("Scenario: streaming totals don't match the nightly batch. Why?", "<p>Late events dropped by the watermark, duplicates, or different time definitions. Measure dropped events, and many teams let batch correct the stream's numbers.</p>")
