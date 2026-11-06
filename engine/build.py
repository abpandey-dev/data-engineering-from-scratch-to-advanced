"""Run every solution against its tests, record the animations, and write a
site's data (data/*.js) and README.md. A site ("book") is a folder with
book.json, index.html and src/{topics,lessons,theory}/.

    python3 engine/build.py --book course          # everything
    python3 engine/build.py --book course spark    # only topics whose file name contains "spark"
"""
import ast
import copy
import hashlib
import importlib.util
import inspect
import json
import re
import textwrap
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
import lib  # noqa: E402

BOOK = ROOT          # set by main() from --book
CONF = {}
DATA = ROOT / "data"


def slug(t):
    return re.sub(r"[^a-z0-9]+", "-", t.lower().replace("'", "")).strip("-")


def run(q, fn, args):
    if "runner" in q:
        return q["runner"](fn, copy.deepcopy(args))
    if q.get("design"):
        ctor, ops = copy.deepcopy(args)
        obj = fn(*ctor)
        return [getattr(obj, m)(*a) for m, a in ops]
    if hasattr(fn, "__globals__"):
        fn.__globals__[fn.__name__] = fn  # recursive calls by name hit this version
    a = copy.deepcopy(args)
    if "prep" in q:
        a = q["prep"](a)
    res = fn(*a)
    if "inplace" in q:
        res = a[q["inplace"]]
    if "post" in q:
        res = q["post"](res)
    return res


def _result_text(q, args, kind="opt"):
    try:
        res = run(q, q[kind], args)
        lib.close_figures()
        out = repr(lib.plain(res) if CONF.get("plain") and "check" not in q else res)
    except Exception:  # noqa: BLE001
        return "(see above)"
    return out if len(out) <= 160 else out[:157] + "..."


def passes(q, args, want, got):
    if "check" in q:
        return q["check"](copy.deepcopy(args), got)
    norm = q.get("norm", lib.plain if CONF.get("plain") else (lambda x: x))
    return norm(copy.deepcopy(got)) == norm(copy.deepcopy(want))


def fmt_args(q, args):
    if q.get("design"):
        ctor, ops = args
        calls = [f"{type_name(q)}({', '.join(map(repr, ctor))})"]
        calls += [f"{m}({', '.join(map(repr, a))})" for m, a in ops]
        return " → ".join(calls)
    names = q.get("names") or list(inspect.signature(q["opt"]).parameters)
    return ", ".join(f"{n} = {v!r}" for n, v in zip(names, args))


def type_name(q):
    return q["opt"].__name__


def load(path):
    lib.REG.update(topic=None, questions=[], demo=None, lessons=[], theory=[], faq=[])
    for kind, file in (("topic", path), ("lessons", BOOK / "src" / "lessons" / path.name), ("theory", BOOK / "src" / "theory" / path.name)):
        if not file.exists():
            continue
        spec = importlib.util.spec_from_file_location(f"{kind}_{path.stem}", file)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod  # inspect needs this to find class sources
        spec.loader.exec_module(mod)
    return dict(lib.REG)


def trace(fn, call):
    """Frames from T() calls if the code has them, otherwise an automatic line-by-line trace."""
    if lib.uses_T(fn):
        code = lib.start_trace(fn)
        try:
            call()
        finally:
            frames = lib.stop_trace()
        return code, frames
    code, frames, _ = lib.auto_trace(fn, call)
    return code, frames


def _plain(html_text):
    import html
    return html.unescape(re.sub(r"<[^>]+>", "", html_text))


def _literal(value):
    """repr(value) if it evaluates back to an equal value, else None."""
    text = repr(value)
    try:
        return text if eval(text, {"inf": float("inf")}) == value else None  # noqa: S307
    except Exception:  # noqa: BLE001
        return None


def ide_payload(q):
    """Starter code, example usage and checkable tests for the in-browser IDE."""
    fn = q["opt"]
    name = fn.__name__
    doc = "\n".join("    " + line for line in textwrap.wrap(_plain(q["statement"]), 76))
    tests, usage = [], None
    if q.get("design"):
        ctor, ops = q["tests"][0][0]
        lines = [f"class {name}:", "    " + chr(34) * 3, doc, "    " + chr(34) * 3, ""]
        lines += [f"    def __init__{inspect.signature(fn.__init__)}:", "        pass", ""]
        for m in dict.fromkeys(m for m, _ in ops):
            lines += [f"    def {m}{inspect.signature(getattr(fn, m))}:", "        pass", ""]
        stub = "\n".join(lines)
        usage = [f"obj = {name}({', '.join(map(repr, ctor))})"] + [f"print(obj.{m}({', '.join(map(repr, a))}))" for m, a in ops]
        for (c, o), want in q["tests"]:
            parts = (_literal(tuple(c)), _literal([list(x) for x in o]), _literal(want))
            if all(parts):
                tests.append({"ctor": parts[0], "ops": parts[1], "want": parts[2]})
    else:
        sig = inspect.signature(fn)
        stub = f"def {name}{sig}:\n    {chr(34) * 3}\n{doc}\n    {chr(34) * 3}\n    # Write your code here\n    pass\n"
        simple = not any(k in q for k in ("prep", "post", "norm", "check", "runner", "inplace")) or (
            set(k for k in ("prep", "post", "norm", "check", "runner", "inplace") if k in q) == {"post"} and inspect.isgeneratorfunction(fn))
        gen = inspect.isgeneratorfunction(fn)
        args = q.get("viz", q["tests"][0][0])
        if "runner" not in q and "prep" not in q:
            call = f"{name}({', '.join(map(repr, args))})"
            if "inplace" in q:
                usage = [f"args = {args!r}", f"{name}(*args)", f"print(args[{q['inplace']}])"]
            else:
                usage = [f"print(list({call}))" if gen else f"print({call})"]
        if simple:
            for a, want in q["tests"]:
                ar, wr = _literal(tuple(a)), _literal(want)
                if ar and wr:
                    tests.append({"args": ar, "want": wr})
    return {"name": name, "stub": stub, "usage": "\n".join(usage) if usage else None,
            "tests": tests, "listify": bool(not q.get("design") and inspect.isgeneratorfunction(fn)),
            "design": bool(q.get("design")), "plain": bool(CONF.get("plain"))}


def _defined_names(tree):
    names = set()
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names |= {(a.asname or a.name).split(".")[0] for a in node.names}
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            for t in node.targets if isinstance(node, ast.Assign) else [node.target]:
                names |= {n.id for n in ast.walk(t) if isinstance(n, ast.Name)}
        elif isinstance(node, (ast.FunctionDef, ast.ClassDef)) and not node.decorator_list:
            names.add(node.name)
    return names


def setup_for(fn):
    """Module-level imports, data and helpers that fn uses, so its code also runs on its own in the IDE."""
    fn = inspect.unwrap(fn)
    shown = ast.parse(textwrap.dedent(lib._code(fn)[0]))  # the code users see: trace-only names don't count
    tree = ast.parse(Path(inspect.getsourcefile(fn)).read_text())
    src = Path(inspect.getsourcefile(fn)).read_text().split("\n")
    have = _defined_names(ast.parse(CONF.get("prelude", "")))
    stmts = {}
    for node in tree.body:
        defines = _defined_names(ast.Module(body=[node], type_ignores=[]))
        for name in defines - have:
            stmts.setdefault(name, node)
    wanted, todo = {}, {n.id for n in ast.walk(shown) if isinstance(n, ast.Name)}
    while todo:
        name = todo.pop()
        node = stmts.get(name)
        if node is None or id(node) in wanted:
            continue
        wanted[id(node)] = node
        todo |= {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}
    if not wanted:
        return ""
    parts = ["\n".join(src[n.lineno - 1:n.end_lineno]) for n in sorted(wanted.values(), key=lambda n: n.lineno)]
    return "\n".join(parts) + "\n\n\n"


def build_topic(path, failures):
    reg = load(path)
    meta = reg["topic"]
    out = {"id": meta["id"], "theory": meta["theory"], "qs": {}}
    if reg["demo"]:
        code, frames = trace(reg["demo"], reg["demo"])
        out["demo"] = {"code": code, "frames": frames, "title": meta.get("demo_title", "")}
    out["sections"], out["faq"] = reg["theory"], reg["faq"]
    out["prelude"] = CONF.get("prelude", "")
    by_lc = {q["lc"]: slug(q["title"]) for q in reg["questions"]}
    out["lessons"] = []
    levels = {"Basics": 0, "Core": 1, "Advanced": 2}
    for k, les in enumerate(sorted(reg["lessons"], key=lambda l: levels.get(l["level"], 3)), 1):
        item = {"level": les["level"], "title": les["title"], "body": les["body"], "practice": []}
        qids = {slug(q["title"]) for q in reg["questions"]}
        for ref in les["practice"]:
            qid = slug(ref) if isinstance(ref, str) else by_lc.get(ref)
            if qid in qids:
                item["practice"].append(qid)
            else:
                failures.append(f"{meta['id']} lesson {k}: practice {ref!r} is not a question in this topic")
        if les["demo"]:
            code, frames = lib._code(les["demo"])[0], []
            try:
                code, frames = trace(les["demo"], les["demo"])
            except Exception as e:  # noqa: BLE001
                failures.append(f"{meta['id']} lesson {k} demo: {type(e).__name__}: {e}")
            item["demo"] = {"code": code, "frames": frames, "call": les["demo"].__name__ + "()", "setup": setup_for(les["demo"])}
            if not item["demo"]["frames"]:
                failures.append(f"{meta['id']} lesson {k} demo recorded no frames")
        out["lessons"].append(item)
    index = []
    seen = set()
    for n, q in enumerate(reg["questions"], 1):
        qid = slug(q["title"])
        assert qid not in seen, qid
        seen.add(qid)
        where = f"{meta['id']}/{qid}"
        if "brute" not in q or "opt" not in q:
            failures.append(f"{where}: missing @B or @O")
            continue
        times = {}
        for kind in ("brute", "opt"):
            t0 = time.perf_counter()
            for args, want in q["tests"]:
                try:
                    got = run(q, q[kind], args)
                    ok = passes(q, args, want, got)
                except Exception as e:  # noqa: BLE001
                    got, ok = f"{type(e).__name__}: {e}", False
                lib.close_figures()
                if not ok:
                    failures.append(f"{where} [{kind}] args={args!r} want={want!r} got={got!r}")
            times[kind] = time.perf_counter() - t0
        viz_args = q.get("viz", q["tests"][0][0])
        traced = {}
        for kind in ("opt", "brute") if CONF.get("trace_brute") else ("opt",):
            code, frames = lib._code(q[kind])[0], []
            try:
                code, frames = trace(q[kind], lambda: run(q, q[kind], viz_args))
            except Exception as e:  # noqa: BLE001
                failures.append(f"{where} [{kind} trace] {type(e).__name__}: {e}")
            if frames:
                frames.append({"m": f"Result: {_result_text(q, viz_args, kind)}", "l": -1, "v": frames[-1]["v"]})
            else:
                failures.append(f"{where}: {kind} solution recorded no frames")
            traced[kind] = (code, frames)
        opt_code, frames = traced["opt"]
        (bi, bt, bs), (oi, ot, os_) = q["brute_meta"], q["opt_meta"]
        out["qs"][qid] = {
            "statement": q["statement"],
            "examples": [[fmt_args(q, a), repr(w)] for a, w in q["tests"][:3]],
            "vizIn": fmt_args(q, viz_args),
            "brute": {"idea": bi, "tc": bt, "sc": bs, "code": traced["brute"][0] if "brute" in traced else lib._code(q["brute"])[0], "setup": setup_for(q["brute"]),
                      **({"frames": traced["brute"][1]} if "brute" in traced else {})},
            "opt": {"idea": oi, "tc": ot, "sc": os_, "code": opt_code, "frames": frames, "setup": setup_for(q["opt"])},
            "tests": len(q["tests"]),
            "ide": ide_payload(q),
        }
        index.append({"id": qid, "n": n, "lc": q["lc"], "title": q["title"], "diff": q["diff"], "tags": q["tags"]})
    topic_index = {k: meta[k] for k in ("id", "title", "blurb", "glyph")}
    topic_index["lessons"] = len(out["lessons"])
    topic_index["faq"] = len(out["faq"])
    topic_index["qs"] = index
    return out, topic_index


def readme(topics):
    total = sum(len(t["qs"]) for t in topics)
    url = CONF["url"]
    has_lc = any(isinstance(q["lc"], int) for t in topics for q in t["qs"])
    counts = (f"{len(topics)} topics · theory with {sum(t['faq'] for t in topics)} theory questions · "
              f"{sum(t['lessons'] for t in topics)} lessons from basics to advanced · {total} {CONF['unit']}")
    lines = [f"# {CONF['title']}", "", counts + " · " + CONF["summary"], "", f"**Live site:** {url}", "",
             "Every solution is run against its test cases by `build.py` before the site is generated, and each animation is recorded from a real run of the code you see.",
             "", "## Topics", ""]
    for t in topics:
        lines.append(f"- [{t['title']}](#{slug(t['title'])}) — {t['blurb']}")
    for t in topics:
        head = "| # | Question | LeetCode | Level | Pattern |" if has_lc else "| # | Question | Level | Concept |"
        lines += ["", f"## {t['title']}", "", head, "|---|---|---|---|---|" if has_lc else "|---|---|---|---|"]
        for q in t["qs"]:
            link = f"{url}#/q/{t['id']}/{q['id']}"
            if has_lc:
                lc = f"[{q['lc']}](https://leetcode.com/problems/{slug(q['title'])}/)" if isinstance(q["lc"], int) else str(q["lc"])
                lines.append(f"| {q['n']} | [{q['title']}]({link}) | {lc} | {q['diff']} | {q['tags']} |")
            else:
                lines.append(f"| {q['n']} | [{q['title']}]({link}) | {q['diff']} | {q['tags']} |")
    rel = BOOK.relative_to(ROOT.parent)
    lines += ["", "## Build", "", "```bash", f"python3 handbook/build.py{'' if BOOK == ROOT else ' --book ' + str(rel)}", "```", "",
              f"Sources live in `{rel}/src/`: `topics/` (questions and solutions), `lessons/` and `theory/`.", ""]
    return "\n".join(lines)


def stamp_assets():
    """Add ?v=<content hash> to local script and style links so browsers never serve stale files."""
    for page in (BOOK / "index.html", ROOT.parent / "ide" / "index.html", ROOT.parent / "ide" / "sql.html"):
        if not page.exists():
            continue
        html = page.read_text()

        def stamp(m, base=page.parent):
            name = m.group(2)
            v = hashlib.sha1((base / name).read_bytes()).hexdigest()[:10]
            return f'{m.group(1)}="{name}?v={v}"'
        html = re.sub(r'(src|href)="((?!https?:)[^"?#]+\.(?:js|css))(?:\?v=\w+)?"', stamp, html)
        page.write_text(html)


def main():
    global BOOK, DATA, CONF
    args = sys.argv[1:]
    if "--book" in args:
        i = args.index("--book")
        BOOK = (ROOT.parent / args[i + 1]).resolve()
        del args[i:i + 2]
    DATA = BOOK / "data"
    CONF = json.loads((BOOK / "book.json").read_text())
    only = args[0] if args else None
    DATA.mkdir(exist_ok=True)
    failures, topics = [], []
    for path in sorted((BOOK / "src" / "topics").glob("*.py")):
        if only and only not in path.stem:
            continue
        data, idx = build_topic(path, failures)
        topics.append(idx)
        js = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        (DATA / f"{data['id']}.js").write_text(f"(window.DSA_TOPIC=window.DSA_TOPIC||{{}})[{json.dumps(data['id'])}]={js};\n")
        frames = sum(len(q["opt"]["frames"]) for q in data["qs"].values())
        print(f"{idx['title']:<28} {len(idx['qs']):>3} questions  {frames:>5} frames")
    if not only:
        version = hashlib.sha1(b"".join(f.read_bytes() for f in sorted(DATA.glob("*.js")) if f.name != "index.js")).hexdigest()[:10]
        (DATA / "index.js").write_text(f"window.DSA_VERSION={json.dumps(version)};window.DSA_INDEX=" + json.dumps(topics, ensure_ascii=False, separators=(",", ":")) + ";\n")
        (BOOK / "README.md").write_text(readme(topics))
        stamp_assets()
    if failures:
        print(f"\n{len(failures)} FAILURES")
        for f in failures:
            print("  " + f[:400])
        sys.exit(1)
    print("\nAll tests passed.")


if __name__ == "__main__":
    main()
