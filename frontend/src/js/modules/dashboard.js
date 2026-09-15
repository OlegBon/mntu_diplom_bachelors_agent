import { ApiRequestError, getCurrentUser, getExperts, getReportDashboard } from "./api.js";
import { logout } from "./auth.js";

const PAGE_SIZE = 25;
const DEFAULT_SORT = "report_date_desc";

function createElement(tagName, className, textContent) {
  const element = document.createElement(tagName);
  if (className) element.className = className;
  if (textContent !== undefined) element.textContent = textContent;
  return element;
}

function formatDate(value) {
  return new Intl.DateTimeFormat("uk-UA", { dateStyle: "medium" }).format(new Date(value));
}

function formatCode(value) {
  return String(value ?? "—").replaceAll("_", " ");
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

  const view = createElement("button", "report-actions__item", "Переглянути");
  const edit = createElement("button", "report-actions__item", "Редагувати");
  const print = createElement("button", "report-actions__item", "Друк");
  for (const item of [view, edit, print]) {
    item.type = "button";
    item.disabled = true;
    item.title = "Буде доступно після реалізації приватного перегляду звіту";
    menu.append(item);
  }

  toggle.addEventListener("click", () => {
    const isOpen = menu.hidden;
    menu.hidden = !isOpen;
    toggle.setAttribute("aria-expanded", String(isOpen));
  });
  wrapper.append(toggle, menu);
  return wrapper;
}

function renderRows(tbody, reports) {
  tbody.replaceChildren();
  for (const report of reports) {
    const row = document.createElement("tr");
    const values = [
      report.report_id,
      formatDate(report.report_date),
      report.stone.shape,
      `${report.stone.carat_weight} ct`,
      formatCode(report.stone.origin),
      formatCode(report.status),
      formatCode(report.stone.market_status),
    ];
    for (const value of values) row.append(createElement("td", "", value));
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
  for (let item = start; item <= end; item += 1) {
    container.append(makeButton(String(item), item, false, item === page));
  }
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
  if (!token || !tbody || !pagination || !stateNode || !form) return;

  let state = getUrlState();
  const controls = Object.fromEntries(
    [...form.elements]
      .filter((element) => element.name)
      .map((element) => [element.name, element]),
  );
  for (const [key, control] of Object.entries(controls)) control.value = state[key] || "";

  try {
    const currentUser = await getCurrentUser(token);
    const expertFilter = root.querySelector("#expert-filter-wrap");
    if (currentUser.role === "admin" && expertFilter) {
      const experts = await getExperts(token);
      const select = controls.expert_id;
      for (const expert of experts) {
        const option = createElement("option", "", expert.username);
        option.value = String(expert.expert_id);
        select.append(option);
      }
      expertFilter.hidden = false;
      select.value = state.expert_id;
    }
  } catch (error) {
    if (error instanceof ApiRequestError && error.status === 401) logout("/login.html");
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
      renderRows(tbody, result.items);
      renderPagination(pagination, result.page, result.total_pages, (page) => load({ ...state, page }));
    } catch (error) {
      if (error instanceof ApiRequestError && error.status === 401) {
        logout("/login.html");
        return;
      }
      setStatus(stateNode, "Не вдалося завантажити звіти. Оновіть сторінку або спробуйте пізніше.", "error");
    }
  };

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const data = new FormData(form);
    load({
      page: 1,
      search: String(data.get("search") || "").trim(),
      report_status: String(data.get("report_status") || ""),
      market_status: String(data.get("market_status") || ""),
      sort: String(data.get("sort") || DEFAULT_SORT),
      expert_id: String(data.get("expert_id") || ""),
    });
  });
  form.addEventListener("reset", () => window.setTimeout(() => load({ page: 1, sort: DEFAULT_SORT }), 0));
  await load(state);
}
