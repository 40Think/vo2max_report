const state = {
  clientId: null,
  measurementId: null,
  workspace: null,
  charts: null,
  zones: [],
  selectedItemId: null,
};

const $ = (id) => document.getElementById(id);

async function request(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || "Request failed");
  }
  return payload;
}

function setStatus(id, text) {
  $(id).textContent = text;
}

function setText(id, text) {
  const element = $(id);
  if (element) {
    element.textContent = text;
  }
}

async function createClient() {
  const client = await request("/clients", {
    method: "POST",
    body: JSON.stringify({
      first_name: $("firstName").value,
      last_name: $("lastName").value,
    }),
  });
  state.clientId = client.id;
  state.measurementId = null;
  state.workspace = null;
  state.charts = null;
  state.zones = [];
  state.selectedItemId = null;
  setStatus("clientStatus", `Создан клиент: ${client.full_name}`);
  renderReportLinks([]);
  renderWorkspace();
}

async function importTest() {
  if (!state.clientId) {
    setStatus("importStatus", "Сначала создайте клиента");
    return;
  }
  const measurement = await request(`/clients/${state.clientId}/measurements`, {
    method: "POST",
    body: JSON.stringify({
      source_path: $("csvPath").value,
      measurement_date: $("testDate").value,
      activity_type: $("activityType").value,
      title: "Imported test",
    }),
  });
  state.measurementId = measurement.id;
  setStatus("importStatus", `Импортировано строк: ${measurement.items_count}`);
  await loadWorkspace();
}

async function uploadTest() {
  if (!state.clientId) {
    setStatus("importStatus", "Сначала создайте клиента");
    return;
  }
  const file = $("csvFile").files[0];
  if (!file) {
    setStatus("importStatus", "Выберите CSV-файл");
    return;
  }
  const contentBase64 = await readFileAsBase64(file);
  const measurement = await request(`/clients/${state.clientId}/measurements/upload`, {
    method: "POST",
    body: JSON.stringify({
      filename: file.name,
      content_base64: contentBase64,
      measurement_date: $("testDate").value,
      activity_type: $("activityType").value,
      title: file.name,
    }),
  });
  state.measurementId = measurement.id;
  setStatus("importStatus", `Загружено строк: ${measurement.items_count}`);
  await loadWorkspace();
}

async function createManualMeasurement() {
  if (!state.clientId) {
    setStatus("manualEntryStatus", "Сначала создайте клиента");
    return null;
  }
  const measurement = await request(`/clients/${state.clientId}/measurements/manual`, {
    method: "POST",
    body: JSON.stringify({
      measurement_date: $("testDate").value,
      activity_type: $("activityType").value,
      title: "Manual test",
    }),
  });
  state.measurementId = measurement.id;
  return measurement;
}

async function addManualRow() {
  if (!state.clientId) {
    setStatus("manualEntryStatus", "Сначала создайте клиента");
    return;
  }
  if (!state.measurementId) {
    await createManualMeasurement();
  }
  if (!state.measurementId) {
    return;
  }

  const payload = {
    time_sec: numericInputValue("manualTimeSec", true),
    power: numericInputValue("manualPower"),
    hr: numericInputValue("manualHr"),
    vo2_ml_kg_min: numericInputValue("manualVo2"),
    ve: numericInputValue("manualVe"),
    lactate: numericInputValue("manualLactate"),
  };
  await request(`/measurements/${state.measurementId}/items`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
  clearManualEntry();
  setStatus("manualEntryStatus", "Строка добавлена");
  await loadWorkspace();
}

function numericInputValue(id, required = false) {
  const value = $(id).value.trim();
  if (!value) {
    if (required) {
      throw new Error("Укажите время точки в секундах");
    }
    return null;
  }
  const number = Number(value);
  if (!Number.isFinite(number)) {
    throw new Error(`Некорректное число: ${value}`);
  }
  return number;
}

function clearManualEntry() {
  for (const id of ["manualTimeSec", "manualPower", "manualHr", "manualVo2", "manualVe", "manualLactate"]) {
    $(id).value = "";
  }
}

function readFileAsBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const value = String(reader.result || "");
      resolve(value.includes(",") ? value.split(",", 2)[1] : value);
    };
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
}

async function loadWorkspace(measurementId = state.measurementId) {
  if (!state.clientId || !measurementId) {
    return;
  }
  state.measurementId = measurementId;
  state.workspace = await request(`/clients/${state.clientId}/measurements/${state.measurementId}`);
  state.charts = await request(`/clients/${state.clientId}/measurements/${state.measurementId}/charts`);
  state.zones = await request(`/measurements/${state.measurementId}/zones`);
  if (!state.workspace.table_rows.some((row) => row.id === state.selectedItemId)) {
    state.selectedItemId = state.workspace.table_rows[0]?.id || null;
  }
  renderWorkspace();
}

function renderWorkspace() {
  renderSummary();
  renderHistory();
  renderTable();
  renderCharts();
  renderZones();
}

function renderSummary() {
  if (!state.workspace) {
    setText("topClientName", "Клиент не выбран");
    setText("topTestMeta", "Создайте клиента и загрузите CSV");
    setText("workspaceTitle", "Импортируйте тест");
    setText("metricHr", "-");
    setText("metricVo2", "-");
    setText("metricPower", "-");
    setText("metricThreshold", "-");
    return;
  }

  const rows = state.workspace.table_rows || [];
  const measurement = state.workspace.active_measurement || {};
  setText("topClientName", state.workspace.client.full_name);
  setText("topTestMeta", `${measurement.measurement_date || measurement.date || "-"} · ${measurement.activity_type || "activity"} · ${rows.length} строк`);
  setText("workspaceTitle", state.workspace.client.full_name);
  setText("metricHr", formatMetric(maxValue(rows, "hr"), 0));
  setText("metricVo2", formatMetric(maxValue(rows, "vo2_ml_kg_min"), 1));
  setText("metricPower", formatMetric(maxValue(rows, "power"), 0));
  setText("metricThreshold", thresholdSummary(rows));
}

function maxValue(rows, field) {
  const values = rows
    .map((row) => row[field])
    .filter((value) => typeof value === "number" && Number.isFinite(value));
  return values.length ? Math.max(...values) : null;
}

function formatMetric(value, digits) {
  return value == null ? "-" : value.toFixed(digits);
}

function thresholdSummary(rows) {
  const selected = rows.find((row) => row.id === state.selectedItemId && row.sport_parameter);
  const first = selected || rows.find((row) => row.sport_parameter);
  if (!first) {
    return "-";
  }
  return `${String(first.sport_parameter).toUpperCase()} ${first.hr ?? "-"} bpm`;
}

function renderHistory() {
  const history = $("history");
  history.innerHTML = "";
  const items = state.workspace?.history || [];
  if (items.length === 0) {
    history.textContent = "Пока нет тестов";
    history.classList.add("empty");
    return;
  }
  history.classList.remove("empty");
  for (const measurement of items) {
    const button = document.createElement("button");
    button.textContent = `${measurement.date} · ${measurement.activity_type} · ${measurement.items_count} строк`;
    button.className = measurement.id === state.measurementId ? "active" : "";
    button.addEventListener("click", () => loadWorkspace(measurement.id));
    history.appendChild(button);
  }
}

function renderTable() {
  const table = $("measurementTable");
  const head = table.querySelector("thead");
  const body = table.querySelector("tbody");
  head.innerHTML = "";
  body.innerHTML = "";

  if (!state.workspace) {
    body.innerHTML = '<tr><td class="empty-table">Создайте клиента и импортируйте CSV</td></tr>';
    renderCharts();
    renderZones();
    return;
  }

  $("startPower").value = state.workspace.active_measurement.start_power ?? "";
  $("powerStep").value = state.workspace.active_measurement.power_step ?? "";

  const columns = state.workspace.table_columns;
  const headerRow = document.createElement("tr");
  for (const column of columns) {
    const th = document.createElement("th");
    th.textContent = column.unit ? `${column.label}, ${column.unit}` : column.label;
    headerRow.appendChild(th);
  }
  head.appendChild(headerRow);

  for (const row of state.workspace.table_rows) {
    const tr = document.createElement("tr");
    const classes = [];
    if (row.id === state.selectedItemId) classes.push("selected");
    if (!row.use_in_report) classes.push("excluded");
    if (row.sport_parameter) classes.push(`threshold-${row.sport_parameter}`);
    tr.className = classes.join(" ");
    tr.addEventListener("click", () => {
      state.selectedItemId = row.id;
      renderWorkspace();
    });
    for (const column of columns) {
      const td = document.createElement("td");
      td.appendChild(createCell(row, column));
      tr.appendChild(td);
    }
    body.appendChild(tr);
  }
}

function createCell(row, column) {
  if (!column.editable) {
    const span = document.createElement("span");
    span.textContent = row[column.field] ?? "";
    return span;
  }

  if (column.field === "use_in_report") {
    const input = document.createElement("input");
    input.type = "checkbox";
    input.checked = Boolean(row[column.field]);
    input.addEventListener("change", () => updateItem(row.id, { use_in_report: input.checked }));
    return input;
  }

  if (column.field === "sport_parameter") {
    const select = document.createElement("select");
    for (const value of ["", "mam", "aep", "anp", "do2", "vo2max"]) {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = value || "-";
      select.appendChild(option);
    }
    select.value = row[column.field] || "";
    select.addEventListener("change", () => {
      if (select.value) {
        setThreshold(row.id, select.value);
      } else {
        updateItem(row.id, { sport_parameter: null });
      }
    });
    return select;
  }

  const input = document.createElement("input");
  input.type = "number";
  input.step = "any";
  input.value = row[column.field] ?? "";
  input.addEventListener("change", () => {
    updateItem(row.id, { [column.field]: input.value === "" ? null : Number(input.value) });
  });
  return input;
}

async function updateItem(itemId, payload) {
  await request(`/measurements/${state.measurementId}/items/${itemId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
  await loadWorkspace();
}

async function setThreshold(itemId, parameter) {
  await request(`/measurements/${state.measurementId}/thresholds`, {
    method: "POST",
    body: JSON.stringify({ item_id: itemId, parameter }),
  });
  state.selectedItemId = itemId;
  await loadWorkspace();
}

async function savePower() {
  await request(`/measurements/${state.measurementId}/power`, {
    method: "PATCH",
    body: JSON.stringify({
      start_power: $("startPower").value === "" ? null : Number($("startPower").value),
      power_step: $("powerStep").value === "" ? null : Number($("powerStep").value),
    }),
  });
  await loadWorkspace();
}

async function applySampling() {
  await request(`/measurements/${state.measurementId}/sampling`, {
    method: "POST",
    body: JSON.stringify({ every_n: Number($("sampleEvery").value) }),
  });
  await loadWorkspace();
}

function ensureMeasurementSelected() {
  if (!state.measurementId) {
    setStatus("importStatus", "Сначала импортируйте тест");
    return false;
  }
  return true;
}

function previewReport() {
  if (!ensureMeasurementSelected()) return;
  window.open(`/measurements/${state.measurementId}/report-preview`, "_blank", "noopener");
}

async function generateReports() {
  if (!ensureMeasurementSelected()) return;
  const result = await request(`/measurements/${state.measurementId}/reports`, {
    method: "POST",
    body: JSON.stringify({}),
  });
  renderReportLinks(result.files);
}

function renderReportLinks(files) {
  const host = $("reportLinks");
  host.innerHTML = "";
  if (!files || files.length === 0) {
    host.textContent = "Файлы отчета еще не созданы";
    host.classList.add("empty");
    return;
  }
  host.classList.remove("empty");
  for (const file of files) {
    const link = document.createElement("a");
    link.href = file.download_url;
    link.target = "_blank";
    link.rel = "noopener";
    link.textContent = `${file.format.toUpperCase()} · ${file.filename}`;
    host.appendChild(link);
  }
}

function renderZones() {
  $("selectedRowStatus").textContent = state.selectedItemId
    ? `Выбрана строка: ${selectedRowLabel()}`
    : "Выберите строку таблицы";

  const zones = $("zones");
  zones.innerHTML = "";
  if (!state.zones || state.zones.length === 0) {
    zones.textContent = "Зоны появятся после назначения порогов";
    zones.classList.add("empty");
    return;
  }
  zones.classList.remove("empty");
  for (const zone of state.zones) {
    const row = document.createElement("div");
    row.className = "zone-row";
    row.textContent = `${zone.name}: HR ${range(zone.lower_hr, zone.upper_hr)}, W ${range(zone.lower_power, zone.upper_power)}`;
    zones.appendChild(row);
  }
}

function selectedRowLabel() {
  const row = state.workspace?.table_rows.find((item) => item.id === state.selectedItemId);
  if (!row) {
    return "-";
  }
  return `${row.time_label || row.time_sec + "s"} · HR ${row.hr ?? "-"} · W ${row.power ?? "-"}`;
}

function range(lower, upper) {
  if (lower == null && upper == null) return "-";
  if (lower == null) return `< ${Math.round(upper)}`;
  if (upper == null) return `> ${Math.round(lower)}`;
  return `${Math.round(lower)}-${Math.round(upper)}`;
}

function renderCharts() {
  for (const metric of ["hr", "ventilation", "oxygen", "lactate"]) {
    renderChart(metric);
  }
}

function renderChart(metric) {
  const host = $(`chart-${metric}`);
  if (!host) return;
  const seriesList = state.charts?.charts?.[metric] || [];
  const nonEmpty = seriesList.filter((series) => series.points.length > 0);
  if (nonEmpty.length === 0) {
    host.innerHTML = '<div class="chart-empty">Нет данных</div>';
    return;
  }

  const width = 640;
  const height = 220;
  const padding = { left: 42, right: 16, top: 14, bottom: 28 };
  const allPoints = nonEmpty.flatMap((series) => series.points);
  const xMin = Math.min(...allPoints.map((point) => point.x));
  const xMax = Math.max(...allPoints.map((point) => point.x));
  const yMinRaw = Math.min(...allPoints.map((point) => point.y));
  const yMaxRaw = Math.max(...allPoints.map((point) => point.y));
  const yPad = Math.max(1, (yMaxRaw - yMinRaw) * 0.1);
  const yMin = yMinRaw - yPad;
  const yMax = yMaxRaw + yPad;
  const colors = ["#147c72", "#375a9e", "#b36b00", "#7b4dbb", "#8a3842"];

  const xScale = (x) => padding.left + ((x - xMin) / Math.max(1, xMax - xMin)) * (width - padding.left - padding.right);
  const yScale = (y) => height - padding.bottom - ((y - yMin) / Math.max(1, yMax - yMin)) * (height - padding.top - padding.bottom);
  const lines = nonEmpty.map((series, index) => {
    const points = series.points.map((point) => `${xScale(point.x)},${yScale(point.y)}`).join(" ");
    return `<polyline points="${points}" fill="none" stroke="${colors[index % colors.length]}" stroke-width="2.5" />`;
  }).join("");
  const dots = nonEmpty.map((series, index) => series.points.map((point) => {
    const selected = point.item_id === state.selectedItemId;
    return `<circle cx="${xScale(point.x)}" cy="${yScale(point.y)}" r="${selected ? 5 : 3}" fill="${selected ? "#d43f3a" : colors[index % colors.length]}" />`;
  }).join("")).join("");
  const thresholdLines = (state.charts?.thresholds || [])
    .filter((threshold) => threshold.time_sec != null)
    .map((threshold) => {
      const x = xScale(threshold.time_sec);
      return `<line x1="${x}" y1="${padding.top}" x2="${x}" y2="${height - padding.bottom}" stroke="#a56a00" stroke-dasharray="4 4" /><text x="${x + 4}" y="${padding.top + 12}" font-size="11" fill="#a56a00">${threshold.parameter}</text>`;
    }).join("");
  const legend = nonEmpty.map((series, index) => `<span style="color:${colors[index % colors.length]}">${series.label}</span>`).join(" · ");

  host.innerHTML = `
    <svg viewBox="0 0 ${width} ${height}" role="img">
      <line x1="${padding.left}" y1="${height - padding.bottom}" x2="${width - padding.right}" y2="${height - padding.bottom}" stroke="#d9e0ea" />
      <line x1="${padding.left}" y1="${padding.top}" x2="${padding.left}" y2="${height - padding.bottom}" stroke="#d9e0ea" />
      <text x="6" y="${padding.top + 10}" font-size="11" fill="#65738a">${Math.round(yMax)}</text>
      <text x="6" y="${height - padding.bottom}" font-size="11" fill="#65738a">${Math.round(yMin)}</text>
      ${thresholdLines}
      ${lines}
      ${dots}
    </svg>
    <div class="status">${legend}</div>
  `;
}

$("createClient").addEventListener("click", () => createClient().catch((error) => setStatus("clientStatus", error.message)));
$("importTest").addEventListener("click", () => importTest().catch((error) => setStatus("importStatus", error.message)));
$("uploadTest").addEventListener("click", () => uploadTest().catch((error) => setStatus("importStatus", error.message)));
$("savePower").addEventListener("click", () => savePower().catch((error) => setStatus("importStatus", error.message)));
$("applySampling").addEventListener("click", () => applySampling().catch((error) => setStatus("importStatus", error.message)));
$("previewReport").addEventListener("click", previewReport);
$("generateReports").addEventListener("click", () => generateReports().catch((error) => setStatus("importStatus", error.message)));
$("topPreviewReport").addEventListener("click", previewReport);
$("topGenerateReports").addEventListener("click", () => generateReports().catch((error) => setStatus("importStatus", error.message)));
$("addManualRow").addEventListener("click", () => addManualRow().catch((error) => setStatus("manualEntryStatus", error.message)));
document.querySelectorAll("[data-threshold]").forEach((button) => {
  button.addEventListener("click", () => {
    if (!state.measurementId || !state.selectedItemId) {
      setStatus("selectedRowStatus", "Сначала выберите строку таблицы");
      return;
    }
    setThreshold(state.selectedItemId, button.dataset.threshold).catch((error) => setStatus("selectedRowStatus", error.message));
  });
});
renderWorkspace();
