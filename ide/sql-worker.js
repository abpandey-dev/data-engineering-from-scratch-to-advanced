/* Runs SQLite (sql.js) off the main thread, so a runaway query can be stopped. */
importScripts("https://cdnjs.cloudflare.com/ajax/libs/sql.js/1.10.3/sql-wasm.js");
const CDN = "https://cdnjs.cloudflare.com/ajax/libs/sql.js/1.10.3/";
const MAX_SHOWN = 1000;
const MAX_CHECK = 100000;
let SQL = null;
let db = null;

function cell(v) {
  return v instanceof Uint8Array ? "[blob]" : v;
}

/* Runs every statement, returning a result for each one that produces columns. */
function execute(database, sql, limit) {
  const results = [];
  let changed = 0;
  for (const stmt of database.iterateStatements(sql)) {
    const columns = stmt.getColumnNames();
    const rows = [];
    let total = 0;
    while (stmt.step()) {
      total += 1;
      if (rows.length < limit) rows.push(stmt.get().map(cell));
      if (total >= MAX_CHECK) break;
    }
    if (columns.length) results.push({ columns, rows, total });
    else changed += database.getRowsModified();
  }
  return { results, changed };
}

function schemaInfo(database) {
  const list = database.exec("SELECT name, type FROM sqlite_master WHERE type IN ('table', 'view') AND name NOT LIKE 'sqlite_%' ORDER BY type, name");
  if (!list.length) return [];
  return list[0].values.map(([name, type]) => {
    const quoted = '"' + name.replace(/"/g, '""') + '"';
    const info = database.exec(`PRAGMA table_info(${quoted})`);
    const count = database.exec(`SELECT COUNT(*) FROM ${quoted}`);
    return {
      name, type,
      columns: info.length ? info[0].values.map((c) => ({ name: c[1], type: c[2] || "" })) : [],
      rows: count[0].values[0][0],
    };
  });
}

initSqlJs({ locateFile: (f) => CDN + f }).then((lib) => {
  SQL = lib;
  postMessage({ type: "ready", version: new SQL.Database().exec("SELECT sqlite_version()")[0].values[0][0] });
}).catch((e) => postMessage({ type: "fatal", error: String(e) }));

onmessage = (e) => {
  const { id, cmd, schema, sql } = e.data;
  const started = performance.now();
  try {
    let reply = {};
    if (cmd === "open") {
      if (db) db.close();
      db = new SQL.Database();
      db.exec(schema);
      reply = { schema: schemaInfo(db) };
    } else if (cmd === "run") {
      reply = { ...execute(db, sql, MAX_SHOWN), schema: schemaInfo(db) };
    } else if (cmd === "check") {
      const fresh = new SQL.Database();   // a clean copy, so earlier experiments can't change the answer
      fresh.exec(schema);
      reply = execute(fresh, sql, MAX_CHECK);
      fresh.close();
    }
    postMessage({ type: "result", id, cmd, ms: Math.round(performance.now() - started), ...reply });
  } catch (err) {
    postMessage({ type: "result", id, cmd, error: err.message || String(err) });
  }
};
