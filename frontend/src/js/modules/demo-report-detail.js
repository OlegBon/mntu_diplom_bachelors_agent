import { getDemoPassportPreviewPdf, getDemoReport, getGradeMappings } from "./api.js";
import { formatCurrency, formatDate as formatLocalizedDate, t } from "./i18n.js";

const ORIGIN_LABELS = { natural: "Природний", lab_grown: "Лабораторно вирощений", other: "Інше", unknown: "Не визначено" };
const TREATMENT_LABELS = { not_assessed: "Не оцінено", none_detected: "Не виявлено", disclosed: "Заявлено", confirmed: "Підтверджено" };
const IDENTIFICATION_LABELS = { preliminary: "Попередній", confirmed: "Підтверджено", inconclusive: "Невизначено" };
const SHOWCASE_REPORT_ID = "DEMO-00999";
const REPORT_STATUS_LABELS = { issued: "Видано", void: "Анульовано" };

function download(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function formatAmount(value, currency = "USD") {
  return formatCurrency(Number(value), currency, { maximumFractionDigits: 2 });
  return `${currency} ${new Intl.NumberFormat("uk-UA", { maximumFractionDigits: 2 }).format(Number(value))}`;
}

function formatDate(value) {
  return formatLocalizedDate(new Date(value), { dateStyle: "medium", timeStyle: "short" });
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
    for (const [term, value] of [
      ["Провайдер", valuation.source_name],
      ["Знімок провайдера", "Не передбачено для synthetic demo"],
      ["Отримано", formatDate(valuation.observed_at)],
      ["Еквівалент", "Не розраховується для synthetic demo"],
      ["Курс НБУ", "Не застосовується для synthetic demo"],
    ]) {
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

function reportStatusLabel(status) {
  if (status === "issued") return t("dashboard.statusIssued");
  if (status === "void") return t("dashboard.statusVoid");
  return status;
}

function localizeDemoDetailShell(root) {
  const textKeys = [
    ["#demo-report-subtitle", "demoDetail.subtitle"],
    [".page-header > .btn", "demoDetail.back"],
    ["label[for=demo-date]", "demoDetail.examinationDate"],
    ["label[for=demo-shape]", "demoDetail.shape"],
    ["label[for=demo-carat]", "demoDetail.carat"],
    ["label[for=demo-color]", "demoDetail.color"],
    ["label[for=demo-clarity]", "demoDetail.clarity"],
    ["label[for=demo-origin]", "demoDetail.origin"],
    ["label[for=demo-treatment]", "demoDetail.treatment"],
    ["label[for=demo-identification-status]", "demoDetail.identificationLevel"],
    ["label[for=demo-method]", "demoDetail.identificationMethod"],
    ["label[for=demo-conclusion]", "demoDetail.identificationConclusion"],
    ["label[for=demo-comment]", "demoDetail.expertComment"],
  ];
  for (const [selector, key] of textKeys) {
    const node = root.querySelector(selector);
    if (node) node.textContent = t(key);
  }
  const formHeadings = root.querySelectorAll(".report-detail__section > h2");
  ["demoDetail.identification", "demoDetail.geometry", "demoDetail.conclusion"].forEach((key, index) => {
    if (formHeadings[index]) formHeadings[index].textContent = t(key);
  });
  const sideHeadings = root.querySelectorAll(".report-detail__side h2");
  ["demoDetail.reportState", "demoDetail.references", "demoDetail.attachments", "demoDetail.passport", "demoDetail.history"].forEach((key, index) => {
    if (sideHeadings[index]) sideHeadings[index].textContent = t(key);
  });
}

export async function initDemoReportDetail() {
  const root = document.querySelector("[data-demo-report-detail]"); if (!root || localStorage.getItem("role") !== "admin") return;
  localizeDemoDetailShell(root);
  document.addEventListener("diamant:locale-change", () => localizeDemoDetailShell(root));
  const params = new URLSearchParams(window.location.search); const requestedDataset = params.get("dataset"); let dataset = requestedDataset || "synthetic-demo-v4"; const reportId = params.get("id"); const token = localStorage.getItem("token");
  if (!reportId) return;
  const status = document.getElementById("demo-report-status");
  try {
    let report;
    try {
      report = await getDemoReport(dataset, reportId, token);
    } catch (error) {
      if (requestedDataset) throw error;
      dataset = "synthetic-demo-v3";
      try {
        report = await getDemoReport(dataset, reportId, token);
      } catch {
        dataset = "synthetic-demo-v2";
        try {
          report = await getDemoReport(dataset, reportId, token);
        } catch {
          dataset = "synthetic-demo-v1";
          report = await getDemoReport(dataset, reportId, token);
        }
      }
    }
    const mappings = await getGradeMappings(token);
    const label = (category, value) => mappings.find((item) => item.category === category && item.grade_value === value)?.grade_label || "—";
    document.getElementById("demo-report-id").textContent = report.report_id;
    document.getElementById("demo-som-link").href = `/demo-reports.html?tab=stones&som_report=${encodeURIComponent(report.report_id)}`;
    const isShowcase = report.report_id === SHOWCASE_REPORT_ID;
    document.getElementById("demo-showcase-media-event").hidden = !isShowcase;
    const statusBadge = document.getElementById("demo-status-badge");
    const statusLabel = reportStatusLabel(report.status);
    statusBadge.textContent = statusLabel;
    statusBadge.dataset.status = report.status;
    document.getElementById("demo-status-event").textContent = `Чернетка → ${statusLabel} · змодельована системна подія`;
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
