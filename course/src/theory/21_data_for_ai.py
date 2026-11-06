from lib import *

THEORY("Your path from data engineer to AI engineer", """
<table><tr><th>You already know</th><th>It becomes</th></tr>
<tr><td>Incremental loads and hashing</td><td>incremental embedding</td></tr>
<tr><td>Data quality tests</td><td>LLM and model evaluation</td></tr>
<tr><td>SCD 2 and point-in-time joins</td><td>leakage-free training data</td></tr>
<tr><td>Orchestration</td><td>training and ingestion pipelines</td></tr>
<tr><td>Streaming</td><td>real-time features</td></tr>
<tr><td>Access control</td><td>permission-aware retrieval</td></tr></table>
""")
FAQ("What is a feature store?", "<p>A shared system that defines features once and serves them both offline, for point-in-time training, and online, at low latency.</p>")
FAQ("What is data leakage?", "<p>Training with information unavailable at prediction time. Results look great in testing, and fail in production. Point-in-time joins and time-based splits prevent it.</p>")
FAQ("How do you keep a RAG index up to date?", "<p>Run ingestion as an incremental pipeline: hash chunks, embed only changes, delete removed items, and monitor freshness.</p>")
FAQ("What happens when you change the embedding model?", "<p>Everything must be re-embedded, since vectors from different models aren't comparable. Build a new index, test it, then switch.</p>")
FAQ("Why deduplicate training data?", "<p>Duplicates bias the model, and leak across train and test splits, giving inflated results.</p>")
FAQ("Scenario: a model is great offline, and poor in production. What's the data engineer's checklist?", "<p>Look for leakage in training, training-serving skew, drift since training, and missing or stale online features.</p>")
FAQ("Scenario: a RAG app cites a document that was deleted. What failed?", "<p>Ingestion handled new content but not deletes. Compare source and index on each run, delete what's gone, and alert on mismatches.</p>")
FAQ("Scenario: legal says a customer's data must be removed from your AI system. What do you do?", "<p>Delete from sources, indexes and training sets using lineage. A trained model is harder, and may need retraining, so scrub before training in the first place.</p>")
