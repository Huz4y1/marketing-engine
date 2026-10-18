const numberFormat = new Intl.NumberFormat("en-GB");
const percentFormat = new Intl.NumberFormat("en-GB", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
const LAYERS = ["bronze", "silver", "gold"];
const TILES = "https://tile.openstreetmap.org/{z}/{x}/{y}.png";
const UK_BOUNDS = [[50.3, -6.0], [57.6, 1.4]];

const state = { industry: null, industries: [] };
const cards = new Map();
let leafletMap;
let markerLayer;

function endpoint(path, params = {}) {
  const query = new URLSearchParams(Object.entries(params).filter(([, value]) => value !== null && value !== undefined)).toString();
  return query ? `${path}?${query}` : path;
}

const CHARTS = [
  { key: "overview", title: "Overview", layout: "full", url: (industry) => endpoint("/api/overview", { industry }), render: renderKpis },
  { key: "reachability", title: "Reachability", url: (industry) => endpoint("/api/overview", { industry }), render: renderReachability },
  { key: "email", title: "Email type", url: (industry) => endpoint("/api/breakdowns/email-type", { industry }), render: renderDonut },
  { key: "size", title: "Company size", url: (industry) => endpoint("/api/breakdowns/company-size", { industry }), render: renderDonut },
  { key: "map", title: "Lead locations", layout: "double", url: (industry) => endpoint("/api/locations", { industry }), render: renderMap },
  { key: "towns", title: "Top towns", url: (industry) => endpoint("/api/towns", { industry, limit: 10 }), render: renderBars },
  { key: "industries", title: "Leads by industry", url: () => "/api/industries", render: (target, rows) => renderRank(target, rows, "leads") },
  { key: "tps", title: "TPS-registered rate by industry", url: () => "/api/industries", render: (target, rows) => renderRank(target, rows, "tps_rate", true) },
  { key: "turnover", title: "Turnover profile vs all industries", url: (industry) => endpoint("/api/turnover/comparison", { industry }), render: renderCompare },
  { key: "divisions", title: "Top SIC divisions", layout: "double", url: (industry) => endpoint("/api/breakdowns/sic-division", { industry, limit: 8 }), render: renderBars },
  { key: "roles", title: "Contact job roles", url: (industry) => endpoint("/api/breakdowns/job-role", { industry }), render: renderBars },
  { key: "incorporations", title: "Companies incorporated per year", layout: "full", url: (industry) => endpoint("/api/incorporations", { industry }), render: renderColumns },
  { key: "pipeline", title: "How the data was built", layout: "full", url: () => "/api/pipeline/stages", render: renderPipeline },
];

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function formatValue(value, percent = false) {
  if (value === null || value === undefined) return "—";
  return percent ? `${percentFormat.format(value)}%` : numberFormat.format(value);
}

function share(value, total) {
  return total ? (100 * Number(value)) / total : 0;
}

function industryName(code) {
  return state.industries.find((industry) => industry.sector_code === code)?.industry ?? "All industries";
}

function bar(width, className = "bar") {
  const node = el("div", className);
  node.style.width = `${Math.max(width, 0)}%`;
  return node;
}

function barRow(label, content, selected = false) {
  const row = el("div", selected ? "bar-row selected" : "bar-row");
  row.append(el("span", "bar-label", label ?? "—"), content);
  return row;
}

function renderKpis(target, overview) {
  const tiles = [
    ["Leads", formatValue(overview.leads)],
    ["Companies", formatValue(overview.companies)],
    ["Callable leads", formatValue(overview.callable_leads)],
    ["TPS registered", formatValue(overview.tps_rate, true)],
  ];
  const wrap = el("div", "kpis");
  for (const [label, value] of tiles) {
    const tile = el("div");
    tile.append(el("div", "kpi-label", label), el("div", "kpi-value", value));
    wrap.append(tile);
  }
  target.replaceChildren(wrap);
}

function renderReachability(target, overview) {
  renderDonut(target, [
    { label: "Callable", leads: overview.callable_leads },
    { label: "TPS registered", leads: overview.tps_leads },
  ]);
}

function renderDonut(target, slices) {
  const total = slices.reduce((sum, slice) => sum + Number(slice.leads || 0), 0);
  const stops = [];
  let angle = 0;
  slices.forEach((slice, i) => {
    const sweep = total ? (Number(slice.leads || 0) / total) * 360 : 0;
    const gap = slices.length > 1 && sweep > 3 ? 1.5 : 0;
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
  slices.forEach((slice, i) => {
    const item = el("li");
    const swatch = el("span", "swatch");
    swatch.style.background = `var(--c${i + 1})`;
    item.title = `${slice.label}: ${formatValue(slice.leads)} leads`;
    item.append(
      swatch,
      el("span", "legend-label", slice.label),
      el("span", "legend-value", formatValue(share(slice.leads, total), true)),
      el("span", "legend-count", formatValue(slice.leads)),
    );
    legend.append(item);
  });

  const wrap = el("div", "donut-wrap");
  wrap.append(donut, legend);
  target.replaceChildren(wrap);
}

function renderBars(target, rows) {
  const max = Math.max(...rows.map((row) => Number(row.leads)), 1);
  const wrap = el("div", "bars");
  for (const row of rows) {
    const track = el("div", "bar-track");
    track.append(bar((Number(row.leads) / max) * 82), el("span", "bar-value", formatValue(row.leads)));
    const line = barRow(row.label, track);
    line.title = `${row.label}: ${formatValue(row.leads)}`;
    wrap.append(line);
  }
  target.replaceChildren(wrap);
}

function renderRank(target, industries, key, percent = false) {
  const rows = [...industries].sort((a, b) => Number(b[key]) - Number(a[key]));
  const max = Math.max(...rows.map((row) => Number(row[key])), 1);
  const wrap = el("div", "bars");
  for (const row of rows) {
    const highlighted = state.industry === null || state.industry === row.sector_code;
    const track = el("div", "bar-track");
    track.append(bar((Number(row[key]) / max) * 82, highlighted ? "bar" : "bar dimmed"), el("span", "bar-value", formatValue(row[key], percent)));
    const line = barRow(row.industry, track, state.industry === row.sector_code);
    line.title = `${row.industry}: ${formatValue(row[key], percent)}`;
    wrap.append(line);
  }
  target.replaceChildren(wrap);
}

function renderCompare(target, rows) {
  const comparing = state.industry !== null;
  const max = Math.max(...rows.flatMap((row) => [Number(row.selected_pct), Number(row.all_pct)]), 1);
  const series = comparing
    ? [[industryName(state.industry), "var(--accent)"], ["All industries", "var(--benchmark)"]]
    : [["All industries", "var(--accent)"]];

  const legend = el("ul", "legend");
  for (const [name, color] of series) {
    const item = el("li");
    const swatch = el("span", "swatch");
    swatch.style.background = color;
    item.append(swatch, el("span", "", name));
    legend.append(item);
  }

  const wrap = el("div", "bars");
  for (const row of rows) {
    const primary = comparing ? row.selected_pct : row.all_pct;
    const pair = el("div", "bar-pair");
    const main = el("div", "bar-track");
    main.append(bar((Number(primary) / max) * 82), el("span", "bar-value", formatValue(primary, true)));
    pair.append(main);
    if (comparing) {
      const benchmark = el("div", "bar-track");
      benchmark.append(bar((Number(row.all_pct) / max) * 82, "bar benchmark"), el("span", "bar-value", formatValue(row.all_pct, true)));
      pair.append(benchmark);
    }
    const line = barRow(row.turnover_band, pair);
    line.title = comparing
      ? `${row.turnover_band}: ${formatValue(row.selected_pct, true)} vs ${formatValue(row.all_pct, true)} across all industries`
      : `${row.turnover_band}: ${formatValue(row.all_pct, true)}`;
    wrap.append(line);
  }
  target.replaceChildren(legend, wrap);
}

function renderColumns(target, rows) {
  const max = Math.max(...rows.map((row) => Number(row.companies)), 1);
  const plot = el("div", "columns");
  for (const row of rows) {
    const column = el("div", "column");
    column.style.height = `${(Number(row.companies) / max) * 100}%`;
    column.title = `${row.year}: ${formatValue(row.companies)} companies`;
    plot.append(column);
  }
  const axis = el("div", "column-axis");
  axis.append(el("span", "", rows[0]?.year ?? ""), el("span", "", rows.at(-1)?.year ?? ""));
  target.replaceChildren(plot, axis);
}

function renderMap(target, rows) {
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
  const max = Math.max(...rows.map((row) => Number(row.leads)), 1);
  for (const row of rows) {
    const tooltip = el("div");
    tooltip.append(el("strong", "", `${row.town} (${row.postcode_area})`), el("div", "", `${formatValue(row.leads)} leads`));
    L.circleMarker([row.latitude, row.longitude], {
      radius: 3 + 22 * Math.sqrt(Number(row.leads) / max),
      color: accent,
      weight: 1.5,
      fillColor: accent,
      fillOpacity: 0.35,
    }).bindTooltip(tooltip).addTo(markerLayer);
  }
}

function renderPipeline(target, stages) {
  const wrap = el("div", "pipeline");
  LAYERS.forEach((layer, i) => {
    const layerStages = stages.filter((stage) => stage.layer === layer);
    const headline = layerStages.at(-1);
    const tile = el("div", `layer layer-${layer}`);
    tile.append(
      el("div", "layer-name", layer),
      el("div", "layer-value", headline ? formatValue(headline.row_count) : "—"),
      el("div", "layer-stage", headline ? headline.stage : "Not loaded yet"),
    );
    if (layerStages.length > 1) {
      const detail = el("ul", "layer-detail");
      layerStages.slice(0, -1).forEach((stage) => detail.append(el("li", "", `${formatValue(stage.row_count)} · ${stage.stage}`)));
      tile.append(detail);
    }
    if (i > 0) wrap.append(el("div", "arrow", "→"));
    wrap.append(tile);
  });
  target.replaceChildren(wrap);
}

function cardFor(chart) {
  if (!cards.has(chart.key)) {
    const card = document.getElementById("card-template").content.firstElementChild.cloneNode(true);
    if (chart.layout) card.classList.add(chart.layout);
    card.querySelector("h2").textContent = chart.title;
    document.getElementById("cards").append(card);
    cards.set(chart.key, card.querySelector(".chart"));
  }
  return cards.get(chart.key);
}

function renderFilters() {
  const options = [
    [null, "All industries"],
    ...state.industries.map((industry) => [industry.sector_code, industry.industry]).sort((a, b) => a[1].localeCompare(b[1])),
  ];
  document.getElementById("filters").replaceChildren(
    ...options.map(([code, name]) => {
      const button = el("button", "", name);
      button.type = "button";
      button.setAttribute("aria-pressed", String(code === state.industry));
      button.addEventListener("click", () => selectIndustry(code));
      return button;
    }),
  );
}

async function fetchJSON(url) {
  const response = await fetch(url);
  const body = await response.json();
  if (!response.ok) throw new Error(typeof body.detail === "string" ? body.detail : `${response.status} ${response.statusText}`);
  return body;
}

async function load() {
  const grid = document.getElementById("cards");
  const error = document.getElementById("error");
  grid.classList.add("loading");
  try {
    const urls = [...new Set(["/api/industries", ...CHARTS.map((chart) => chart.url(state.industry))])];
    const results = await Promise.all(urls.map(fetchJSON));
    const responses = Object.fromEntries(urls.map((url, i) => [url, results[i]]));

    state.industries = responses["/api/industries"];
    renderFilters();
    for (const chart of CHARTS) chart.render(cardFor(chart), responses[chart.url(state.industry)]);
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
  history.replaceState(null, "", code === null ? location.pathname : `#${code}`);
  load();
}

const fromHash = location.hash.slice(1).toUpperCase();
state.industry = /^[A-Z]$/.test(fromHash) ? fromHash : null;
load();
