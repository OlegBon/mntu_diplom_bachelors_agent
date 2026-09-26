import { getDemoDataset, getDemoReports, getDemoWorkflowAnalytics, getGradeMappings } from "./api.js";
import { closeReportOverlays, formatDateTime, renderMarketReferencePrice } from "./dashboard.js";

const PREFERRED_DATASET_ID = "synthetic-demo-v3";
const FALLBACK_DATASET_IDS = ["synthetic-demo-v2", "synthetic-demo-v1"];
const PAGE_SIZE = 25;
const REPORT_STATUS_LABELS = { issued: "Видано" };
const SALE_STATUS_LABELS = { not_for_sale: "Не продається" };

function createElement(tagName, className, textContent) {
  const element = document.createElement(tagName);
  if (className) element.className = className;
  if (textContent !== undefined) element.textContent = textContent;
  return element;
}

function createBadge(value, kind) {
  return createElement("span", `status-badge status-badge--${kind}`, value);
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
    sort: params.get("sort") || "report_id_desc",
  };
}

function updateUrl(state) {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(state)) {
    if (value && !(key === "page" && Number(value) === 1)) params.set(key, String(value));
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
  menu.append(detail, edit, print);
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
    reportStatus.append(createBadge(REPORT_STATUS_LABELS[report.status] || report.status, report.status));
    row.append(reportStatus);
    const saleStatus = document.createElement("td");
    saleStatus.append(createBadge(SALE_STATUS_LABELS[report.stone.market_status] || report.stone.market_status, "sale-not-sold"));
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

function formatDuration(totalSeconds) {
  if (!totalSeconds) return "—";
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.round((totalSeconds % 3600) / 60);
  return hours ? `${hours} год ${minutes} хв` : `${minutes} хв`;
}

function workflowPeriodSummary(filters) {
  if (filters.date_from && filters.date_to) return `Поточний зріз: з ${filters.date_from} до ${filters.date_to}.`;
  if (filters.date_from) return `Поточний зріз: від ${filters.date_from}.`;
  if (filters.date_to) return `Поточний зріз: до ${filters.date_to}.`;
  return "Поточний зріз: за весь доступний час.";
}

function openSyntheticActorDialog(dialog, content, actor) {
  const metrics = document.createElement("dl");
  metrics.className = "analytics-metrics";
  const rows = [
    ["Роль", actor.role === "admin" ? "Synthetic administrator" : "Synthetic gemologist"],
    ["Звітів у workflow", actor.reports_touched],
    ["Завершених інтервалів", actor.completed_intervals],
    ["Сумарний synthetic час", formatDuration(actor.total_duration_seconds)],
    ["Середній інтервал", formatDuration(actor.avg_duration_seconds)],
  ];
  for (const [label, value] of rows) metrics.append(createElement("dt", "", label), createElement("dd", "", String(value)));
  content.replaceChildren(
    createElement("h3", "analytics-dialog-name", actor.display_name),
    metrics,
    createElement("p", "account-help", "Це вигаданий, детермінований actor demo-набору. Він не є обліковим записом, не має профілю та не представляє реальну людину."),
  );
  dialog.showModal();
}

function renderWorkflowRows(tbody, actors, dialog, dialogContent) {
  tbody.replaceChildren();
  if (!actors.length) {
    const row = document.createElement("tr");
    const cell = createElement("td", "", "За обраний період synthetic-подій немає.");
    cell.colSpan = 5;
    row.append(cell);
    tbody.append(row);
    return;
  }
  for (const actor of actors) {
    const row = document.createElement("tr");
    const actorButton = createElement("button", "analytics-expert-button", actor.display_name);
    actorButton.type = "button";
    actorButton.addEventListener("click", () => openSyntheticActorDialog(dialog, dialogContent, actor));
    const actorCell = document.createElement("td");
    actorCell.append(actorButton);
    row.append(
      actorCell,
      createElement("td", "", String(actor.reports_touched)),
      createElement("td", "", String(actor.completed_intervals)),
      createElement("td", "", formatDuration(actor.total_duration_seconds)),
      createElement("td", "", formatDuration(actor.avg_duration_seconds)),
    );
    tbody.append(row);
  }
}

function initDemoWorkflowTabs(root, datasetId, token) {
  const tabButtons = [...root.querySelectorAll("[data-demo-tab]")];
  const panels = {
    reports: root.querySelector("#demo-reports-panel"),
    experts: root.querySelector("#demo-experts-panel"),
    administrators: root.querySelector("#demo-administrators-panel"),
  };
  const form = root.querySelector("#demo-workflow-slice");
  const controls = root.querySelector("#demo-workflow-controls");
  const periodSummary = root.querySelector("#demo-workflow-period-summary");
  const expertBody = root.querySelector("#demo-experts-body");
  const administratorBody = root.querySelector("#demo-administrators-body");
  const expertStatus = root.querySelector("#demo-experts-status");
  const administratorStatus = root.querySelector("#demo-administrators-status");
  const dialog = root.querySelector("#demo-workflow-actor-dialog");
  const dialogContent = root.querySelector("#demo-workflow-actor-dialog-content");
  if (!form || !controls || !periodSummary || !expertBody || !administratorBody || !expertStatus || !administratorStatus || !dialog || !dialogContent) return;

  const activate = (tab) => {
    for (const [name, panel] of Object.entries(panels)) panel.hidden = name !== tab;
    controls.hidden = tab === "reports";
    for (const button of tabButtons) {
      const active = button.dataset.demoTab === tab;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-selected", String(active));
    }
  };
  const load = async () => {
    const filters = Object.fromEntries(new FormData(form).entries());
    if (filters.date_from && filters.date_to && filters.date_from > filters.date_to) {
      setStatus(expertStatus, "Дата «Від» не може бути пізнішою за дату «До».", "error");
      setStatus(administratorStatus, "Дата «Від» не може бути пізнішою за дату «До».", "error");
      return;
    }
    setStatus(expertStatus, "Завантаження synthetic workflow…");
    setStatus(administratorStatus, "Завантаження synthetic workflow…");
    try {
      const data = await getDemoWorkflowAnalytics(datasetId, token, filters);
      expertStatus.replaceChildren();
      administratorStatus.replaceChildren();
      periodSummary.textContent = workflowPeriodSummary(filters);
      renderWorkflowRows(expertBody, data.experts, dialog, dialogContent);
      renderWorkflowRows(administratorBody, data.administrators, dialog, dialogContent);
    } catch {
      setStatus(expertStatus, "Не вдалося завантажити synthetic workflow.", "error");
      setStatus(administratorStatus, "Не вдалося завантажити synthetic workflow.", "error");
    }
  };
  for (const button of tabButtons) button.addEventListener("click", () => activate(button.dataset.demoTab));
  form.addEventListener("submit", (event) => { event.preventDefault(); void load(); });
  form.addEventListener("reset", () => window.setTimeout(() => void load(), 0));
  dialog.addEventListener("close", () => dialogContent.replaceChildren());
  void load();
}

export async function initDemoReports() {
  const root = document.querySelector("[data-demo-reports]");
  if (!root || localStorage.getItem("role") !== "admin") return;
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
  for (const control of [...form.elements].filter((element) => element.name)) control.value = state[control.name] || "";

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

  let searchTimer;
  search.addEventListener("input", () => {
    window.clearTimeout(searchTimer);
    searchTimer = window.setTimeout(() => load({ ...state, page: 1, search: search.value.trim() }), 300);
  });
  status.addEventListener("change", () => load({ ...state, page: 1, report_status: status.value }));
  marketStatus.addEventListener("change", () => load({ ...state, page: 1, market_status: marketStatus.value }));
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    load({ ...state, ...Object.fromEntries(new FormData(form).entries()), page: 1 });
  });
  form.addEventListener("reset", () => window.setTimeout(() => {
    const cleared = Object.fromEntries([...form.elements].filter((element) => element.name).map((element) => [element.name, ""]));
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
  initDemoWorkflowTabs(root, datasetId, token);
  await load(state);
}
