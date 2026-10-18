const numberFormat = new Intl.NumberFormat("en-GB");
const runners = [];

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function humanize(name) {
  const words = name.replace(/_/g, " ");
  return words.charAt(0).toUpperCase() + words.slice(1);
}

function summary({ rows, ms }) {
  return `${rows.length} row${rows.length === 1 ? "" : "s"} · ${ms} ms`;
}

function formatValue(value) {
  if (value === null || value === undefined) return "NULL";
  if (typeof value === "number") return numberFormat.format(value);
  return String(value);
}

async function fetchJSON(url, options) {
  const response = await fetch(url, options);
  const body = await response.json();
  if (!response.ok) throw new Error(body.detail || response.statusText);
  return body;
}

function renderKpis(target, { columns, rows }) {
  const wrap = el("div", "kpis");
  columns.forEach((column, i) => {
    const tile = el("div");
    tile.append(el("div", "kpi-label", humanize(column)), el("div", "kpi-value", formatValue(rows[0]?.[i])));
    wrap.append(tile);
  });
  target.replaceChildren(wrap);
}

function renderBars(target, { rows }) {
  const max = Math.max(...rows.map((row) => Number(row[1])), 1);
  const wrap = el("div", "bars");
  for (const [label, value] of rows) {
    const row = el("div", "bar-row");
    row.title = `${label}: ${formatValue(value)}`;
    const bar = el("div", "bar");
    bar.style.width = `${(Number(value) / max) * 82}%`;
    const track = el("div", "bar-track");
    track.append(bar, el("span", "bar-value", formatValue(value)));
    row.append(el("span", "bar-label", label ?? "NULL"), track);
    wrap.append(row);
  }
  target.replaceChildren(wrap);
}

function renderColumns(target, { columns, rows }) {
  const max = Math.max(...rows.map((row) => Number(row[1])), 1);
  const plot = el("div", "columns");
  for (const [label, value] of rows) {
    const column = el("div", "column");
    column.style.height = `${(Number(value) / max) * 100}%`;
    column.title = `${label}: ${formatValue(value)} ${columns[1]}`;
    plot.append(column);
  }
  const axis = el("div", "column-axis");
  axis.append(el("span", "", rows[0]?.[0] ?? ""), el("span", "", rows.at(-1)?.[0] ?? ""));
  target.replaceChildren(plot, axis);
}

function renderTable(target, { columns, rows }) {
  const table = el("table");
  const headRow = el("tr");
  columns.forEach((column) => headRow.append(el("th", "", column)));
  const body = el("tbody");
  for (const row of rows) {
    const tr = el("tr");
    row.forEach((value) => tr.append(el("td", typeof value === "number" ? "number" : "", formatValue(value))));
    body.append(tr);
  }
  const head = el("thead");
  head.append(headRow);
  table.append(head, body);
  target.replaceChildren(table);
}

const renderers = { kpi: renderKpis, bar: renderBars, column: renderColumns };

function addCard(query) {
  const card = document.getElementById("card-template").content.firstElementChild.cloneNode(true);
  if (query.chart === "kpi" || query.chart === "column") card.classList.add("wide");
  card.querySelector("h2").textContent = query.title;
  card.querySelector("pre").textContent = query.sql;
  const chart = card.querySelector(".chart");
  const status = card.querySelector(".status");
  const button = card.querySelector(".run");

  async function run() {
    button.disabled = true;
    status.className = "status";
    status.textContent = "Running…";
    try {
      const data = await fetchJSON(`/api/queries/${query.key}`);
      renderers[query.chart](chart, data);
      status.textContent = summary(data);
    } catch (error) {
      status.className = "status error";
      status.textContent = error.message;
    } finally {
      button.disabled = false;
    }
  }

  button.addEventListener("click", run);
  document.getElementById("cards").append(card);
  runners.push(run);
  run();
}

async function runConsole() {
  const button = document.getElementById("run-sql");
  const status = document.getElementById("sql-status");
  const result = document.getElementById("sql-result");
  button.disabled = true;
  status.className = "status";
  status.textContent = "Running…";
  try {
    const data = await fetchJSON("/api/sql", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sql: document.getElementById("sql").value }),
    });
    renderTable(result, data);
    status.textContent = summary(data);
  } catch (error) {
    result.replaceChildren();
    status.className = "status error";
    status.textContent = error.message;
  } finally {
    button.disabled = false;
  }
}

document.getElementById("run-sql").addEventListener("click", runConsole);
document.getElementById("sql").addEventListener("keydown", (event) => {
  if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) runConsole();
});
document.getElementById("run-all").addEventListener("click", () => runners.forEach((run) => run()));

fetchJSON("/api/queries")
  .then((queries) => queries.forEach(addCard))
  .catch((error) => {
    const message = el("p", "error", `Could not load queries: ${error.message}`);
    document.getElementById("cards").replaceChildren(message);
  });
