"""Runs learner code inside Pyodide for the in-browser IDE.

execute(code, stdin, trace) runs a program, optionally recording a frame before
every line (the same frame format as the handbook's step player).
check_code(code, stdin, payload) runs the program, then calls the learner's
function or class on a question's tests. Both return JSON strings.
"""
import builtins
import contextlib
import copy
import inspect
import io
import json
import os
import sys
import traceback
import warnings

os.environ.setdefault("MPLBACKEND", "AGG")  # draw charts off-screen; we send them back as PNGs
warnings.filterwarnings("ignore", message=r"(?s).*pyarrow", category=DeprecationWarning)  # pandas 2.2 notice, not the learner's concern

MAX_STEPS = 400
INTERNAL = ("<genexpr>", "<listcomp>", "<dictcomp>", "<setcomp>", "<lambda>")

HINTS = {
    "NameError": "A name is used before it was created, or it's misspelled. Python is case-sensitive.",
    "TypeError": "An operation got the wrong type, e.g. adding a str and an int. Convert with int(), str() …",
    "ValueError": "The type is right but the value isn't, e.g. int('abc').",
    "IndexError": "A list or string index is past the end. Valid indices are 0 … len − 1.",
    "KeyError": "That key isn't in the dictionary. Use d.get(key) or check with `in` first.",
    "ZeroDivisionError": "Division by zero.",
    "AttributeError": "That object has no attribute or method with this name. Check the spelling and the type.",
    "IndentationError": "Indentation is wrong. Blocks after a colon must be indented by the same amount (4 spaces).",
    "SyntaxError": "This line isn't valid Python. Look for a missing colon, bracket or quote.",
    "RecursionError": "Too many nested calls — is the base case missing or never reached?",
    "EOFError": "input() needs more lines. Type them in the Input box, one line per input() call.",
    "UnboundLocalError": "A variable is used inside a function before it's assigned there.",
}


# ---------- Python Tutor style views ----------

def _short(v, limit=40):
    if type(v).__module__ == "numpy" and getattr(v, "shape", None) == ():
        v = v.item()
    r = repr(v)
    return r if len(r) <= limit else r[:limit - 3] + "..."


def _cell(v):
    if type(v).__module__ == "numpy" and getattr(v, "shape", None) == ():
        v = v.item()
    if isinstance(v, float):
        if v != v or v in (float("inf"), float("-inf")):
            return repr(v)  # JSON has no NaN / inf
        return v if v == int(v) or abs(v) >= 1e6 else round(v, 4)
    if isinstance(v, str) and len(v) == 1:
        return v
    return _short(v, 16)


def _ds_view(name, v):
    """NumPy arrays and pandas objects as tables (only when the program imported them)."""
    np = sys.modules.get("numpy")
    pd = sys.modules.get("pandas")
    if np is not None and isinstance(v, np.ndarray):
        label = f"{name}  (array {v.dtype}, shape {v.shape})"
        if v.ndim == 1:
            return {"k": "arr", "n": label, "v": [_cell(x) for x in v[:30].tolist()], "p": {}, "hl": [], "ok": [], "bad": []}
        if v.ndim == 2:
            return {"k": "grid", "n": label, "v": [[_cell(x) for x in r] for r in v[:10, :10].tolist()],
                    "hl": [], "ok": [], "bad": [], "rl": None, "cl": None}
        return {"k": "vars", "n": label, "v": [["values", _short(v.tolist())]]}
    if pd is not None and isinstance(v, pd.DataFrame):
        head = v.iloc[:8, :8]
        more = f", showing {len(head)} of {len(v)} rows" if len(v) > 8 else ""
        return {"k": "grid", "n": f"{name}  (DataFrame {v.shape[0]}×{v.shape[1]}{more})",
                "v": [[_cell(x) for x in row] for row in head.itertuples(index=False)], "hl": [], "ok": [], "bad": [],
                "rl": [_cell(i) for i in head.index], "cl": [str(c) for c in head.columns]}
    if pd is not None and isinstance(v, pd.Series):
        head = v.iloc[:20]
        return {"k": "arr", "n": f"{name}  (Series {v.dtype})", "v": [_cell(x) for x in head.tolist()],
                "p": {}, "hl": [], "ok": [], "bad": [], "il": [_cell(i) for i in head.index]}
    return None


def _library_object(v):
    mod = getattr(type(v), "__module__", "") or ""
    return mod.split(".")[0] in ("numpy", "pandas", "matplotlib", "seaborn")


def _view(name, v):
    ds = _ds_view(name, v)
    if ds is not None:
        return ds
    if _library_object(v):
        return None
    if isinstance(v, list):
        if v and len(v) <= 12 and all(isinstance(r, list) and len(r) <= 12 for r in v):
            return {"k": "grid", "n": name, "v": [[_cell(x) for x in r] for r in v],
                    "hl": [], "ok": [], "bad": [], "rl": None, "cl": None}
        return {"k": "arr", "n": name, "v": [_cell(x) for x in v[:40]], "p": {}, "hl": [], "ok": [], "bad": []}
    if isinstance(v, tuple):
        return {"k": "arr", "n": name + "  (tuple)", "v": [_cell(x) for x in v[:40]], "p": {}, "hl": [], "ok": [], "bad": []}
    if isinstance(v, (set, frozenset)):
        return {"k": "map", "n": name + "  (set)", "v": [[_short(x, 20), None] for x in sorted(v, key=repr)[:40]], "hl": None}
    if isinstance(v, dict):
        return {"k": "map", "n": name + "  (dict)", "v": [[_short(k, 20), _short(x, 24)] for k, x in list(v.items())[:40]], "hl": None}
    if hasattr(v, "__dict__") and not inspect.isroutine(v) and not inspect.isclass(v) and not inspect.ismodule(v):
        attrs = {k: x for k, x in vars(v).items() if not k.startswith("_")}
        return {"k": "map", "n": f"{name}  ({type(v).__name__} object)", "v": [[k, _short(x, 24)] for k, x in attrs.items()], "hl": None}
    return None


def _views(frame, stack, out, hidden):
    views = []
    if len(stack) > 1:
        views.append({"k": "stack", "n": "call stack (newest on top)", "v": stack, "hl": [len(stack) - 1]})
    scalars, rich = [], []
    for k, v in frame.f_locals.items():
        if k.startswith("__") or k in hidden:
            continue
        if inspect.ismodule(v) or inspect.isclass(v) or inspect.isroutine(v):
            continue
        view = _view(k, v)
        if view is None:
            scalars.append([k, _short(v)])
        else:
            rich.append(view)
    if scalars:
        views.append({"k": "vars", "n": "variables", "v": scalars})
    views += rich
    text = out.getvalue()
    if text:
        views.append({"k": "out", "n": "printed output", "v": text.rstrip("\n").split("\n")[-30:]})
    return views


# ---------- charts and library results ----------

def _close_figures():
    plt = sys.modules.get("matplotlib.pyplot")
    if plt is not None:
        plt.close("all")


def _figures(dpi=80):
    """Every open matplotlib figure as a base64 PNG, then close them."""
    plt = sys.modules.get("matplotlib.pyplot")
    if plt is None:
        return []
    import base64
    images = []
    for num in plt.get_fignums():
        buf = io.BytesIO()
        plt.figure(num).savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
        images.append("data:image/png;base64," + base64.b64encode(buf.getvalue()).decode())
    plt.close("all")
    return images


def plain(x, digits=4):
    """NumPy / pandas results as plain Python values, so they compare with a test's expected answer."""
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


# ---------- helpers available to every program (used by DSA handbook answers) ----------

class ListNode:
    def __init__(self, val=0, next=None):
        self.val, self.next = val, next


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val, self.left, self.right = val, left, right


def mk_list(vals, pos=-1):
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


from dataclasses import dataclass, field  # noqa: E402

PRELUDE = {"dataclass": dataclass, "field": field, "ListNode": ListNode, "TreeNode": TreeNode, "mk_list": mk_list, "list_arr": list_arr, "mk_tree": mk_tree}


# ---------- running ----------

def _error_info(e):
    tb = [f for f in traceback.extract_tb(e.__traceback__) if f.filename == "<main>"]
    line = tb[-1].lineno if tb else getattr(e, "lineno", None)
    name = type(e).__name__
    msg = f"{name}: {e}" if str(e) else name
    if isinstance(e, SyntaxError):
        msg = f"{name}: {e.msg}"
    return {"error": msg, "line": line, "hint": HINTS.get(name, "")}


def _run(code, stdin, trace):
    out = io.StringIO()
    feed = iter(stdin.splitlines())

    def fake_input(prompt=""):
        out.write(str(prompt))
        try:
            line = next(feed)
        except StopIteration:
            raise EOFError("input() was called but the Input box has no more lines") from None
        out.write(line + "\n")
        return line

    g = {"__name__": "__main__", "input": fake_input, **PRELUDE}
    hidden = set(PRELUDE) | {"input"}
    frames, lines = [], code.split("\n")
    state = {"truncated": False}

    def stack_of(f):
        names = []
        while f is not None and f.f_code.co_filename == "<main>":
            co = f.f_code
            if co.co_name == "<module>":
                names.append("main program")
            elif co.co_name not in INTERNAL:
                args = ", ".join(f"{a}={_short(f.f_locals.get(a), 14)}" for a in co.co_varnames[:co.co_argcount] if a != "self")
                names.append(f"{co.co_name}({args})")
            f = f.f_back
        return names[::-1]

    def record(f, msg):
        if len(frames) >= MAX_STEPS:
            state["truncated"] = True
            return
        frames.append({"m": msg, "l": f.f_lineno - 1, "v": _views(f, stack_of(f), out, hidden)})

    def tracer(f, event, arg):
        if f.f_code.co_filename != "<main>":
            return None
        if event == "line":
            text = lines[f.f_lineno - 1].strip() if 0 < f.f_lineno <= len(lines) else ""
            record(f, f"Line {f.f_lineno}: {text}")
        elif event == "return" and f.f_code.co_name not in INTERNAL and f.f_code.co_name != "<module>":
            record(f, f"{f.f_code.co_name}() returns {_short(arg)}")
        elif event == "exception":
            record(f, f"{arg[0].__name__}: {arg[1]}")
        return tracer

    result = {"out": "", "frames": frames}
    try:
        compiled = compile(code, "<main>", "exec")
    except SyntaxError as e:
        result.update(_error_info(e))
        return result, None
    _close_figures()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        if trace:
            sys.settrace(tracer)
        try:
            exec(compiled, g)  # noqa: S102
        except BaseException as e:  # noqa: BLE001
            result.update(_error_info(e))
        finally:
            sys.settrace(None)
    result["out"] = out.getvalue()
    result["truncated"] = state["truncated"]
    result["images"] = _figures()
    if frames and result["images"]:
        frames.append({"m": "Charts drawn by the program", "l": frames[-1]["l"],
                       "v": [v for v in frames[-1]["v"] if v["k"] != "img"] +
                            [{"k": "img", "n": "chart", "src": src} for src in result["images"]]})
    return result, g


def execute(code, stdin, trace):
    result, _ = _run(code, stdin, bool(trace))
    return json.dumps(result)


def check_code(code, stdin, payload_json):
    p = json.loads(payload_json)
    result, g = _run(code, stdin, False)
    result["tests"] = []
    if g is None or "error" in result:
        return json.dumps(result)
    target = g.get(p["name"])
    if target is None:
        result["error"] = f"Define a {'class' if p.get('design') else 'function'} named {p['name']} so it can be checked."
        return json.dumps(result)
    for t in p["tests"]:
        call = p["name"]
        try:
            if p.get("design"):
                ctor, ops = eval(t["ctor"]), eval(t["ops"])  # noqa: S307
                call = f"{p['name']}({', '.join(map(repr, ctor))}) then " + ", ".join(f"{m}({', '.join(map(repr, a))})" for m, a in ops)
                obj = target(*ctor)
                got = [getattr(obj, m)(*a) for m, a in ops]
            else:
                args = eval(t["args"])  # noqa: S307
                call = f"{p['name']}({', '.join(map(repr, args))})"
                with contextlib.redirect_stdout(io.StringIO()):
                    got = target(*copy.deepcopy(args))
                if p.get("listify"):
                    got = list(got)
            want = eval(t["want"])  # noqa: S307
            if p.get("plain"):
                got, want = plain(got), plain(want)
            _close_figures()
            try:
                ok = got == want
                ok = ok if isinstance(ok, bool) else False  # e.g. an unconverted NumPy array compares element by element
            except Exception:  # noqa: BLE001
                ok = False
            result["tests"].append({"call": call, "want": t["want"], "got": repr(got), "ok": ok})
        except BaseException as e:  # noqa: BLE001
            result["tests"].append({"call": call, "want": t["want"], "got": _error_info(e)["error"], "ok": False})
    return json.dumps(result)
