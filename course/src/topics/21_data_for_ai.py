from lib import *
import hashlib
import json
import math
import re
from collections import Counter, defaultdict


TOPIC(
    id="data-for-ai", title="Data Engineering for AI", glyph="DE→AI",
    blurb="The data behind models and LLMs: feature stores and point-in-time joins, leakage, dataset versioning, RAG ingestion pipelines, incremental embedding, deduplication, PII scrubbing and evaluation data. It's a bridge from data engineering to AI engineering.",
    theory="""
<h3>Cheat sheet</h3>
<pre><code class="py">Features: same logic in training and serving, joined point in time
Dataset: versioned by content hash; split by a stable hash of the id
RAG ingest: load → clean → chunk → hash → embed only what's new → upsert → delete what's gone
Before embedding or training: remove personal data and duplicates</code></pre>
""")


Q(None, "Point-in-Time Feature Join", "Hard", "No peeking at the future",
  "For each label (user, time), attach the user's latest feature value with time ≤ the label's time, or None. Features are (user, time, value).",
  [(([("a", 10), ("a", 25), ("b", 5)], [("a", 5, 1), ("a", 20, 2), ("a", 30, 3), ("b", 9, 7)]),  [['a', 10, 1], ['a', 25, 2], ['b', 5, None]])],
  ("Scan all feature rows per label.", "O(l·f)", "O(l)"),
  ("Group and sort features per user, then binary search.", "O((l + f) log f)", "O(f)"),
  names=["labels", "features"])


@B
def pit_join(labels, features):
    out = []
    for user, t in labels:
        best, best_t = None, -1
        for u, ft, v in features:
            if u == user and ft <= t and ft > best_t:
                best, best_t = v, ft
        out.append([user, t, best])
    return out


@O
def pit_join(labels, features):
    import bisect
    by_user = defaultdict(list)
    for u, t, v in sorted(features, key=lambda x: x[1]):
        by_user[u].append((t, v))
    out = []
    for user, t in labels:
        rows = by_user[user]
        i = bisect.bisect_right([r[0] for r in rows], t)
        out.append([user, t, rows[i - 1][1] if i else None])
    return out


Q(None, "What a Leak Looks Like", "Medium", "Too good to be true",
  "Compare a naive join (latest value overall) to a point-in-time one. Return how many labels would see a future value.",
  [(([("a", 10), ("a", 25), ("b", 5)], {"a": 30, "b": 3}),  2)],
  ("A loop.", "O(l)", "O(1)"),
  ("A generator.", "O(l)", "O(1)"),
  names=["labels", "latest_time"])


@B
def leaked_labels(labels, latest_time):
    count = 0
    for user, t in labels:
        if latest_time[user] > t:
            count += 1
    return count


@O
def leaked_labels(labels, latest_time):
    return sum(latest_time[u] > t for u, t in labels)


Q(None, "Rolling Feature", "Medium", "Spend in the last 7 days",
  "For each (day, amount) row in order, return the sum of amounts in the previous w days, excluding today, as training must not see the present value.",
  [(([(1, 10), (2, 20), (9, 5), (10, 1)], 7),  [0, 10, 20, 5])],
  ("Rescan for each row.", "O(n²)", "O(1)"),
  ("A deque for the sliding window.", "O(n)", "O(w)"),
  names=["rows", "w"])


@B
def rolling_feature(rows, w):
    out = []
    for day, _ in rows:
        out.append(sum(a for d, a in rows if day - w <= d < day))
    return out


@O
def rolling_feature(rows, w):
    from collections import deque
    win, total, out = deque(), 0, []
    for day, amount in rows:
        while win and win[0][0] < day - w:
            total -= win.popleft()[1]
        out.append(total)
        win.append((day, amount))
        total += amount
    return out


Q(None, "Stable Train/Test Split", "Medium", "Same split every run",
  "Assign by hash: md5(id) as an integer, mod 100, below test_pct goes to test. Random splits change between runs, and leak users across sets. Return (train ids, test ids).",
  [((["u1", "u2", "u3", "u4", "u5", "u6"], 34),  (['u2', 'u4', 'u6'], ['u1', 'u3', 'u5']))],
  ("A loop.", "O(n)", "O(n)"),
  ("A helper in comprehensions.", "O(n)", "O(n)"),
  names=["ids", "test_pct"])


@B
def stable_split(ids, test_pct):
    train, test = [], []
    for i in ids:
        bucket = int(hashlib.md5(i.encode()).hexdigest(), 16) % 100
        if bucket < test_pct:
            test.append(i)
        else:
            train.append(i)
    return (train, test)


@O
def stable_split(ids, test_pct):
    is_test = lambda i: int(hashlib.md5(i.encode()).hexdigest(), 16) % 100 < test_pct
    return ([i for i in ids if not is_test(i)], [i for i in ids if is_test(i)])


Q(None, "Version a Dataset", "Medium", "Which data trained this model?",
  "Return a short content hash of rows that doesn't depend on row order: md5 of the sorted JSON lines, first 8 characters. Also return whether two orders give the same version.",
  [(([{"a": 1}, {"a": 2}],),  ('1ba60f45', True))],
  ("Build the lines in a loop.", "O(n log n)", "O(n)"),
  ("A helper used twice.", "O(n log n)", "O(n)"))


@B
def dataset_version(rows):
    lines = []
    for r in rows:
        lines.append(json.dumps(r, sort_keys=True))
    lines.sort()
    v1 = hashlib.md5("\n".join(lines).encode()).hexdigest()[:8]
    lines2 = sorted(json.dumps(r, sort_keys=True) for r in reversed(rows))
    v2 = hashlib.md5("\n".join(lines2).encode()).hexdigest()[:8]
    return (v1, v1 == v2)


@O
def dataset_version(rows):
    v = lambda x: hashlib.md5("\n".join(sorted(json.dumps(r, sort_keys=True) for r in x)).encode()).hexdigest()[:8]
    return (v(rows), v(rows) == v(rows[::-1]))


Q(None, "Label Balance", "Easy", "Know your classes",
  "Return each label's share, rounded to 3 decimals and sorted, and whether the rarest is below min_share.",
  [((["a", "a", "a", "b"], 0.3),  ({'a': 0.75, 'b': 0.25}, True))],
  ("A dictionary.", "O(n)", "O(k)"),
  ("<code>Counter</code>.", "O(n)", "O(k)"),
  names=["labels", "min_share"])


@B
def label_balance(labels, min_share):
    counts = {}
    for l in labels:
        counts[l] = counts.get(l, 0) + 1
    shares = {k: round(counts[k] / len(labels), 3) for k in sorted(counts)}
    return (shares, min(shares.values()) < min_share)


@O
def label_balance(labels, min_share):
    s = {k: round(v / len(labels), 3) for k, v in sorted(Counter(labels).items())}
    return (s, min(s.values()) < min_share)


Q(None, "Clean Text for Ingestion", "Easy", "Garbage in, garbage out",
  "Strip HTML tags, collapse whitespace, and drop documents under min_words. Return cleaned documents.",
  [((["<p>Hello   <b>world</b> today</p>", "<div>hi</div>"], 2),  ['Hello world today'])],
  ("Walk characters, tracking whether inside a tag.", "O(n)", "O(n)"),
  ("Regular expressions. Real HTML is better parsed by a library.", "O(n)", "O(n)"),
  names=["docs", "min_words"])


@B
def clean_docs(docs, min_words):
    out = []
    for d in docs:
        text, inside = "", False
        for ch in d:
            if ch == "<":
                inside = True
            elif ch == ">":
                inside = False
            elif not inside:
                text += ch
        words = text.split()
        if len(words) >= min_words:
            out.append(" ".join(words))
    return out


@O
def clean_docs(docs, min_words):
    clean = (" ".join(re.sub(r"<[^>]+>", "", d).split()) for d in docs)
    return [c for c in clean if len(c.split()) >= min_words]


Q(None, "Chunk With Overlap", "Easy", "Splitting for retrieval",
  "Split words into chunks of size words, stepping by size − overlap. Return chunks as strings.",
  [(("a b c d e f g", 3, 1),  ['a b c', 'c d e', 'e f g'])],
  ("A while loop.", "O(n)", "O(n)"),
  ("A comprehension with a step.", "O(n)", "O(n)"),
  names=["text", "size", "overlap"])


@B
def chunk_text(text, size, overlap):
    words = text.split()
    out, i = [], 0
    while True:
        out.append(" ".join(words[i:i + size]))
        if i + size >= len(words):
            break
        i += size - overlap
    return out


@O
def chunk_text(text, size, overlap):
    w, step = text.split(), size - overlap
    n = max(0, math.ceil((len(w) - size) / step)) + 1
    return [" ".join(w[i * step:i * step + size]) for i in range(n)]


Q(None, "Embed Only What Changed", "Medium", "Embeddings cost money",
  "Given stored {chunk_id: hash} and current {chunk_id: text}, return (ids to embed, ids to delete, ids unchanged), sorted. Hash = md5 of the text.",
  [(({"a": hashlib.md5(b"one").hexdigest(), "b": hashlib.md5(b"two").hexdigest()}, {"a": "one", "b": "TWO", "c": "three"}),  (['b', 'c'], [], ['a']))],
  ("Loops.", "O(n)", "O(n)"),
  ("Sets and a comprehension.", "O(n log n)", "O(n)"),
  names=["stored", "current"])


@B
def embed_plan(stored, current):
    embed, keep = [], []
    for k, text in current.items():
        if stored.get(k) == hashlib.md5(text.encode()).hexdigest():
            keep.append(k)
        else:
            embed.append(k)
    delete = [k for k in stored if k not in current]
    return (sorted(embed), sorted(delete), sorted(keep))


@O
def embed_plan(stored, current):
    now = {k: hashlib.md5(t.encode()).hexdigest() for k, t in current.items()}
    same = {k for k in now if stored.get(k) == now[k]}
    return (sorted(now.keys() - same), sorted(stored.keys() - now.keys()), sorted(same))


Q(None, "Embedding Cost and Time", "Easy", "Plan the backfill",
  "Given documents, tokens per document, a made-up price per million tokens and tokens per second, return cost and hours, rounded to 2 decimals.",
  [((1000000, 500, 0.1, 50000),  (50.0, 2.78))],
  ("Step by step.", "O(1)", "O(1)"),
  ("Compact.", "O(1)", "O(1)"),
  names=["docs", "tokens", "price", "rate"])


@B
def embed_cost(docs, tokens, price, rate):
    total = docs * tokens
    cost = total / 1e6 * price
    hours = total / rate / 3600
    return (round(cost, 2), round(hours, 2))


@O
def embed_cost(docs, tokens, price, rate):
    t = docs * tokens
    return (round(t * price / 1e6, 2), round(t / rate / 3600, 2))


Q(None, "Batch for an Embedding API", "Medium", "Respect both limits",
  "Group token counts into batches with at most max_items and max_tokens each. A single item over max_tokens goes to skipped. Return (batches, skipped).",
  [(([100, 300, 900, 200, 2000], 2, 1000),  ([[100, 300], [900], [200]], [2000]))],
  ("Grow a list, checking the sum.", "O(n)", "O(n)"),
  ("A running total.", "O(n)", "O(n)"),
  names=["counts", "max_items", "max_tokens"])


@B
def embed_batches(counts, max_items, max_tokens):
    batches, cur, skipped = [], [], []
    for c in counts:
        if c > max_tokens:
            skipped.append(c)
            continue
        if cur and (len(cur) == max_items or sum(cur) + c > max_tokens):
            batches.append(cur)
            cur = []
        cur.append(c)
    if cur:
        batches.append(cur)
    return (batches, skipped)


@O
def embed_batches(counts, max_items, max_tokens):
    batches, cur, total = [], [], 0
    for c in (x for x in counts if x <= max_tokens):
        if cur and (len(cur) == max_items or total + c > max_tokens):
            batches.append(cur)
            cur, total = [], 0
        cur.append(c)
        total += c
    return (batches + [cur] if cur else batches, [x for x in counts if x > max_tokens])


Q(None, "Near-Duplicate Documents", "Medium", "Don't index ten copies",
  "Keep a document only if its word-set Jaccard similarity to every kept one is below limit. Return kept indexes.",
  [((["the cat sat here", "the cat sat there", "stock prices fell"], 0.5),  [0, 2])],
  ("Compute overlaps with lists.", "O(n²·w)", "O(w)"),
  ("Precompute sets.", "O(n²·w)", "O(n·w)"),
  names=["docs", "limit"])


@B
def near_dupes(docs, limit):
    kept = []
    for i, d in enumerate(docs):
        a = set(d.split())
        dup = False
        for j in kept:
            b = set(docs[j].split())
            if len(a & b) / len(a | b) >= limit:
                dup = True
                break
        if not dup:
            kept.append(i)
    return kept


@O
def near_dupes(docs, limit):
    sets = [set(d.split()) for d in docs]
    kept = []
    for i, s in enumerate(sets):
        if all(len(s & sets[j]) / len(s | sets[j]) < limit for j in kept):
            kept.append(i)
    return kept


Q(None, "MinHash: Similarity at Scale", "Hard", "Avoid comparing every pair",
  "Estimate Jaccard similarity with k hash functions: the share of positions where the minimum md5(f'{i}{word}') is equal for both sets. Round to 2 decimals. Compare with the true value.",
  [(("a b c d e f g h", "a b c d e f x y", 200),  (0.59, 0.6))],
  ("Loop for each hash.", "O(k·w)", "O(k)"),
  ("A signature helper.", "O(k·w)", "O(k)"),
  names=["doc_a", "doc_b", "k"])


@B
def minhash(doc_a, doc_b, k):
    a, b = set(doc_a.split()), set(doc_b.split())
    h = lambda i, w: hashlib.md5(f"{i}{w}".encode()).hexdigest()
    same = 0
    for i in range(k):
        if min(h(i, w) for w in a) == min(h(i, w) for w in b):
            same += 1
    return (round(same / k, 2), round(len(a & b) / len(a | b), 2))


@O
def minhash(doc_a, doc_b, k):
    a, b = set(doc_a.split()), set(doc_b.split())
    sig = lambda s: [min(hashlib.md5(f"{i}{w}".encode()).hexdigest() for w in s) for i in range(k)]
    return (round(sum(x == y for x, y in zip(sig(a), sig(b))) / k, 2), round(len(a & b) / len(a | b), 2))


Q(None, "Scrub Personal Data", "Medium", "Before embedding or training",
  "Replace emails and 10-digit numbers with placeholders, and count replacements. Once in a vector index or model, it's hard to remove.",
  [(("Mail a@b.io or call 9876543210, or c@d.io",),  ('Mail [EMAIL] or call [PHONE], or [EMAIL]', 3))],
  ("Word by word.", "O(n)", "O(n)"),
  ("<code>re.subn</code>.", "O(n)", "O(n)"))


@B
def scrub(text):
    a = re.findall(r"\S+@\S+\.\w+", text)
    for x in a:
        text = text.replace(x, "[EMAIL]")
    b = re.findall(r"\b\d{10}\b", text)
    for x in b:
        text = text.replace(x, "[PHONE]")
    return (text, len(a) + len(b))


@O
def scrub(text):
    text, a = re.subn(r"\S+@\S+\.\w+", "[EMAIL]", text)
    text, b = re.subn(r"\b\d{10}\b", "[PHONE]", text)
    return (text, a + b)


Q(None, "Freshness of a Vector Index", "Easy", "Is the answer out of date?",
  "Given each document's last update and last index time, return stale ids, sorted, and the percent stale, rounded to 1 decimal.",
  [(({"a": (10, 12), "b": (20, 15), "c": (5, 5)},),  (['b'], 33.3))],
  ("A loop.", "O(n log n)", "O(n)"),
  ("A sorted comprehension.", "O(n log n)", "O(n)"))


@B
def stale_docs(docs):
    out = []
    for k, (updated, indexed) in docs.items():
        if updated > indexed:
            out.append(k)
    return (sorted(out), round(100 * len(out) / len(docs), 1))


@O
def stale_docs(docs):
    s = sorted(k for k, (u, i) in docs.items() if u > i)
    return (s, round(100 * len(s) / len(docs), 1))


Q(None, "Build a Training File", "Medium", "JSON Lines for LLM evaluation or tuning",
  "Turn (question, answer) pairs into JSONL lines with messages, skipping empties and duplicate questions. Return (lines, skipped).",
  [(([("Hi?", "Hello"), ("", "x"), ("Hi?", "Dup")],),  (['{"messages": [{"role": "user", "content": "Hi?"}, {"role": "assistant", "content": "Hello"}]}'], 2))],
  ("A loop with checks.", "O(n)", "O(n)"),
  ("Same, with a seen set and a helper.", "O(n)", "O(n)"))


@B
def training_lines(pairs):
    seen, lines, skipped = [], [], 0
    for q, a in pairs:
        if not q or not a or q in seen:
            skipped += 1
            continue
        seen.append(q)
        lines.append(json.dumps({"messages": [{"role": "user", "content": q}, {"role": "assistant", "content": a}]}))
    return (lines, skipped)


@O
def training_lines(pairs):
    unique = {}
    for q, a in pairs:
        if q and a:
            unique.setdefault(q, a)
    msg = lambda q, a: json.dumps({"messages": [{"role": "user", "content": q}, {"role": "assistant", "content": a}]})
    return ([msg(q, a) for q, a in unique.items()], len(pairs) - len(unique))


Q(None, "Check an Eval Set", "Medium", "Test data needs testing",
  "An eval set must have no overlap with the training ids, and every case needs an expected answer. Return (leaked ids sorted, ids with no answer sorted).",
  [(({"a": "x", "b": "", "c": "y"}, ["a", "z"]),  (['a'], ['b']))],
  ("Loops.", "O(n·t)", "O(n)"),
  ("A set.", "O(n + t)", "O(t)"),
  names=["eval_set", "train_ids"])


@B
def check_eval(eval_set, train_ids):
    leaked, empty = [], []
    for k, v in eval_set.items():
        if k in train_ids:
            leaked.append(k)
        if not v:
            empty.append(k)
    return (sorted(leaked), sorted(empty))


@O
def check_eval(eval_set, train_ids):
    return (sorted(eval_set.keys() & set(train_ids)), sorted(k for k, v in eval_set.items() if not v))


Q(None, "Serving Features: Online vs Offline", "Medium", "Training-serving skew",
  "Compare the same feature for the same keys in offline and online stores. Return (keys missing online, mismatched keys beyond tol), sorted.",
  [(({"a": 1.0, "b": 2.0, "c": 3.0}, {"a": 1.0, "b": 2.5}, 0.01),  (['c'], ['b']))],
  ("A loop.", "O(k)", "O(k)"),
  ("Comprehensions.", "O(k log k)", "O(k)"),
  names=["offline", "online", "tol"])


@B
def feature_skew(offline, online, tol):
    missing, bad = [], []
    for k, v in offline.items():
        if k not in online:
            missing.append(k)
        elif abs(online[k] - v) > tol:
            bad.append(k)
    return (sorted(missing), sorted(bad))


@O
def feature_skew(offline, online, tol):
    return (sorted(offline.keys() - online.keys()), sorted(k for k in offline.keys() & online.keys() if abs(offline[k] - online[k]) > tol))


Q(None, "Which Embedding Model Built This?", "Medium", "Mixed vectors are useless",
  "Vectors from different models can't be compared. Given chunk → model, and the current model, return the count to re-embed, and whether the index is safe to query.",
  [(({"a": "m2", "b": "m1", "c": "m2"}, "m2"), (1, False)), (({"a": "m2"}, "m2"), (0, True))],
  ("A loop.", "O(n)", "O(1)"),
  ("A generator.", "O(n)", "O(1)"),
  names=["chunks", "current"])


@B
def reembed_needed(chunks, current):
    n = 0
    for model in chunks.values():
        if model != current:
            n += 1
    return (n, n == 0)


@O
def reembed_needed(chunks, current):
    n = sum(m != current for m in chunks.values())
    return (n, not n)


Q(None, "Find Bad Retrieval Sources", "Medium", "Feedback into the pipeline",
  "From logs (source, helpful), return sources with at least min_n uses and a helpful rate below limit, sorted.",
  [(([("wiki", True), ("wiki", False), ("old", False), ("old", False), ("x", False)], 2, 0.3),  ['old'])],
  ("Two dictionaries.", "O(n)", "O(s)"),
  ("<code>defaultdict(list)</code>.", "O(n)", "O(s)"),
  names=["logs", "min_n", "limit"])


@B
def bad_sources(logs, min_n, limit):
    total, good = {}, {}
    for s, ok in logs:
        total[s] = total.get(s, 0) + 1
        good[s] = good.get(s, 0) + (1 if ok else 0)
    return sorted(s for s in total if total[s] >= min_n and good[s] / total[s] < limit)


@O
def bad_sources(logs, min_n, limit):
    g = defaultdict(list)
    for s, ok in logs:
        g[s].append(ok)
    return sorted(s for s, v in g.items() if len(v) >= min_n and sum(v) / len(v) < limit)
