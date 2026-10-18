const numberFormat = new Intl.NumberFormat("en-GB");
const percentFormat = new Intl.NumberFormat("en-GB", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
const LAYERS = ["bronze", "silver", "gold"];
const LAYOUT = { kpis: "full", map: "double", divisions: "double", incorporations: "full", pipeline: "full" };
const TILES = "https://tile.openstreetmap.org/{z}/{x}/{y}.png";
const UK_BOUNDS = [[50.3, -6.0], [57.6, 1.4]];

const state = { industry: "ALL", industries: [] };
const cards = new Map();
let leafletMap;
let markerLayer;

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function isPercent(column) {
  return /%|_pct$/.test(column);
}

function humanize(column) {
  const words = column.replace(/_/g, " ").replace(/\s*%$/, "");
  return words.charAt(0).toUpperCase() + words.slice(1);
}

function formatValue(value, percent = false) {
  if (value === null || value === undefined) return "—";
  return percent ? `${percentFormat.format(value)}%` : numberFormat.format(value);
}

function share(value, total) {
  return total ? (100 * Number(value)) / total : 0;
}

function industryName(code) {
  return state.industries.find(([sector]) => sector === code)?.[1] ?? "All industries";
}

function barRow(label, bars, selected = false) {
  const row = el("div", selected ? "bar-row selected" : "bar-row");
  row.append(el("span", "bar-label", label ?? "—"), bars);
  return row;
}

function bar(width, className = "bar") {
  const node = el("div", className);
  node.style.width = `${Math.max(width, 0)}%`;
  return node;
}

function renderKpis(target, { columns, rows }) {
  const wrap = el("div", "kpis");
  columns.forEach((column, i) => {
    const tile = el("div");
    tile.append(el("div", "kpi-label", humanize(column)), el("div", "kpi-value", formatValue(rows[0]?.[i], isPercent(column))));
    wrap.append(tile);
  });
  target.replaceChildren(wrap);
}

function renderDonut(target, { rows }) {
  const total = rows.reduce((sum, [, value]) => sum + Number(value || 0), 0);
  const stops = [];
  let angle = 0;
  rows.forEach(([, value], i) => {
    const sweep = total ? (Number(value || 0) / total) * 360 : 0;
    const gap = rows.length > 1 && sweep > 3 ? 1.5 : 0;
    stops.push(`var(--c${i + 1}) ${angle}deg ${angle + sweep - gap}deg`, `transparent ${angle + sweep - gap}deg ${angle + sweep}deg`);
    angle += sweep;
  });

  const ring = el("div", "donut-ring");
  ring.style.background = total ? `conic-gradient(${stops.join(", ")})` : "var(--dimmed)";
  const center = el("div", "donut-center");
  center.append(el("strong", "", formatValue(total)), el("span", "", "leads"));
  const donut = el("div", "donut");
  donut.append(ring, center);

  const legend = el("ul", "legend");
  rows.forEach(([label, value], i) => {
    const item = el("li");
    const swatch = el("span", "swatch");
    swatch.style.background = `var(--c${i + 1})`;
    item.title = `${label}: ${formatValue(value)} leads`;
    item.append(swatch, el("span", "legend-label", label), el("span", "legend-value", formatValue(share(value, total), true)), el("span", "legend-count", formatValue(value)));
    legend.append(item);
  });

  const wrap = el("div", "donut-wrap");
  wrap.append(donut, legend);
  target.replaceChildren(wrap);
}

function renderBars(target, { columns, rows }) {
  const percent = isPercent(columns[1]);
  const max = Math.max(...rows.map(([, value]) => Number(value)), 1);
  const wrap = el("div", "bars");
  for (const [label, value] of rows) {
    const track = el("div", "bar-track");
    track.append(bar((Number(value) / max) * 82), el("span", "bar-value", formatValue(value, percent)));
    const row = barRow(label, track);
    row.title = `${label}: ${formatValue(value, percent)}`;
    wrap.append(row);
  }
  target.replaceChildren(wrap);
}

function renderRank(target, { columns, rows }) {
  const percent = isPercent(columns[2]);
  const max = Math.max(...rows.map((row) => Number(row[2])), 1);
  const wrap = el("div", "bars");
  for (const [code, label, value] of rows) {
    const highlighted = state.industry === "ALL" || state.industry === code;
    const track = el("div", "bar-track");
    track.append(bar((Number(value) / max) * 82, highlighted ? "bar" : "bar dimmed"), el("span", "bar-value", formatValue(value, percent)));
    const row = barRow(label, track, state.industry === code);
    row.title = `${label}: ${formatValue(value, percent)}`;
    wrap.append(row);
  }
  target.replaceChildren(wrap);
}

function renderCompare(target, { rows }) {
  const comparing = state.industry !== "ALL";
  const max = Math.max(...rows.flatMap(([, selected, all]) => [Number(selected), Number(all)]), 1);
  const legend = el("ul", "legend");
  const series = comparing ? [[industryName(state.industry), "var(--accent)"], ["All industries", "var(--benchmark)"]] : [["All industries", "var(--accent)"]];
  for (const [name, color] of series) {
    const item = el("li");
    const swatch = el("span", "swatch");
    swatch.style.background = color;
    item.append(swatch, el("span", "", name));
    legend.append(item);
  }

  const wrap = el("div", "bars");
  for (const [label, selected, all] of rows) {
    const pair = el("div", "bar-pair");
    const main = el("div", "bar-track");
    main.append(bar((Number(comparing ? selected : all) / max) * 82), el("span", "bar-value", formatValue(comparing ? selected : all, true)));
    pair.append(main);
    if (comparing) {
      const benchmark = el("div", "bar-track");
      benchmark.append(bar((Number(all) / max) * 82, "bar benchmark"), el("span", "bar-value", formatValue(all, true)));
      pair.append(benchmark);
    }
    const row = barRow(label, pair);
    row.title = comparing ? `${label}: ${formatValue(selected, true)} vs ${formatValue(all, true)} across all industries` : `${label}: ${formatValue(all, true)}`;
    wrap.append(row);
  }
  target.replaceChildren(legend, wrap);
}

function renderColumns(target, { columns, rows }) {
  const max = Math.max(...rows.map(([, value]) => Number(value)), 1);
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

function renderMap(target, { rows }) {
  if (!window.L) {
    target.replaceChildren(el("p", "muted", "The map needs an internet connection to load its tiles."));
    return;
  }
  if (!leafletMap) {
    const node = el("div", "map");
    target.replaceChildren(node);
    leafletMap = L.map(node, { scrollWheelZoom: false, zoomSnap: 0.1 }).fitBounds(UK_BOUNDS);
    L.tileLayer(TILES, {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 12,
    }).addTo(leafletMap);
    markerLayer = L.layerGroup().addTo(leafletMap);
  }

  markerLayer.clearLayers();
  const accent = getComputedStyle(document.documentElement).getPropertyValue("--accent").trim();
  const max = Math.max(...rows.map((row) => Number(row[4])), 1);
  for (const [town, area, latitude, longitude, leads] of rows) {
    const tooltip = el("div");
    tooltip.append(el("strong", "", `${town} (${area})`), el("div", "", `${formatValue(leads)} leads`));
    L.circleMarker([latitude, longitude], {
      radius: 3 + 22 * Math.sqrt(Number(leads) / max),
      color: accent,
      weight: 1.5,
      fillColor: accent,
      fillOpacity: 0.35,
    }).bindTooltip(tooltip).addTo(markerLayer);
  }
}

function renderPipeline(target, { rows }) {
  const wrap = el("div", "pipeline");
  LAYERS.forEach((layer, i) => {
    const stages = rows.filter(([name]) => name === layer);
    const headline = stages.at(-1);
    const tile = el("div", `layer layer-${layer}`);
    tile.append(
      el("div", "layer-name", layer),
      el("div", "layer-value", headline ? formatValue(headline[2]) : "—"),
      el("div", "layer-stage", headline ? headline[1] : "Not loaded yet"),
    );
    if (stages.length > 1) {
      const detail = el("ul", "layer-detail");
      stages.slice(0, -1).forEach(([, stage, count]) => detail.append(el("li", "", `${formatValue(count)} · ${stage}`)));
      tile.append(detail);
    }
    if (i > 0) wrap.append(el("div", "arrow", "→"));
    wrap.append(tile);
  });
  target.replaceChildren(wrap);
}

const renderers = {
  kpi: renderKpis,
  donut: renderDonut,
  bar: renderBars,
  rank: renderRank,
  compare: renderCompare,
  column: renderColumns,
  map: renderMap,
  pipeline: renderPipeline,
};

function cardFor(item) {
  if (!cards.has(item.key)) {
    const card = document.getElementById("card-template").content.firstElementChild.cloneNode(true);
    if (LAYOUT[item.key]) card.classList.add(LAYOUT[item.key]);
    card.querySelector("h2").textContent = item.title;
    document.getElementById("cards").append(card);
    cards.set(item.key, card.querySelector(".chart"));
  }
  return cards.get(item.key);
}

function renderFilters() {
  const nav = document.getElementById("filters");
  const options = [["ALL", "All industries"], ...[...state.industries].sort((a, b) => a[1].localeCompare(b[1]))];
  nav.replaceChildren(
    ...options.map(([code, name]) => {
      const button = el("button", "", name);
      button.type = "button";
      button.setAttribute("aria-pressed", String(code === state.industry));
      button.addEventListener("click", () => selectIndustry(code));
      return button;
    }),
  );
}

async function load() {
  const grid = document.getElementById("cards");
  const error = document.getElementById("error");
  grid.classList.add("loading");
  try {
    const response = await fetch(`/api/dashboard?industry=${encodeURIComponent(state.industry)}`);
    const body = await response.json();
    if (!response.ok) throw new Error(typeof body.detail === "string" ? body.detail : response.statusText);

    const industries = body.find((item) => item.key === "industries");
    if (industries) state.industries = industries.rows;
    renderFilters();
    for (const item of body) renderers[item.chart](cardFor(item), item);
    error.hidden = true;
  } catch (e) {
    error.textContent = `Could not load the dashboard: ${e.message}`;
    error.hidden = false;
  } finally {
    grid.classList.remove("loading");
  }
}

function selectIndustry(code) {
  state.industry = code;
  history.replaceState(null, "", code === "ALL" ? location.pathname : `#${code}`);
  load();
}

const fromHash = location.hash.slice(1).toUpperCase();
state.industry = /^[A-Z]$/.test(fromHash) ? fromHash : "ALL";
load();
