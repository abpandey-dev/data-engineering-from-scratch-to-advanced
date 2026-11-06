"""Shared helpers for handbook topic files.

A topic file calls Q(...) once per question, then decorates a brute-force
function with @B and an optimal one with @O. Lines that start with `T(` are
trace calls: build.py runs the optimal solution once with tracing on, records a
frame per T() call, and strips those lines from the code shown on the site.
"""
import inspect
import math
import os
import sys
import textwrap

REG = {"topic": None, "questions": [], "demo": None, "lessons": [], "theory": [], "faq": []}
MAX_FRAMES = 90


# ---------- data structures used by list / tree problems ----------

class ListNode:
    def __init__(self, val=0, next=None):
        self.val, self.next = val, next


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val, self.left, self.right = val, left, right


def mk_list(vals, pos=-1):
    """Build a linked list; pos >= 0 links the tail back to that index (a cycle)."""
    dummy = cur = ListNode()
    nodes = []
    for v in vals:
        cur.next = ListNode(v)
        cur = cur.next
        nodes.append(cur)
    if pos >= 0 and nodes:
        nodes[-1].next = nodes[pos]
    return dummy.next


def list_arr(head):
    out, seen = [], set()
    while head and id(head) not in seen:
        seen.add(id(head))
        out.append(head.val)
        head = head.next
    return out


def mk_tree(vals):
    """Level-order list with None for gaps, LeetCode style."""
    if not vals or vals[0] is None:
        return None
    root = TreeNode(vals[0])
    queue, i = [root], 1
    while queue and i < len(vals):
        node = queue.pop(0)
        for side in ("left", "right"):
            if i < len(vals) and vals[i] is not None:
                child = TreeNode(vals[i])
                setattr(node, side, child)
                queue.append(child)
            i += 1
    return root


def tree_arr(root):
    out, queue = [], [root]
    while queue:
        node = queue.pop(0)
        if node:
            out.append(node.val)
            queue += [node.left, node.right]
        else:
            out.append(None)
    while out and out[-1] is None:
        out.pop()
    return out


def find(root, val):
    if not root or root.val == val:
        return root
    return find(root.left, val) or find(root.right, val)


# ---------- registration ----------

def TOPIC(**kw):
    REG["topic"] = kw


def Q(lc, title, diff, tags, statement, tests, brute, opt, **kw):
    """brute/opt are (idea, time, space). Optional kw: prep, post, norm, check,
    viz (args for the visual run), design (tests are (ctor_args, [(method, args)]))."""
    q = dict(lc=lc, title=title, diff=diff, tags=tags, statement=statement,
             tests=tests, brute_meta=brute, opt_meta=opt, **kw)
    REG["questions"].append(q)
    return q


def _code(fn):
    src = textwrap.dedent(inspect.getsource(fn)).rstrip("\n").split("\n")
    kept, raw_to_kept = [], {}
    indent = lambda l: len(l) - len(l.lstrip())
    for i, line in enumerate(src):
        s = line.strip()
        if s in ("@B", "@O", "@D", "@LD"):
            continue
        if s.startswith("T("):
            # Keep the block valid if the trace call was its only statement.
            nxt = next((l for l in src[i + 1:] if l.strip() and not l.strip().startswith("T(")), "")
            opens_block = kept and kept[-1].split("#")[0].rstrip().endswith(":") and indent(kept[-1]) < indent(line)
            if opens_block and (not nxt or indent(nxt) < indent(line)):
                raw_to_kept[i] = len(kept)
                kept.append(" " * indent(line) + "pass")
            continue
        raw_to_kept[i] = len(kept)
        kept.append(line)
    first = fn.__code__.co_firstlineno if hasattr(fn, "__code__") else inspect.getsourcelines(fn)[1]
    return "\n".join(kept), raw_to_kept, first, len(src)


def B(fn):
    REG["questions"][-1]["brute"] = fn
    return fn


def O(fn):
    REG["questions"][-1]["opt"] = fn
    return fn


def D(fn):
    """Topic concept demo: a small traced function shown with the theory."""
    REG["demo"] = fn
    return fn


def LESSON(level, title, body, practice=()):
    """One step of a topic's learning path. level: Basics, Core or Advanced.
    practice: LeetCode numbers of this topic's questions that use the idea."""
    REG["lessons"].append(dict(level=level, title=title, body=body, practice=list(practice), demo=None))


def LD(fn):
    """Animated example attached to the most recent LESSON."""
    REG["lessons"][-1]["demo"] = fn
    return fn


def THEORY(heading, body):
    """A textbook-style theory section for the topic's Theory tab."""
    REG["theory"].append({"h": heading, "body": body})


def FAQ(question, answer):
    """A conceptual interview question with its answer."""
    REG["faq"].append({"q": question, "a": answer})


# ---------- tracing ----------

class _Trace:
    on = False
    frames = []
    first = 0
    raw_to_kept = {}
    nraw = 0
    file = None


def start_trace(fn):
    code, raw_to_kept, first, nraw = _code(fn)
    _Trace.on, _Trace.frames = True, []
    _Trace.first, _Trace.raw_to_kept, _Trace.nraw = first, raw_to_kept, nraw
    _Trace.file = inspect.getsourcefile(fn)
    return code


def stop_trace():
    _Trace.on = False
    return _Trace.frames


def T(msg, *views, at="next"):
    if not _Trace.on or len(_Trace.frames) >= MAX_FRAMES:
        return
    f = sys._getframe(1)
    line = -1
    if f.f_code.co_filename == _Trace.file:
        raw = f.f_lineno - _Trace.first
        if 0 <= raw < _Trace.nraw:
            for step in ((1, -1) if at == "next" else (-1, 1)):
                r = raw
                while 0 <= r < _Trace.nraw and r not in _Trace.raw_to_kept:
                    r += step
                line = _Trace.raw_to_kept.get(r, -1)
                if line > 0:
                    break
    _Trace.frames.append({"m": msg, "l": line, "v": [v for v in views if v]})


# ---------- automatic line-by-line tracing (Python Tutor style) ----------

def _ds_view(name, v):
    """NumPy arrays and pandas objects as tables (only if those libraries are loaded)."""
    np = sys.modules.get("numpy")
    pd = sys.modules.get("pandas")
    if np is not None and isinstance(v, np.ndarray):
        label = f"{name}  (array {v.dtype}, shape {v.shape})"
        if v.ndim == 1:
            return {"k": "arr", "n": label, "v": [s(x) for x in v[:30].tolist()], "p": {}, "hl": [], "ok": [], "bad": []}
        if v.ndim == 2:
            return G(label, v[:10, :10].tolist())
        return {"k": "vars", "n": label, "v": [["values", _short(v.tolist())]]}
    if pd is not None and isinstance(v, pd.DataFrame):
        head = v.iloc[:8, :8]
        rows = [[s(x) for x in row] for row in head.itertuples(index=False)]
        more = f", showing {len(head)} of {len(v)} rows" if len(v) > 8 else ""
        return {"k": "grid", "n": f"{name}  (DataFrame {v.shape[0]}×{v.shape[1]}{more})", "v": rows, "hl": [], "ok": [], "bad": [],
                "rl": [s(i) for i in head.index], "cl": [str(c) for c in head.columns]}
    if pd is not None and isinstance(v, pd.Series):
        head = v.iloc[:20]
        return {"k": "arr", "n": f"{name}  (Series {v.dtype}{', ' + str(v.name) if v.name is not None else ''})", "v": [s(x) for x in head.tolist()],
                "p": {}, "hl": [], "ok": [], "bad": [], "il": [s(i) for i in head.index]}
    return None


def _user_object(v):
    mod = getattr(type(v), "__module__", "") or ""
    return mod.startswith(("topic_", "lessons_", "theory_", "__main__"))


def _value_views(name, v):
    ds = _ds_view(name, v)
    if ds is not None:
        return ds
    if isinstance(v, bool) or v is None or isinstance(v, (int, float, complex)):
        return None
    if isinstance(v, str):
        return None
    if isinstance(v, list):
        return A(name, v)
    if isinstance(v, tuple):
        return A(name + "  (tuple)", v)
    if isinstance(v, (set, frozenset)):
        return M(name + "  (set)", sorted(v, key=repr))
    if isinstance(v, dict):
        return M(name + "  (dict)", v)
    if isinstance(v, range):
        return None
    if hasattr(v, "__dict__") and not callable(v) and _user_object(v):
        return M(f"{name}  ({type(v).__name__} object)", {k: x for k, x in vars(v).items() if not k.startswith("_")})
    return None


def _short(v):
    np = sys.modules.get("numpy")
    if np is not None and isinstance(v, np.generic):
        v = v.item()
    r = repr(v)
    return r if len(r) <= 40 else r[:37] + "..."


def _frame_views(frame, stack, out):
    views = []
    if len(stack) > 1:
        views.append(S("call stack (newest on top)", stack, hl=[len(stack) - 1]))
    scalars, rich = {}, []
    for k, v in frame.f_locals.items():
        if k.startswith("_") or k == "self" and False:
            continue
        if inspect.ismodule(v) or inspect.isclass(v) or inspect.isfunction(v) or inspect.isbuiltin(v) or inspect.ismethod(v):
            continue
        view = _value_views(k, v)
        if view is None:
            scalars[k] = _short(v) if isinstance(v, (str, range)) or v is None or isinstance(v, (int, float, bool, complex)) else type(v).__name__
        else:
            rich.append(view)
    if scalars:
        views.append({"k": "vars", "n": "variables", "v": [[k, x] for k, x in scalars.items()]})
    views += rich
    text = out.getvalue()
    if text:
        views.append({"k": "out", "n": "printed output", "v": text.rstrip("\n").split("\n")})
    return views


def auto_trace(fn, call, limit=MAX_FRAMES):
    """Run call() and record a frame before every line of fn's source (and on returns and errors)."""
    import contextlib
    import io
    code, raw_to_kept, first, nraw = _code(fn)
    lines = code.split("\n")
    file = inspect.getsourcefile(fn)
    frames, out = [], io.StringIO()

    def ours(f):
        return f.f_code.co_filename == file and 0 <= f.f_lineno - first < nraw

    def stack_of(f):
        names = []
        while f is not None and ours(f):
            co = f.f_code
            args = ", ".join(f"{a}={_short(f.f_locals.get(a))}" for a in co.co_varnames[:co.co_argcount] if a != "self")
            names.append(f"{co.co_name}({args})")
            f = f.f_back
        return names[::-1]

    def record(f, msg):
        if len(frames) >= limit:
            return
        kept = raw_to_kept.get(f.f_lineno - first, -1)
        frames.append({"m": msg.replace("{line}", lines[kept].strip() if kept >= 0 else "").replace("{num}", str(kept + 1)), "l": kept,
                       "v": _frame_views(f, stack_of(f), out)})

    def local(f, event, arg):
        if not ours(f):
            return local
        if event == "line":
            record(f, "Line {num}: {line}")
        elif event == "return":
            if f.f_code.co_name not in ("<genexpr>", "<listcomp>", "<dictcomp>", "<setcomp>", "<lambda>"):
                record(f, f"{f.f_code.co_name}() returns {_short(arg)}")
        elif event == "exception":
            record(f, f"{arg[0].__name__} raised: {arg[1]}")
        return local

    def glob(f, event, arg):
        return local if ours(f) else None

    close_figures()
    with contextlib.redirect_stdout(out):
        sys.settrace(glob)
        try:
            result = call()
        finally:
            sys.settrace(None)
    charts = capture_figures()
    if charts and frames:
        frames[-1]["v"] = frames[-1]["v"] + charts
    if len(frames) >= limit:
        frames[-1]["m"] += f"  (animation stops after {limit} steps)"
    return code, frames, result


def uses_T(fn):
    return any(l.strip().startswith("T(") for l in inspect.getsource(fn).split("\n"))


# ---------- view builders (each returns a JSON-ready dict) ----------

def s(x):
    """Short display string for a cell value."""
    if x is None:
        return "None"
    if isinstance(x, bool):
        return "T" if x else "F"
    if isinstance(x, float):
        if math.isinf(x):
            return "∞" if x > 0 else "-∞"
        return f"{x:.4g}"
    if isinstance(x, str):
        return x
    if isinstance(x, (list, tuple)):
        return "[" + ",".join(s(y) for y in x) + "]"
    if isinstance(x, ListNode):
        return f"node({x.val})"
    if isinstance(x, TreeNode):
        return f"node({x.val})"
    np = sys.modules.get("numpy")
    if np is not None and isinstance(x, np.generic):
        return s(x.item())
    return str(x)


def _idx(xs):
    if xs is None:
        return []
    if isinstance(xs, (int,)):
        return [xs]
    return [i for i in xs if i is not None]


def A(name, arr, /, hl=(), ok=(), bad=(), **ptrs):
    """Array / string row. ptrs: label=index (None hides the pointer)."""
    return {"k": "arr", "n": name, "v": [s(x) for x in arr],
            "p": {k: v for k, v in ptrs.items() if isinstance(v, int) and not isinstance(v, bool)},
            "hl": _idx(hl), "ok": _idx(ok), "bad": _idx(bad)}


def V(**kw):
    return {"k": "vars", "v": [[k, s(v)] for k, v in kw.items()]}


def M(name, d, hl=None):
    if isinstance(d, dict):
        items = [[s(k), s(v)] for k, v in d.items()]
    else:
        items = [[s(k), None] for k in d]
    return {"k": "map", "n": name, "v": items, "hl": None if hl is None else s(hl)}


def S(name, st, hl=()):
    return {"k": "stack", "n": name, "v": [s(x) for x in st], "hl": _idx(hl)}


def G(name, grid, hl=(), ok=(), bad=(), rl=None, cl=None):
    cells = lambda xs: [[r, c] for r, c in (xs or [])]
    return {"k": "grid", "n": name, "v": [[s(x) for x in row] for row in grid],
            "hl": cells(hl), "ok": cells(ok), "bad": cells(bad),
            "rl": None if rl is None else [s(x) for x in rl],
            "cl": None if cl is None else [s(x) for x in cl]}


def L(name, head, /, hl=(), **ptrs):
    nodes, index, cur = [], {}, head
    while cur and id(cur) not in index and len(nodes) < 30:
        index[id(cur)] = len(nodes)
        nodes.append(cur)
        cur = cur.next
    cyc = index.get(id(cur), -1) if cur else -1
    p = {}
    for k, node in ptrs.items():
        if node is not None and id(node) in index:
            p[k] = index[id(node)]
    hl_ids = [index[id(n)] for n in (hl or []) if n is not None and id(n) in index]
    return {"k": "list", "n": name, "v": [s(n.val) for n in nodes], "p": p, "cyc": cyc, "hl": hl_ids}


def TR(name, root, /, hl=(), ok=(), **ptrs):
    nodes, index = [], {}

    def walk(n):
        if not n or id(n) in index:
            return
        index[id(n)] = len(nodes)
        nodes.append(n)
        walk(n.left)
        walk(n.right)

    walk(root)

    def ids(xs):
        out = []
        for x in xs or []:
            if isinstance(x, TreeNode):
                if id(x) in index:
                    out.append(index[id(x)])
            else:
                out += [i for i, n in enumerate(nodes) if n.val == x]
        return out

    return {"k": "tree", "n": name,
            "v": [[s(n.val), index.get(id(n.left), -1) if n.left else -1,
                   index.get(id(n.right), -1) if n.right else -1] for n in nodes],
            "hl": ids(hl), "ok": ids(ok),
            "p": {k: index[id(n)] for k, n in ptrs.items() if n is not None and id(n) in index}}


def GR(name, nodes, edges, hl=(), ok=(), he=(), directed=False):
    """Graph. nodes: count or list of labels; edges: (u, v) or (u, v, w)."""
    labels = list(range(nodes)) if isinstance(nodes, int) else list(nodes)
    pos = {lab: i for i, lab in enumerate(labels)}
    es = []
    for e in edges:
        es.append([pos[e[0]], pos[e[1]], s(e[2]) if len(e) > 2 else None])
    hes = {(pos[a], pos[b]) for a, b, *_ in (he or [])}
    return {"k": "graph", "n": name, "v": [s(x) for x in labels], "e": es, "d": directed,
            "hl": [pos[x] for x in hl or [] if x in pos], "ok": [pos[x] for x in ok or [] if x in pos],
            "he": [list(x) for x in hes]}


def H(name, heap, hl=()):
    """A binary heap (list) drawn as the complete tree it represents. hl: heap indices."""
    nodes = [TreeNode(s(v)) for v in heap]
    for i, n in enumerate(nodes):
        if 2 * i + 1 < len(nodes):
            n.left = nodes[2 * i + 1]
        if 2 * i + 2 < len(nodes):
            n.right = nodes[2 * i + 2]
    view = TR(name, nodes[0] if nodes else None, hl=[nodes[i] for i in _idx(hl) if 0 <= i < len(nodes)])
    return view


def BITS(name, x, width=8, hl=(), ok=()):
    """Binary digits of x, most significant bit on the left. hl/ok are bit positions (0 = lowest bit)."""
    shown = x & ((1 << width) - 1)
    bits = [(shown >> (width - 1 - i)) & 1 for i in range(width)]
    pos = lambda ps: [width - 1 - p for p in _idx(ps) if 0 <= p < width]
    return {"k": "arr", "n": f"{name} = {x}", "v": [str(b) for b in bits], "p": {},
            "hl": pos(hl), "ok": pos(ok), "bad": [], "il": [str(width - 1 - i) for i in range(width)]}


def TRIE(name, root, hl=(), ok=()):
    """A trie drawn as a tree. Nodes are dicts (end marker "$") or objects with .children and .end/.word."""
    nodes, index = [], {}

    def kids(n):
        if isinstance(n, dict):
            return [(k, v) for k, v in n.items() if isinstance(v, dict)], "$" in n
        return list(n.children.items()), bool(getattr(n, "end", False) or getattr(n, "word", None))

    def walk(n, label):
        if len(nodes) >= 60:
            return -1
        i = len(nodes)
        index[id(n)] = i
        ch, end = kids(n)
        nodes.append([label, [], end])
        for k, c in sorted(ch, key=lambda kv: str(kv[0])):
            j = walk(c, s(k))
            if j >= 0:
                nodes[i][1].append(j)
        return i

    if root is not None:
        walk(root, "")
    ids = lambda xs: [index[id(n)] for n in xs or [] if id(n) in index]
    return {"k": "ntree", "n": name, "v": nodes, "hl": ids(hl), "ok": ids(ok)}


# ---------- data science helpers ----------

os.environ.setdefault("MPLBACKEND", "Agg")


def close_figures():
    plt = sys.modules.get("matplotlib.pyplot")
    if plt is not None:
        plt.close("all")


def capture_figures(dpi=64):
    """Every open matplotlib figure as an image view (base64 PNG), then close them."""
    plt = sys.modules.get("matplotlib.pyplot")
    if plt is None:
        return []
    import base64
    import io as _io
    views = []
    for num in plt.get_fignums():
        fig = plt.figure(num)
        buf = _io.BytesIO()
        fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
        views.append({"k": "img", "n": "chart", "src": "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()})
    plt.close("all")
    return views


def plain(x, digits=4):
    """Turn NumPy / pandas / matplotlib results into plain Python values for comparison and display."""
    np = sys.modules.get("numpy")
    pd = sys.modules.get("pandas")
    if pd is not None:
        if isinstance(x, pd.DataFrame):
            return {str(c): plain(x[c].tolist(), digits) for c in x.columns}
        if isinstance(x, pd.Series):
            return {plain(k, digits): plain(v, digits) for k, v in x.items()}
        if isinstance(x, pd.Index):
            return plain(x.tolist(), digits)
        if x is pd.NaT:
            return None
        if isinstance(x, pd.Timestamp):
            return str(x.date()) if x == x.normalize() else str(x)
    if np is not None:
        if isinstance(x, np.ndarray):
            return plain(x.tolist(), digits)
        if isinstance(x, np.generic):
            return plain(x.item(), digits)
    if isinstance(x, float):
        return None if x != x else round(x, digits) + 0.0
    if isinstance(x, list):
        return [plain(v, digits) for v in x]
    if isinstance(x, tuple):
        return tuple(plain(v, digits) for v in x)
    if isinstance(x, dict):
        return {plain(k, digits): plain(v, digits) for k, v in x.items()}
    if isinstance(x, (set, frozenset)):
        return {plain(v, digits) for v in x}
    return x


__all__ = ["ListNode", "TreeNode", "mk_list", "list_arr", "mk_tree", "tree_arr", "find",
           "TOPIC", "Q", "B", "O", "D", "LESSON", "LD", "THEORY", "FAQ", "T", "A", "V", "M", "S", "G", "L", "TR", "GR", "H", "BITS", "TRIE", "math", "auto_trace", "plain"]
