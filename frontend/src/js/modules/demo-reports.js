import { getDemoDataset, getDemoReports, getDemoNarrativeQualityAnalytics, getDemoOperationalQualityAnalytics, getDemoProviderAnalytics, getDemoWorkflowAnalytics, getDemoSom, getFxDataSnapshots, getGradeMappings } from "./api.js";
import { closeReportOverlays, formatDateTime, renderMarketReferencePrice } from "./dashboard.js";
import { duration as formatDuration, element as createElement, periodSummary, renderNarrativeAnalytics, renderNbuCurrencySource, renderOperationalQuality, renderTable } from "./analytics-ui.js";
import { applyNarrativeCompleteness, narrativeCompletenessFromUrl, narrativePresenceFromUrl, readNarrativeCompleteness, readNarrativePresence } from "./narrative-completeness-filters.js";
import { t } from "./i18n.js";

const PREFERRED_DATASET_ID = "synthetic-demo-v4";
const FALLBACK_DATASET_IDS = ["synthetic-demo-v3", "synthetic-demo-v2", "synthetic-demo-v1"];
const PAGE_SIZE = 25;
const REPORT_STATUS_LABELS = { issued: "Видано", void: "Анульовано" };
const SALE_STATUS_LABELS = { not_for_sale: "Не продається" };

function localizeDemoShell(root) {
  const textKeys = [
    [".page-title", "demo.title"],
    [".page-subtitle", "demo.subtitle"],
    ["#demo-tab-reports", "demo.reports"],
    ["#demo-tab-stones", "demo.stones"],
    ["#demo-tab-experts", "demo.experts"],
    ["#demo-tab-narratives", "demo.texts"],
    ["#demo-tab-quality", "demo.quality"],
    ["#demo-tab-administrators", "demo.administrators"],
    ["#demo-tab-providers", "demo.providers"],
    ["#demo-tab-currency", "demo.currencySources"],
    [".demo-scope__showcase strong", "demo.previewTitle"],
    [".demo-scope__showcase p", "demo.previewDescription"],
    [".demo-scope__showcase a", "demo.openPreview"],
    ["#demo-currency-panel h2", "demo.currencyTitle"],
    ["#demo-experts-panel h2", "demo.workflowTitle"],
    ["#demo-narratives-panel h2", "demo.narrativesTitle"],
    ["#demo-quality-panel h2", "demo.qualityTitle"],
    ["#demo-administrators-panel h2", "demo.administratorsTitle"],
    ["#demo-providers-panel h2", "demo.providersTitle"],
    ["#demo-stones-panel h2", "demo.somTitle"],
    ["#demo-workflow-actor-dialog-title", "demo.workflowDialogTitle"],
    ["#demo-provider-dialog-title", "demo.providerDialogTitle"],
  ];
  for (const [selector, key] of textKeys) {
    const element = root.querySelector(selector);
    if (element) element.textContent = t(key);
  }
  root.querySelector(".analytics-tabs")?.setAttribute("aria-label", t("demo.tabs"));
  for (const closeButton of root.querySelectorAll(".account-dialog__close")) closeButton.setAttribute("aria-label", t("demo.close"));

  const notice = root.querySelector(".demo-scope__notice");
  const marker = notice?.querySelector("strong");
  if (!notice || !marker) return;
  for (const node of [...notice.childNodes]) {
    if (node !== marker) node.remove();
  }
  const copy = document.createElement("span");
  copy.textContent = ` ${t("demo.syntheticNotice")}`;
  notice.append(copy);
}

function createBadge(value, kind) {
  return createElement("span", `status-badge status-badge--${kind}`, value);
}

function reportStatusLabel(status) {
  if (status === "issued") return t("dashboard.statusIssued");
  if (status === "void") return t("dashboard.statusVoid");
  return status;
}

function saleStatusLabel(status) {
  return status === "not_for_sale" ? t("dashboard.notSold") : status;
}

function getUrlState() {
  const params = new URLSearchParams(window.location.search);
  return {
    page: Math.max(Number.parseInt(params.get("page") || "1", 10) || 1, 1),
    search: params.get("search") || "",
    report_status: params.get("report_status") || "",
    market_status: params.get("market_status") || "",
    shape: params.get("shape") || "",
    carat_min: params.get("carat_min") || "",
    carat_max: params.get("carat_max") || "",
    color_grade: params.get("color_grade") || "",
    clarity_grade: params.get("clarity_grade") || "",
    cut_grade: params.get("cut_grade") || "",
    price_min: params.get("price_min") || "",
    price_max: params.get("price_max") || "",
    date_from: params.get("date_from") || "",
    date_to: params.get("date_to") || "",
    empty_narrative: narrativeCompletenessFromUrl(params),
    narrative_presence: narrativePresenceFromUrl(params),
    sort: params.get("sort") || "report_id_desc",
  };
}

function updateUrl(state) {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(state)) {
    const serialized = Array.isArray(value) ? value.join(",") : String(value);
    if (serialized && !(key === "page" && Number(serialized) === 1) && !(key === "narrative_presence" && serialized === "empty")) params.set(key, serialized);
  }
  const query = params.toString();
  window.history.replaceState({}, "", `${window.location.pathname}${query ? `?${query}` : ""}`);
}

function setStatus(container, message, kind = "info") {
  container.replaceChildren(createElement("p", `dashboard-state dashboard-state--${kind}`, message));
}

function toggleSort(currentSort, key) {
  return currentSort === `${key}_asc` ? `${key}_desc` : `${key}_asc`;
}

function updateSortIndicators(root, sort) {
  const separator = sort.lastIndexOf("_");
  const key = sort.slice(0, separator);
  const direction = sort.slice(separator + 1);
  for (const button of root.querySelectorAll("[data-demo-sort-key]")) {
    const active = button.dataset.demoSortKey === key;
    button.toggleAttribute("data-sort-direction", active);
    if (active) button.dataset.sortDirection = direction;
    button.parentElement.setAttribute("aria-sort", active ? (direction === "asc" ? "ascending" : "descending") : "none");
  }
}

function renderActions(report, datasetId) {
  const detailUrl = `/demo-report-detail.html?dataset=${datasetId}&id=${encodeURIComponent(report.report_id)}`;
  const wrapper = createElement("div", "report-actions");
  const toggle = createElement("button", "report-actions__toggle", "⋮");
  toggle.type = "button";
  toggle.setAttribute("aria-label", `Відкрити дії для demo-звіту ${report.report_id}`);
  toggle.setAttribute("aria-expanded", "false");
  const menu = createElement("div", "report-actions__menu");
  menu.hidden = true;
  const detail = createElement("a", "report-actions__item", "Переглянути");
  detail.href = detailUrl;
  const edit = createElement("button", "report-actions__item", "Редагувати");
  edit.type = "button";
  edit.disabled = true;
  edit.title = "Demo-звіт доступний лише для читання";
  const print = createElement("a", "report-actions__item", "Друк");
  print.href = `${detailUrl}&print=1`;
  print.target = "_blank";
  print.rel = "noopener noreferrer";
  const som = createElement("a", "report-actions__item", "Аналіз SOM");
  som.href = `/demo-reports.html?tab=stones&som_report=${encodeURIComponent(report.report_id)}`;
  menu.append(detail, som, edit, print);
  toggle.addEventListener("click", (event) => {
    event.stopPropagation();
    const isOpen = menu.hidden;
    closeReportOverlays();
    menu.hidden = !isOpen;
    toggle.setAttribute("aria-expanded", String(isOpen));
  });
  wrapper.append(toggle, menu);
  return wrapper;
}

function renderRows(tbody, reports, labelFor, datasetId) {
  tbody.replaceChildren();
  for (const report of reports) {
    const row = document.createElement("tr");
    const detailUrl = `/demo-report-detail.html?dataset=${datasetId}&id=${encodeURIComponent(report.report_id)}`;
    const idCell = document.createElement("td");
    const id = createElement("a", "id-link", report.report_id);
    id.href = detailUrl;
    id.title = "Відкрити read-only demo-звіт";
    idCell.append(id);
    row.append(idCell);
    const dateCell = document.createElement("td");
    const date = formatDateTime(report.report_date);
    dateCell.append(
      createElement("strong", "date-primary", date.date),
      createElement("span", "date-secondary", date.time),
    );
    row.append(dateCell);
    row.append(createElement("td", "", report.stone.shape));
    row.append(createElement("td", "", report.stone.carat_weight));
    row.append(createElement("td", "", labelFor("color", report.stone.color_grade)));
    row.append(createElement("td", "", labelFor("clarity", report.stone.clarity_grade)));
    const cut = document.createElement("td");
    cut.append(createBadge(labelFor("cut", report.system_cut_grade), "cut"));
    row.append(cut);
    const price = document.createElement("td");
    price.append(renderMarketReferencePrice(report));
    row.append(price);
    const reportStatus = document.createElement("td");
    reportStatus.append(createBadge(reportStatusLabel(report.status), report.status));
    row.append(reportStatus);
    const saleStatus = document.createElement("td");
    saleStatus.append(createBadge(saleStatusLabel(report.stone.market_status), "sale-not-sold"));
    row.append(saleStatus);
    const actions = document.createElement("td");
    actions.append(renderActions(report, datasetId));
    row.append(actions);
    tbody.append(row);
  }
}

function renderPagination(container, page, totalPages, onPageChange) {
  container.replaceChildren();
  if (totalPages <= 1) return;
  const addButton = (label, target, { disabled = false, active = false, icon = false } = {}) => {
    const button = createElement("button", `page-btn${active ? " active" : ""}${icon ? " page-btn--icon" : ""}`, label);
    button.type = "button";
    button.disabled = disabled;
    if (active) button.setAttribute("aria-current", "page");
    button.addEventListener("click", () => onPageChange(target));
    container.append(button);
  };
  addButton("«", 1, { disabled: page === 1, icon: true });
  addButton("‹", page - 1, { disabled: page === 1, icon: true });
  for (const target of [1, page - 1, page, page + 1, totalPages]) {
    if (target >= 1 && target <= totalPages && !container.querySelector(`[data-page="${target}"]`)) {
      addButton(String(target), target, { active: target === page });
      container.lastElementChild.dataset.page = String(target);
    }
  }
  addButton("›", page + 1, { disabled: page === totalPages, icon: true });
  addButton("»", totalPages, { disabled: page === totalPages, icon: true });
}

function populateGradeFilter(select, category, mappings) {
  for (const item of mappings.filter((mapping) => mapping.category === category)) {
    const option = createElement("option", "", item.grade_label);
    option.value = String(item.grade_value);
    select.append(option);
  }
}

function openSyntheticActorDialog(dialog, content, actor) {
  const metrics = document.createElement("dl");
  metrics.className = "analytics-metrics";
  const rows = [
    ["Стан actor", "Synthetic · non-account"],
    ["Усього demo-звітів", actor.reports_touched],
    ["Чернетки", "Не моделюються"],
    ["На перевірці", "Не моделюються"],
    ["Видано", actor.issued_reports],
    ["Анульовано", actor.void_reports],
    ["Завершені робочі сесії", actor.completed_intervals],
    ["Активний час", formatDuration(actor.total_duration_seconds)],
    ["Середня активна сесія", formatDuration(actor.avg_duration_seconds)],
    ["Медіанна активна сесія", formatDuration(actor.median_duration_seconds)],
    ["Збережень із виміром підготовки", "Не моделюються"],
    ["Час до першого збереження", "Не моделюється"],
    ["Середній час до першого збереження", "Не моделюється"],
    ["Медіанний час до першого збереження", "Не моделюється"],
  ];
  for (const [label, value] of rows) metrics.append(createElement("dt", "", label), createElement("dd", "", String(value)));
  content.replaceChildren(
    createElement("h3", "analytics-dialog-name", actor.display_name),
    metrics,
    createElement("p", "account-help", "Активний час — лише детермінований synthetic інтервал demo workflow, а не server-timed сесія чи вимір продуктивності людини."),
    createElement("p", "account-help", "Час до першого збереження для demo-набору не моделюється. Actor є вигаданим, не має профілю та не представляє реальну людину."),
    renderDemoIntervalList("Три найкоротші synthetic активні інтервали", actor.shortest_intervals, actor.dataset_id),
    renderDemoIntervalList("Три найдовші synthetic активні інтервали", actor.longest_intervals, actor.dataset_id),
  );
  dialog.showModal();
}

function renderDemoIntervalList(title, items = [], datasetId) {
  const section = createElement("section", "analytics-review-list");
  section.append(createElement("h3", "", title));
  if (!items.length) {
    section.append(createElement("p", "account-help", "Завершених synthetic інтервалів у цьому періоді немає."));
    return section;
  }
  const list = document.createElement("ol");
  for (const item of items) {
    const row = document.createElement("li");
    const reportLink = createElement("a", "", item.report_id);
    reportLink.href = `/demo-report-detail.html?dataset=${encodeURIComponent(datasetId)}&id=${encodeURIComponent(item.report_id)}`;
    const occurredAt = new Intl.DateTimeFormat("uk-UA", { dateStyle: "medium", timeStyle: "short" }).format(new Date(item.occurred_at));
    const decision = {
      review_completed: "Видано",
      review_returned: "Повернено у чернетку",
      review_voided: "Анульовано",
    }[item.action];
    row.append(reportLink, document.createTextNode(`: ${formatDuration(item.duration_seconds)} · ${decision ? `${decision} · ` : ""}${occurredAt}`));
    list.append(row);
  }
  section.append(list);
  return section;
}

function renderWorkflowRows(container, actors, dialog, dialogContent, datasetId) {
  renderTable(container, ["Експерт", "Стан", "Усього", "Чернетки", "На перевірці", "Видано", "Анульовано", "Активний час"], actors.map((actor) => {
    const actorButton = createElement("button", "analytics-expert-button", actor.display_name);
    actorButton.type = "button";
    actorButton.addEventListener("click", () => openSyntheticActorDialog(dialog, dialogContent, { ...actor, dataset_id: datasetId }));
    return [actorButton, "Synthetic", String(actor.reports_touched), "—", "—", String(actor.issued_reports), String(actor.void_reports), formatDuration(actor.total_duration_seconds)];
  }), "За обраний період synthetic-подій немає.");
}

function renderSyntheticAdministrators(container, actors, datasetId) {
  const fragment = document.createDocumentFragment();
  const cards = createElement("div", "analytics-admin-list");
  for (const actor of actors) {
    const card = createElement("article", "analytics-admin-card");
    const heading = createElement("h3", "", actor.display_name);
    const metrics = createElement("dl", "analytics-metrics");
    [
      ["Завершено перевірок", actor.completed_intervals],
      ["Видано", actor.issued_reports],
      ["Повернуто", actor.returned_to_draft],
      ["Анульовано", actor.void_reports],
      ["Середня тривалість", formatDuration(actor.avg_duration_seconds)],
      ["Медіанна тривалість", formatDuration(actor.median_duration_seconds)],
    ].forEach(([label, value]) => metrics.append(createElement("dt", "", label), createElement("dd", "", String(value))));
    card.append(
      heading,
      metrics,
      renderDemoIntervalList("Найкоротші synthetic перевірки", actor.shortest_intervals, datasetId),
      renderDemoIntervalList("Найдовші synthetic перевірки", actor.longest_intervals, datasetId),
      createElement("p", "account-help", "Synthetic administrator · non-account. Дані сформовано детермінованим demo workflow."),
    );
    cards.append(card);
  }
  if (actors.length) fragment.append(cards);
  else fragment.append(createElement("p", "account-help", "Synthetic адміністраторів для цього зрізу немає."));
  container.replaceChildren(fragment);
}

function formatUsd(value) {
  return new Intl.NumberFormat("uk-UA", { style: "currency", currency: "USD" }).format(Number(value));
}

function openDemoProviderDialog(dialog, content, provider, datasetId) {
  const metrics = document.createElement("dl");
  metrics.className = "analytics-metrics";
  [
    ["Тип джерела", provider.source_class],
    ["Походження даних", provider.provenance],
    ["Статус договору й умов", provider.terms_status],
    ["Покриття у зрізі", `${provider.covered_report_count} із ${provider.candidate_report_count} demo-звітів`],
    ["Тип значень", "Synthetic demonstration reference"],
    ["Кількість значень", provider.reference_count],
    ["Період значень", `${provider.first_period} — ${provider.last_period}`],
    ["Медіанний орієнтир", provider.median_amount === null ? "—" : formatUsd(provider.median_amount)],
    ["Діапазон орієнтирів", provider.min_amount === null || provider.max_amount === null ? "—" : `${formatUsd(provider.min_amount)} — ${formatUsd(provider.max_amount)}`],
    ["Знімок провайдера", "Не передбачено: значення детерміновано генерує локальний demo-набір."],
    ["Останнє отримання", "Не застосовується: немає зовнішнього сервісу."],
  ].forEach(([label, value]) => metrics.append(createElement("dt", "", label), createElement("dd", "", String(value))));
  const sample = provider.latest_report_id ? createElement("a", "id-link", provider.latest_report_id) : null;
  if (sample) sample.href = `/demo-report-detail.html?dataset=${encodeURIComponent(datasetId)}&id=${encodeURIComponent(provider.latest_report_id)}`;
  const sampleSection = createElement("section", "analytics-review-list");
  sampleSection.append(createElement("h3", "", "Останній synthetic приклад"), sample || createElement("p", "account-help", "У цьому зрізі немає прикладу."));
  const scenario = createElement("section", "analytics-review-list");
  scenario.append(
    createElement("h3", "", "Synthetic policy scenario"),
    createElement("p", "account-help", "Режим: demo-only. Мережеві виклики вимкнені; договори, trial-призначення та журнал реальних provider-умов для цього fictional джерела не створюються."),
  );
  content.replaceChildren(
    createElement("h3", "analytics-dialog-name", provider.provider_name),
    metrics,
    createElement("p", "account-help", provider.usage_policy),
    createElement("p", "account-help", "Ці умови описують лише demo-сценарій. Вони не є договором, ліцензією чи дозволом використовувати реальні provider data."),
    scenario,
    sampleSection,
  );
  dialog.showModal();
}

function renderCurrencySources(container, snapshots, dialog, dialogContent) {
  renderNbuCurrencySource(container, snapshots, dialog, dialogContent, formatDateTime, "table-container demo-provider-analytics__table");
}

function renderDemoProviderAnalytics(container, data, datasetId, dialog, dialogContent) {
  const formatPeriod = (value) => value ? formatDateTime(value).date : "—";
  const latestReportLink = (reportId) => {
    if (!reportId) return "—";
    const link = createElement("a", "id-link", reportId);
    link.href = `/demo-report-detail.html?dataset=${encodeURIComponent(datasetId)}&id=${encodeURIComponent(reportId)}`;
    link.title = "Відкрити read-only demo-звіт";
    return link;
  };
  const overview = createElement("p", "account-help", `${data.candidate_report_count} demo-звітів у зрізі · ${data.reference_count} synthetic орієнтирів.`);
  const tableHost = createElement("div", "demo-provider-analytics__table");
  renderTable(tableHost, ["Провайдер", "Покриття", "Значень", "Період", "Медіана", "Діапазон", "Останній приклад"], data.providers.map((provider) => {
    const providerButton = createElement("button", "analytics-expert-button", provider.provider_name);
    providerButton.type = "button";
    providerButton.addEventListener("click", () => openDemoProviderDialog(dialog, dialogContent, {
      ...provider,
      candidate_report_count: data.candidate_report_count,
      first_period: formatPeriod(provider.first_observed_at),
      last_period: formatPeriod(provider.last_observed_at),
    }, datasetId));
    return [
    providerButton,
    `${provider.covered_report_count} із ${data.candidate_report_count}`,
    String(provider.reference_count),
    `${formatPeriod(provider.first_observed_at)} — ${formatPeriod(provider.last_observed_at)}`,
    provider.median_amount === null ? "—" : formatUsd(provider.median_amount),
    provider.min_amount === null || provider.max_amount === null ? "—" : `${formatUsd(provider.min_amount)} — ${formatUsd(provider.max_amount)}`,
    latestReportLink(provider.latest_report_id),
  ]; }), "У вибраному зрізі немає synthetic provider values.");
  const note = createElement("p", "account-help", "Суми — immutable synthetic reference values у USD для всього каменю. Вони не є ринковими даними, прогнозом, ціною продажу або рейтингом провайдера.");
  container.replaceChildren(overview, tableHost, note);
}

function formatUsdPerCarat(value, compact = false) {
  return `${new Intl.NumberFormat("uk-UA", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: compact ? 0 : 2,
  }).format(Number(value))}/ct`;
}

function formatCompactUsdPerCarat(value) {
  const amount = Number(value);
  if (amount >= 1000) return `${(amount / 1000).toLocaleString("uk-UA", { maximumFractionDigits: 1 })}k`;
  return new Intl.NumberFormat("uk-UA", { maximumFractionDigits: 0 }).format(amount);
}

function createSomCellDetails() {
  const details = createElement("p", "demo-som-cell-details account-help");
  details.hidden = true;
  details.setAttribute("role", "status");
  return details;
}

function showSomCellDetails(container, text) {
  container.textContent = text;
  container.hidden = false;
}

function renderSom(container, data, labelFor) {
  const selected = data.selected_report;
  const grid = createElement("div", "demo-som-grid");
  const mainCellDetails = createSomCellDetails();
  grid.style.setProperty("--som-size", String(data.grid_size));
  for (const cell of data.cells) {
    const button = createElement("button", `demo-som-cell demo-som-cell--${cell.segment_label.slice(-1).toLowerCase()}`, String(cell.report_count));
    button.type = "button";
    button.title = `${cell.segment_label}: ${cell.report_count} synthetic звітів`;
    button.setAttribute("aria-label", `${cell.segment_label}, клітинка ${cell.x + 1} × ${cell.y + 1}: ${cell.report_count} synthetic звітів. Показати деталі клітинки.`);
    button.addEventListener("click", () => showSomCellDetails(mainCellDetails, [
      `Клітинка ${cell.x + 1} × ${cell.y + 1} · ${cell.segment_label}.`,
      `${cell.report_count} synthetic звітів.`,
      cell.median_carat_weight === null || cell.median_carat_weight === undefined ? "Медіанна вага: —." : `Медіанна вага: ${cell.median_carat_weight} ct.`,
      cell.median_reference_amount === null || cell.median_reference_amount === undefined ? "Медіанний synthetic орієнтир: —." : `Медіанний synthetic орієнтир: ${formatUsd(cell.median_reference_amount)}.`,
    ].join(" ")));
    if (selected && cell.x === selected.som_x && cell.y === selected.som_y) button.classList.add("is-selected");
    grid.append(button);
  }
  const mainMapViewport = createElement("div", "demo-som-map__viewport");
  mainMapViewport.append(grid);
  const coverage = data.coverage || {};
  const left = createElement("section", "demo-som-map");
  const legend = createElement("div", "demo-som-legend");
  for (const segment of data.segments) {
    const item = createElement("div", `demo-som-legend__item demo-som-legend__item--${segment.key.toLowerCase()}`);
    item.append(createElement("strong", "", `${segment.label} · ${segment.report_count}`), createElement("span", "", `${segment.carat_min}–${segment.carat_max} ct · ${segment.dominant_shapes.join(" / ")}`));
    legend.append(item);
  }
  left.append(createElement("h3", "", "Карта сегментів"), mainMapViewport, mainCellDetails, createElement("p", "demo-som-scroll-hint", "На вузькому екрані проведіть карту горизонтально."), legend, createElement("p", "account-help", `Клітинка містить кількість demo-звітів. Кольори відповідають описовим профілям у легенді, не класам якості.`));
  const right = createElement("aside", "demo-som-profile");
  right.append(createElement("h3", "", "Профіль показового каменю"));
  if (selected) {
    const details = document.createElement("dl");
    details.className = "analytics-metrics";
    [["Звіт", selected.report_id], ["SOM-клітинка", `${selected.som_x + 1} × ${selected.som_y + 1}`], ["У клітинці", `${selected.cell_count} demo-звітів`], ["У сусідстві", `${selected.neighborhood_count} demo-звітів`], ["Колір / чистота", `${labelFor("color", selected.color_grade)} / ${labelFor("clarity", selected.clarity_grade)}`], ["Системний Final Cut", labelFor("cut", selected.system_cut_grade)]].forEach(([label, value]) => details.append(createElement("dt", "", label), createElement("dd", "", value)));
    const formWeight = createElement("dd", "demo-som-value-stack");
    formWeight.append(createElement("strong", "", selected.shape), createElement("span", "", `${selected.carat_weight} ct`));
    details.append(createElement("dt", "", "Форма / вага"), formWeight);
    const reference = createElement("dd", "demo-som-value-stack");
    reference.append(createElement("strong", "", formatUsd(selected.selected_reference_amount)), createElement("span", "", selected.selected_provider));
    details.append(createElement("dt", "", "Synthetic орієнтир"), reference);
    const position = createElement("section", "demo-som-position");
    position.append(createElement("h4", "", "Позиція в сегменті"), createElement("strong", "", selected.segment_label), createElement("p", "account-help", selected.segment_description));
    const peers = createElement("p", "account-help");
    if (selected.peer_report_ids.length) {
      peers.append(document.createTextNode("Найближчі synthetic приклади: "));
      selected.peer_report_ids.forEach((reportId, index) => {
        if (index) peers.append(document.createTextNode(", "));
        const link = createElement("a", "", reportId);
        link.href = `/demo-reports.html?tab=stones&som_report=${encodeURIComponent(reportId)}`;
        peers.append(link);
      });
      peers.append(document.createTextNode("."));
    } else peers.textContent = "У клітинці поки немає інших synthetic прикладів.";
    const benchmark = createElement("section", "demo-som-benchmark");
    benchmark.append(createElement("h4", "", "Демо-орієнтир сегмента"), createElement("strong", "", `${formatUsd(selected.segment_reference_min)} – ${formatUsd(selected.segment_reference_max)}`), createElement("span", "", "Діапазон значень усієї описової зони SOM, а не лише трьох найближчих прикладів."));
    right.append(details, position, peers, benchmark);
  }
  right.append(createElement("p", "account-help", `Охоплення: ${coverage.accepted_reports ?? 0} включено з ${coverage.candidate_reports ?? 0}; ${coverage.excluded_reports ?? 0} виключено через відсутність повного дозволеного synthetic вектора.`), createElement("p", "account-help", coverage.policy_explanation || "Для виключених звітів policy scenario не залишає дозволеного synthetic орієнтиру."));
  right.append(createElement("p", "account-help", "Synthetic орієнтир — лише демонстраційна величина сценарію, не прогнозована чи ринкова ціна."));
  const layout = createElement("div", "demo-som-layout");
  layout.append(left, right);
  const overview = data.map_overview || {};
  const overviewSection = createElement("section", "demo-som-overview");
  overviewSection.append(createElement("h3", "", "Огляд карти"));
  const overviewMetrics = createElement("dl", "demo-som-overview__metrics");
  const providerUsage = Object.entries(overview.provider_usage || {}).map(([provider, count]) => `${provider}: ${count}`).join(" · ") || "—";
  [
    ["Охоплення", `${coverage.accepted_reports ?? 0} включено · ${coverage.excluded_reports ?? 0} виключено`],
    ["Зайнято клітинок", `${overview.occupied_cells ?? 0} із ${data.grid_size ** 2}`],
    ["Найщільніша клітинка", `${overview.densest_cell ?? "—"} · ${overview.densest_cell_report_count ?? 0} каменів`],
    ["Найбільша зона", `${overview.largest_segment_label ?? "—"} · ${overview.largest_segment_report_count ?? 0} каменів`],
    ["Дозволені орієнтири", providerUsage],
  ].forEach(([term, value]) => {
    const item = createElement("div", "demo-som-overview__item");
    item.append(createElement("dt", "", term), createElement("dd", "", value));
    overviewMetrics.append(item);
  });
  overviewSection.append(overviewMetrics);
  const benchmarkMap = createElement("section", "demo-som-map");
  const benchmarkGrid = createElement("div", "demo-som-grid demo-som-grid--benchmark");
  const benchmarkCellDetails = createSomCellDetails();
  benchmarkGrid.style.setProperty("--som-size", String(data.grid_size));
  for (const cell of data.cells) {
    const band = cell.benchmark_band || "empty";
    const value = cell.median_reference_usd_per_carat;
    const button = createElement("button", `demo-som-cell demo-som-benchmark-cell demo-som-benchmark-cell--${band}`, value === null || value === undefined ? "—" : formatCompactUsdPerCarat(value));
    button.type = "button";
    button.title = value === null || value === undefined
      ? "У цій SOM-клітинці немає synthetic benchmark"
      : `${formatUsdPerCarat(value)} · ${cell.report_count} synthetic звітів`;
    button.setAttribute("aria-label", button.title);
    button.addEventListener("click", () => {
      const bandLabel = (data.benchmark_bands || []).find((band) => band.key === cell.benchmark_band)?.label || "Synthetic benchmark недоступний";
      showSomCellDetails(benchmarkCellDetails, value === null || value === undefined
        ? `Клітинка ${cell.x + 1} × ${cell.y + 1}. У ній немає synthetic benchmark.`
        : `Клітинка ${cell.x + 1} × ${cell.y + 1} · ${bandLabel}. Медіанний дозволений synthetic орієнтир: ${formatUsdPerCarat(value)}. ${cell.report_count} synthetic звітів.`);
    });
    if (selected && cell.x === selected.som_x && cell.y === selected.som_y) button.classList.add("is-selected");
    benchmarkGrid.append(button);
  }
  const benchmarkViewport = createElement("div", "demo-som-map__viewport");
  benchmarkViewport.append(benchmarkGrid);
  const benchmarkLegend = createElement("div", "demo-som-legend demo-som-benchmark-legend");
  for (const band of data.benchmark_bands || []) {
    const item = createElement("div", `demo-som-legend__item demo-som-benchmark-legend__item--${band.key}`);
    const lower = band.lower_bound_usd_per_carat === null || band.lower_bound_usd_per_carat === undefined ? null : formatUsdPerCarat(band.lower_bound_usd_per_carat);
    const upper = band.upper_bound_usd_per_carat === null || band.upper_bound_usd_per_carat === undefined ? null : formatUsdPerCarat(band.upper_bound_usd_per_carat);
    const range = lower && upper ? `${lower} – ${upper}` : lower ? `від ${lower}` : `до ${upper}`;
    item.append(createElement("strong", "", band.label), createElement("span", "", `${range} · ${band.cell_count} клітинок`));
    benchmarkLegend.append(item);
  }
  benchmarkMap.append(
    createElement("h3", "", "Карта synthetic benchmark сегментів · USD/ct"),
    benchmarkViewport,
    benchmarkCellDetails,
    createElement("p", "demo-som-scroll-hint", "На вузькому екрані проведіть карту горизонтально."),
    benchmarkLegend,
    createElement("p", "account-help", "Та самі SOM-координати й marker. Значення в клітинці — медіанний дозволений synthetic USD/ct; це не прогноз, не market value і не інвестиційна категорія."),
  );
  const benchmarkProfile = createElement("aside", "demo-som-profile");
  const selectedBenchmarkCell = selected
    ? data.cells.find((cell) => cell.x === selected.som_x && cell.y === selected.som_y)
    : null;
  if (selectedBenchmarkCell?.median_reference_usd_per_carat !== null && selectedBenchmarkCell?.median_reference_usd_per_carat !== undefined) {
    const selectedBenchmark = createElement("section", "demo-som-benchmark demo-som-benchmark--summary");
    selectedBenchmark.append(
      createElement("h4", "", "Медіанний дозволений synthetic орієнтир клітинки"),
      createElement("strong", "", formatUsdPerCarat(selectedBenchmarkCell.median_reference_usd_per_carat)),
      createElement("span", "", `Клітинка ${selected.som_x + 1} × ${selected.som_y + 1} · ${selectedBenchmarkCell.report_count} synthetic звітів.`),
    );
    benchmarkProfile.append(selectedBenchmark);
  }
  benchmarkProfile.append(
    createElement("h3", "", "Як читати benchmark-карту"),
    createElement("p", "account-help", "Кожна клітинка показує медіанний дозволений synthetic USD/ct каменів у цій самій SOM-клітинці. Тому карта зберігає сусідство основної SOM, але підсвічує відносний рівень synthetic орієнтирів."),
    createElement("p", "account-help", "Чотири кольори — квартилі медіан клітинок поточного immutable artifact. Вони не є класами якості, ринковими сегментами, predicted price чи investment category."),
    createElement("p", "account-help", "Значення у клітинках скорочені до k для читабельності; повне USD/ct доступне у підказці та доступній назві клітинки. Marker відповідає вибраному звіту і збігається з marker основної карти."),
  );
  const benchmarkLayout = createElement("div", "demo-som-layout demo-som-layout--benchmark");
  benchmarkLayout.append(benchmarkMap, benchmarkProfile);
  container.replaceChildren(overviewSection, layout, benchmarkLayout);
}

function initDemoWorkflowTabs(root, datasetId, token, labelFor) {
  const tabButtons = [...root.querySelectorAll("[data-demo-tab]")];
  const panels = {
    reports: root.querySelector("#demo-reports-panel"),
    experts: root.querySelector("#demo-experts-panel"),
    administrators: root.querySelector("#demo-administrators-panel"),
    narratives: root.querySelector("#demo-narratives-panel"),
    quality: root.querySelector("#demo-quality-panel"),
    providers: root.querySelector("#demo-providers-panel"),
    stones: root.querySelector("#demo-stones-panel"),
    currency: root.querySelector("#demo-currency-panel"),
  };
  const form = root.querySelector("#demo-workflow-slice");
  const controls = root.querySelector("#demo-workflow-controls");
  const periodSummaryNode = root.querySelector("#demo-workflow-period-summary");
  const expertResults = root.querySelector("#demo-experts-results");
  const administratorResults = root.querySelector("#demo-administrators-results");
  const narrativeStatus = root.querySelector("#demo-narratives-status");
  const narrativeResults = root.querySelector("#demo-narratives-results");
  const qualityStatus = root.querySelector("#demo-quality-status");
  const qualityResults = root.querySelector("#demo-quality-results");
  const expertStatus = root.querySelector("#demo-experts-status");
  const administratorStatus = root.querySelector("#demo-administrators-status");
  const providerStatus = root.querySelector("#demo-providers-status");
  const providerResults = root.querySelector("#demo-providers-results");
  const currencyStatus = root.querySelector("#demo-currency-status");
  const currencyResults = root.querySelector("#demo-currency-results");
  const periodHelpNode = root.querySelector("#demo-workflow-period-help");
  const somStatus = root.querySelector("#demo-som-status");
  const somResults = root.querySelector("#demo-som-results");
  const somSearchForm = root.querySelector("#demo-som-report-search");
  const somSearchInput = root.querySelector("#demo-som-report-id");
  const dialog = root.querySelector("#demo-workflow-actor-dialog");
  const dialogContent = root.querySelector("#demo-workflow-actor-dialog-content");
  const providerDialog = root.querySelector("#demo-provider-dialog");
  const providerDialogContent = root.querySelector("#demo-provider-dialog-content");
  if (!form || !controls || !periodSummaryNode || !periodHelpNode || !expertResults || !administratorResults || !narrativeStatus || !narrativeResults || !qualityStatus || !qualityResults || !providerResults || !currencyStatus || !currencyResults || !expertStatus || !administratorStatus || !providerStatus || !somStatus || !somResults || !somSearchForm || !somSearchInput || !dialog || !dialogContent || !providerDialog || !providerDialogContent) return;

  let activeTab = "reports";

  const activate = (tab) => {
    activeTab = tab;
    for (const [name, panel] of Object.entries(panels)) panel.hidden = name !== tab;
    controls.hidden = !["experts", "narratives", "quality", "administrators", "providers", "currency"].includes(tab);
    periodHelpNode.textContent = tab === "currency"
      ? "Зріз застосовується до офіційної дати курсу НБУ. Він не фільтрує demo-звіти, орієнтири чи SOM."
      : "Дані за весь доступний період. У demo зрізі події та тривалості формуються детерміновано; вони не є active-time, review-cycle, SLA чи оцінкою реальних людей.";
    for (const button of tabButtons) {
      const active = button.dataset.demoTab === tab;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-selected", String(active));
    }
  };
  const filtersForSlice = () => Object.fromEntries(new FormData(form).entries());
  const validateSlice = (filters) => {
    if (!filters.date_from || !filters.date_to || filters.date_from <= filters.date_to) return true;
    const message = "Дата «Від» не може бути пізнішою за дату «До».";
    setStatus(expertStatus, message, "error");
    setStatus(administratorStatus, message, "error");
    setStatus(narrativeStatus, message, "error");
    setStatus(qualityStatus, message, "error");
    setStatus(providerStatus, message, "error");
    setStatus(currencyStatus, message, "error");
    return false;
  };
  const loadWorkflow = async () => {
    const filters = filtersForSlice();
    if (!validateSlice(filters)) return;
    setStatus(expertStatus, "Завантаження synthetic workflow…");
    setStatus(administratorStatus, "Завантаження synthetic workflow…");
    try {
      const data = await getDemoWorkflowAnalytics(datasetId, token, filters);
      expertStatus.replaceChildren();
      administratorStatus.replaceChildren();
      periodSummaryNode.textContent = periodSummary(filters);
      renderWorkflowRows(expertResults, data.experts, dialog, dialogContent, data.dataset_id);
      renderSyntheticAdministrators(administratorResults, data.administrators, data.dataset_id);
    } catch {
      setStatus(expertStatus, "Не вдалося завантажити synthetic workflow.", "error");
      setStatus(administratorStatus, "Не вдалося завантажити synthetic workflow.", "error");
    }
  };
  const loadProviders = async () => {
    const filters = filtersForSlice();
    if (!validateSlice(filters)) return;
    setStatus(providerStatus, "Завантаження synthetic provider analytics…");
    try {
      const data = await getDemoProviderAnalytics(datasetId, token, filters);
      providerStatus.replaceChildren();
      periodSummaryNode.textContent = periodSummary(filters);
      renderDemoProviderAnalytics(providerResults, data, data.dataset_id, providerDialog, providerDialogContent);
    } catch {
      setStatus(providerStatus, "Не вдалося завантажити synthetic provider analytics.", "error");
    }
  };
  const loadNarratives = async () => {
    const filters = filtersForSlice();
    if (!validateSlice(filters)) return;
    setStatus(narrativeStatus, "Завантаження synthetic текстових метаданих…");
    try {
      const data = await getDemoNarrativeQualityAnalytics(datasetId, token, filters);
      narrativeStatus.replaceChildren();
      periodSummaryNode.textContent = periodSummary(filters);
      renderNarrativeAnalytics(narrativeResults, data, {
        reportHref: (reportId) => `/demo-report-detail.html?dataset=${encodeURIComponent(datasetId)}&id=${encodeURIComponent(reportId)}`,
        formatDateTime,
      });
    } catch {
      setStatus(narrativeStatus, "Не вдалося завантажити synthetic текстові метадані.", "error");
    }
  };
  const loadQuality = async () => {
    const filters = filtersForSlice();
    if (!validateSlice(filters)) return;
    setStatus(qualityStatus, "Завантаження synthetic операцій та повноти даних…");
    try {
      const data = await getDemoOperationalQualityAnalytics(datasetId, token, filters);
      qualityStatus.replaceChildren();
      periodSummaryNode.textContent = periodSummary(filters);
      renderOperationalQuality(qualityResults, data, { formatDateTime });
    } catch {
      setStatus(qualityStatus, "Не вдалося завантажити synthetic операції та повноту даних.", "error");
    }
  };
  const loadCurrencySources = async () => {
    const filters = filtersForSlice();
    if (!validateSlice(filters)) return;
    setStatus(currencyStatus, "Завантаження офіційних FX-знімків НБУ…");
    try {
      const snapshots = await getFxDataSnapshots(filters, token);
      currencyStatus.replaceChildren();
      periodSummaryNode.textContent = periodSummary(filters);
      renderCurrencySources(currencyResults, snapshots, providerDialog, providerDialogContent);
    } catch {
      setStatus(currencyStatus, "Не вдалося завантажити FX-знімки НБУ.", "error");
    }
  };
  const loadSom = async (requestedId = new URLSearchParams(window.location.search).get("som_report") || "") => {
    setStatus(somStatus, "Завантаження synthetic SOM…");
    try {
      const selectedId = requestedId.trim().toUpperCase();
      const data = await getDemoSom(datasetId, token, selectedId);
      somSearchInput.value = data.selected_report?.report_id || selectedId;
      somStatus.replaceChildren();
      renderSom(somResults, data, labelFor);
    } catch {
      setStatus(somStatus, "Для цього номера немає доступного synthetic SOM-профілю. Перевірте DEMO-ідентифікатор.", "error");
    }
  };
  for (const button of tabButtons) button.addEventListener("click", () => {
    activate(button.dataset.demoTab);
    if (button.dataset.demoTab === "stones") void loadSom();
    if (button.dataset.demoTab === "narratives") void loadNarratives();
    if (button.dataset.demoTab === "quality") void loadQuality();
    if (button.dataset.demoTab === "providers") void loadProviders();
    if (button.dataset.demoTab === "currency") void loadCurrencySources();
  });
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    if (activeTab === "narratives") void loadNarratives();
    else if (activeTab === "quality") void loadQuality();
    else if (activeTab === "providers") void loadProviders();
    else if (activeTab === "currency") void loadCurrencySources();
    else void loadWorkflow();
  });
  somSearchForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const reportId = somSearchInput.value.trim().toUpperCase();
    if (!reportId) return;
    const params = new URLSearchParams(window.location.search);
    params.set("tab", "stones");
    params.set("som_report", reportId);
    window.history.replaceState({}, "", `${window.location.pathname}?${params}`);
    void loadSom(reportId);
  });
  form.addEventListener("reset", () => window.setTimeout(() => {
    if (activeTab === "narratives") void loadNarratives();
    else if (activeTab === "quality") void loadQuality();
    else if (activeTab === "providers") void loadProviders();
    else if (activeTab === "currency") void loadCurrencySources();
    else void loadWorkflow();
  }, 0));
  dialog.addEventListener("close", () => dialogContent.replaceChildren());
  providerDialog.addEventListener("close", () => providerDialogContent.replaceChildren());
  void loadWorkflow();
  const requestedTab = new URLSearchParams(window.location.search).get("tab");
  if (requestedTab === "stones") { activate("stones"); void loadSom(); }
  if (requestedTab === "providers") { activate("providers"); void loadProviders(); }
  if (requestedTab === "narratives") { activate("narratives"); void loadNarratives(); }
  if (requestedTab === "quality") { activate("quality"); void loadQuality(); }
  if (requestedTab === "currency") { activate("currency"); void loadCurrencySources(); }
}

export async function initDemoReports() {
  const root = document.querySelector("[data-demo-reports]");
  if (!root || localStorage.getItem("role") !== "admin") return;
  localizeDemoShell(root);
  document.addEventListener("diamant:locale-change", () => localizeDemoShell(root));
  const token = localStorage.getItem("token");
  const tbody = root.querySelector("#demo-reports-body");
  const pagination = root.querySelector("#demo-pagination");
  const stateNode = root.querySelector("#demo-dashboard-status");
  const form = root.querySelector("#demo-dashboard-filters");
  const search = root.querySelector("#demo-report-search");
  const status = root.querySelector("#demo-quick-report-status");
  const marketStatus = root.querySelector("#demo-quick-market-status");
  const toggleFilters = root.querySelector("#demo-toggle-filters");
  const advanced = root.querySelector("#demo-advanced-filters");
  if (!token || !tbody || !pagination || !stateNode || !form || !search || !status || !marketStatus) return;

  let state = getUrlState();
  let datasetId = PREFERRED_DATASET_ID;
  let labelFor = (_category, value) => String(value ?? "—");
  search.value = state.search;
  status.value = state.report_status;
  marketStatus.value = state.market_status;
  for (const control of [...form.elements].filter((element) => element.name && !["empty_narrative", "narrative_presence"].includes(element.name))) control.value = state[control.name] || "";
  applyNarrativeCompleteness(form, state.empty_narrative, state.narrative_presence);

  try {
    let dataset;
    for (const candidate of [PREFERRED_DATASET_ID, ...FALLBACK_DATASET_IDS]) {
      try {
        dataset = await getDemoDataset(candidate, token);
        datasetId = candidate;
        break;
      } catch {
        // A local environment can intentionally retain an earlier immutable dataset.
      }
    }
    if (!dataset) throw new Error("Demo dataset is unavailable");
    const mappings = await getGradeMappings(token);
    root.querySelector("#demo-dataset-meta").textContent = `${dataset.label} · ${dataset.record_count} записів · ${dataset.version}`;
    labelFor = (category, value) => mappings.find((item) => item.category === category && item.grade_value === value)?.grade_label || "—";
    populateGradeFilter(root.querySelector("#demo-color-filter"), "color", mappings);
    populateGradeFilter(root.querySelector("#demo-clarity-filter"), "clarity", mappings);
    populateGradeFilter(root.querySelector("#demo-cut-filter"), "cut", mappings);
    for (const control of [root.querySelector("#demo-color-filter"), root.querySelector("#demo-clarity-filter"), root.querySelector("#demo-cut-filter")]) control.value = state[control.name] || "";
  } catch {
    setStatus(stateNode, "Demo-набір недоступний.", "error");
    return;
  }

  const load = async (nextState = state) => {
    state = { ...nextState, page: Math.max(Number(nextState.page) || 1, 1) };
    updateUrl(state);
    updateSortIndicators(root, state.sort);
    setStatus(stateNode, "Завантаження demo-звітів…");
    tbody.replaceChildren();
    pagination.replaceChildren();
    try {
      const result = await getDemoReports(datasetId, token, state.page, { ...state, page_size: PAGE_SIZE });
      if (!result.items.length) {
        setStatus(stateNode, "Demo-звітів за поточними умовами не знайдено.");
        return;
      }
      stateNode.replaceChildren();
      renderRows(tbody, result.items, labelFor, datasetId);
      renderPagination(pagination, result.page, result.total_pages, (page) => load({ ...state, page }));
    } catch {
      setStatus(stateNode, "Не вдалося завантажити demo-звіти. Спробуйте пізніше.", "error");
    }
  };

  document.addEventListener("diamant:locale-change", () => { void load(state); });
  let searchTimer;
  search.addEventListener("input", () => {
    window.clearTimeout(searchTimer);
    searchTimer = window.setTimeout(() => load({ ...state, page: 1, search: search.value.trim() }), 300);
  });
  status.addEventListener("change", () => load({ ...state, page: 1, report_status: status.value }));
  marketStatus.addEventListener("change", () => load({ ...state, page: 1, market_status: marketStatus.value }));
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const advancedFilters = Object.fromEntries(new FormData(form).entries());
    advancedFilters.empty_narrative = readNarrativeCompleteness(form);
    advancedFilters.narrative_presence = readNarrativePresence(form);
    load({ ...state, ...advancedFilters, page: 1 });
  });
  form.addEventListener("reset", () => window.setTimeout(() => {
    const cleared = Object.fromEntries([...form.elements].filter((element) => element.name).map((element) => [element.name, ""]));
    cleared.empty_narrative = [];
    cleared.narrative_presence = "empty";
    load({ ...state, ...cleared, page: 1 });
  }, 0));
  toggleFilters.addEventListener("click", () => {
    const isOpen = advanced.classList.toggle("is-visible");
    toggleFilters.setAttribute("aria-expanded", String(isOpen));
  });
  for (const button of root.querySelectorAll("[data-demo-sort-key]")) {
    button.addEventListener("click", () => load({ ...state, page: 1, sort: toggleSort(state.sort, button.dataset.demoSortKey) }));
  }
  document.addEventListener("click", closeReportOverlays);
  document.addEventListener("keydown", (event) => { if (event.key === "Escape") closeReportOverlays(); });
  initDemoWorkflowTabs(root, datasetId, token, labelFor);
  await load(state);
}
