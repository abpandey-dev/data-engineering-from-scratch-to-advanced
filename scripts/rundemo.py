"""Run every lesson demo in the given lesson files, printing their output."""
import importlib.util
import inspect
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "engine"), str(ROOT / "engine" / "src")]
import matplotlib
matplotlib.use("Agg")
for f in sys.argv[1:]:
    spec = importlib.util.spec_from_file_location("m", f)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    for n, fn in vars(m).items():
        if inspect.isfunction(fn) and fn.__module__ == "m" and not inspect.signature(fn).parameters:
            print("--", n)
            fn()
