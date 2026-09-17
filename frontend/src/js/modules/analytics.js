import { ApiRequestError, getAdminReviewStatistics, getExpertStatistics } from "./api.js";
import { logout } from "./auth.js";

function element(tagName, className, text) {
  const node = document.createElement(tagName);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function fullName(row) {
  return [row.last_name, row.first_name, row.middle_name].filter(Boolean).join(" ") || "Не вказано";
}

function duration(value) {
  if (value === null || value === undefined) return "—";
  const hours = Math.floor(value / 3600);
  const minutes = Math.floor((value % 3600) / 60);
  const seconds = value % 60;
  if (hours) return `${hours} год ${minutes} хв`;
  if (minutes) return `${minutes} хв ${seconds} с`;
  return `${seconds} с`;
}

const decisionLabels = {
  draft: "Повернено у чернетку",
  issued: "Видано",
  void: "Анульовано",
};

function dateTime(value) {
  if (!value) return null;
  return new Intl.DateTimeFormat("uk-UA", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

function renderTable(container, headers, rows) {
  if (!rows.length) {
    container.replaceChildren(element("p", "account-help", "Даних за цим зрізом поки немає."));
    return;
  }
  const wrapper = element("div", "analytics-table-wrap");
  const table = element("table", "analytics-table");
  const thead = document.createElement("thead");
  const headerRow = document.createElement("tr");
  headers.forEach((header) => headerRow.append(element("th", "", header)));
  thead.append(headerRow);
  const tbody = document.createElement("tbody");
  rows.forEach((row) => {
    const tableRow = document.createElement("tr");
    row.forEach((value) => tableRow.append(element("td", "", value)));
    tbody.append(tableRow);
  });
  table.append(thead, tbody);
  wrapper.append(table);
  container.replaceChildren(wrapper);
}

function renderExperts(container, rows) {
  renderTable(container, ["Експерт", "Стан", "Усього", "Чернетки", "На перевірці", "Видано", "Анульовано"], rows.map((row) => [
    `${fullName(row)} (${row.expert_username})`, row.is_active ? "Активний" : "Неактивний",
    String(row.total_reports), String(row.draft_reports), String(row.review_reports),
    String(row.issued_reports), String(row.void_reports),
  ]));
}

function renderReviewList(title, items) {
  const section = element("section", "analytics-review-list");
  section.append(element("h3", "", title));
  if (!items.length) {
    section.append(element("p", "account-help", "Завершених перевірок поки немає."));
    return section;
  }
  const list = document.createElement("ol");
  items.forEach((item) => {
    const row = document.createElement("li");
    const reportLink = element("a", "", item.report_id);
    reportLink.href = `/report-detail.html?id=${encodeURIComponent(item.report_id)}`;
    row.append(reportLink, document.createTextNode(`: ${duration(item.duration_seconds)} · ${decisionLabels[item.decision] || item.decision}`));
    list.append(row);
  });
  section.append(list);
  return section;
}

function renderAdmins(container, snapshot) {
  const fragment = document.createDocumentFragment();
  const queueText = snapshot.pending_review_count
    ? `Зараз на перевірці: ${snapshot.pending_review_count}.`
    : "Зараз немає звітів на перевірці.";
  const oldest = dateTime(snapshot.oldest_review_started_at);
  fragment.append(element("p", "analytics-queue", oldest ? `${queueText} Найдавніший передано: ${oldest}.` : queueText));
  snapshot.admins.forEach((admin) => {
    const card = element("article", "analytics-admin-card");
    card.append(element("h3", "", `${fullName(admin)} (${admin.admin_username})`));
    const metrics = element("dl", "analytics-metrics");
    [
      ["Завершено перевірок", admin.completed_reviews], ["Видано", admin.issued_reports],
      ["Повернуто", admin.returned_to_draft], ["Анульовано", admin.voided_reports],
      ["Середня тривалість", duration(admin.avg_review_duration_seconds)],
      ["Медіанна тривалість", duration(admin.median_review_duration_seconds)],
    ].forEach(([label, value]) => { metrics.append(element("dt", "", label), element("dd", "", String(value))); });
    card.append(metrics, renderReviewList("Найкоротші перевірки", admin.shortest_reviews), renderReviewList("Найдовші перевірки", admin.longest_reviews));
    fragment.append(card);
  });
  container.replaceChildren(fragment);
}

export async function initAnalytics() {
  const page = document.querySelector("[data-analytics-page]");
  if (!page) return;
  const status = document.getElementById("analytics-status");
  const token = localStorage.getItem("token");
  const expertResults = document.getElementById("analytics-expert-results");
  const adminResults = document.getElementById("analytics-admin-results");
  const panels = Object.fromEntries([...page.querySelectorAll(".analytics-panel")].map((panel) => [panel.id.replace("analytics-", ""), panel]));

  page.querySelectorAll("[data-analytics-tab]").forEach((tab) => tab.addEventListener("click", () => {
    const selected = tab.dataset.analyticsTab;
    page.querySelectorAll("[data-analytics-tab]").forEach((item) => {
      const active = item === tab;
      item.classList.toggle("is-active", active);
      item.setAttribute("aria-selected", String(active));
    });
    Object.entries(panels).forEach(([name, panel]) => { panel.hidden = name !== selected; });
  }));
  try {
    const [experts, admins] = await Promise.all([getExpertStatistics(token), getAdminReviewStatistics(token)]);
    renderExperts(expertResults, experts);
    renderAdmins(adminResults, admins);
  } catch (error) {
    if (error instanceof ApiRequestError && error.status === 401) { logout("/login.html"); return; }
    status.textContent = error instanceof ApiRequestError && error.status === 403
      ? "Аналітика доступна лише адміністратору."
      : "Не вдалося завантажити аналітику. Спробуйте оновити сторінку пізніше.";
    status.hidden = false;
  }
}
