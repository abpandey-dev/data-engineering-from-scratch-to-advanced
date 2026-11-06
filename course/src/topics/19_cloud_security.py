from lib import *
import fnmatch
import hashlib
import math
from collections import Counter, defaultdict


TOPIC(
    id="cloud-security", title="Cloud, Cost & Security", glyph="☁",
    blurb="Running data platforms on AWS responsibly: S3, Glue, EMR, Athena and Redshift, IAM permissions, encryption, masking and pseudonymising personal data, access control, privacy law, reliability targets and controlling the bill.",
    theory="""
<h3>Cheat sheet</h3>
<table><tr><th>Need</th><th>AWS</th><th>GCP</th><th>Azure</th></tr>
<tr><td>Object storage</td><td>S3</td><td>GCS</td><td>Blob / ADLS</td></tr>
<tr><td>Catalog / ETL</td><td>Glue</td><td>Dataplex / Dataflow</td><td>Data Factory</td></tr>
<tr><td>Spark clusters</td><td>EMR</td><td>Dataproc</td><td>Synapse / Databricks</td></tr>
<tr><td>Serverless SQL on files</td><td>Athena</td><td>BigQuery external</td><td>Synapse serverless</td></tr>
<tr><td>Warehouse</td><td>Redshift</td><td>BigQuery</td><td>Synapse</td></tr>
<tr><td>Streaming</td><td>Kinesis / MSK</td><td>Pub/Sub</td><td>Event Hubs</td></tr></table>
""")


Q(None, "IAM Policy Evaluation", "Medium", "Explicit deny wins",
  "Statements are (effect, action pattern, resource pattern), with * allowed. Return 'deny' if any matching statement denies, 'allow' if any allows, otherwise 'deny' by default.",
  [(([("Allow", "s3:Get*", "lake/*"), ("Deny", "s3:*", "lake/secret/*")], "s3:GetObject", "lake/a"), 'allow'),
   (([("Allow", "s3:Get*", "lake/*"), ("Deny", "s3:*", "lake/secret/*")], "s3:GetObject", "lake/secret/x"), 'deny'),
   (([("Allow", "s3:Get*", "lake/*")], "s3:PutObject", "lake/a"), 'deny')],
  ("A loop with flags.", "O(s)", "O(1)"),
  ("Comprehension of matching effects.", "O(s)", "O(s)"),
  names=["statements", "action", "resource"])


@B
def iam_check(statements, action, resource):
    allowed = False
    for effect, a, r in statements:
        if fnmatch.fnmatch(action, a) and fnmatch.fnmatch(resource, r):
            if effect == "Deny":
                return "deny"
            allowed = True
    return "allow" if allowed else "deny"


@O
def iam_check(statements, action, resource):
    effects = {e for e, a, r in statements if fnmatch.fnmatch(action, a) and fnmatch.fnmatch(resource, r)}
    return "allow" if effects == {"Allow"} else "deny"


Q(None, "Find Overly Broad Policies", "Easy", "Least privilege",
  "Return indexes of statements allowing action '*' or resource '*'.",
  [(([("Allow", "*", "lake/*"), ("Allow", "s3:Get*", "lake/*"), ("Allow", "s3:Get*", "*"), ("Deny", "*", "*")],),  [0, 2])],
  ("A loop.", "O(s)", "O(m)"),
  ("A comprehension.", "O(s)", "O(m)"))


@B
def broad_policies(statements):
    out = []
    for i, (effect, a, r) in enumerate(statements):
        if effect == "Allow" and (a == "*" or r == "*"):
            out.append(i)
    return out


@O
def broad_policies(statements):
    return [i for i, (e, a, r) in enumerate(statements) if e == "Allow" and "*" in (a, r)]


Q(None, "Role-Based Access", "Easy", "Roles, not people",
  "Users have roles, and roles have tables. Return whether a user may read a table.",
  [(({"a": ["analyst"]}, {"analyst": ["sales"], "admin": ["sales", "hr"]}, "a", "hr"), False), (({"a": ["analyst"]}, {"analyst": ["sales"]}, "a", "sales"), True)],
  ("Nested loops.", "O(r·t)", "O(1)"),
  ("<code>any</code>.", "O(r·t)", "O(1)"),
  names=["users", "roles", "user", "table"])


@B
def can_read(users, roles, user, table):
    for role in users.get(user, []):
        if table in roles.get(role, []):
            return True
    return False


@O
def can_read(users, roles, user, table):
    return any(table in roles.get(r, []) for r in users.get(user, []))


Q(None, "Row-Level Security", "Medium", "Same table, different rows",
  "Filter rows to the regions a user can see. Admins see all. Return ids.",
  [(([(1, "IN"), (2, "US"), (3, "IN")], {"asha": ["IN"], "root": ["*"]}, "asha"), [1, 3]), (([(1, "IN"), (2, "US")], {"root": ["*"]}, "root"), [1, 2]), (([(1, "IN")], {}, "x"), [])],
  ("A loop.", "O(n)", "O(m)"),
  ("A set and a comprehension. Unknown users see nothing.", "O(n)", "O(m)"),
  names=["rows", "access", "user"])


@B
def visible_rows(rows, access, user):
    regions = access.get(user, [])
    out = []
    for i, region in rows:
        if "*" in regions or region in regions:
            out.append(i)
    return out


@O
def visible_rows(rows, access, user):
    allowed = set(access.get(user, []))
    return [i for i, r in rows if "*" in allowed or r in allowed]


Q(None, "Column Masking", "Easy", "Hide what isn't needed",
  "Mask a phone number to keep only the last 4 digits for non-privileged users.",
  [(("9876543210", False), '******3210'), (("9876543210", True), '9876543210')],
  ("An if, with string building.", "O(n)", "O(n)"),
  ("A conditional expression.", "O(n)", "O(n)"),
  names=["phone", "privileged"])


@B
def mask_phone(phone, privileged):
    if privileged:
        return phone
    stars = ""
    for _ in phone[:-4]:
        stars += "*"
    return stars + phone[-4:]


@O
def mask_phone(phone, privileged):
    return phone if privileged else "*" * (len(phone) - 4) + phone[-4:]


Q(None, "Pseudonymise With a Secret", "Medium", "Hashes alone can be reversed",
  "A plain hash of a phone number can be undone by hashing all possible numbers. Use a keyed hash (HMAC-SHA256) instead. Return the first 8 hex characters, and whether it differs from the plain SHA-256.",
  [(("9876543210", "secret"), ('fc2c6287', True))],
  ("Build it with <code>hmac.new</code>, step by step.", "O(n)", "O(1)"),
  ("Compact.", "O(n)", "O(1)"),
  names=["value", "key"])


@B
def pseudonymise(value, key):
    import hmac
    digest = hmac.new(key.encode(), value.encode(), hashlib.sha256).hexdigest()
    plain = hashlib.sha256(value.encode()).hexdigest()
    return (digest[:8], digest != plain)


@O
def pseudonymise(value, key):
    import hmac
    d = hmac.digest(key.encode(), value.encode(), "sha256").hex()
    return (d[:8], d != hashlib.sha256(value.encode()).hexdigest())


Q(None, "How Easily Can It Be Reversed?", "Easy", "Small spaces fall fast",
  "Return days to try every value of a 10-digit phone number at r hashes per second, rounded to 2 decimals. This is why plain hashing doesn't protect it.",
  [((10, 1000000), 0.12), ((10, 1000), 115.74)],
  ("Step by step.", "O(1)", "O(1)"),
  ("Compact.", "O(1)", "O(1)"),
  names=["digits", "rate"])


@B
def brute_days(digits, rate):
    space = 10 ** digits
    seconds = space / rate
    return round(seconds / 86400, 2)


@O
def brute_days(digits, rate):
    return round(10 ** digits / rate / 86400, 2)


Q(None, "k-Anonymity", "Medium", "Can someone be singled out?",
  "Given quasi-identifiers per person (such as age band and postcode), return the smallest group size. k = 1 means someone is unique, even with names removed.",
  [(([("30s", "411"), ("30s", "411"), ("40s", "110")],), 1)],
  ("A dictionary.", "O(n)", "O(g)"),
  ("<code>Counter</code>.", "O(n)", "O(g)"))


@B
def k_anonymity(rows):
    groups = {}
    for r in rows:
        groups[r] = groups.get(r, 0) + 1
    return min(groups.values())


@O
def k_anonymity(rows):
    return min(Counter(rows).values())


Q(None, "Find Personal Data", "Medium", "Scan before you share",
  "Return columns where over half of sampled values look like an email or 10-digit phone number, sorted.",
  [(({"a": ["x@y.io", "z@y.io", "1"], "b": ["hello", "9876543210", "k"], "c": ["9876543210", "9876500000"]},),  ['a', 'c'])],
  ("Checks in loops.", "O(c·s)", "O(c)"),
  ("A regular expression.", "O(c·s)", "O(c)"))


@B
def pii_columns(sample):
    out = []
    for col, values in sample.items():
        hits = 0
        for v in values:
            if ("@" in v and "." in v) or (v.isdigit() and len(v) == 10):
                hits += 1
        if hits * 2 > len(values):
            out.append(col)
    return sorted(out)


@O
def pii_columns(sample):
    import re
    p = re.compile(r"\S+@\S+\.\S+|\d{10}$")
    return sorted(c for c, v in sample.items() if sum(bool(p.match(x)) for x in v) * 2 > len(v))


Q(None, "Retention Policy", "Easy", "Keep it only as long as needed",
  "Items are (name, class, age_days). Limits by class: logs 30, events 365, finance 2555. Return names to delete, sorted.",
  [(([("a", "logs", 31), ("b", "logs", 2), ("c", "events", 400), ("d", "finance", 400)],),  ['a', 'c'])],
  ("Ifs.", "O(n)", "O(m)"),
  ("A dictionary of limits.", "O(n)", "O(m)"))


@B
def to_delete(items):
    out = []
    for name, kind, age in items:
        if (kind == "logs" and age > 30) or (kind == "events" and age > 365) or (kind == "finance" and age > 2555):
            out.append(name)
    return sorted(out)


@O
def to_delete(items):
    limit = {"logs": 30, "events": 365, "finance": 2555}
    return sorted(n for n, k, a in items if a > limit[k])


Q(None, "Who Touched This Data?", "Easy", "Audit logs",
  "From (user, table, action) records, return users who read a sensitive table, sorted, and how many times.",
  [(([("a", "hr", "read"), ("a", "hr", "read"), ("b", "hr", "write"), ("c", "sales", "read")], "hr"),  {'a': 2})],
  ("A dictionary.", "O(n)", "O(u)"),
  ("<code>Counter</code>.", "O(n)", "O(u)"),
  names=["log", "table"])


@B
def who_read(log, table):
    out = {}
    for user, t, action in log:
        if t == table and action == "read":
            out[user] = out.get(user, 0) + 1
    return dict(sorted(out.items()))


@O
def who_read(log, table):
    return dict(sorted(Counter(u for u, t, a in log if t == table and a == "read").items()))


Q(None, "Rotate Old Keys", "Easy", "Secrets expire",
  "Return key names older than max_days as of today, sorted.",
  [(({"a": 10, "b": 95}, 100, 30),  ['a'])],
  ("A loop.", "O(k log k)", "O(k)"),
  ("A comprehension.", "O(k log k)", "O(k)"),
  names=["created", "today", "max_days"])


@B
def old_keys(created, today, max_days):
    out = []
    for name, day in created.items():
        if today - day > max_days:
            out.append(name)
    return sorted(out)


@O
def old_keys(created, today, max_days):
    return sorted(n for n, d in created.items() if today - d > max_days)


Q(None, "Spot vs On-Demand", "Medium", "Cheap but interruptible",
  "Spot saves a discount share but can be interrupted, adding a share of rework time. Return (on-demand cost, spot cost), rounded to 2 decimals, and the cheaper.",
  [((100, 0.7, 0.2),  (100, 36.0, 'spot')), ((100, 0.1, 0.5), (100, 135.0, 'on-demand'))],
  ("Step by step.", "O(1)", "O(1)"),
  ("Compact.", "O(1)", "O(1)"),
  names=["cost", "discount", "rework"])


@B
def spot_vs_ondemand(cost, discount, rework):
    spot = cost * (1 - discount) * (1 + rework)
    name = "spot" if spot < cost else "on-demand"
    return (round(cost, 2), round(spot, 2), name)


@O
def spot_vs_ondemand(cost, discount, rework):
    s = cost * (1 - discount) * (1 + rework)
    return (round(cost, 2), round(s, 2), "spot" if s < cost else "on-demand")


Q(None, "Athena or a Cluster?", "Medium", "Break-even",
  "With a made-up serverless price per TB scanned, and a cluster's hourly price, return monthly costs for t TB scanned and h cluster hours, rounded to 2 decimals, and the cheaper.",
  [((100, 5, 200, 4), (500, 800, 'serverless')), ((5000, 5, 200, 4), (25000, 800, 'cluster'))],
  ("Multiply and compare.", "O(1)", "O(1)"),
  ("Compact.", "O(1)", "O(1)"),
  names=["t", "price_tb", "h", "price_hour"])


@B
def serverless_or_cluster(t, price_tb, h, price_hour):
    a = t * price_tb
    b = h * price_hour
    if a < b:
        return (round(a, 2), round(b, 2), "serverless")
    return (round(a, 2), round(b, 2), "cluster")


@O
def serverless_or_cluster(t, price_tb, h, price_hour):
    a, b = t * price_tb, h * price_hour
    return (round(a, 2), round(b, 2), "serverless" if a < b else "cluster")


Q(None, "Data Transfer Costs", "Easy", "The hidden bill",
  "Given GB moved per route, and made-up prices (same AZ 0, cross-AZ 0.01, cross-region 0.02, internet 0.09), return the total rounded to 2 decimals, and the largest route.",
  [(({"cross-az": 1000, "internet": 500, "same-az": 9000},),  (55.0, 'internet'))],
  ("A loop.", "O(r)", "O(r)"),
  ("A dictionary comprehension.", "O(r)", "O(r)"))


@B
def transfer_cost(routes):
    prices = {"same-az": 0, "cross-az": 0.01, "cross-region": 0.02, "internet": 0.09}
    total, best, best_cost = 0.0, None, -1
    for route, gb in routes.items():
        cost = gb * prices[route]
        total += cost
        if cost > best_cost:
            best, best_cost = route, cost
    return (round(total, 2), best)


@O
def transfer_cost(routes):
    prices = {"same-az": 0, "cross-az": 0.01, "cross-region": 0.02, "internet": 0.09}
    costs = {r: g * prices[r] for r, g in routes.items()}
    return (round(sum(costs.values()), 2), max(costs, key=costs.get))


Q(None, "S3 Lifecycle Rule", "Easy", "Move and expire automatically",
  "Objects are (name, age). Rule: age ≥ 30 → 'infrequent', ≥ 90 → 'archive', ≥ 365 → 'delete', otherwise 'standard'. Return {name: action}.",
  [(([("a", 1), ("b", 30), ("c", 100), ("d", 400)],),  {'a': 'standard', 'b': 'infrequent', 'c': 'archive', 'd': 'delete'})],
  ("Ifs.", "O(n)", "O(n)"),
  ("A helper in a comprehension.", "O(n)", "O(n)"))


@B
def lifecycle(objects):
    out = {}
    for name, age in objects:
        if age >= 365:
            out[name] = "delete"
        elif age >= 90:
            out[name] = "archive"
        elif age >= 30:
            out[name] = "infrequent"
        else:
            out[name] = "standard"
    return out


@O
def lifecycle(objects):
    rule = lambda a: "delete" if a >= 365 else "archive" if a >= 90 else "infrequent" if a >= 30 else "standard"
    return {n: rule(a) for n, a in objects}


Q(None, "Multipart Upload", "Easy", "Large files in pieces",
  "Return the number of parts for a file with a part size, both in MB, and how many parts re-upload if one fails (1, as only that part is retried).",
  [((10000, 100), (100, 1)), ((250, 100), (3, 1))],
  ("Divide with a remainder check.", "O(1)", "O(1)"),
  ("<code>ceil</code>.", "O(1)", "O(1)"),
  names=["size", "part"])


@B
def multipart(size, part):
    n = size // part
    if size % part:
        n += 1
    return (n, 1)


@O
def multipart(size, part):
    return (math.ceil(size / part), 1)


Q(None, "Availability Math", "Medium", "What do the nines mean?",
  "Return allowed downtime minutes a year for a target, and the availability of services that all must work, rounded to 2 and 4 decimals.",
  [((0.999, [0.999, 0.999, 0.99]),  (525.6, 0.988))],
  ("Multiply step by step.", "O(n)", "O(1)"),
  ("<code>math.prod</code>.", "O(n)", "O(1)"),
  names=["target", "services"])


@B
def availability(target, services):
    minutes = 365 * 24 * 60 * (1 - target)
    chain = 1.0
    for s in services:
        chain *= s
    return (round(minutes, 2), round(chain, 4))


@O
def availability(target, services):
    return (round(525600 * (1 - target), 2), round(math.prod(services), 4))


Q(None, "Recovery Objectives", "Medium", "RPO and RTO",
  "With backups every b hours and restore taking r hours: worst-case data loss (RPO) is b and downtime (RTO) is r. Return whether both meet targets, and which fail.",
  [((4, 2, 6, 4), (True, [])), ((24, 8, 6, 4), (False, ['rpo', 'rto']))],
  ("Two ifs.", "O(1)", "O(1)"),
  ("A comprehension.", "O(1)", "O(1)"),
  names=["b", "r", "rpo", "rto"])


@B
def recovery(b, r, rpo, rto):
    failed = []
    if b > rpo:
        failed.append("rpo")
    if r > rto:
        failed.append("rto")
    return (not failed, failed)


@O
def recovery(b, r, rpo, rto):
    failed = [n for n, ok in (("rpo", b <= rpo), ("rto", r <= rto)) if not ok]
    return (not failed, failed)


Q(None, "Tag Everything", "Easy", "Find what has no owner",
  "Return resources missing any required tag, as {name: missing tags sorted}.",
  [(({"bucket": {"team": "x"}, "cluster": {"team": "y", "env": "prod"}}, ["team", "env"]),  {'bucket': ['env']})],
  ("Loops.", "O(r·t)", "O(r)"),
  ("Set differences.", "O(r·t)", "O(r)"),
  names=["resources", "required"])


@B
def missing_tags(resources, required):
    out = {}
    for name, tags in resources.items():
        missing = [t for t in required if t not in tags]
        if missing:
            out[name] = sorted(missing)
    return out


@O
def missing_tags(resources, required):
    need = set(required)
    return {n: sorted(need - t.keys()) for n, t in resources.items() if need - t.keys()}
