import json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "engine")); sys.path.insert(0, str(ROOT / "engine" / "src"))
import build, lib
book, name = "course", sys.argv[1]
build.BOOK = ROOT / book
build.CONF = json.loads((build.BOOK / "book.json").read_text())
path = build.BOOK / "src" / "topics" / name
reg = build.load(path)
values, problems = [], []
for q in reg["questions"]:
    for args, want in q["tests"]:
        if want is not Ellipsis: continue
        try:
            o = lib.plain(build.run(q, q["opt"], args)); b = lib.plain(build.run(q, q["brute"], args))
        except Exception as e:
            problems.append(f"{q['title']}: {type(e).__name__}: {e}"); values.append(None); continue
        finally:
            lib.close_figures()
        if o != b: problems.append(f"{q['title']} args={args!r}: opt={o!r} brute={b!r}")
        values.append(o)
if problems:
    print("NOT WRITTEN:"); print("\n".join(problems)); sys.exit(1)
text = path.read_text()
assert len(re.findall(r"\bWANT\b(?! = )", text)) == len(values)
it = iter(values)
text = re.sub(r"\bWANT\b(?! = )", lambda m: repr(next(it)), text).replace("WANT = ...\n", "")
path.write_text(text)
print(f"filled {len(values)}; questions {len(reg['questions'])}")
