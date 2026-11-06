from lib import *

THEORY("Security checklist", """
<ul><li>Roles and temporary credentials, not long-lived keys.</li>
<li>Least privilege, reviewed regularly.</li>
<li>Encryption at rest and in transit.</li>
<li>Block public access to buckets by default.</li>
<li>Secrets in a manager, never in code.</li>
<li>Masked or synthetic data outside production.</li>
<li>Audit logs kept and monitored.</li>
<li>Network isolation with private endpoints.</li></ul>
""")
FAQ("How does IAM evaluate a request?", "<p>Denied by default. An explicit Allow permits it, and an explicit Deny always overrides.</p>")
FAQ("Anonymisation vs pseudonymisation?", "<p>Anonymised data can't reasonably be linked back to a person. Pseudonymised data can, with a key or lookup, so it's still personal data.</p>")
FAQ("Why is hashing a phone number weak?", "<p>The space of numbers is small, so an attacker can hash them all. Use a keyed hash or tokens.</p>")
FAQ("How do you implement the right to erasure?", "<p>Use lineage to find all copies, delete by user key across tables, expire snapshots and old files, handle backups by policy, and log what was done.</p>")
FAQ("EMR vs Glue vs Athena?", "<p>Athena is for serverless SQL over S3. Glue runs serverless Spark jobs with little management. EMR gives more control and can be cheaper at steady scale.</p>")
FAQ("What are RPO and RTO?", "<p>RPO is the maximum acceptable data loss. RTO is the maximum acceptable downtime.</p>")
FAQ("Scenario: an S3 bucket with customer data was public. What do you do?", "<p>Close access at once, and tell security and legal. Use access logs to see what was read, rotate anything exposed, and add a guardrail that blocks public buckets.</p>")
FAQ("Scenario: your AWS bill spiked overnight. How do you investigate?", "<p>Use cost tools by service and tag. Look for forgotten clusters, cross-region transfer, or runaway jobs. Set budgets and alerts so that you hear sooner next time.</p>")
FAQ("Scenario: a job fails with AccessDenied. How do you debug it?", "<p>Find which role it runs as, the exact action and resource from the error, then look for missing allows, explicit denies, bucket policies and KMS key permissions.</p>")
