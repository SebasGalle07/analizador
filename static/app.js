const state = {
  overview: null,
  algorithms: [],
};

const $ = (selector) => document.querySelector(selector);

function setStatus(message, type = "info") {
  const box = $("#status-box");
  box.textContent = message;
  box.dataset.type = type;
}

function formatNumber(value) {
  return new Intl.NumberFormat("es-CO").format(value);
}

function formatMs(value) {
  return `${Number(value).toFixed(4)} ms`;
}

function renderAlgorithms(algorithms) {
  const container = $("#algorithm-list");
  container.innerHTML = "";

  algorithms.forEach((name) => {
    const label = document.createElement("label");
    label.className = "algorithm-option";

    const input = document.createElement("input");
    input.type = "checkbox";
    input.name = "algoritmos";
    input.value = name;
    input.checked = true;

    const text = document.createElement("span");
    text.textContent = name;

    label.append(input, text);
    container.appendChild(label);
  });
}

function renderSymbolOptions(symbols) {
  const select = $("#symbol-select");
  select.innerHTML = "";

  symbols.forEach((symbol) => {
    const option = document.createElement("option");
    option.value = symbol;
    option.textContent = symbol;
    select.appendChild(option);
  });

  if (symbols.includes("VOO")) {
    select.value = "VOO";
  }
}

function renderSymbolCloud(symbols) {
  const cloud = $("#symbol-cloud");
  cloud.innerHTML = "";

  symbols.forEach((symbol) => {
    const pill = document.createElement("span");
    pill.className = "pill";
    pill.textContent = symbol;
    cloud.appendChild(pill);
  });
}

function renderOverview(overview) {
  state.overview = overview;
  $("#dataset-path").value = overview.source_file;
  $("#hero-dataset-name").textContent = overview.source_file;
  $("#hero-dataset-range").textContent =
    `${overview.date_min} a ${overview.date_max}`;
  $("#stat-rows").textContent = formatNumber(overview.rows);
  $("#stat-columns").textContent = formatNumber(overview.columns);
  $("#stat-symbols").textContent = formatNumber(overview.symbol_count);
  $("#stat-range").textContent = `${overview.date_min} / ${overview.date_max}`;
  renderSymbolOptions(overview.symbols);
  renderSymbolCloud(overview.symbols);
  renderPreviewTable(overview.preview);
}

function renderPreviewTable(rows) {
  const table = $("#preview-table");
  table.innerHTML = "";

  if (!rows || !rows.length) {
    table.innerHTML = "<tbody><tr><td class='empty-row'>Sin datos para vista previa.</td></tr></tbody>";
    return;
  }

  const headers = Object.keys(rows[0]);
  const thead = document.createElement("thead");
  const headRow = document.createElement("tr");
  headers.forEach((header) => {
    const th = document.createElement("th");
    th.textContent = header;
    headRow.appendChild(th);
  });
  thead.appendChild(headRow);

  const tbody = document.createElement("tbody");
  rows.forEach((row) => {
    const tr = document.createElement("tr");
    headers.forEach((header) => {
      const td = document.createElement("td");
      td.textContent = row[header] ?? "";
      if (header === "Fecha") {
        td.className = "mono";
      }
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });

  table.append(thead, tbody);
}

function renderBenchmark(rows) {
  const body = $("#benchmark-body");
  body.innerHTML = "";

  if (!rows.length) {
    body.innerHTML = "<tr><td colspan='3' class='empty-row'>No hubo benchmark para mostrar.</td></tr>";
    return;
  }

  const sorted = [...rows].sort((a, b) => a.tiempo_ms - b.tiempo_ms);
  const maxTime = Math.max(...sorted.map((item) => item.tiempo_ms), 1);

  sorted.forEach((item) => {
    const tr = document.createElement("tr");
    const width = Math.max((item.tiempo_ms / maxTime) * 100, 4);

    tr.innerHTML = `
      <td>${item.algoritmo}</td>
      <td>${formatMs(item.tiempo_ms)}</td>
      <td class="bar-cell">
        <div class="bar-track">
          <div class="bar-fill" style="width: ${width}%"></div>
        </div>
      </td>
    `;
    body.appendChild(tr);
  });
}

function renderTopVolume(rows, symbol) {
  const body = $("#top-volume-body");
  body.innerHTML = "";

  if (!rows.length) {
    body.innerHTML = "<tr><td colspan='4' class='empty-row'>No hubo resultados para top volumen.</td></tr>";
    return;
  }

  rows.forEach((row, index) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${index + 1}</td>
      <td class="mono">${row.Fecha}</td>
      <td>${row[`${symbol}_Close`] ?? "-"}</td>
      <td>${formatNumber(row[`${symbol}_Volume`] ?? 0)}</td>
    `;
    body.appendChild(tr);
  });
}

async function loadAlgorithms() {
  const response = await fetch("/algorithms");
  if (!response.ok) {
    throw new Error("No se pudo obtener la lista de algoritmos.");
  }
  const data = await response.json();
  state.algorithms = data.algorithms;
  renderAlgorithms(data.algorithms);
}

async function loadOverview() {
  const datasetPath = $("#dataset-path").value.trim();
  const url = datasetPath
    ? `/dataset/overview?ruta_archivo=${encodeURIComponent(datasetPath)}`
    : "/dataset/overview";

  const response = await fetch(url);
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "No se pudo cargar el resumen del dataset.");
  }

  const overview = await response.json();
  renderOverview(overview);
  setStatus(
    `Dataset cargado: ${overview.source_file} con ${formatNumber(overview.rows)} filas y ${overview.symbol_count} activos.`
  );
}

function getSelectedAlgorithms() {
  return Array.from(document.querySelectorAll("input[name='algoritmos']:checked"))
    .map((input) => input.value);
}

async function runAnalysis(event) {
  event.preventDefault();
  const ruta_archivo = $("#dataset-path").value.trim() || null;
  const simbolo = $("#symbol-select").value;
  const top_n = Number($("#top-n").value);
  const algoritmos = getSelectedAlgorithms();

  setStatus(`Ejecutando analisis para ${simbolo}...`);

  const response = await fetch("/dataset/analyze", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      ruta_archivo,
      simbolo,
      top_n,
      algoritmos,
    }),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "No se pudo ejecutar el analisis.");
  }

  renderBenchmark(data.benchmark);
  renderTopVolume(data.top_n, simbolo);
  setStatus(
    `Analisis completo para ${simbolo}. Benchmark ejecutado con ${data.benchmark.length} algoritmos sobre ${formatNumber(data.rows)} filas.`
  );
}

async function bootstrap() {
  try {
    setStatus("Cargando configuracion inicial...");
    await loadAlgorithms();
    await loadOverview();
  } catch (error) {
    setStatus(error.message, "error");
  }
}

$("#analysis-form").addEventListener("submit", async (event) => {
  try {
    await runAnalysis(event);
  } catch (error) {
    setStatus(error.message, "error");
  }
});

$("#refresh-overview").addEventListener("click", async () => {
  try {
    setStatus("Actualizando resumen del dataset...");
    await loadOverview();
  } catch (error) {
    setStatus(error.message, "error");
  }
});

bootstrap();
