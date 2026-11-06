"""A complete small pipeline with no setup: raw files → clean → star schema → quality checks → publish.

    python labs/mini_pipeline.py

It uses only Python's standard library. Read it top to bottom, then try to break it.
It shows idempotent loads, a dead-letter table, deduplication, write-audit-publish and reruns.
"""
import csv
import io
import sqlite3

RAW = {
    "2026-01-05": "order_id,customer,amount,ts\n1,asha,100,2026-01-05T10:00\n2,ben,50,2026-01-05T11:00\n2,ben,50,2026-01-05T11:00\n3,asha,oops,2026-01-05T12:00\n",
    "2026-01-06": "order_id,customer,amount,ts\n4,chen,75,2026-01-06T09:00\n5,asha,25,2026-01-06T10:00\n",
}


def setup(db):
    db.executescript("""
    CREATE TABLE IF NOT EXISTS dead_letter (day TEXT, row TEXT, reason TEXT);
    CREATE TABLE IF NOT EXISTS dim_customer (customer_key INTEGER PRIMARY KEY, name TEXT UNIQUE);
    CREATE TABLE IF NOT EXISTS fact_orders (order_id INT, customer_key INT, amount REAL, day TEXT);
    CREATE TABLE IF NOT EXISTS mart_daily (day TEXT PRIMARY KEY, orders INT, revenue REAL);
    """)


def extract(day):
    return list(csv.DictReader(io.StringIO(RAW[day])))


def transform(rows, day):
    """Returns clean, deduplicated rows and the rejected ones."""
    good, bad, seen = [], [], set()
    for r in rows:
        try:
            amount = float(r["amount"])
        except ValueError:
            bad.append((day, str(r), "amount is not a number"))
            continue
        if r["order_id"] in seen:
            continue
        seen.add(r["order_id"])
        good.append((int(r["order_id"]), r["customer"].title(), amount))
    return good, bad


def audit(good, bad, raw_rows):
    """Quality checks that run before anything is published."""
    problems = []
    if not good:
        problems.append("no rows")
    if len(bad) / max(1, len(raw_rows)) > 0.5:
        problems.append("too many bad rows")
    if len({g[0] for g in good}) != len(good):
        problems.append("duplicate order_id")
    return problems


def load_day(db, day):
    """Idempotent: running a day twice gives the same result, in one transaction."""
    raw = extract(day)
    good, bad = transform(raw, day)
    problems = audit(good, bad, raw)
    if problems:
        raise ValueError(f"{day}: not published: {problems}")
    with db:   # commit together, or roll back together
        db.execute("DELETE FROM dead_letter WHERE day = ?", (day,))
        db.executemany("INSERT INTO dead_letter VALUES (?, ?, ?)", bad)
        db.execute("DELETE FROM fact_orders WHERE day = ?", (day,))
        for order_id, name, amount in good:
            db.execute("INSERT OR IGNORE INTO dim_customer (name) VALUES (?)", (name,))
            key = db.execute("SELECT customer_key FROM dim_customer WHERE name = ?", (name,)).fetchone()[0]
            db.execute("INSERT INTO fact_orders VALUES (?, ?, ?, ?)", (order_id, key, amount, day))
        db.execute("DELETE FROM mart_daily WHERE day = ?", (day,))
        db.execute("""INSERT INTO mart_daily
                      SELECT day, COUNT(*), SUM(amount) FROM fact_orders WHERE day = ? GROUP BY day""", (day,))
    print(f"{day}: loaded {len(good)}, rejected {len(bad)}")


def main():
    db = sqlite3.connect(":memory:")
    setup(db)
    for day in RAW:
        load_day(db, day)
    print("Mart:", db.execute("SELECT * FROM mart_daily ORDER BY day").fetchall())
    before = db.execute("SELECT * FROM mart_daily ORDER BY day").fetchall()

    load_day(db, "2026-01-05")          # a rerun must change nothing
    after = db.execute("SELECT * FROM mart_daily ORDER BY day").fetchall()
    print("Rerun changed nothing:", before == after)
    print("Dead letter:", db.execute("SELECT COUNT(*) FROM dead_letter").fetchone()[0], "row(s)")

    RAW["2026-01-07"] = "order_id,customer,amount,ts\n6,asha,x,t\n7,ben,y,t\n"
    try:
        load_day(db, "2026-01-07")
    except ValueError as e:
        print("Blocked bad data:", e)
    print("Users still see:", db.execute("SELECT day FROM mart_daily ORDER BY day").fetchall())


if __name__ == "__main__":
    main()
