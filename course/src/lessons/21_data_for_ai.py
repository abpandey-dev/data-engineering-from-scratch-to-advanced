from lib import *
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import hashlib


LESSON("Basics", "AI runs on data pipelines", """
<p>This is your bridge from data engineering to AI engineering. Models get the attention, but most production AI problems are data problems.</p>
<table><tr><th>AI system</th><th>What the data engineer builds</th></tr>
<tr><td>Classic ML</td><td>feature pipelines, training sets, feature stores</td></tr>
<tr><td>RAG / LLM apps</td><td>ingestion, chunking, embedding, keeping indexes fresh</td></tr>
<tr><td>Fine-tuning</td><td>clean, deduplicated, versioned training data</td></tr>
<tr><td>Evaluation</td><td>eval sets, logging, feedback loops</td></tr></table>
<p><b>Skills you already have from this course apply directly:</b> idempotency, incremental loads, data quality, lineage and cost control.</p>
<p><b>Rule one of training data: never leak the future.</b> A model predicting churn in January mustn't see February's data. This is the same point-in-time idea as SCD 2.</p>
<table><tr><th>Label</th><th>Feature history for a</th><th>Correct value</th></tr>
<tr><td>a at time 10</td><td>t5: 1, t20: 2, t30: 3</td><td><b>1</b></td></tr>
<tr><td>a at time 25</td><td>same</td><td><b>2</b></td></tr>
<tr><td>b at time 5</td><td>t9: 7</td><td><b>None</b>: it didn't exist yet</td></tr></table>
<p>A naive join on the latest value would give every label 3, and 2 of the 3 labels would see the future. The model looks brilliant in testing and fails in production.</p>
<p><b>Rolling features</b> must exclude the present: "spend in the previous 7 days" for days 1, 2, 9, 10 with amounts 10, 20, 5, 1 gives 0, 10, 20, 5.</p>
""", practice=["Point-in-Time Feature Join", "What a Leak Looks Like", "Rolling Feature"])


LESSON("Core", "Reliable training data", """
<p><b>Stable splits.</b> Random splits change on each run, and the same user can land in both train and test. Hash the id instead: <code>md5(id) % 100 &lt; 20</code> always puts a user in the same set, and new data doesn't shuffle old assignments.</p>
<p><b>Version your datasets.</b> "Which data trained this model?" should have an exact answer. A content hash that doesn't depend on row order works, and tools like Iceberg snapshots or DVC can help.</p>
<p><b>Check before training:</b></p>
<table><tr><th>Check</th><th>Example</th></tr>
<tr><td>Label balance</td><td>a 75%, b 25%; is the minority too rare?</td></tr>
<tr><td>Duplicates</td><td>the same question twice leaks across a split</td></tr>
<tr><td>Eval isolation</td><td>id "a" in both eval and training is a leak</td></tr>
<tr><td>Missing answers</td><td>an eval case with no expected answer is useless</td></tr></table>
<p><b>Feature stores</b> solve training-serving skew. A feature is defined once, and it's served offline for training (point in time) and online with low latency. Compare both regularly: key c missing online, and b at 2.0 vs 2.5, are both bugs that crash nothing but hurt the model.</p>
<p><b>Training files</b> are often JSON Lines of messages. Clean them like any data: of 3 pairs here, one empty and one duplicate leave a single valid example.</p>
""", practice=["Stable Train/Test Split", "Version a Dataset", "Label Balance", "Check an Eval Set", "Serving Features: Online vs Offline", "Build a Training File"])


LESSON("Core", "A RAG ingestion pipeline", """
<p>A demo RAG app embeds a folder once. A production one is a <b>data pipeline that never stops</b>, since documents change and get deleted.</p>
<div class="pic">Sources → Load → Clean → Scrub PII → Chunk → Hash → Embed new only → Upsert → Delete removed
                                                        ↑
                                 stored hashes say what's changed</div>
<p><b>Clean.</b> "&lt;p&gt;Hello   &lt;b&gt;world&lt;/b&gt; today&lt;/p&gt;" becomes "Hello world today". Navigation menus and boilerplate hurt retrieval, so strip them.</p>
<p><b>Chunk.</b> With size 3 and overlap 1, "a b c d e f g" gives "a b c", "c d e", "e f g". Keep titles with chunks, and test sizes on your own questions.</p>
<p><b>Incremental embedding is where this course pays off.</b> Hash each chunk, and compare with what's stored:</p>
<table><tr><th>Chunk</th><th>State</th><th>Action</th></tr>
<tr><td>a: unchanged</td><td>hash matches</td><td>skip: saves money</td></tr>
<tr><td>b: edited</td><td>hash differs</td><td>re-embed</td></tr>
<tr><td>c: new</td><td>no stored hash</td><td>embed</td></tr>
<tr><td>d: gone</td><td>not in source</td><td><b>delete</b>, or answers cite dead documents</td></tr></table>
<p><b>Cost.</b> 1 million documents of 500 tokens at a made-up 0.10 per million tokens costs 50, and takes 2.78 hours at 50,000 tokens a second. Batch within both limits, and set aside anything too large.</p>
<p><b>Model upgrades.</b> Vectors from different models can't be compared, so changing the model means re-embedding everything. Store the model name with each vector. An index with mixed models isn't safe to query.</p>
<p><b>Freshness.</b> If one of three documents changed after being indexed, 33% of your index is stale. Alert on that, as you would with any table.</p>
""", practice=["Clean Text for Ingestion", "Chunk With Overlap", "Embed Only What Changed", "Embedding Cost and Time", "Batch for an Embedding API", "Which Embedding Model Built This?", "Freshness of a Vector Index"])


LESSON("Advanced", "Quality, privacy and feedback for AI data", """
<p><b>Near-duplicates waste money and crowd out useful results.</b> Word-set Jaccard similarity finds them: "the cat sat here" and "the cat sat there" share 3 of 5 words, 0.6.</p>
<p>Comparing all pairs is impossible at scale, so <b>MinHash</b> estimates similarity using small signatures: the chance that two sets share a minimum hash equals their Jaccard similarity. Our test with 200 hashes estimates 0.59, against a true 0.60. Combined with locality-sensitive hashing, it finds likely matches without comparing everything.</p>
<p>The chart shows how the estimate settles as hashes are added.</p>
<p><b>Scrub personal data before embedding or training.</b> Once it's in a vector index, or worse a trained model, removing it is hard or impossible. "Mail a@b.io or call 9876543210" becomes "Mail [EMAIL] or call [PHONE]". Simple patterns miss a lot, so use dedicated tools on real data, and apply access control at retrieval time too.</p>
<p><b>Close the loop.</b> Log which sources were retrieved, and whether answers helped. A source used twice with 0% helpfulness is a data problem you can fix. Requiring a minimum number of uses avoids judging from one example.</p>
<p><b>Where to go next as an AI engineer:</b></p>
<ul><li>Vector databases and hybrid search.</li><li>Evaluation pipelines for LLM apps.</li><li>Data contracts for AI features.</li><li>Streaming features for real-time models.</li></ul>
""", practice=["Near-Duplicate Documents", "MinHash: Similarity at Scale", "Scrub Personal Data", "Find Bad Retrieval Sources"])


@LD
def minhash_convergence():
    a = {f"w{i}" for i in range(100)}
    b = {f"w{i}" for i in range(50, 150)}
    true = len(a & b) / len(a | b)
    h = lambda i, w: hashlib.md5(f"{i}{w}".encode()).hexdigest()
    hits = [min(h(i, w) for w in a) == min(h(i, w) for w in b) for i in range(400)]
    estimates = np.cumsum(hits) / np.arange(1, 401)
    print("true:", round(true, 3), "estimate at 400:", round(float(estimates[-1]), 3))
    fig, ax = plt.subplots(figsize=(4.6, 2.7))
    ax.plot(range(1, 401), estimates, label="MinHash estimate")
    ax.axhline(true, color="black", linestyle="--", label="true Jaccard")
    ax.set_xlabel("number of hash functions")
    ax.legend(fontsize=7)
