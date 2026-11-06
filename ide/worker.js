/* Runs Python (Pyodide) off the main thread so a stuck program can be stopped by terminating the worker. */
importScripts("https://cdn.jsdelivr.net/pyodide/v0.26.4/full/pyodide.js");

const ready = (async () => {
  const py = await loadPyodide();
  const src = await (await fetch("runner.py")).text();
  py.runPython(src);
  postMessage({ type: "ready", version: py.runPython("import sys; sys.version.split()[0]") });
  return py;
})().catch((err) => postMessage({ type: "fatal", error: String(err) }));

/* numpy, pandas, matplotlib … ship with Pyodide; seaborn is pure Python and comes from PyPI. */
const fromPyPI = { seaborn: "seaborn" };
const installed = new Set();

async function loadLibraries(py, code) {
  const wanted = new Set();
  for (const m of code.matchAll(/^\s*(?:import|from)\s+([A-Za-z_]\w*)/gm)) wanted.add(m[1]);
  const fresh = [...wanted].filter((name) => !installed.has(name));
  if (!fresh.length) return;
  postMessage({ type: "loading", names: fresh });
  await py.loadPackagesFromImports(code);
  const extra = fresh.filter((name) => fromPyPI[name]);
  if (extra.length) {
    await py.loadPackage("micropip");
    const micropip = py.pyimport("micropip");
    await micropip.install(extra.map((name) => fromPyPI[name]));
  }
  fresh.forEach((name) => installed.add(name));
}

onmessage = async (e) => {
  const py = await ready;
  if (!py) return;
  const { id, cmd, code, stdin, payload } = e.data;
  try {
    await loadLibraries(py, code);
    const text = cmd === "check"
      ? py.globals.get("check_code")(code, stdin || "", JSON.stringify(payload))
      : py.globals.get("execute")(code, stdin || "", cmd === "trace");
    postMessage({ type: "result", id, cmd, result: JSON.parse(text) });
  } catch (err) {
    postMessage({ type: "result", id, cmd, result: { out: "", error: String(err), frames: [] } });
  }
};
