import { getDemoPassportPreviewPdf, getDemoReport, getGradeMappings } from "./api.js";

const ORIGIN_LABELS = { natural: "Природний", lab_grown: "Лабораторно вирощений", other: "Інше", unknown: "Не визначено" };
const TREATMENT_LABELS = { not_assessed: "Не оцінено", none_detected: "Не виявлено", disclosed: "Заявлено", confirmed: "Підтверджено" };
const IDENTIFICATION_LABELS = { preliminary: "Попередній", confirmed: "Підтверджено", inconclusive: "Невизначено" };

function download(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function formatAmount(value, currency = "USD") {
  return `${currency} ${new Intl.NumberFormat("uk-UA", { maximumFractionDigits: 2 }).format(Number(value))}`;
}

function formatDate(value) {
  return new Intl.DateTimeFormat("uk-UA", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

function renderDemoValuations(container, valuations) {
  container.replaceChildren();
  if (!valuations.length) {
    container.append(createElement("li", "", "Демонстраційних орієнтирів немає."));
    return;
  }
  for (const [index, valuation] of valuations.entries()) {
    const item = createElement("li", "market-reference-card");
    const disclosure = document.createElement("details");
    disclosure.className = "market-reference-card__disclosure";
    disclosure.open = index === 0;
    const summary = createElement("summary", "market-reference-card__summary");
    summary.append(
      createElement("strong", "", formatAmount(valuation.amount, valuation.currency_code)),
      createElement("span", "", "DEMO · демонстраційний орієнтир"),
    );
    const details = createElement("dl", "market-reference-card__details");
    for (const [term, value] of [["Провайдер", valuation.source_name], ["Набір", "synthetic-demo-v1"], ["Отримано", formatDate(valuation.observed_at)]]) {
      const row = document.createElement("div");
      row.append(createElement("dt", "", term), createElement("dd", "", value));
      details.append(row);
    }
    const note = createElement("p", "market-reference-card__note", "Synthetic demonstration reference only. Не є ринковою, експертною, продажною чи транзакційною ціною.");
    disclosure.append(summary, details, note);
    item.append(disclosure);
    container.append(item);
  }
}

function createElement(tagName, className, textContent) {
  const element = document.createElement(tagName);
  if (className) element.className = className;
  if (textContent !== undefined) element.textContent = textContent;
  return element;
}
export async function initDemoReportDetail() {
  const root = document.querySelector("[data-demo-report-detail]"); if (!root || localStorage.getItem("role") !== "admin") return;
  const params = new URLSearchParams(window.location.search); const dataset = params.get("dataset") || "synthetic-demo-v1"; const reportId = params.get("id"); const token = localStorage.getItem("token");
  if (!reportId) return;
  const status = document.getElementById("demo-report-status");
  try {
    const [report, mappings] = await Promise.all([getDemoReport(dataset, reportId, token), getGradeMappings(token)]);
    const label = (category, value) => mappings.find((item) => item.category === category && item.grade_value === value)?.grade_label || "—";
    document.getElementById("demo-report-id").textContent = report.report_id;
    const statusBadge = document.getElementById("demo-status-badge");
    statusBadge.textContent = "Видано";
    statusBadge.dataset.status = report.status;
    document.getElementById("demo-system-summary").textContent = `Системний IDC: Proportions ${label("proportions", report.system_proportions_grade)}, Final Cut ${label("cut", report.system_cut_grade)}.`;
    const values = {
      "demo-date": report.examination_date,
      "demo-shape": report.stone.shape,
      "demo-carat": report.stone.carat_weight,
      "demo-color": label("color", report.stone.color_grade),
      "demo-clarity": label("clarity", report.stone.clarity_grade),
      "demo-fluorescence": label("fluorescence", report.stone.fluorescence_grade),
      "demo-length": report.stone.measurements_length,
      "demo-width": report.stone.measurements_width,
      "demo-depth-mm": report.stone.measurements_depth,
      "demo-table": report.stone.table_percent,
      "demo-depth": report.stone.depth_percent,
      "demo-crown": report.stone.crown_angle,
      "demo-pavilion": report.stone.pavilion_angle,
      "demo-girdle": report.stone.girdle_thickness,
      "demo-culet": report.stone.culet_size,
      "demo-origin": ORIGIN_LABELS[report.stone.origin] || "—",
      "demo-treatment": TREATMENT_LABELS[report.stone.treatment_status] || "—",
      "demo-identification-status": IDENTIFICATION_LABELS[report.stone.identification_status] || "—",
      "demo-method": report.stone.identification_method,
      "demo-conclusion": report.stone.identification_conclusion,
      "demo-comment": report.expert_comment,
      "demo-cut": label("cut", report.system_cut_grade),
    };
    for (const [id, value] of Object.entries(values)) document.getElementById(id).value = value ?? "—";
    renderDemoValuations(document.getElementById("demo-valuations"), report.market_references || []);
    document.getElementById("demo-preview-pdf").addEventListener("click", async () => {
      try {
        download(await getDemoPassportPreviewPdf(dataset, reportId, token), `demo-preview-${reportId}.pdf`);
      } catch {
        status.hidden = false;
        status.textContent = "Не вдалося сформувати demo PDF.";
      }
    });
  } catch {
    document.getElementById("demo-report-id").textContent = "Demo-звіт недоступний.";
  }
}
