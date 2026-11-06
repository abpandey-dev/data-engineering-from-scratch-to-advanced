"""Check the notebooks: every hidden answer must pass its self-check cell, and every notebook must run top to bottom.

    python3 notebooks/verify_notebooks.py answers      # run all answers through the notebook's own checker
    python3 notebooks/verify_notebooks.py run [filter] # execute notebooks, saving chart output in them
"""
import contextlib
import io
import json
import re
import sys
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import nbformat as nbf

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_notebooks as B  # noqa: E402


def answers_for(job):
    book, folder, number, tid = job
    import matplotlib
    matplotlib.use("Agg")
    topics, conf, _ = B.load_book(book)
    t = next(x for x in topics if x["id"] == tid)
    d = B.load_topic(book, tid)
    src = B.TopicSource(next((B.ROOT / book / "src" / "topics").glob(f"{number:02d}_*.py")))
    setup = B.setup_cell(conf).replace("%matplotlib inline", "")
    base = {"__name__": "__main__"}
    with contextlib.redirect_stdout(io.StringIO()):
        exec(setup, base)
    res = dict(total=0, ok=0, nocheck=[], fails=[], where=f"{book}/{tid}")
    for qm in t["qs"]:
        q = d["qs"][qm["id"]]
        before, call = B.question_code(src, qm, q)
        if call is None:
            res["nocheck"].append(qm["title"])
            continue
        for kind in ("brute", "opt"):
            res["total"] += 1
            g = dict(base)
            buf = io.StringIO()
            try:
                with contextlib.redirect_stdout(buf):
                    exec(before + B.answer_code(q, kind, before) + "\n\n" + call, g)
                if "✅" in buf.getvalue():
                    res["ok"] += 1
                else:
                    res["fails"].append((qm["title"], kind, buf.getvalue()[-400:]))
            except BaseException:
                res["fails"].append((qm["title"], kind, traceback.format_exc()[-400:]))
    return res


def run_answers():
    jobs = []
    for book, folder, _ in B.COURSES:
        if (B.ROOT / book / "data" / "index.js").exists():
            topics, _, _ = B.load_book(book)
            jobs += [(book, folder, n, t["id"]) for n, t in enumerate(topics, 1)]
    tot = ok = 0
    nocheck, fails = [], []
    with ProcessPoolExecutor(6) as ex:
        for f in as_completed([ex.submit(answers_for, j) for j in jobs]):
            r = f.result()
            tot += r["total"]
            ok += r["ok"]
            nocheck += [r["where"] + ": " + x for x in r["nocheck"]]
            fails += [(r["where"],) + tuple(x) for x in r["fails"]]
    print(f"answers checked: {ok}/{tot} passed; questions without an automatic check: {len(nocheck)}")
    print("\n".join(nocheck[:40]))
    for x in fails[:25]:
        print("FAIL", x[0], "|", x[1], "|", x[2], "\n   ", x[3].replace("\n", "\n    "))
    print("failures:", len(fails))
    return not fails


def run_one(path):
    from nbclient import NotebookClient
    nb = nbf.read(path, as_version=4)
    client = NotebookClient(nb, timeout=240, kernel_name="python3", allow_errors=True, cwd=str(HERE))
    client.execute()
    errors = []
    for c in nb.cells:
        if c.cell_type != "code":
            continue
        for o in c.outputs:
            if o.output_type == "error":
                errors.append((c.metadata.get("tags"), c.metadata.get("question"), o.ename, o.evalue[:200], c.source[:80]))
        if "practice" in c.metadata.get("tags", []):
            c.outputs = []     # the student's cells start clean
            c.execution_count = None
    nbf.write(nb, path)
    return str(path), errors, path.stat().st_size


def run_notebooks(flt):
    paths = sorted(p for p in list(HERE.glob("topics/*.ipynb")) + list(HERE.glob("*.ipynb")) if not flt or flt in str(p))
    bad = total = size = 0
    with ProcessPoolExecutor(6) as ex:
        for f in as_completed([ex.submit(run_one, p) for p in paths]):
            path, errors, s = f.result()
            total += 1
            size += s
            for e in errors:
                bad += 1
                print("ERROR", Path(path).name, e)
    print(f"notebooks executed: {total}; cell errors: {bad}; total size {size / 1e6:.1f} MB")
    return not bad


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "answers"
    done = run_answers() if mode == "answers" else run_notebooks(sys.argv[2] if len(sys.argv) > 2 else None)
    sys.exit(0 if done else 1)
