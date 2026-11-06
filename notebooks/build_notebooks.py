"""Turn every course into teacher-style Jupyter notebooks, from the tested site data.

    python3 notebooks/build_notebooks.py            # all courses
    python3 notebooks/build_notebooks.py rag        # only topics whose id contains "rag"

Run `python3 engine/build.py --book course` first so that data/*.js is current.
"""
import ast
import html
import json
import re
import sys
import textwrap
from html.parser import HTMLParser
from pathlib import Path

import nbformat as nbf

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from teacher_notes import NOTES  # noqa: E402

REPO = "abpandey-dev/data-engineering-from-scratch-to-advanced"
SITE = "https://abpandey-dev.github.io/data-engineering-from-scratch-to-advanced"
COURSES = [("course", "topics", "Data Engineering from Scratch to Advanced")]


# ---------- HTML to Markdown ----------

def esc_text(t, table=False):
    t = t.replace("\\", "\\\\")
    for ch in "*_$`":
        t = t.replace(ch, "\\" + ch)
    t = t.replace("<", "&lt;").replace(">", "&gt;")
    t = re.sub(r"(?m)^(\s*)#", r"\1\\#", t)
    return t.replace("|", "\\|") if table else t


class Md(HTMLParser):
    def __init__(self, table=False):
        super().__init__(convert_charrefs=True)
        self.out, self.lists, self.pre, self.code, self.table = [], [], False, False, table
        self.href, self.pic = None, False

    def w(self, s):
        self.out.append(s)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if self.pre:
            return
        if tag == "pre":
            self.pre = True
            self.w("\n\n```python\n")
        elif tag == "code":
            self.code = True
            self.w("`")
        elif tag in ("b", "strong"):
            self.w("**")
        elif tag in ("i", "em"):
            self.w("*")
        elif tag == "s":
            self.w("~~")
        elif tag == "p":
            self.w("\n\n")
        elif tag in ("h3", "h4", "h5"):
            self.w("\n\n" + {"h3": "### ", "h4": "#### ", "h5": "##### "}[tag])
        elif tag in ("ul", "ol"):
            self.lists.append([tag, 0])
            self.w("\n\n" if len(self.lists) == 1 else "\n")
        elif tag == "li":
            kind = self.lists[-1] if self.lists else ["ul", 0]
            kind[1] += 1
            pad = "   " * (len(self.lists) - 1)
            self.w("\n" + pad + (f"{kind[1]}. " if kind[0] == "ol" else "- "))
        elif tag == "br":
            self.w("  \n")
        elif tag == "sup":
            self.w("^")
        elif tag == "sub":
            self.w("~")
        elif tag == "a":
            self.href = a.get("href")
            self.w("[")
        elif tag == "div":
            cls = a.get("class", "")
            if cls == "pic":
                self.pic = self.pre = True
                self.w("\n\n```text\n")
                return
            self.w({"warn": "\n\n**⚠️ Watch out:** ", "tip": "\n\n**💡 Tip:** ", "pro": "\n\n**👍 Pros**\n", "con": "\n\n**👎 Cons**\n"}.get(cls, "\n\n"))

    def handle_endtag(self, tag):
        if tag == "div" and self.pic:
            self.pic = self.pre = False
            self.w("\n```\n\n")
        elif tag == "pre":
            self.pre = False
            self.w("\n```\n\n")
        elif self.pre:
            return
        elif tag == "code":
            self.code = False
            self.w("`")
        elif tag in ("b", "strong"):
            self.w("**")
        elif tag in ("i", "em"):
            self.w("*")
        elif tag == "s":
            self.w("~~")
        elif tag in ("p", "h3", "h4", "h5", "div"):
            self.w("\n\n")
        elif tag in ("ul", "ol"):
            self.lists.pop()
            self.w("\n\n" if not self.lists else "")
        elif tag == "a":
            href = self.href or ""
            self.w(f"]({SITE}/{href.lstrip('./')})")

    def handle_data(self, d):
        if self.pre:
            self.w(d)
        elif self.code:
            self.w(d.replace("`", "'").replace("|", "\\|") if self.table else d.replace("`", "'"))
        else:
            self.w(esc_text(re.sub(r"\s+", " ", d), self.table))


def inline(fragment, table=False):
    m = Md(table)
    m.feed(fragment)
    m.close()
    return "".join(m.out)


def table_md(raw):
    if re.search(r"(rowspan|colspan)=", raw) or "<pre" in raw:
        return "\n\n" + re.sub(r"\s*\n\s*", " ", raw) + "\n\n"
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", raw, re.S)
    grid = []
    for r in rows:
        grid.append([inline(c, True).strip().replace("\n", " ") or " " for _, c in re.findall(r"<(t[dh])[^>]*>(.*?)</t[dh]>", r, re.S)])
    if not grid:
        return ""
    width = max(map(len, grid))
    grid = [g + [" "] * (width - len(g)) for g in grid]
    has_head = "<th" in rows[0]
    head = grid[0] if has_head else [" "] * width
    body = grid[1:] if has_head else grid
    lines = ["| " + " | ".join(head) + " |", "|" + " --- |" * width] + ["| " + " | ".join(g) + " |" for g in body]
    return "\n\n" + "\n".join(lines) + "\n\n"


def md(fragment):
    parts = re.split(r"(<table.*?</table>)", fragment or "", flags=re.S)
    text = "".join(table_md(p) if p.startswith("<table") else inline(p) for p in parts)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return re.sub(r"[ \t]+\n", "\n", text)


# ---------- source details the site's data doesn't carry ----------

def plain_text(fragment):
    return html.unescape(re.sub(r"<[^>]+>", "", fragment or "")).strip()


class TopicSource:
    """Reads a topic file's Q(...) calls, for tests that need prep/post/check helpers."""
    def __init__(self, path):
        self.src = path.read_text()
        self.tree = ast.parse(self.src)
        self.calls = {}
        for node in self.tree.body:
            call = node.value if isinstance(node, (ast.Expr, ast.Assign)) else None
            if isinstance(call, ast.Call) and getattr(call.func, "id", "") == "Q" and len(call.args) >= 6:
                try:
                    title = ast.literal_eval(call.args[1])
                except ValueError:
                    continue
                self.calls[title] = call
        self.defs = {}
        for node in self.tree.body:
            names = set()
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and not node.decorator_list:
                names.add(node.name)
            elif isinstance(node, ast.Assign):
                names |= {n.id for t in node.targets for n in ast.walk(t) if isinstance(n, ast.Name)}
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                if getattr(node, "module", "") != "lib":
                    names |= {(a.asname or a.name).split(".")[0] for a in node.names}
            for n in names:
                self.defs.setdefault(n, node)

    def seg(self, node):
        return ast.get_source_segment(self.src, node)

    def needs(self, snippets, already=""):
        wanted, todo = {}, set()
        for s in snippets:
            todo |= {n.id for n in ast.walk(ast.parse(s)) if isinstance(n, ast.Name)}
        while todo:
            name = todo.pop()
            node = self.defs.get(name)
            if node is None or id(node) in wanted:
                continue
            wanted[id(node)] = node
            todo |= {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}
        parts = [self.seg(n) for n in sorted(wanted.values(), key=lambda n: n.lineno)]
        parts = [p for p in parts if p not in already]
        return "\n".join(parts) + "\n\n" if parts else ""

    def check_call(self, title, name):
        """Source of a check(...) call for a question with custom test logic, or (None, '')."""
        call = self.calls.get(title)
        if call is None:
            return None, []
        kws = {k.arg: self.seg(k.value) for k in call.keywords if k.arg in ("prep", "post", "norm", "check", "runner", "inplace", "design")}
        tests = self.seg(call.args[5])
        extra = ", ".join(f"{'verify' if k == 'check' else k}={v}" for k, v in kws.items())
        return f"check({name}, {tests}{', ' + extra if extra else ''})", [tests] + [v for k, v in kws.items()]


# ---------- the notebook's first cell ----------

RUNNER = (ROOT / "ide" / "runner.py").read_text()
LIB = (ROOT / "engine" / "src" / "lib.py").read_text()


def pull(src, *names):
    tree = ast.parse(src)
    found = {n.name: ast.get_source_segment(src, n) for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
    return "\n\n".join(found[n] for n in names)


STRUCTURES = pull(RUNNER, "ListNode", "TreeNode", "mk_list", "list_arr", "mk_tree") + "\n\n" + pull(LIB, "tree_arr", "find") + """

ListNode.__repr__ = lambda self: f"ListNode{list_arr(self)}"
TreeNode.__repr__ = lambda self: f"TreeNode{tree_arr(self)}"
"""

CHECKER = pull(RUNNER, "plain") + '''


def check(fn, tests, plain_compare=None, listify=False, design=False, prep=None, post=None,
          norm=None, verify=None, runner=None, inplace=None):
    """Run your code against the tests and show which pass."""
    use_plain = PLAIN if plain_compare is None else plain_compare
    passed, problems = 0, []
    for args, want in tests:
        try:
            a = copy.deepcopy(args)
            if design:
                obj = fn(*a[0])
                got = [getattr(obj, m)(*p) for m, p in a[1]]
            elif runner is not None:
                got = runner(fn, a)
            else:
                if prep is not None:
                    a = prep(a)
                with contextlib.redirect_stdout(io.StringIO()):
                    got = fn(*a)
                if inplace is not None:
                    got = a[inplace]
                if listify:
                    got = list(got)
                if post is not None:
                    got = post(got)
            if verify is not None:
                ok = bool(verify(copy.deepcopy(args), got))
            elif norm is not None:
                ok = norm(copy.deepcopy(got)) == norm(copy.deepcopy(want))
            else:
                ok = (plain(got), plain(want)) if use_plain else (got, want)
                ok = ok[0] == ok[1]
            ok = ok if isinstance(ok, bool) else False
        except Exception as e:  # your code raised an error: report it, don't stop the notebook
            ok, got = False, f"{type(e).__name__}: {e}"
        passed += ok
        if not ok:
            problems.append((args, want, got))
    plt.close("all")
    if passed == len(tests):
        print(f"✅ All {len(tests)} tests passed. Well done! Now compare with the answers below.")
    else:
        print(f"❌ {passed}/{len(tests)} tests passed. First one to fix:")
        args, want, got = problems[0]
        print("   input:   ", repr(args)[:300])
        print("   expected:", repr(want)[:300])
        print("   you got: ", repr(got)[:300])
    return None
'''


def setup_cell(conf):
    prelude = conf.get("prelude", "")
    parts = ["# ▶ Run this cell first. It prepares the notebook; you don't need to read it.",
             "import contextlib, copy, io, math, sys",
             "import numpy as np, matplotlib.pyplot as plt",
             "%matplotlib inline", prelude.strip(), f"PLAIN = {bool(conf.get('plain'))}", "", STRUCTURES, CHECKER,
             'print("Ready! Scroll down and start learning.")']
    return "\n".join(p for p in parts)


# ---------- the notebook ----------

DIFF_ORDER = {"Easy": 0, "Medium": 1, "Hard": 2}
LEVEL = {"Easy": "🟢 Warm-up", "Medium": "🟡 Interview standard", "Hard": "🔴 Stretch"}


def details(summary, body):
    return f"<details>\n<summary><b>{summary}</b></summary>\n\n{body}\n\n</details>\n"


def code_block(code):
    return f"```python\n{code.rstrip()}\n```"


def good_steps(frames):
    msgs = [f.get("m", "") for f in frames or []]
    msgs = [m for m in msgs if m and not re.match(r"(Line \d+|Result:|Start|Enter |Back in)", m)]
    return msgs if len(msgs) >= 3 and sum(":" in m or " " in m for m in msgs) else []


SHARED_HELPERS = {"run_sql"}   # tools a student is meant to use, rather than part of an answer


def split_setup(setup):
    """(data and imports a student needs, helper functions that belong in the answer)."""
    if not setup.strip():
        return "", ""
    tree = ast.parse(setup)
    defs = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))]
    keep = [n for n in tree.body if n not in defs]
    needed = {x.id for n in keep for x in ast.walk(n) if isinstance(x, ast.Name)} | SHARED_HELPERS
    changed = True
    while changed:
        changed = False
        for n in list(defs):
            if n.name in needed:
                defs.remove(n)
                keep.append(n)
                needed |= {x.id for x in ast.walk(n) if isinstance(x, ast.Name)}
                changed = True
    seg = lambda nodes: "\n\n".join(ast.get_source_segment(setup, n) for n in sorted(nodes, key=lambda n: n.lineno))
    return (seg(keep) + "\n\n" if keep else ""), (seg(defs) + "\n\n\n" if defs else "")


def answer_code(q, kind, before):
    """The answer as shown: any helper functions it uses, then the code itself."""
    _, helpers = split_setup(q[kind].get("setup", ""))
    if helpers:
        tree = ast.parse(helpers)
        helpers = "\n\n".join(ast.get_source_segment(helpers, n) for n in tree.body if ast.get_source_segment(helpers, n) not in before)
        helpers = helpers + "\n\n\n" if helpers else ""
    return helpers + q[kind]["code"]


def question_code(topic_src, q_meta, q):
    """(code placed before the student's function, check call) for one question."""
    ide = q["ide"]
    name = ide["name"]
    setup = split_setup(q["opt"].get("setup", ""))[0] + split_setup(q["brute"].get("setup", ""))[0]
    if ide["tests"]:
        if ide["design"]:
            tests = "[\n    " + ",\n    ".join(f"(({t['ctor']}, {t['ops']}), {t['want']})" for t in ide["tests"]) + ",\n]"
            return setup, f"check({name}, {tests}, design=True)"
        tests = "[\n    " + ",\n    ".join(f"({t['args']}, {t['want']})" for t in ide["tests"]) + ",\n]"
        extra = ", listify=True" if ide["listify"] else ""
        return setup, f"check({name}, {tests}{extra})"
    call, snippets = topic_src.check_call(q_meta["title"], name)
    if call:
        return setup + topic_src.needs(snippets, setup), call
    return setup, None


def statements(code):
    """Top-level statements of a block of code, as text, with the names each one defines."""
    tree = ast.parse(code)
    out = []
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.ClassDef)):
            names = {n.name}
        elif isinstance(n, ast.Assign):
            names = {x.id for t in n.targets for x in ast.walk(t) if isinstance(x, ast.Name)}
        else:
            names = {(a.asname or a.name) for a in getattr(n, "names", [])}
        out.append((ast.get_source_segment(code, n), names))
    return out


def shared_setup(blocks):
    """Statements used by several questions, to run once. Returns (their code, the same statements as a set)."""
    count, order, defs = {}, [], {}
    for block in blocks:
        for text, names in dict.fromkeys((t, frozenset(n)) for t, n in statements(block)):
            if text not in count:
                order.append(text)
            count[text] = count.get(text, 0) + 1
            for name in names:
                defs.setdefault(name, set()).add(text)
    clash = {t for texts in defs.values() if len(texts) > 1 for t in texts}
    keep = [t for t in order if count[t] >= 2 and t not in clash]
    return "\n\n".join(keep) + "\n" if keep else "", set(keep)


def without(code, shared):
    kept = [t for t, _ in statements(code) if t not in shared]
    return "\n\n".join(dict.fromkeys(kept)) + "\n\n" if kept else ""


def build_topic(book, folder, title, conf, labels, number, total, t, d):
    notes = NOTES[book].get(t["id"])
    if notes is None:
        raise SystemExit(f"Missing teacher note: {book}/{t['id']}")
    picture, tested = notes
    nb = nbf.v4.new_notebook()
    nb.metadata.update(kernelspec={"name": "python3", "display_name": "Python 3", "language": "python"},
                       language_info={"name": "python"}, colab={"provenance": []})
    cells = nb.cells
    M = lambda s: cells.append(nbf.v4.new_markdown_cell(s))
    C = lambda s, **meta: cells.append(nbf.v4.new_code_cell(s, metadata=meta))
    file = f"{number:02d}_{t['id']}.ipynb"
    colab = f"https://colab.research.google.com/github/{REPO}/blob/main/notebooks/{folder}/{file}"
    qs = sorted(t["qs"], key=lambda q: DIFF_ORDER.get(q["diff"], 1))
    qnum = {q["id"]: i for i, q in enumerate(qs, 1)}
    lessons = d["lessons"]

    M(f"[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)]({colab})\n\n"
      f"*{title} · Notebook {number} of {total}*\n\n# {t['title']}\n\n{esc_text(plain_text(t['blurb']))}\n\n"
      f"### 👩‍🏫 From your teacher\n\n**The picture to keep in your head:** {picture}\n\n"
      f"**What interviewers really test here:** {tested}\n\n"
      "### How to use this notebook\n\n"
      "1. **Run the setup cell** just below.\n2. **Read each lesson slowly.** Work the numbers on paper before reading on.\n"
      "3. **Run and then change the examples.** Breaking code on purpose is how you learn.\n"
      "4. **Try each practice question before opening an answer.** If you're stuck, open one hint at a time.\n"
      "5. **Say your interview answers out loud.** Knowing something and explaining it are different skills.\n\n"
      "### Your roadmap\n\n" + "\n".join(f"- [ ] {i}. {esc_text(plain_text(l['title']))} *({l['level']})*" for i, l in enumerate(lessons, 1))
      + f"\n- [ ] {len(qs)} practice questions\n- [ ] Interview questions, out loud")
    C(setup_cell(conf), jupyter={"source_hidden": True}, cellView="form", tags=["setup"])

    if d.get("sections"):
        M("---\n# Part 1: The theory in one place\n\nRead this once for the big picture. It's fine if it doesn't all stick yet: the lessons will make it concrete, and you can come back to revise.")
        for s in d["sections"]:
            M(f"### {esc_text(plain_text(s['h']))}\n\n{md(s['body'])}")
    M("---\n# Part 2: Lessons, step by step")
    for i, l in enumerate(lessons, 1):
        body = f"## Lesson {i}: {esc_text(plain_text(l['title']))}\n\n*Level: {l['level']}*\n\n{md(l['body'])}"
        M(body)
        demo = l.get("demo")
        if demo:
            M("**▶ See it run.** Before you run this, predict what will happen. Then change a number and run it again.")
            C((demo.get("setup", "") + demo["code"].rstrip() + "\n\n\n" + demo["call"]).strip(), tags=["demo"])
            steps = good_steps(demo.get("frames"))
            if steps:
                shown = steps[:25]
                M(details("🔎 What happens, step by step", "\n".join(f"{n}. {esc_text(m)}" for n, m in enumerate(shown, 1))
                          + ("\n\n*…and so on.*" if len(steps) > 25 else "")))
        practice = [p for p in l.get("practice", []) if p in qnum]
        if practice:
            links = ", ".join(f"[Q{qnum[p]}](#q{qnum[p]})" for p in practice)
            M(f"**✏️ Your turn:** you now have what you need for {links}. Try one now, or carry on and do them in Part 3.")

    src_file = next((ROOT / book / "src" / "topics").glob(f"{number:02d}_*.py"))
    topic_src = TopicSource(src_file)
    M(f"---\n# Part 3: Practice like an interview\n\nThere are {len(qs)} questions here, easiest first.\n\n"
      "**Work the way you would in a real interview:** restate the problem, try an example by hand, say the simple approach and its cost, improve it, then write the code. "
      "Test it with the cell. Only open an answer once you've made a real attempt, because struggling is where the learning happens.")
    shared_code, shared = shared_setup([question_code(topic_src, qm, d["qs"][qm["id"]])[0] for qm in qs])
    if shared_code:
        M("**▶ Run this cell before the questions.** It sets up the data and tools they share.")
        C(shared_code, tags=["shared"])
    for k, qm in enumerate(qs, 1):
        q = d["qs"][qm["id"]]
        watch = f"{SITE}/{book}/#/q/{t['id']}/{qm['id']}"
        ex = "\n".join(f"- `{e[0]}` → `{e[1]}`" for e in q["examples"]) if q["examples"] else ""
        M(f'<a id="q{k}"></a>\n### Q{k}. {esc_text(plain_text(qm["title"]))}\n\n{LEVEL.get(qm["diff"], qm["diff"])} · *{esc_text(plain_text(qm["tags"]))}*\n\n{md(q["statement"])}'
          + (f"\n\n**Examples**\n\n{ex}" if ex else ""))
        before, call = question_code(topic_src, qm, q)
        stub = q["ide"]["stub"].rstrip()
        code = without(before, shared) + stub + "\n\n\n"
        if call:
            code += "# ▶ Run this cell to test your answer\n" + call
        elif q["ide"].get("usage"):
            code += "# ▶ Run this cell and compare with the examples above\n" + q["ide"]["usage"]
        else:
            code = code.rstrip() + "\n\n# ▶ Call your function here and compare with the examples above\n"
        C(code, tags=["practice"], question=qm["id"])
        brute, opt = q["brute"], q["opt"]
        same = answer_code(q, "brute", before).strip() == answer_code(q, "opt", before).strip()
        hints = details("💡 Hint 1: a way in", md(brute["idea"]))
        if not same and plain_text(opt["idea"]) != plain_text(brute["idea"]):
            hints += "\n" + details("💡 Hint 2: the better idea", md(opt["idea"]))
        answer = (f"**Idea:** {md(brute['idea'])}\n\n{code_block(answer_code(q, 'brute', before))}\n\n**Cost:** {esc_text(brute['tc'])} time, {esc_text(brute['sc'])} space")
        answers = details(f"✅ Answer: {labels[0]}", answer)
        if not same:
            answers += "\n" + details(f"✅ Answer: {labels[1]}", f"**Idea:** {md(opt['idea'])}\n\n{code_block(answer_code(q, 'opt', before))}\n\n**Cost:** {esc_text(opt['tc'])} time, {esc_text(opt['sc'])} space")
        say = (f"\"My first thought is: {md(brute['idea'])} That costs {esc_text(brute['tc'])} time and {esc_text(brute['sc'])} space.\""
               + (f"\n\n\"I can do better: {md(opt['idea'])} That's {esc_text(opt['tc'])} time and {esc_text(opt['sc'])} space.\"" if not same else ""))
        answers += "\n" + details("🎤 How to explain it out loud", say)
        steps = good_steps(opt.get("frames"))
        if steps:
            answers += "\n" + details("🔎 Walk through an example", f"Input: `{q.get('vizIn', '')}`\n\n" + "\n".join(f"{n}. {esc_text(m)}" for n, m in enumerate(steps[:15], 1)) + ("\n\n*…and so on.*" if len(steps) > 15 else ""))
        M(hints + "\n" + answers + f"\n[▶ Watch both answers run line by line]({watch})")

    if d.get("faq"):
        M("---\n# Part 4: Interview questions, out loud\n\nCover the answer, **say yours out loud**, then open it and compare. Aim for two or three clear sentences, then an example.")
        M("\n".join(details(f"{n}. {esc_text(plain_text(f['q']))}", md(f["a"])) for n, f in enumerate(d["faq"], 1)))
    hard = [f"[Q{qnum[q['id']]}](#q{qnum[q['id']]}) {esc_text(plain_text(q['title']))}" for q in qs if q["diff"] != "Easy"][-5:]
    M("---\n# Check yourself before moving on\n\nYou're ready for the next notebook when you can tick these **without looking**:\n\n"
      + "\n".join(f"- [ ] I can explain: {esc_text(plain_text(l['title']))}" for l in lessons)
      + "\n\n**Revision drill.** Come back in a few days, set a 25-minute timer per question, and solve these from a blank cell:\n\n"
      + "\n".join(f"- [ ] {h}" for h in hard)
      + "\n\nSpaced repetition beats re-reading: redoing a question after you've partly forgotten it is what makes it stick.")
    return file, nb


def load_book(book):
    index = (ROOT / book / "data" / "index.js").read_text()
    topics = json.loads(re.search(r"=\s*(\[.*\])\s*;?\s*$", index, re.S).group(1))
    conf = json.loads((ROOT / book / "book.json").read_text())
    page = (ROOT / book / "index.html").read_text()
    m1, m2 = re.search(r'bruteLabel:\s*"([^"]+)"', page), re.search(r'optLabel:\s*"([^"]+)"', page)
    labels = (m1.group(1) if m1 else "brute force", m2.group(1) if m2 else "optimal")
    return topics, conf, labels


def load_topic(book, tid):
    raw = (ROOT / book / "data" / f"{tid}.js").read_text()
    return json.loads(raw[raw.index("]=") + 2:].rstrip().rstrip(";"))


def colab(path):
    return f"https://colab.research.google.com/github/{REPO}/blob/main/notebooks/{path}"


def write_index():
    lines = ["# Notebooks: learn it, practise it, explain it", "",
             "The whole course as Jupyter notebooks, written the way a teacher would explain it. **[Start here](00_START_HERE.ipynb)** "
             f"([open in Colab]({colab('00_START_HERE.ipynb')})).", "",
             "Each topic notebook has the same shape:", "",
             "1. **From your teacher:** a picture to remember, and what interviewers really test.",
             "2. **Theory** in one place, for revision.",
             "3. **Lessons** with worked numbers and code you can change.",
             "4. **20 practice questions**, easiest first, with a cell that checks your answer, hints, two hidden answers and how to explain it out loud.",
             "5. **Interview questions** to answer aloud, then a checklist and a revision drill.", "",
             "No installation is needed: open any notebook in Colab and run the first cell. Or run them locally with `pip install notebook numpy pandas matplotlib`.", ""]
    totals = [0, 0, 0]
    for book, folder, title in COURSES:
        topics, _, _ = load_book(book)
        q = sum(len(t["qs"]) for t in topics)
        l = sum(t["lessons"] for t in topics)
        totals = [totals[0] + len(topics), totals[1] + l, totals[2] + q]
        lines += ["## Topics, in order", "", "| # | Topic | Lessons | Questions | Open |", "|---|---|---|---|---|"]
        for n, t in enumerate(topics, 1):
            f = f"{folder}/{n:02d}_{t['id']}.ipynb"
            lines.append(f"| {n} | [{t['title']}]({f}) | {t['lessons']} | {len(t['qs'])} | [Colab]({colab(f)}) |")
        lines.append("")
    lines[1:1] = ["", f"**{totals[0]} notebooks · {totals[1]} lessons · {totals[2]} practice questions.**"]
    (HERE / "README.md").write_text("\n".join(lines))
    return totals


def write_start_here():
    from start_here import CELLS
    nb = nbf.v4.new_notebook()
    nb.metadata.update(kernelspec={"name": "python3", "display_name": "Python 3", "language": "python"}, language_info={"name": "python"}, colab={"provenance": []})
    badge = f"[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)]({colab('00_START_HERE.ipynb')})\n\n"
    for i, (kind, text) in enumerate(CELLS):
        if kind == "md":
            nb.cells.append(nbf.v4.new_markdown_cell((badge if i == 0 else "") + text))
        else:
            nb.cells.append(nbf.v4.new_code_cell(text))
    nbf.write(nb, HERE / "00_START_HERE.ipynb")


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    made = 0
    if not only:
        write_start_here()
    for book, folder, title in COURSES:
        if not (ROOT / book / "data" / "index.js").exists():
            continue
        topics, conf, labels = load_book(book)
        out = HERE / folder
        out.mkdir(exist_ok=True)
        for number, t in enumerate(topics, 1):
            if only and only not in t["id"]:
                continue
            file, nb = build_topic(book, folder, title, conf, labels, number, len(topics), t, load_topic(book, t["id"]))
            nbf.write(nb, out / file)
            made += 1
    if not only:
        print("totals (notebooks, lessons, questions):", write_index())
    print("notebooks written:", made)


if __name__ == "__main__":
    main()
