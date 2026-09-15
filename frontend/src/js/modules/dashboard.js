import { ApiRequestError, getCurrentUser, getExperts, getGradeMappings, getReportDashboard } from "./api.js";
import { logout } from "./auth.js";

const PAGE_SIZE = 25;
const DEFAULT_SORT = "report_date_desc";
const DATASET_PERIOD = "01.01.2023–31.12.2025";
const REPORT_STATUS_LABELS = { draft: "Чернетка", review: "На перевірці", issued: "Видано", void: "Анульовано" };
const MARKET_STATUS_LABELS = { not_for_sale: "Не продається", available: "Доступний", reserved: "Зарезервовано", sold: "Продано", withdrawn: "Знято" };

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
    market_status: params.get("market_status") || "",
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

function renderActions(reportId) {
  const wrapper = createElement("div", "report-actions");
  const toggle = createElement("button", "report-actions__toggle", "⋮");
  toggle.type = "button";
  toggle.setAttribute("aria-label", `Відкрити дії для звіту ${reportId}`);
  toggle.setAttribute("aria-expanded", "false");
  const menu = createElement("div", "report-actions__menu");
  menu.hidden = true;
  for (const label of ["Переглянути", "Редагувати", "Друк"]) {
    const item = createElement("button", "report-actions__item", label);
    item.type = "button";
    item.disabled = true;
    item.title = "Буде доступно після реалізації приватного перегляду звіту";
    menu.append(item);
  }
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
    idLink.title = "Приватний перегляд звіту буде додано в задачі 080";
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
    const marketStatusCell = document.createElement("td");
    marketStatusCell.append(createBadge(MARKET_STATUS_LABELS[report.stone.market_status] || report.stone.market_status, `market-${report.stone.market_status}`));
    row.append(marketStatusCell);
    const actionsCell = document.createElement("td");
    actionsCell.append(renderActions(report.report_id));
    row.append(actionsCell);
    tbody.append(row);
  }
}

function renderPagination(container, page, totalPages, onPageChange) {
  container.replaceChildren();
  if (totalPages <= 1) return;
  const makeButton = (label, targetPage, disabled = false, active = false) => {
    const button = createElement("button", `page-btn${active ? " active" : ""}`, label);
    button.type = "button";
    button.disabled = disabled;
    button.addEventListener("click", () => onPageChange(targetPage));
    return button;
  };
  container.append(makeButton("Попередня", page - 1, page === 1));
  const start = Math.max(1, page - 2);
  const end = Math.min(totalPages, start + 4);
  for (let item = start; item <= end; item += 1) container.append(makeButton(String(item), item, false, item === page));
  container.append(makeButton("Наступна", page + 1, page === totalPages));
}

function toggleSort(currentSort, key) {
  return currentSort === `${key}_asc` ? `${key}_desc` : `${key}_asc`;
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
  const sortSelect = root.querySelector("#report-sort");
  const reportStatusSelect = root.querySelector("#quick-report-status");
  const marketStatusSelect = root.querySelector("#quick-market-status");
  const expertSelect = root.querySelector("#expert-filter");
  const toggleFilters = root.querySelector("#toggle-filters");
  const filtersPanel = root.querySelector("#advanced-filters");
  if (!token || !tbody || !pagination || !stateNode || !form || !searchInput || !sortSelect || !reportStatusSelect || !marketStatusSelect) return;

  let state = getUrlState();
  let labelFor = (_category, value) => String(value ?? "—");
  searchInput.value = state.search;
  sortSelect.value = state.sort;
  reportStatusSelect.value = state.report_status;
  marketStatusSelect.value = state.market_status;
  for (const control of [...form.elements].filter((element) => element.name)) control.value = state[control.name] || "";

  try {
    const [currentUser, mappings] = await Promise.all([getCurrentUser(token), getGradeMappings()]);
    labelFor = makeMappingLookup(mappings);
    populateGradeFilter(root.querySelector("#color-filter"), "color", mappings);
    populateGradeFilter(root.querySelector("#clarity-filter"), "clarity", mappings);
    populateGradeFilter(root.querySelector("#cut-filter"), "cut", mappings);
    for (const select of [root.querySelector("#color-filter"), root.querySelector("#clarity-filter"), root.querySelector("#cut-filter")]) select.value = state[select.name] || "";
    const expertFilter = root.querySelector("#expert-filter-wrap");
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

  const load = async (nextState = state) => {
    state = { ...nextState, page: Math.max(Number(nextState.page) || 1, 1) };
    updateUrl(state);
    setStatus(stateNode, "Завантаження звітів…");
    tbody.replaceChildren();
    pagination.replaceChildren();
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
  for (const [control, key] of [[sortSelect, "sort"], [reportStatusSelect, "report_status"], [marketStatusSelect, "market_status"], [expertSelect, "expert_id"]]) {
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
}
