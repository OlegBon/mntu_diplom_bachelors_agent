import { ApiRequestError, getCurrentUser, getExperts, getGradeMappings, getReportDashboard } from "./api.js";
import { logout } from "./auth.js";

const PAGE_SIZE = 25;
const DEFAULT_SORT = "report_date_desc";
const DATASET_PERIOD = "01.01.2023–31.12.2025";

function createElement(tagName, className, textContent) {
  const element = document.createElement(tagName);
  if (className) element.className = className;
  if (textContent !== undefined) element.textContent = textContent;
  return element;
}

function formatDate(value) {
  return new Intl.DateTimeFormat("uk-UA", { dateStyle: "medium" }).format(new Date(value));
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
    sort: params.get("sort") || DEFAULT_SORT,
    expert_id: params.get("expert_id") || "",
  };
}

function updateUrl(state) {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(state)) {
    if (value && !(key === "page" && Number(value) === 1) && !(key === "sort" && value === DEFAULT_SORT)) {
      params.set(key, String(value));
    }
  }
  const query = params.toString();
  window.history.replaceState({}, "", `${window.location.pathname}${query ? `?${query}` : ""}`);
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
  toggle.addEventListener("click", () => {
    const isOpen = menu.hidden;
    for (const openedMenu of document.querySelectorAll(".report-actions__menu:not([hidden])")) openedMenu.hidden = true;
    for (const openedToggle of document.querySelectorAll(".report-actions__toggle[aria-expanded='true']")) openedToggle.setAttribute("aria-expanded", "false");
    menu.hidden = !isOpen;
    toggle.setAttribute("aria-expanded", String(isOpen));
  });
  wrapper.append(toggle, menu);
  return wrapper;
}

function renderPrice(report) {
  if (report.price === null || report.price === undefined) {
    return createElement("span", "report-price__missing", "—");
  }
  const wrapper = createElement("div", "report-price");
  const toggle = createElement("button", "report-price__toggle");
  toggle.type = "button";
  toggle.setAttribute("aria-label", `Пояснення demo-ціни звіту ${report.report_id}`);
  toggle.setAttribute("aria-expanded", "false");
  toggle.append(
    document.createTextNode(`USD ${formatDemoPrice(report.price)} `),
    createElement("sup", "report-price__indicator", "d"),
  );
  const popover = createElement("div", "report-price__popover");
  popover.hidden = true;
  const details = [
    ["Тип", "Demo-значення"],
    ["Джерело", "diamonds_dataset.csv"],
    ["Дата фіксації", formatDate(report.report_date)],
    ["Період набору", DATASET_PERIOD],
  ];
  for (const [label, value] of details) {
    const row = createElement("p", "report-price__detail");
    row.append(createElement("strong", "", `${label}: `), document.createTextNode(value));
    popover.append(row);
  }
  popover.append(createElement("p", "report-price__warning", "Не є актуальним ринковим котируванням."));
  toggle.addEventListener("click", () => {
    const isOpen = popover.hidden;
    for (const openedPopover of document.querySelectorAll(".report-price__popover:not([hidden])")) openedPopover.hidden = true;
    for (const openedToggle of document.querySelectorAll(".report-price__toggle[aria-expanded='true']")) openedToggle.setAttribute("aria-expanded", "false");
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

function createBadge(value, kind) {
  return createElement("span", `status-badge status-badge--${kind}`, value);
}

function renderRows(tbody, reports, labelFor) {
  tbody.replaceChildren();
  for (const report of reports) {
    const row = document.createElement("tr");
    const plainValues = [report.report_id, formatDate(report.report_date), report.stone.shape, report.stone.carat_weight];
    for (const value of plainValues) row.append(createElement("td", "", value));
    row.append(createElement("td", "", labelFor("color", report.stone.color_grade)));
    row.append(createElement("td", "", labelFor("clarity", report.stone.clarity_grade)));
    const cutCell = document.createElement("td");
    cutCell.append(createBadge(labelFor("cut", report.system_cut_grade), "cut"));
    row.append(cutCell);
    const priceCell = document.createElement("td");
    priceCell.append(renderPrice(report));
    row.append(priceCell);
    const statusCell = document.createElement("td");
    statusCell.append(createBadge(report.status, report.status));
    row.append(statusCell);
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
  const toggleFilters = root.querySelector("#toggle-filters");
  const filtersPanel = root.querySelector("#advanced-filters");
  if (!token || !tbody || !pagination || !stateNode || !form || !searchInput || !sortSelect) return;

  let state = getUrlState();
  let labelFor = (_category, value) => String(value ?? "—");
  searchInput.value = state.search;
  sortSelect.value = state.sort;
  for (const control of [...form.elements].filter((element) => element.name)) control.value = state[control.name] || "";

  try {
    const [currentUser, mappings] = await Promise.all([getCurrentUser(token), getGradeMappings()]);
    labelFor = makeMappingLookup(mappings);
    const expertFilter = root.querySelector("#expert-filter-wrap");
    if (currentUser.role === "admin" && expertFilter) {
      const experts = await getExperts(token);
      const select = root.querySelector("#expert-filter");
      for (const expert of experts) {
        const option = createElement("option", "", expert.username);
        option.value = String(expert.expert_id);
        select.append(option);
      }
      expertFilter.hidden = false;
      select.value = state.expert_id;
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
  sortSelect.addEventListener("change", () => load({ ...state, page: 1, sort: sortSelect.value }));
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const data = new FormData(form);
    load({ ...state, page: 1, report_status: String(data.get("report_status") || ""), market_status: String(data.get("market_status") || ""), expert_id: String(data.get("expert_id") || "") });
  });
  form.addEventListener("reset", () => window.setTimeout(() => load({ ...state, page: 1, report_status: "", market_status: "", expert_id: "" }), 0));
  if (toggleFilters && filtersPanel) {
    toggleFilters.addEventListener("click", () => {
      const isOpen = filtersPanel.classList.toggle("is-visible");
      toggleFilters.setAttribute("aria-expanded", String(isOpen));
    });
  }
  await load(state);
}
