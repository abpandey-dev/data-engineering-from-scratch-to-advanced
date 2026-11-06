/* SQL IDE: CodeMirror editor + SQLite in a worker. #q=<topic>/<question> opens a practice question; #s=<base64> opens a shared query. */
(function () {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const store = {
    get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* private mode */ } },
  };
  const DATA = window.SQL_DATA;
  const dbById = (id) => DATA.databases.find((d) => d.id === id);
  const qById = (id) => DATA.questions.find((q) => q.id === id);
  const WELCOME = "-- Write SQL here and press Run (Ctrl/⌘ + Enter).\n-- Select part of the text to run only that part.\n-- See the Tables tab for what's here, and Practice for questions.\n\nSELECT * FROM users;\n";
  const EXAMPLES = {
    shop: {
      "All tables in this database": "SELECT name, type FROM sqlite_master WHERE type = 'table';",
      "Join three tables": "SELECT o.id, u.name, p.name AS product, o.qty\nFROM orders o\nJOIN users u ON u.id = o.user_id\nJOIN products p ON p.id = o.product_id\nORDER BY o.id;",
      "Group and filter groups": "SELECT user_id, COUNT(*) AS orders\nFROM orders\nGROUP BY user_id\nHAVING COUNT(*) >= 2;",
      "Change data, then undo": "UPDATE products SET price = price * 2;\nSELECT * FROM products;\n-- Press Reset data to undo this.",
    },
    analytics: {
      "Rank within a group": "SELECT region, id, amount,\n       RANK() OVER (PARTITION BY region ORDER BY amount DESC) AS rnk\nFROM sales;",
      "Running total": "SELECT day, amount,\n       SUM(amount) OVER (ORDER BY day ROWS UNBOUNDED PRECEDING) AS running\nFROM sales\nWHERE region = 'N';",
      "Previous row with LAG": "SELECT user_id, ts,\n       ts - LAG(ts) OVER (PARTITION BY user_id ORDER BY ts) AS gap\nFROM events;",
      "Recursive CTE": "WITH RECURSIVE t(id, name, depth) AS (\n  SELECT id, name, 0 FROM tree WHERE parent IS NULL\n  UNION ALL\n  SELECT c.id, c.name, t.depth + 1 FROM tree c JOIN t ON c.parent = t.id\n)\nSELECT * FROM t;",
    },
    star: {
      "Fact joined to a dimension": "SELECT p.category, SUM(f.amount) AS total\nFROM fact_orders f\nJOIN dim_product p ON p.product_key = f.product_key\nGROUP BY p.category;",
      "See SCD 2 history": "SELECT * FROM dim_customer ORDER BY customer_id, valid_from;",
    },
    raw: {
      "Find duplicates": "SELECT id, COUNT(*) AS copies\nFROM raw_orders\nGROUP BY id\nHAVING COUNT(*) > 1;",
      "Build a view": "CREATE VIEW stg AS\nSELECT DISTINCT id, day, amount FROM raw_orders WHERE status = 'paid';\n\nSELECT * FROM stg;",
    },
  };

  function decode(s) {
    try { return JSON.parse(decodeURIComponent(escape(atob(s.replace(/-/g, "+").replace(/_/g, "/"))))); } catch (e) { return null; }
  }
  function encode(o) {
    return btoa(unescape(encodeURIComponent(JSON.stringify(o)))).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
  }

  /* ---------- progress ---------- */
  const solved = new Set((() => { try { return JSON.parse(store.get("sql-ide-solved") || "[]"); } catch (e) { return []; } })());
  const saveSolved = () => store.set("sql-ide-solved", JSON.stringify([...solved]));

  /* ---------- state ---------- */
  let current = null;       // the open question
  let dbId = "shop";
  let worker, ready = false, busy = false, seq = 0, timer = null;
  const pending = new Map();
  let schemaInfo = [];

  /* ---------- editor ---------- */
  const editor = CodeMirror.fromTextArea($("code"), {
    mode: "text/x-sql", lineNumbers: true, indentUnit: 2, tabSize: 2, indentWithTabs: false,
    matchBrackets: true, autoCloseBrackets: true, autofocus: true, lineWrapping: true,
    extraKeys: {
      "Ctrl-Enter": () => run(), "Cmd-Enter": () => run(),
      "Shift-Ctrl-Enter": () => check(), "Shift-Cmd-Enter": () => check(),
      "Cmd-/": "toggleComment", "Ctrl-/": "toggleComment",
      "Ctrl-Space": (cm) => cm.showHint({ hint: CodeMirror.hint.sql, tables: hintTables(), completeSingle: false }),
    },
  });
  const hintTables = () => Object.fromEntries(schemaInfo.map((t) => [t.name, t.columns.map((c) => c.name)]));
  const draftKey = () => "sql-ide:" + (current ? current.id : "free:" + dbId);
  editor.on("change", () => store.set(draftKey(), editor.getValue()));

  /* ---------- status ---------- */
  const setStatus = (text, spinning) => { const s = $("status"); s.textContent = text; s.classList.toggle("busy", !!spinning); };
  function setBusy(on) {
    busy = on;
    $("run").disabled = on || !ready;
    $("check").disabled = on || !ready;
    $("stop").hidden = !on;
  }
  function showTab(k) {
    document.querySelectorAll(".ide-tabs [data-tab]").forEach((b) => b.setAttribute("aria-selected", String(b.dataset.tab === k)));
    document.querySelectorAll(".panel").forEach((p) => { p.hidden = p.dataset.panel !== k; });
  }
  document.querySelector(".ide-tabs").addEventListener("click", (e) => { const b = e.target.closest("[data-tab]"); if (b) showTab(b.dataset.tab); });

  /* ---------- worker ---------- */
  function call(msg) {
    return new Promise((resolve) => {
      const id = ++seq;
      pending.set(id, resolve);
      worker.postMessage({ id, ...msg });
    });
  }
  function startWorker() {
    ready = false;
    setBusy(false);
    setStatus("Loading SQLite… (first visit downloads about 1 MB)", true);
    return new Promise((resolve) => {
      worker = new Worker("sql-worker.js");
      worker.onmessage = (e) => {
        const d = e.data;
        if (d.type === "ready") { ready = true; setBusy(false); setStatus(`SQLite ${d.version} ready`); resolve(d.version); }
        else if (d.type === "fatal") setStatus("Couldn't load SQLite: " + d.error);
        else if (d.type === "result") { const f = pending.get(d.id); pending.delete(d.id); if (f) f(d); }
      };
      worker.onerror = () => setStatus("SQLite stopped unexpectedly. Reload the page.");
    });
  }
  async function openDb() {
    const r = await call({ cmd: "open", schema: dbById(dbId).schema });
    schemaInfo = r.schema || [];
    renderTables();
  }
  async function guarded(fn, label) {
    if (!ready || busy) return;
    setBusy(true);
    setStatus(label, true);
    timer = setTimeout(stop, 20000);
    try { await fn(); } finally { clearTimeout(timer); setBusy(false); }
  }
  async function stop() {
    clearTimeout(timer);
    worker.terminate();
    pending.clear();
    setBusy(false);
    $("sql-results").innerHTML = `<div class="sql-error"><b>Stopped.</b> The query ran too long or you pressed Stop. A recursive CTE with no end condition is the usual cause. The database was rebuilt, so any changes you made are gone.</div>`;
    showTab("results");
    await startWorker();
    await openDb();
  }
  $("stop").addEventListener("click", stop);

  /* ---------- rendering results ---------- */
  function cellHtml(v) {
    if (v === null || v === undefined) return `<td class="null">NULL</td>`;
    return typeof v === "number" ? `<td class="num">${esc(v)}</td>` : `<td>${esc(v)}</td>`;
  }
  function tableHtml(columns, rows, badRow) {
    const head = columns.map((c) => `<th>${esc(c)}</th>`).join("");
    const body = rows.map((r, i) => `<tr${i === badRow ? ' class="bad"' : ""}>${r.map(cellHtml).join("")}</tr>`).join("");
    return `<div class="table-wrap"><table class="grid"><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>`;
  }
  function hintFor(message) {
    const tables = schemaInfo.map((t) => t.name).join(", ");
    if (/no such table/i.test(message)) return `Tables available here: ${tables}. Check the spelling, or the Tables tab.`;
    if (/no such column/i.test(message)) return "Check the spelling in the Tables tab. Text values need single quotes, 'like this', or SQL reads them as a column name.";
    if (/ambiguous column/i.test(message)) return "Two joined tables have this column, so say which one, as in u.id or o.id.";
    if (/misuse of aggregate/i.test(message)) return "WHERE runs before grouping, so it can't use COUNT or SUM. Use HAVING, or a CTE.";
    if (/misuse of window/i.test(message)) return "WHERE can't use a window function. Put it in a CTE, then filter outside.";
    if (/near "/i.test(message) && /syntax error/i.test(message)) return "Check for a missing comma or bracket just before that word, and the clause order: SELECT, FROM, JOIN, WHERE, GROUP BY, HAVING, ORDER BY, LIMIT.";
    if (/incomplete input/i.test(message)) return "The query ended early. Check for an unclosed bracket or quote.";
    if (/already exists/i.test(message)) return "Press Reset data to start again with a fresh database.";
    if (/GROUP BY/i.test(message)) return "Every selected column should be grouped or inside an aggregate.";
    return "";
  }
  function errorHtml(message) {
    const hint = hintFor(message);
    return `<div class="sql-error"><b>Error:</b> ${esc(message)}${hint ? `<br><span>💡 ${esc(hint)}</span>` : ""}</div>`;
  }
  function renderRun(d) {
    const out = [];
    if (d.error) out.push(errorHtml(d.error));
    else {
      if (!d.results.length) out.push(`<p class="res-empty">Done. ${d.changed} row${d.changed === 1 ? "" : "s"} changed.</p>`);
      d.results.forEach((r) => {
        const more = r.total > r.rows.length ? ` (showing the first ${r.rows.length})` : "";
        out.push(`<p class="res-meta">${r.total} row${r.total === 1 ? "" : "s"}${more} · ${d.ms} ms</p>`);
        out.push(r.total ? tableHtml(r.columns, r.rows) : tableHtml(r.columns, []));
      });
      if (d.results.length && d.changed) out.unshift(`<p class="res-meta">${d.changed} row${d.changed === 1 ? "" : "s"} changed</p>`);
    }
    $("sql-results").innerHTML = out.join("");
    showTab("results");
  }

  /* ---------- run and check ---------- */
  const queryText = () => editor.getSelection().trim() || editor.getValue();
  function run() {
    return guarded(async () => {
      const d = await call({ cmd: "run", sql: queryText() });
      if (d.schema) { schemaInfo = d.schema; renderTables(); }
      renderRun(d);
      setStatus(d.error ? "Query failed" : `Finished in ${d.ms} ms`);
    }, "Running…");
  }
  const norm = (v) => (typeof v === "number" ? Math.round(v * 10000) / 10000 : v);
  const rowKey = (r) => JSON.stringify(r.map(norm));

  /* Returns {pass, message, badRow}. Exported for testing. */
  function compare(q, columns, rows, expected) {
    const got = rows.map(rowKey);
    const want = (expected || q.rows).map(rowKey);
    if (columns.length !== q.columns.length) {
      return { pass: false, message: `You returned ${columns.length} column${columns.length === 1 ? "" : "s"}, and the answer has ${q.columns.length}. Column names don't matter, but the number and order of columns do.` };
    }
    const sortedGot = [...got].sort(), sortedWant = [...want].sort();
    const same = sortedGot.length === sortedWant.length && sortedGot.every((k, i) => k === sortedWant[i]);
    if (same) {
      if (!q.ordered || got.every((k, i) => k === want[i])) return { pass: true };
      return { pass: false, message: "You have the right rows, in the wrong order. Check the ORDER BY the question asks for." };
    }
    if (got.length !== want.length) {
      const extra = got.length > want.length;
      return { pass: false, message: `You returned ${got.length} row${got.length === 1 ? "" : "s"}, and the answer has ${want.length}. ${extra ? "Too many rows often means a missing filter, a missing DISTINCT, or a join on a non-unique key." : "Too few rows often means a filter that's too strict, or an INNER JOIN that should be a LEFT JOIN."}` };
    }
    const wanted = new Set(want);
    const badRow = got.findIndex((k) => !wanted.has(k));
    return { pass: false, badRow, message: `The row count is right, but some values differ. The first row that doesn't match is highlighted.` };
  }
  function check() {
    if (!current) return;
    const q = current;
    return guarded(async () => {
      const d = await call({ cmd: "check", schema: dbById(q.db).schema, sql: editor.getValue() });
      if (d.error) { $("sql-results").innerHTML = errorHtml(d.error); showTab("results"); setStatus("Query failed"); return; }
      const last = d.results[d.results.length - 1];
      if (!last) {
        $("sql-results").innerHTML = `<div class="verdict fail"><b>✗ Not yet.</b><br>Your SQL didn't return any result. It should end with a SELECT.</div>`;
        showTab("results"); setStatus("Not yet"); return;
      }
      let v = compare(q, last.columns, last.rows);
      if (v.pass) {
        // The same query must also work on data the student hasn't seen.
        const db = dbById(q.db);
        const h = await call({ cmd: "check", schema: db.schema + "\n" + db.hidden, sql: editor.getValue() });
        const hl = h.results && h.results[h.results.length - 1];
        if (h.error || !hl || !compare(q, hl.columns, hl.rows, q.hiddenRows).pass) {
          v = { pass: false, hidden: true, message: "This is right for the sample data, but it fails on a hidden test with more rows. Make sure nothing is hard-coded, and that your filters and ORDER BY follow the question exactly, even where the sample data hides the difference." };
        }
      }
      if (v.pass) {
        solved.add(q.id);
        saveSolved();
        renderPractice();
        renderQuestion();
        const next = nextQuestion(q);
        $("sql-results").innerHTML = `<div class="verdict pass"><b>✓ Correct!</b> ${solved.size} of ${DATA.questions.length} solved. Compare with the model answer, as there's often more than one good way.${next ? `<br><button type="button" id="go-next">Next: ${esc(next.title)} →</button>` : ""}</div><p class="res-meta">${last.total} row${last.total === 1 ? "" : "s"}</p>` + tableHtml(last.columns, last.rows.slice(0, 1000));
        const b = $("go-next");
        if (b) b.addEventListener("click", () => openQuestion(next.id));
        setStatus("Correct");
      } else {
        $("sql-results").innerHTML = `<div class="verdict fail"><b>✗ Not yet.</b><br>${esc(v.message)}</div><p class="res-meta">Your result: ${last.total} row${last.total === 1 ? "" : "s"}</p>` + tableHtml(last.columns, last.rows.slice(0, 1000), v.badRow);
        setStatus("Not yet");
      }
      showTab("results");
    }, "Checking…");
  }
  $("run").addEventListener("click", () => run());
  $("check").addEventListener("click", () => check());

  /* ---------- tables panel ---------- */
  function renderTables() {
    const db = dbById(dbId);
    $("tables").innerHTML = `<p class="res-empty"><b>${esc(db.name)}:</b> ${esc(db.description)}. Click a column to add it to your query.</p>` + schemaInfo.map((t) => `
      <div class="tbl"><div class="tbl-head"><b>${esc(t.name)}</b><span>${t.type === "view" ? "view · " : ""}${t.rows} row${t.rows === 1 ? "" : "s"}</span>
        <button type="button" data-peek="${esc(t.name)}">Preview</button></div>
        <div class="cols">${t.columns.map((c) => `<button type="button" data-col="${esc(c.name)}">${esc(c.name)}<i>${esc(c.type.toLowerCase())}</i></button>`).join("")}</div></div>`).join("");
  }
  $("tables").addEventListener("click", (e) => {
    const peek = e.target.closest("[data-peek]");
    const col = e.target.closest("[data-col]");
    if (peek) {
      guarded(async () => {
        const d = await call({ cmd: "run", sql: `SELECT * FROM "${peek.dataset.peek}" LIMIT 20` });
        renderRun(d);
        setStatus(`Preview of ${peek.dataset.peek}`);
      }, "Running…");
    } else if (col) {
      editor.replaceSelection(col.dataset.col);
      editor.focus();
    }
  });

  /* ---------- practice ---------- */
  function renderPractice() {
    const groups = {};
    DATA.questions.forEach((q) => { (groups[q.topic] = groups[q.topic] || []).push(q); });
    const pct = Math.round((100 * solved.size) / DATA.questions.length);
    $("practice").innerHTML = `<p class="p-sum">${solved.size} of ${DATA.questions.length} solved</p><div class="p-bar"><i style="width:${pct}%"></i></div>` +
      Object.entries(groups).map(([topic, qs]) => `<p class="p-group">${esc(topic)}</p>` + qs.map((q) => `
        <button type="button" class="p-item${current && current.id === q.id ? " on" : ""}" data-q="${esc(q.id)}"><span class="tick">${solved.has(q.id) ? "✓" : ""}</span>${esc(q.title)}<span class="diff-tag ${esc(q.diff)}">${esc(q.diff)}</span></button>`).join("")).join("");
  }
  $("practice").addEventListener("click", (e) => { const b = e.target.closest("[data-q]"); if (b) openQuestion(b.dataset.q); });
  const nextQuestion = (q) => DATA.questions[DATA.questions.indexOf(q) + 1];
  const prevQuestion = (q) => DATA.questions[DATA.questions.indexOf(q) - 1];

  function renderQuestion() {
    const card = $("question");
    if (!current) { card.hidden = true; $("check").hidden = true; $("title").textContent = ""; return; }
    const q = current;
    card.hidden = false;
    $("check").hidden = false;
    $("title").textContent = q.title;
    document.title = q.title + " · SQL IDE";
    const prev = prevQuestion(q), next = nextQuestion(q);
    card.innerHTML = `<div class="q-head"><h2>${solved.has(q.id) ? "✓ " : ""}${esc(q.title)}</h2><span class="diff-tag ${esc(q.diff)}">${esc(q.diff)}</span>
        <div class="q-nav">${prev ? `<button type="button" data-go="${esc(prev.id)}">← Prev</button>` : ""}${next ? `<button type="button" data-go="${esc(next.id)}">Next →</button>` : ""}<button type="button" data-close="1">Exit</button></div></div>
      <p>${esc(q.statement)}</p>
      <p class="q-meta">${esc(q.tags)} · database: ${esc(dbById(q.db).name)}${q.ordered ? " · row order is checked" : ""}</p>
      <div class="q-actions"><button type="button" data-reveal="hint">💡 Hint</button><button type="button" data-reveal="expected">Expected output</button><button type="button" data-reveal="solution">Show answer</button></div>
      <div id="reveal"></div>`;
  }
  $("question").addEventListener("click", (e) => {
    const go = e.target.closest("[data-go]");
    if (go) return openQuestion(go.dataset.go);
    if (e.target.closest("[data-close]")) return closeQuestion();
    const show = e.target.closest("[data-reveal]");
    if (!show || !current) return;
    const box = $("reveal");
    const kind = show.dataset.reveal;
    if (box.dataset.kind === kind) { box.innerHTML = ""; box.dataset.kind = ""; editor.refresh(); return; }
    box.dataset.kind = kind;
    if (kind === "hint") box.innerHTML = `<div class="reveal"><p>${esc(current.hint)}</p></div>`;
    if (kind === "expected") box.innerHTML = `<div class="reveal">${tableHtml(current.columns, current.rows)}</div>`;
    if (kind === "solution") box.innerHTML = `<div class="reveal"><pre>${esc(current.solution)}</pre></div>`;
    editor.refresh();
  });

  async function setDb(id) {
    dbId = id;
    $("db").value = id;
    const sel = $("examples");
    sel.innerHTML = `<option value="">Examples…</option>` + Object.keys(EXAMPLES[id] || {}).map((k) => `<option>${esc(k)}</option>`).join("");
    if (ready) await openDb();
  }
  async function openQuestion(id) {
    const q = qById(id);
    if (!q || busy) return;
    current = q;
    history.replaceState(null, "", "#q=" + id);
    await setDb(q.db);
    editor.setValue(store.get(draftKey()) || `-- ${q.title}\n-- Write your query below, then press Check answer.\n\n`);
    editor.setCursor(editor.lineCount(), 0);
    renderQuestion();
    renderPractice();
    $("sql-results").innerHTML = `<p class="res-empty">Press ▶ Run to see your result, and ✓ Check answer when you're ready. Open the Tables tab to see the columns.</p>`;
    showTab("results");
    editor.focus();
    setTimeout(() => editor.refresh(), 0);
  }
  async function closeQuestion() {
    current = null;
    history.replaceState(null, "", location.pathname);
    document.title = "SQL IDE";
    renderQuestion();
    renderPractice();
    editor.setValue(store.get(draftKey()) || (dbId === "shop" ? WELCOME : `-- ${dbById(dbId).name} database\n\n`));
    setTimeout(() => editor.refresh(), 0);
  }

  /* ---------- toolbar ---------- */
  $("db").innerHTML = DATA.databases.map((d) => `<option value="${esc(d.id)}">${esc(d.name)}</option>`).join("");
  $("db").addEventListener("change", async (e) => {
    current = null;
    history.replaceState(null, "", location.pathname);
    renderQuestion();
    await setDb(e.target.value);
    renderPractice();
    editor.setValue(store.get(draftKey()) || (dbId === "shop" ? WELCOME : `-- ${dbById(dbId).name} database. See the Tables tab, or load an example.\n\n`));
    $("sql-results").innerHTML = `<p class="res-empty">Switched to ${esc(dbById(dbId).name)}.</p>`;
    showTab("tables");
  });
  $("examples").addEventListener("change", (e) => {
    const text = (EXAMPLES[dbId] || {})[e.target.value];
    if (text) { editor.setValue(text); editor.focus(); }
    e.target.value = "";
  });
  $("reset").addEventListener("click", () => guarded(async () => {
    await openDb();
    $("sql-results").innerHTML = `<p class="res-empty">The database is back to its original data.</p>`;
    showTab("results");
    setStatus("Data reset");
  }, "Resetting…"));
  $("share").addEventListener("click", async () => {
    const url = location.href.split("#")[0] + "#s=" + encode({ db: dbId, sql: editor.getValue() });
    try { await navigator.clipboard.writeText(url); setStatus("Link copied"); } catch (e) { prompt("Copy this link:", url); }
  });

  /* ---------- start ---------- */
  (async function start() {
    const hash = location.hash;
    const qm = hash.match(/^#q=(.+)$/);
    const sm = hash.match(/^#s=(.+)$/);
    const shared = sm && decode(sm[1]);
    if (shared && dbById(shared.db)) dbId = shared.db;
    $("db").value = dbId;
    await setDb(dbId);
    renderPractice();
    $("sql-results").innerHTML = `<p class="res-empty">Press ▶ Run (or Ctrl/⌘ + Enter). Results appear here.<br>Everything runs in your browser, so you can't break anything. <b>Reset data</b> restores the original tables.</p>`;
    if (shared) editor.setValue(shared.sql || "");
    else if (!qm) editor.setValue(store.get(draftKey()) || WELCOME);
    await startWorker();
    await openDb();
    if (qm && qById(decodeURIComponent(qm[1]))) await openQuestion(decodeURIComponent(qm[1]));
    else if (qm) editor.setValue(store.get(draftKey()) || WELCOME);
  })();

  window.__sqlIde = { compare, data: DATA };
})();
