const state = {
  overview: null,
  docs: null,
  patternDocs: null,
};

const $ = (sel) => document.querySelector(sel);

function setStatus(msg, type = "info") {
  const box = $("#status-box");
  box.textContent = msg;
  box.dataset.type = type;
}

function formatNumber(value, digits = 2) {
  return new Intl.NumberFormat("es-CO", {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  }).format(Number(value));
}

function formatPct(value, digits = 2) {
  return `${formatNumber(Number(value) * 100, digits)}%`;
}

function cacheBust(url) {
  const sep = url.includes("?") ? "&" : "?";
  return `${url}${sep}t=${Date.now()}`;
}

async function fetchJson(url, options) {
  const response = await fetch(url, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || "Solicitud fallida.");
  return data;
}

function fillSelect(selector, symbols, preferred) {
  const select = $(selector);
  select.innerHTML = "";
  symbols.forEach((s) => {
    const opt = document.createElement("option");
    opt.value = s;
    opt.textContent = s;
    select.appendChild(opt);
  });
  if (preferred && symbols.includes(preferred)) select.value = preferred;
}

// ── Renderizado de resumen y ETL ──────────────────────────────────────────────

function renderOverview(overview) {
  state.overview = overview;
  $("#dataset-name").textContent = overview.source_file;
  $("#dataset-range").textContent = `${overview.date_min} / ${overview.date_max}`;
  $("#dataset-rows").textContent = new Intl.NumberFormat("es-CO").format(overview.rows);
  $("#dataset-symbols").textContent = overview.symbol_count;

  fillSelect("#symbol-a", overview.symbols, overview.symbols.includes("VOO") ? "VOO" : overview.symbols[0]);
  fillSelect("#symbol-b", overview.symbols, overview.symbols.includes("ECOPETROL.CL") ? "ECOPETROL.CL" : overview.symbols[1]);
  fillSelect("#candle-symbol", overview.symbols, overview.symbols.includes("VOO") ? "VOO" : overview.symbols[0]);

  const cloud = $("#symbol-cloud");
  cloud.innerHTML = "";
  overview.symbols.forEach((s) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "pill";
    btn.textContent = s;
    btn.addEventListener("click", () => {
      $("#candle-symbol").value = s;
      refreshCandlestick().catch(console.warn);
      refreshPatterns().catch(console.warn);
    });
    cloud.appendChild(btn);
  });

  renderPreview(overview.preview);
  renderEtlStats(overview.etl_report);
}

function renderPreview(rows) {
  const table = $("#preview-table");
  table.innerHTML = "";
  if (!rows || !rows.length) {
    table.innerHTML = "<tbody><tr><td>Sin datos.</td></tr></tbody>";
    return;
  }
  const headers = Object.keys(rows[0]);
  const thead = document.createElement("thead");
  const tr = document.createElement("tr");
  headers.forEach((h) => {
    const th = document.createElement("th");
    th.textContent = h;
    tr.appendChild(th);
  });
  thead.appendChild(tr);
  const tbody = document.createElement("tbody");
  rows.forEach((row) => {
    const bodyRow = document.createElement("tr");
    headers.forEach((h) => {
      const td = document.createElement("td");
      td.textContent = row[h] ?? "";
      bodyRow.appendChild(td);
    });
    tbody.appendChild(bodyRow);
  });
  table.append(thead, tbody);
}

function renderEtlStats(report) {
  const section = $("#etl-stats-section");
  if (!report || !report.activos) { section.style.display = "none"; return; }
  section.style.display = "";

  const note = $("#etl-method-note");
  const limpieza = report.limpieza || {};
  note.textContent = limpieza.metodo_faltantes || "";

  const tbody = $("#etl-tbody");
  tbody.innerHTML = "";
  const faltantes = (limpieza.faltantes_por_activo) || {};

  Object.entries(report.activos).forEach(([simbolo, stats]) => {
    const tr = document.createElement("tr");
    const imputados = faltantes[simbolo] ?? "-";
    tr.innerHTML = `
      <td><strong>${simbolo}</strong></td>
      <td>${stats.crudos}</td>
      <td class="${stats.descartados > 0 ? "td-warn" : ""}">${stats.descartados}</td>
      <td class="${imputados > 0 ? "td-info" : ""}">${imputados}</td>
      <td>${stats.limpios}</td>
    `;
    tbody.appendChild(tr);
  });

  if (report.errores && Object.keys(report.errores).length > 0) {
    Object.entries(report.errores).forEach(([simbolo, msg]) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `<td><strong>${simbolo}</strong></td><td colspan="4" class="td-error">${msg}</td>`;
      tbody.appendChild(tr);
    });
  }
}

// ── Renderizado de algoritmos ─────────────────────────────────────────────────

function renderDocs(docs) {
  const list = $("#algorithm-docs");
  list.innerHTML = "";
  Object.entries(docs).forEach(([name, doc]) => {
    const li = document.createElement("li");
    li.innerHTML = `
      <strong>${name}</strong>
      <span>${doc.time} tiempo &nbsp;·&nbsp; ${doc.space} espacio</span>
      <details class="pseudocode-details">
        <summary>Pseudocodigo y formula</summary>
        <code>${doc.formula}</code>
        ${doc.formula_band ? `<code>${doc.formula_band}</code>` : ""}
        ${doc.formula_norm ? `<code>${doc.formula_norm}</code>` : ""}
        <code class="pseudo">${doc.pseudocode}</code>
      </details>
    `;
    list.appendChild(li);
  });
}

function renderPatternDocs(docs) {
  state.patternDocs = docs;
  const box = $("#pattern-formulas");
  if (!box || !docs) return;
  box.innerHTML = "";
  Object.values(docs).forEach((doc) => {
    const div = document.createElement("div");
    div.className = "pattern-formula-card";
    div.innerHTML = `
      <strong>${doc.name}</strong>
      <code class="formula-formal">${doc.formal}</code>
      <span>${doc.description}</span>
      <span class="complexity-badge">${doc.complexity}</span>
    `;
    box.appendChild(div);
  });
}

// ── Renderizado de similitud ──────────────────────────────────────────────────

function renderSimilarity(data) {
  const container = $("#similarity-metrics");
  const m = data.metrics;
  const cards = [
    ["Euclidiana precios", m.euclidean_prices, "cruda — sensible a escala"],
    ["Euclidiana Z-norm", m.euclidean_prices_norm, "normalizada Z-score — escala comparable"],
    ["Euclidiana retornos", m.euclidean_returns, "sobre retornos diarios"],
    ["Pearson retornos", m.pearson_returns, "correlacion lineal [−1, 1]"],
    ["DTW completo", m.dtw_returns, `O(n·m) — distorsion temporal`],
    [`DTW Sakoe w=${m.dtw_band_width}`, m.dtw_returns_band, `O(n·w) — banda reducida`],
    ["Coseno retornos", m.cosine_returns, "similitud angular [−1, 1]"],
  ];
  container.innerHTML = "";
  cards.forEach(([label, value, hint]) => {
    const card = document.createElement("article");
    card.className = "metric-card";
    card.title = hint;
    card.innerHTML = `<span>${label}</span><strong>${formatNumber(value, 6)}</strong><em>${hint}</em>`;
    container.appendChild(card);
  });
}

// ── Renderizado de riesgo ─────────────────────────────────────────────────────

function renderRisk(items) {
  const tbody = $("#risk-table");
  tbody.innerHTML = "";
  items.slice(0, 15).forEach((item) => {
    const sharpeClass = item.sharpe_ratio >= 1 ? "sharpe-good" : item.sharpe_ratio >= 0 ? "sharpe-mid" : "sharpe-bad";
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${item.symbol}</td>
      <td>${formatPct(item.annual_volatility)}</td>
      <td>${formatPct(item.annual_return)}</td>
      <td><span class="${sharpeClass}">${formatNumber(item.sharpe_ratio, 2)}</span></td>
      <td><span class="risk ${item.risk_category}">${item.risk_category}</span></td>
    `;
    tbody.appendChild(tr);
  });
}

// ── Renderizado de patrones ───────────────────────────────────────────────────

function renderPatterns(data) {
  const box = $("#patterns-box");
  const p = data.patterns;
  box.innerHTML = `
    <article class="pattern-item">
      <span>P1 · ${p.k} dias positivos consecutivos</span>
      <strong>${p.positive_streak_k}</strong>
    </article>
    <article class="pattern-item">
      <span>P2 · ${p.k} negativos + rebote ≥ ${formatPct(p.rebound_threshold)}</span>
      <strong>${p.negative_then_strong_rebound}</strong>
    </article>
  `;
}

// ── Renderizado de tabla de correlacion ──────────────────────────────────────

function renderCorrelationTable(data) {
  const wrap = $("#correlation-table-wrap");
  const { symbols, matrix } = data;
  if (!symbols || !matrix) { wrap.innerHTML = ""; return; }

  let html = "<table class='corr-table'><thead><tr><th></th>";
  symbols.forEach((s) => { html += `<th>${s}</th>`; });
  html += "</tr></thead><tbody>";

  matrix.forEach((row, i) => {
    html += `<tr><th>${symbols[i]}</th>`;
    row.forEach((val) => {
      const v = Number(val).toFixed(2);
      const cls = val > 0.7 ? "corr-high" : val < -0.3 ? "corr-neg" : val === 1 ? "corr-self" : "";
      html += `<td class="${cls}">${v}</td>`;
    });
    html += "</tr>";
  });
  html += "</tbody></table>";
  wrap.innerHTML = html;
}

// ── Funciones de carga y refresco ────────────────────────────────────────────

async function loadOverview() {
  const overview = await fetchJson("/dataset/overview");
  renderOverview(overview);
  setStatus(`Dataset listo: ${overview.symbol_count} activos, ${overview.rows} filas.`);
}

async function loadDocs() {
  const docs = await fetchJson("/algorithm-docs");
  state.docs = docs;
  renderDocs(docs);
}

async function loadPatternDocs() {
  const docs = await fetchJson("/pattern-docs");
  renderPatternDocs(docs);
}

async function refreshSimilarity() {
  const symbolA = $("#symbol-a").value;
  const symbolB = $("#symbol-b").value;
  const data = await fetchJson("/similarity", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ symbol_a: symbolA, symbol_b: symbolB }),
  });
  renderSimilarity(data);
  const q = `symbol_a=${encodeURIComponent(symbolA)}&symbol_b=${encodeURIComponent(symbolB)}`;
  $("#series-plot").src = cacheBust(`/plot/series.png?${q}`);
  $("#returns-plot").src = cacheBust(`/plot/returns.png?${q}`);
  $("#download-report").href = `/report.pdf?${q}`;
}

async function refreshCandlestick() {
  const symbol = $("#candle-symbol").value;
  const shortWindow = $("#short-window").value;
  const longWindow = $("#long-window").value;
  $("#candlestick-plot").src = cacheBust(
    `/plot/candlestick.png?symbol=${encodeURIComponent(symbol)}&short_window=${shortWindow}&long_window=${longWindow}`
  );
}

async function refreshRisk() {
  const data = await fetchJson("/risk");
  renderRisk(data.items);
  $("#risk-plot").src = cacheBust("/plot/risk.png");
}

async function refreshPatterns() {
  const symbol = $("#candle-symbol").value;
  const k = $("#pattern-k").value;
  const threshold = $("#rebound-threshold").value;
  const data = await fetchJson(
    `/patterns?symbol=${encodeURIComponent(symbol)}&k=${k}&threshold=${threshold}`
  );
  renderPatterns(data);
}

async function refreshCorrelation() {
  $("#correlation-plot").src = cacheBust("/plot/correlation.png");
  const data = await fetchJson("/correlation");
  renderCorrelationTable(data);
}

async function runDashboard(event) {
  if (event) event.preventDefault();
  setStatus("Ejecutando metricas y generando graficas...");
  const warn = (label) => (err) => console.warn(`${label}:`, err.message);
  await Promise.allSettled([
    refreshSimilarity().catch(warn("similitud")),
    refreshCandlestick().catch(warn("velas")),
    refreshRisk().catch(warn("riesgo")),
    refreshPatterns().catch(warn("patrones")),
    refreshCorrelation().catch(warn("correlacion")),
  ]);
  setStatus("Analisis actualizado.");
}

async function rebuildDataset() {
  setStatus("Reconstruyendo dataset desde Yahoo Finance. Puede tardar varios minutos...");
  const data = await fetchJson("/dataset/build", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ years: 5, nombre_archivo: "dataset_maestro.csv" }),
  });
  await loadOverview();
  await runDashboard();
  setStatus(`ETL completado: ${data.rows} filas generadas.`);
}

// ── Eventos ───────────────────────────────────────────────────────────────────

$("#controls").addEventListener("submit", runDashboard);

$("#refresh-overview").addEventListener("click", async () => {
  try {
    await loadOverview();
    await runDashboard();
  } catch (err) {
    setStatus(err.message, "error");
  }
});

$("#build-dataset").addEventListener("click", async () => {
  try {
    await rebuildDataset();
  } catch (err) {
    setStatus(err.message, "error");
  }
});

// ── Bootstrap ─────────────────────────────────────────────────────────────────

async function bootstrap() {
  try {
    await Promise.all([loadDocs(), loadPatternDocs()]);
    await loadOverview();
    await runDashboard();
  } catch (err) {
    setStatus(err.message, "error");
  }
}

bootstrap();
