import { ApiRequestError, getCurrentUser, getExperts, getGradeMappings, getReportDashboard } from "./api.js";
import { logout } from "./auth.js";
import { registerVisibleDataRefresh } from "./page-refresh.js";

const PAGE_SIZE = 25;
const DEFAULT_SORT = "report_date_desc";
const DATASET_PERIOD = "01.01.2023–31.12.2025";
const REPORT_STATUS_LABELS = { draft: "Чернетка", review: "На перевірці", issued: "Видано", void: "Анульовано" };
const SALE_STATUS_LABELS = { false: "Не продано", true: "Продано" };

function createElement(tagName, className, textContent) {
  const element = document.createElement(tagName);
  if (className) element.className = className;
  if (textContent !== undefined) element.textContent = textContent;
  return element;
}

function formatDateTime(value) {
  const date = new Date(value);
  return {
    date: new Intl.DateTimeFormat("uk-UA", { dateStyle: "medium" }).format(date),
    time: new Intl.DateTimeFormat("uk-UA", { hour: "2-digit", minute: "2-digit" }).format(date),
  };
}

function formatDemoPrice(value) {
  if (value === null || value === undefined) return "—";
  return new Intl.NumberFormat("uk-UA", { maximumFractionDigits: 2 }).format(Number(value));
}

function setStatus(container, message, kind = "info") {
  container.replaceChildren(createElement("p", `dashboard-state dashboard-state--${kind}`, message));
}

function getUrlState() {
  const params = new URLSearchParams(window.location.search);
  return {
    page: Math.max(Number.parseInt(params.get("page") || "1", 10) || 1, 1),
    search: params.get("search") || "",
    report_status: params.get("report_status") || "",
    sold: params.get("sold") || "",
    expert_id: params.get("expert_id") || "",
    sort: params.get("sort") || DEFAULT_SORT,
    shape: params.get("shape") || "",
    color_grade: params.get("color_grade") || "",
    clarity_grade: params.get("clarity_grade") || "",
    cut_grade: params.get("cut_grade") || "",
    carat_min: params.get("carat_min") || "",
    carat_max: params.get("carat_max") || "",
    price_min: params.get("price_min") || "",
    price_max: params.get("price_max") || "",
    date_from: params.get("date_from") || "",
    date_to: params.get("date_to") || "",
  };
}

function updateUrl(state) {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(state)) {
    if (value && !(key === "page" && Number(value) === 1) && !(key === "sort" && value === DEFAULT_SORT)) params.set(key, String(value));
  }
  const query = params.toString();
  window.history.replaceState({}, "", `${window.location.pathname}${query ? `?${query}` : ""}`);
}

function closeOverlays() {
  for (const menu of document.querySelectorAll(".report-actions__menu:not([hidden]), .report-price__popover:not([hidden])")) menu.hidden = true;
  for (const toggle of document.querySelectorAll(".report-actions__toggle[aria-expanded='true'], .report-price__toggle[aria-expanded='true']")) toggle.setAttribute("aria-expanded", "false");
}

function renderActions(report) {
  const { report_id: reportId, status } = report;
  const wrapper = createElement("div", "report-actions");
  const toggle = createElement("button", "report-actions__toggle", "⋮");
  toggle.type = "button";
  toggle.setAttribute("aria-label", `Відкрити дії для звіту ${reportId}`);
  toggle.setAttribute("aria-expanded", "false");
  const menu = createElement("div", "report-actions__menu");
  menu.hidden = true;
  const detail = createElement("a", "report-actions__item", "Переглянути");
  detail.href = `/report-detail.html?id=${encodeURIComponent(reportId)}`;
  const edit = status === "draft"
    ? createElement("a", "report-actions__item", "Редагувати")
    : createElement("button", "report-actions__item", "Редагувати");
  if (status === "draft") {
    edit.href = `/report-detail.html?id=${encodeURIComponent(reportId)}&edit=1`;
  } else {
    edit.type = "button";
    edit.disabled = true;
    edit.title = "Редагування доступне лише для чернетки";
  }
  const print = createElement("a", "report-actions__item", "Друк");
  print.href = `/report-detail.html?id=${encodeURIComponent(reportId)}&print=1`;
  print.target = "_blank";
  print.rel = "noopener noreferrer";
  menu.append(detail, edit, print);
  toggle.addEventListener("click", (event) => {
    event.stopPropagation();
    const isOpen = menu.hidden;
    closeOverlays();
    menu.hidden = !isOpen;
    toggle.setAttribute("aria-expanded", String(isOpen));
  });
  wrapper.append(toggle, menu);
  return wrapper;
}

function renderPrice(report) {
  if (report.market_reference) return renderMarketReferencePrice(report);
  if (report.price === null || report.price === undefined) return createElement("span", "report-price__missing", "—");
  const wrapper = createElement("div", "report-price");
  const toggle = createElement("button", "report-price__toggle");
  toggle.type = "button";
  toggle.setAttribute("aria-label", `Пояснення demo-ціни звіту ${report.report_id}`);
  toggle.setAttribute("aria-expanded", "false");
  toggle.append(document.createTextNode(`USD ${formatDemoPrice(report.price)} `), createElement("sup", "report-price__indicator", "d"));
  const popover = createElement("div", "report-price__popover");
  popover.hidden = true;
  const date = formatDateTime(report.report_date);
  for (const [label, value] of [["Тип", "Demo-значення"], ["Джерело", "diamonds_dataset.csv"], ["Дата фіксації", date.date], ["Період набору", DATASET_PERIOD]]) {
    const row = createElement("p", "report-price__detail");
    row.append(createElement("strong", "", `${label}: `), document.createTextNode(value));
    popover.append(row);
  }
  popover.append(createElement("p", "report-price__warning", "Не є актуальним ринковим котируванням."));
  toggle.addEventListener("click", (event) => {
    event.stopPropagation();
    const isOpen = popover.hidden;
    closeOverlays();
    popover.hidden = !isOpen;
    toggle.setAttribute("aria-expanded", String(isOpen));
  });
  wrapper.append(toggle, popover);
  return wrapper;
}

function formatFxRate(value) {
  if (value === null || value === undefined) return "—";
  return new Intl.NumberFormat("uk-UA", { maximumFractionDigits: 8 }).format(Number(value));
}

function formatDateOnly(value) {
  if (!value) return "—";
  return new Intl.DateTimeFormat("uk-UA", { dateStyle: "medium" }).format(new Date(`${value}T12:00:00`));
}

function renderMarketReferencePrice(report) {
  const reference = report.market_reference;
  const isSystemReference = reference.valuation_kind === "system_market_reference";
  const marker = "of";
  const referenceType = isSystemReference
    ? "Системний довідковий орієнтир"
    : "Підтверджений довідковий орієнтир";
  const wrapper = createElement("div", "report-price");
  const toggle = createElement("button", "report-price__toggle");
  toggle.type = "button";
  toggle.setAttribute("aria-label", `Пояснення ринкового орієнтира звіту ${report.report_id}`);
  toggle.setAttribute("aria-expanded", "false");
  toggle.append(document.createTextNode(`USD ${formatDemoPrice(reference.amount)} `), createElement("sup", "report-price__indicator", marker));
  const popover = createElement("div", "report-price__popover");
  popover.hidden = true;
  const observed = formatDateTime(reference.observed_at);
  const details = [
    ["Тип", referenceType],
    ["Провайдер", reference.source_name],
    ["Знімок OpenFacet", `#${reference.market_snapshot_id ?? "—"}`],
    ["Отримано", observed.date],
  ];
  if (reference.converted_amount && reference.converted_currency_code) {
    details.push(["Еквівалент", `${reference.converted_currency_code} ${formatDemoPrice(reference.converted_amount)}`]);
    details.push(["Курс НБУ", `${formatFxRate(reference.fx_rate)} UAH/USD · ${formatDateOnly(reference.fx_rate_date)} · знімок #${reference.fx_snapshot_id ?? "—"}`]);
  }
  for (const [label, value] of details) {
    const row = createElement("p", "report-price__detail");
    row.append(createElement("strong", "", `${label}: `), document.createTextNode(value));
    popover.append(row);
  }
  popover.append(createElement(
    "p",
    "report-price__warning",
    isSystemReference
      ? "Розраховано системою за останнім затвердженим знімком; не є експертною, продажною чи транзакційною ціною."
      : "Застосовність підтверджена адміністратором; не є експертною, продажною чи транзакційною ціною.",
  ));
  toggle.addEventListener("click", (event) => {
    event.stopPropagation();
    const isOpen = popover.hidden;
    closeOverlays();
    popover.hidden = !isOpen;
    toggle.setAttribute("aria-expanded", String(isOpen));
  });
  wrapper.append(toggle, popover);
  return wrapper;
}

function makeMappingLookup(mappings) {
  const lookup = new Map();
  for (const mapping of mappings) lookup.set(`${mapping.category}:${mapping.grade_value}`, mapping.grade_label);
  return (category, value) => lookup.get(`${category}:${value}`) || String(value ?? "—");
}

function populateGradeFilter(select, category, mappings) {
  for (const mapping of mappings.filter((item) => item.category === category)) {
    const option = createElement("option", "", mapping.grade_label);
    option.value = String(mapping.grade_value);
    select.append(option);
  }
}

function createBadge(value, kind) {
  return createElement("span", `status-badge status-badge--${kind}`, value);
}

function renderRows(tbody, reports, labelFor) {
  tbody.replaceChildren();
  for (const report of reports) {
    const row = document.createElement("tr");
    const idCell = document.createElement("td");
    const idLink = createElement("a", "id-link", report.report_id);
    idLink.href = `/report-detail.html?id=${encodeURIComponent(report.report_id)}`;
    idLink.title = "Відкрити приватний перегляд звіту";
    idCell.append(idLink);
    row.append(idCell);
    const dateCell = document.createElement("td");
    const date = formatDateTime(report.report_date);
    dateCell.append(createElement("strong", "date-primary", date.date), createElement("span", "date-secondary", date.time));
    row.append(dateCell);
    for (const value of [report.stone.shape, report.stone.carat_weight]) row.append(createElement("td", "", value));
    row.append(createElement("td", "", labelFor("color", report.stone.color_grade)));
    row.append(createElement("td", "", labelFor("clarity", report.stone.clarity_grade)));
    const cutCell = document.createElement("td");
    cutCell.append(createBadge(labelFor("cut", report.system_cut_grade), "cut"));
    row.append(cutCell);
    const priceCell = document.createElement("td");
    priceCell.append(renderPrice(report));
    row.append(priceCell);
    const reportStatusCell = document.createElement("td");
    reportStatusCell.append(createBadge(REPORT_STATUS_LABELS[report.status] || report.status, report.status));
    row.append(reportStatusCell);
    const saleStatusCell = document.createElement("td");
    const isSold = report.stone.market_status === "sold";
    saleStatusCell.append(createBadge(SALE_STATUS_LABELS[String(isSold)], `sale-${isSold ? "sold" : "not-sold"}`));
    row.append(saleStatusCell);
    const actionsCell = document.createElement("td");
    actionsCell.append(renderActions(report));
    row.append(actionsCell);
    tbody.append(row);
  }
}

function renderPagination(container, page, totalPages, onPageChange) {
  container.replaceChildren();
  if (totalPages <= 1) return;
  const makeButton = (label, targetPage, { disabled = false, active = false, icon = false, context = false, ariaLabel } = {}) => {
    const button = createElement("button", `page-btn${active ? " active" : ""}${icon ? " page-btn--icon" : ""}${context ? " page-btn--context" : ""}`, label);
    button.type = "button";
    button.disabled = disabled;
    if (ariaLabel) button.setAttribute("aria-label", ariaLabel);
    if (active) button.setAttribute("aria-current", "page");
    button.addEventListener("click", () => onPageChange(targetPage));
    return button;
  };
  const appendEllipsis = () => container.append(createElement("span", "pagination__ellipsis", "…"));
  const appendPage = (targetPage, context = false) => container.append(makeButton(String(targetPage), targetPage, { active: targetPage === page, context }));

  container.append(
    makeButton("«", 1, { disabled: page === 1, icon: true, ariaLabel: "На першу сторінку" }),
    makeButton("‹", page - 1, { disabled: page === 1, icon: true, ariaLabel: "На попередню сторінку" }),
  );
  appendPage(1);
  const start = Math.max(2, page - 1);
  const end = Math.min(totalPages - 1, page + 1);
  if (start > 2) appendEllipsis();
  for (let item = start; item <= end; item += 1) appendPage(item, item !== page);
  if (end < totalPages - 1) appendEllipsis();
  if (totalPages > 1) appendPage(totalPages);
  container.append(
    makeButton("›", page + 1, { disabled: page === totalPages, icon: true, ariaLabel: "На наступну сторінку" }),
    makeButton("»", totalPages, { disabled: page === totalPages, icon: true, ariaLabel: "На останню сторінку" }),
  );
}

function toggleSort(currentSort, key) {
  return currentSort === `${key}_asc` ? `${key}_desc` : `${key}_asc`;
}

function updateSortIndicators(root, sort) {
  const separator = sort.lastIndexOf("_");
  const key = sort.slice(0, separator);
  const direction = sort.slice(separator + 1);
  for (const button of root.querySelectorAll(".table-sort")) {
    const active = button.dataset.sortKey === key;
    button.toggleAttribute("data-sort-direction", active);
    if (active) button.dataset.sortDirection = direction;
    button.parentElement.setAttribute("aria-sort", active ? (direction === "asc" ? "ascending" : "descending") : "none");
  }
}

export async function initDashboard() {
  const root = document.querySelector("[data-dashboard]");
  if (!root) return;
  const token = localStorage.getItem("token");
  const tbody = root.querySelector("tbody");
  const pagination = root.querySelector(".pagination");
  const stateNode = root.querySelector("#dashboard-status");
  const form = root.querySelector("#dashboard-filters");
  const searchInput = root.querySelector("#report-search");
  const reportStatusSelect = root.querySelector("#quick-report-status");
  const saleStatusSelect = root.querySelector("#quick-market-status");
  const expertSelect = root.querySelector("#expert-filter");
  const toggleFilters = root.querySelector("#toggle-filters");
  const filtersPanel = root.querySelector("#advanced-filters");
  if (!token || !tbody || !pagination || !stateNode || !form || !searchInput || !reportStatusSelect || !saleStatusSelect) return;

  let state = getUrlState();
  let labelFor = (_category, value) => String(value ?? "—");
  searchInput.value = state.search;
  reportStatusSelect.value = state.report_status;
  saleStatusSelect.value = state.sold;
  for (const control of [...form.elements].filter((element) => element.name)) control.value = state[control.name] || "";
  const expertFilter = root.querySelector("#expert-filter-wrap");
  // This only prevents a visual layout shift. The API still determines the real role and access.
  if (expertFilter) expertFilter.hidden = localStorage.getItem("username") !== "admin";

  try {
    const [currentUser, mappings] = await Promise.all([getCurrentUser(token), getGradeMappings()]);
    labelFor = makeMappingLookup(mappings);
    populateGradeFilter(root.querySelector("#color-filter"), "color", mappings);
    populateGradeFilter(root.querySelector("#clarity-filter"), "clarity", mappings);
    populateGradeFilter(root.querySelector("#cut-filter"), "cut", mappings);
    for (const select of [root.querySelector("#color-filter"), root.querySelector("#clarity-filter"), root.querySelector("#cut-filter")]) select.value = state[select.name] || "";
    if (expertFilter) expertFilter.hidden = currentUser.role !== "admin";
    if (currentUser.role === "admin" && expertFilter && expertSelect) {
      const experts = await getExperts(token);
      for (const expert of experts) {
        const option = createElement("option", "", expert.username);
        option.value = String(expert.expert_id);
        expertSelect.append(option);
      }
      expertFilter.hidden = false;
      expertSelect.value = state.expert_id;
    }
  } catch (error) {
    if (error instanceof ApiRequestError && error.status === 401) {
      logout("/login.html");
      return;
    }
  }

  const load = async (nextState = state, { silent = false } = {}) => {
    state = { ...nextState, page: Math.max(Number(nextState.page) || 1, 1) };
    updateUrl(state);
    updateSortIndicators(root, state.sort);
    if (!silent) {
      setStatus(stateNode, "Завантаження звітів…");
      tbody.replaceChildren();
      pagination.replaceChildren();
    }
    try {
      const result = await getReportDashboard({ ...state, page_size: PAGE_SIZE }, token);
      if (result.items.length === 0) {
        setStatus(stateNode, "Звітів за поточними умовами не знайдено.");
        return;
      }
      stateNode.replaceChildren();
      renderRows(tbody, result.items, labelFor);
      renderPagination(pagination, result.page, result.total_pages, (page) => load({ ...state, page }));
    } catch (error) {
      if (error instanceof ApiRequestError && error.status === 401) {
        logout("/login.html");
        return;
      }
      setStatus(stateNode, "Не вдалося завантажити звіти. Оновіть сторінку або спробуйте пізніше.", "error");
    }
  };

  let searchTimer;
  searchInput.addEventListener("input", () => {
    window.clearTimeout(searchTimer);
    searchTimer = window.setTimeout(() => load({ ...state, page: 1, search: searchInput.value.trim() }), 300);
  });
  for (const [control, key] of [[reportStatusSelect, "report_status"], [saleStatusSelect, "sold"], [expertSelect, "expert_id"]]) {
    if (control) control.addEventListener("change", () => load({ ...state, page: 1, [key]: control.value }));
  }
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const advancedFilters = Object.fromEntries(new FormData(form).entries());
    load({ ...state, ...advancedFilters, page: 1 });
  });
  form.addEventListener("reset", () => window.setTimeout(() => {
    const cleared = Object.fromEntries([...form.elements].filter((element) => element.name).map((element) => [element.name, ""]));
    load({ ...state, ...cleared, page: 1 });
  }, 0));
  if (toggleFilters && filtersPanel) {
    toggleFilters.addEventListener("click", () => {
      const isOpen = filtersPanel.classList.toggle("is-visible");
      toggleFilters.setAttribute("aria-expanded", String(isOpen));
    });
  }
  for (const button of root.querySelectorAll(".table-sort")) {
    button.addEventListener("click", () => load({ ...state, page: 1, sort: toggleSort(state.sort, button.dataset.sortKey) }));
  }
  document.addEventListener("click", closeOverlays);
  document.addEventListener("keydown", (event) => { if (event.key === "Escape") closeOverlays(); });
  await load(state);
  registerVisibleDataRefresh(() => load(state, { silent: true }));
}
