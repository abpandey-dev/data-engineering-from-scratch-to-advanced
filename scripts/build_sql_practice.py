"""Build ide/sql-data.js and ide/sql-index.js from the tested SQL questions in the course.

Only questions whose efficient answer is one run_sql(...) call become practice questions,
because those are a single query a student can write and have checked.
"""
import ast
import html
import json
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOPICS = [
    ("03_sql_foundations.py", "sql-foundations", "shop", "Shop", "Users, products and orders"),
    ("04_sql_advanced.py", "sql-advanced", "analytics", "Analytics", "Events, sales, logins, retention and a category tree"),
    ("06_data_modeling.py", "data-modeling", "star", "Star schema", "A fact table with dimensions, including SCD 2"),
    ("18_warehouses_dbt.py", "warehouses-dbt", "raw", "Raw orders", "A raw table to clean with staging models"),
]


# Extra rows used only for checking, so that an answer must really follow the question's rules.
# They avoid ties in sorted columns, so any correct query gives the same order.
HIDDEN = {
    "shop": """
INSERT INTO users VALUES (6,'Fay','Agra','2026-03-05'), (7,'Gus',NULL,'2026-03-06');
INSERT INTO products VALUES (14,'Clip','office',1), (15,'Ink','office',1.5), (16,'Rice','food',1);
INSERT INTO orders VALUES (8,6,15,2,'2026-01-07','paid'), (9,5,13,1,'2026-02-02','refunded'), (10,6,10,1,'2026-03-03','paid');
""",
    "analytics": """
INSERT INTO events VALUES (4,10,'home'), (4,20,'cart'), (2,4100,'buy');
INSERT INTO sales VALUES (7,'E','e','2026-01-01',70), (8,'N','a','2026-01-04',150), (9,'S','d','2026-01-05',5);
INSERT INTO customer_updates VALUES (6,4,'d@x',1), (7,3,'c2@x',9);
INSERT INTO logins VALUES (4,10), (4,11), (2,3);
INSERT INTO tree VALUES (6,3,'lamp');
INSERT INTO signups VALUES (6,2);
INSERT INTO activity VALUES (6,2), (6,3);
INSERT INTO seats VALUES (9,0), (10,1);
""",
    "star": """
INSERT INTO dim_product VALUES (4,'Mug','home');
INSERT INTO dim_customer VALUES (4,300,'Agra','2026-01-01','9999-12-31');
INSERT INTO fact_orders VALUES (5,300,4,'2026-02-01',1,30), (6,200,3,'2026-03-03',1,2);
""",
    "raw": """
INSERT INTO raw_orders VALUES (5,'d1','paid',3), (6,'d4','failed',9), (5,'d1','paid',3);
""",
}


def strip(fragment):
    return html.unescape(re.sub(r"<[^>]+>", "", fragment or "")).strip()


def run_script(schema, sql):
    con = sqlite3.connect(":memory:")
    con.executescript(schema)
    *setup, last = [s for s in sql.split(";") if s.strip()]
    for s in setup:
        con.execute(s)
    cur = con.execute(last)
    cols = [d[0] for d in cur.description]
    rows = [list(r) for r in cur.fetchall()]
    con.close()
    return cols, rows


ORDER_WORDS = re.compile(r"\b(order(ed)? by|sorted|first|in order|by day|in month order|by id|by order id)\b", re.I)


def is_ordered(sql, statement):
    """Row order is only checked when the query sorts and the question asks for an order."""
    tail = sql[sql.rfind(")") + 1:] if ")" in sql else sql
    return "ORDER BY" in tail.upper() and bool(ORDER_WORDS.search(statement))


def main():
    databases, questions, skipped = [], [], []
    for file, topic, db_id, db_name, db_desc in TOPICS:
        source = (ROOT / "course" / "src" / "topics" / file).read_text()
        tree = ast.parse(source)
        schema = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "SCHEMA")
        databases.append({"id": db_id, "name": db_name, "description": db_desc, "schema": schema.strip(), "hidden": HIDDEN[db_id].strip()})
        raw = (ROOT / "course" / "data" / f"{topic}.js").read_text()
        data = json.loads(raw[raw.index("]=") + 2:].rstrip().rstrip(";"))
        index = (ROOT / "course" / "data" / "index.js").read_text()
        meta = next(t for t in json.loads(re.search(r"DSA_INDEX=(\[.*\]);", index, re.S).group(1)) if t["id"] == topic)
        for qm in meta["qs"]:
            q = data["qs"][qm["id"]]
            code = ast.parse(q["opt"]["code"])
            calls = [n for n in ast.walk(code) if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "run_sql"]
            if len(calls) != 1 or not isinstance(calls[0].args[0], ast.Constant):
                skipped.append(qm["title"])
                continue
            sql = "\n".join(line.strip() if i == 0 else line.rstrip() for i, line in enumerate(calls[0].args[0].value.strip().split("\n")))
            sql = re.sub(r"(?m)^ {8}", "", sql)
            cols, rows = run_script(schema, sql)
            _, hidden_rows = run_script(schema + HIDDEN[db_id], sql)
            questions.append({"id": f"{topic}/{qm['id']}", "topic": meta["title"], "title": qm["title"], "diff": qm["diff"],
                              "tags": strip(qm["tags"]), "statement": strip(q["statement"]), "hint": strip(q["opt"]["idea"]),
                              "db": db_id, "solution": sql, "columns": cols, "rows": rows, "hiddenRows": hidden_rows, "ordered": is_ordered(sql, strip(q["statement"]))})
    (ROOT / "ide" / "sql-data.js").write_text("window.SQL_DATA=" + json.dumps({"databases": databases, "questions": questions}, ensure_ascii=False, separators=(",", ":")) + ";\n")
    (ROOT / "ide" / "sql-index.js").write_text("window.SQL_QUESTIONS=" + json.dumps([q["id"] for q in questions]) + ";\n")
    print(f"databases: {len(databases)}, practice questions: {len(questions)}")
    print("not single-query, left out:", skipped)


if __name__ == "__main__":
    main()
