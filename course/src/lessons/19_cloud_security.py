from lib import *
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np



LESSON("Basics", "The cloud data stack", """
<p>Most data platforms run in the cloud, and the concepts carry across providers. Here's a typical AWS design, which is close to the stack many Indian and global companies use:</p>
<div class="pic">Sources → Kinesis/MSK or DMS → S3 (raw) → Glue/EMR Spark → S3 (clean, Parquet)
                                   ↓                         ↓
                             Glue Catalog ──────→ Athena / Redshift → BI
                 Orchestrated by Airflow (MWAA)     Secured by IAM</div>
<table><tr><th>Service</th><th>Use it for</th></tr>
<tr><td>S3</td><td>the lake: cheap, durable storage</td></tr>
<tr><td>Glue Catalog</td><td>table definitions, shared by engines</td></tr>
<tr><td>Glue / EMR</td><td>running Spark, serverless or as clusters</td></tr>
<tr><td>Athena</td><td>SQL over S3, paying per scan</td></tr>
<tr><td>Redshift</td><td>a warehouse for heavy, repeated BI</td></tr>
<tr><td>Kinesis / MSK</td><td>streaming</td></tr>
<tr><td>Lambda</td><td>small event-driven jobs</td></tr></table>
<p><b>Serverless or cluster?</b> At made-up prices of 5 per TB scanned and 4 per cluster hour, scanning 100 TB a month costs 500 against 800 for 200 cluster hours, so serverless wins. At 5,000 TB it's 25,000 against 800, so the cluster wins. Do this sum for your own workload.</p>
<p><b>S3 basics:</b> files upload in parts, so a 10 GB file at 100 MB per part has 100 parts, and a failed part alone is retried. Lifecycle rules move old data to cheaper tiers, and delete it eventually.</p>
<pre><code class="py">import boto3
s3 = boto3.client("s3")                  # credentials come from an IAM role
s3.upload_file("day.parquet", "my-lake", "orders/day=2026-01-05/day.parquet")</code></pre>
""", practice=["Athena or a Cluster?", "Multipart Upload", "S3 Lifecycle Rule"])


LESSON("Core", "Permissions: least privilege", """
<p><b>IAM</b> decides who can do what, to which resource. Three rules cover most of it:</p>
<ol><li><b>Everything's denied by default.</b></li><li><b>An explicit Allow grants access.</b></li><li><b>An explicit Deny always wins.</b></li></ol>
<pre><code class="py">{"Effect": "Allow", "Action": "s3:Get*", "Resource": "lake/*"}
{"Effect": "Deny",  "Action": "s3:*",    "Resource": "lake/secret/*"}</code></pre>
<table><tr><th>Request</th><th>Result</th><th>Why</th></tr>
<tr><td>GetObject lake/a</td><td>allow</td><td>matches the Allow</td></tr>
<tr><td>GetObject lake/secret/x</td><td>deny</td><td>explicit Deny wins</td></tr>
<tr><td>PutObject lake/a</td><td>deny</td><td>nothing allows it</td></tr></table>
<p><b>Least privilege:</b> give each job only what it needs. Treat <code>"Action": "*"</code> or <code>"Resource": "*"</code> as a warning sign.</p>
<p><b>Prefer roles to long-lived keys.</b> A job assumes a role and gets temporary credentials. Any stored keys must be rotated, and audited for age.</p>
<p><b>Access at the data level:</b></p>
<table><tr><th>Control</th><th>Example</th></tr>
<tr><td>Role-based</td><td>analysts read sales, not hr</td></tr>
<tr><td>Row-level</td><td>Asha sees only India rows</td></tr>
<tr><td>Column-level or masking</td><td>phone shows as ******3210</td></tr></table>
<p>Unknown users should get nothing. <b>Encrypt</b> in transit (TLS) and at rest (KMS keys). <b>Audit logs</b> answer "who read this table?", which you'll need for an investigation.</p>
""", practice=["IAM Policy Evaluation", "Find Overly Broad Policies", "Role-Based Access", "Row-Level Security", "Column Masking", "Who Touched This Data?", "Rotate Old Keys", "Tag Everything"])


LESSON("Core", "Personal data and privacy", """
<p>Data engineers build the systems that hold people's personal information, so this is your responsibility. Laws including GDPR in Europe and India's DPDP Act set rules on it. This lesson teaches the engineering, so check real obligations with your legal team.</p>
<table><tr><th>Principle</th><th>What you build</th></tr>
<tr><td>Collect less</td><td>don't ingest columns no one needs</td></tr>
<tr><td>Limit purpose and access</td><td>access controls, masking</td></tr>
<tr><td>Keep it only as long as needed</td><td>retention rules: logs 30 days, say</td></tr>
<tr><td>Right to erasure</td><td>find and delete a person across tables</td></tr></table>
<p><b>Hashing isn't anonymising.</b> A 10-digit phone number has only 10¹⁰ possibilities. At a million hashes a second, you can try them all in 0.12 days, and modern hardware is far faster. So a plain hash of a phone number is easily reversed.</p>
<p>Use a <b>keyed hash (HMAC)</b> with a secret, or a token vault. This is <b>pseudonymisation</b>: it's still personal data, since someone with the key can link it back.</p>
<p><b>Removing names isn't enough.</b> A rare combination of age band and postcode can identify someone. <b>k-anonymity</b> asks for the smallest group sharing those values. A group of one means that person is unique in the data.</p>
<p><b>Find it before it spreads.</b> Scan samples for columns that look like emails or phone numbers. Over half matching is a useful signal, but a scan like this misses plenty.</p>
<p><b>Never put real personal data in dev, or in Git.</b> Use synthetic or masked data.</p>
""", practice=["Pseudonymise With a Secret", "How Easily Can It Be Reversed?", "k-Anonymity", "Find Personal Data", "Retention Policy"])


LESSON("Advanced", "Reliability and the bill", """
<p><b>What the nines mean:</b></p>
<table><tr><th>Availability</th><th>Downtime a year</th></tr>
<tr><td>99%</td><td>about 3.65 days</td></tr><tr><td>99.9%</td><td>525.6 minutes (8.8 hours)</td></tr><tr><td>99.99%</td><td>about 53 minutes</td></tr></table>
<p><b>Dependencies multiply.</b> A chain of services at 99.9%, 99.9% and 99% gives 98.8%, worse than any single one.</p>
<p><b>Recovery targets:</b> <b>RPO</b> is how much data you can lose, and <b>RTO</b> is how long you can be down. With daily backups and an 8-hour restore, targets of 6 and 4 hours both fail. <b>Test your restores:</b> a backup you've never restored isn't really a backup.</p>
<p><b>Cost levers:</b></p>
<table><tr><th>Lever</th><th>Example, at made-up prices</th></tr>
<tr><td>Spot instances</td><td>70% off with 20% rework: 100 becomes 36</td></tr>
<tr><td>But if interruptions are bad</td><td>10% off with 50% rework: 135, which is worse</td></tr>
<tr><td>Storage tiers and lifecycle rules</td><td>move old data, delete what's unused</td></tr>
<tr><td>Parquet and partitions</td><td>far less scanned</td></tr>
<tr><td>Same region and AZ</td><td>avoid transfer charges</td></tr></table>
<p><b>Transfer costs surprise people.</b> 500 GB to the internet at 0.09 costs 45, which is more than 1,000 GB cross-AZ at 0.01. Tag every resource by team and environment, or you can't tell who's spending what.</p>
<p><b>Infrastructure as code</b> (Terraform) keeps environments reproducible and reviewable.</p>
""", practice=["Availability Math", "Recovery Objectives", "Spot vs On-Demand", "Data Transfer Costs"])
