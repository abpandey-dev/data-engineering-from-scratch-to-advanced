from lib import *

THEORY("Where to put checks", """
<table><tr><th>Stage</th><th>Check</th></tr>
<tr><td>On arrival</td><td>schema, file complete, row count above zero</td></tr>
<tr><td>After transform</td><td>keys unique, not null, ranges, joins kept their rows</td></tr>
<tr><td>Before publish</td><td>totals reconcile, no sudden changes</td></tr>
<tr><td>After publish</td><td>freshness, drift, monitored continuously</td></tr></table>
""")
FAQ("What are the dimensions of data quality?", "<p>Completeness, uniqueness, validity, consistency, timeliness and accuracy.</p>")
FAQ("What is a data contract?", "<p>An agreement between producer and consumer on schema, meaning and service levels, ideally enforced automatically in CI.</p>")
FAQ("How do you detect anomalies without fixed rules?", "<p>Compare metrics like volume to history, accounting for seasonality, using z-scores or similar, and track distribution drift.</p>")
FAQ("Should a failed check stop the pipeline?", "<p>It depends on severity. Critical failures should block publishing. Minor ones warn and carry on. Bad rows can be quarantined so good data still flows.</p>")
FAQ("What is data observability?", "<p>Continuously monitoring freshness, volume, schema, distribution and lineage, so you find problems before users do.</p>")
FAQ("Scenario: a stakeholder says the numbers look wrong. What do you do?", "<p>Get a specific example, then trace it back layer by layer, comparing counts and totals against the source. Tell them what you find, then add a test for it.</p>")
FAQ("Scenario: row count dropped 40% but all tests passed. Why, and what next?", "<p>The tests were only rule-based. Check upstream for a partial load or a filter change, and add volume anomaly monitoring.</p>")
FAQ("Scenario: you're asked to add quality checks to an old pipeline. Where do you start?", "<p>Profile the data, ask users what would hurt most, then add keys, nulls, freshness and volume checks on the most-used tables first.</p>")
FAQ("Scenario: an upstream team keeps breaking your pipeline. How do you fix this?", "<p>Show them the impact, agree a contract, add schema checks to their CI, and set up a shared alert. This is as much about people as about tools.</p>")
