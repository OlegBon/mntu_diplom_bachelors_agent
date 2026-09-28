import { ApiRequestError, getAdminReviewStatistics, getExpertStatistics, getFxDataSnapshots, getNarrativeQualityAnalytics, getOperationalProviderAnalytics } from "./api.js";
import { logout } from "./auth.js";
import { duration, element, periodSummary, renderNbuCurrencySource, renderTable } from "./analytics-ui.js";

function fullName(row) {
  return [row.last_name, row.first_name, row.middle_name].filter(Boolean).join(" ") || "Не вказано";
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

function openExpertDialog(dialog, dialogContent, row) {
  const fragment = document.createDocumentFragment();
  fragment.append(element("h3", "analytics-dialog-name", `${fullName(row)} (${row.expert_username})`));
  const metrics = element("dl", "analytics-metrics");
  [
    ["Стан облікового запису", row.is_active ? "Активний" : "Неактивний"],
    ["Усього звітів", row.total_reports], ["Чернетки", row.draft_reports],
    ["На перевірці", row.review_reports], ["Видано", row.issued_reports], ["Анульовано", row.void_reports],
    ["Завершені робочі сесії", row.completed_work_sessions],
    ["Активний час", duration(row.total_active_seconds)],
    ["Середня активна сесія", duration(row.avg_active_seconds)],
    ["Медіанна активна сесія", duration(row.median_active_seconds)],
    ["Збережень із виміром підготовки", row.completed_first_save_timings],
    ["Час до першого збереження", duration(row.total_time_to_first_save_seconds)],
    ["Середній час до першого збереження", duration(row.avg_time_to_first_save_seconds)],
    ["Медіанний час до першого збереження", duration(row.median_time_to_first_save_seconds)],
  ].forEach(([label, value]) => metrics.append(element("dt", "", label), element("dd", "", String(value))));
  fragment.append(metrics, element("p", "account-help", "Активний час — лише server-timed сесії автора збереженої чернетки. Відкрита, прихована або offline-вкладка без взаємодії не зараховується."));
  fragment.append(element("p", "account-help", "Час до першого збереження — окремий server-timed elapsed time від першої взаємодії з майстром до створення чернетки. Покинуті, замінені іншою вкладкою або offline-майстри не враховуються."));
  fragment.append(renderWorkSessionList("Три найкоротші активні сесії", row.shortest_work_sessions), renderWorkSessionList("Три найдовші активні сесії", row.longest_work_sessions));
  dialogContent.replaceChildren(fragment);
  dialog.showModal();
}

function renderWorkSessionList(title, items = []) {
  const section = element("section", "analytics-review-list");
  section.append(element("h3", "", title));
  if (!items.length) {
    section.append(element("p", "account-help", "Завершених активних сесій у цьому періоді поки немає."));
    return section;
  }
  const list = document.createElement("ol");
  items.forEach((item) => {
    const row = document.createElement("li");
    const reportLink = element("a", "", item.report_id);
    reportLink.href = `/report-detail.html?id=${encodeURIComponent(item.report_id)}`;
    row.append(reportLink, document.createTextNode(`: ${duration(item.duration_seconds)} · ${dateTime(item.finished_at)}`));
    list.append(row);
  });
  section.append(list);
  return section;
}

function renderExperts(container, rows, dialog, dialogContent) {
  renderTable(container, ["Експерт", "Стан", "Усього", "Чернетки", "На перевірці", "Видано", "Анульовано", "Активний час"], rows.map((row) => [
    (() => {
      const button = element("button", "analytics-expert-button", `${fullName(row)} (${row.expert_username})`);
      button.type = "button";
      button.addEventListener("click", () => openExpertDialog(dialog, dialogContent, row));
      return button;
    })(), row.is_active ? "Активний" : "Неактивний",
    String(row.total_reports), String(row.draft_reports), String(row.review_reports),
    String(row.issued_reports), String(row.void_reports), duration(row.total_active_seconds),
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
  const cards = element("div", "analytics-admin-list");
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
    cards.append(card);
  });
  if (snapshot.admins.length) fragment.append(cards);
  else fragment.append(element("p", "account-help", "Адміністраторів для цього зрізу поки немає."));
  container.replaceChildren(fragment);
}

function providerFreshnessLabel(value) {
  return { fresh: "Актуальний", warning: "Потребує уваги", stale: "Застарілий", missing: "Немає знімка" }[value] || value;
}

function openProviderDialog(dialog, content, provider) {
  const coverage = provider.coverage;
  const fragment = document.createDocumentFragment();
  fragment.append(element("h3", "analytics-dialog-name", provider.display_name));
  const metrics = element("dl", "analytics-metrics");
  [
    ["Стан freshness", providerFreshnessLabel(provider.freshness_status)],
    ["Останній затверджений знімок", provider.latest_snapshot_id ? `#${provider.latest_snapshot_id}` : "Немає"],
    ["Усього знімків", provider.snapshots_total], ["Кандидати", provider.snapshots_candidate],
    ["Затверджено", provider.snapshots_approved], ["Відхилено", provider.snapshots_rejected],
    ["Усього спроб", provider.operations_total], ["За графіком", provider.scheduled_operations],
    ["Вручну", provider.manual_operations], ["Повторні спроби", provider.retry_operations],
    ["Невдалі спроби", provider.failed_operations], ["Чернеток у зрізі", coverage.candidate_draft_reports],
    ["Покрито орієнтиром", coverage.covered_draft_reports], ["Виключено за origin", coverage.excluded_non_natural_reports],
    ["Бракує характеристик", coverage.missing_characteristics_reports],
    ["Немає актуального знімка", coverage.snapshot_unavailable_reports], ["Не покрито quote", coverage.quote_not_covered_reports],
  ].forEach(([label, value]) => metrics.append(element("dt", "", label), element("dd", "", String(value))));
  fragment.append(metrics, element("p", "account-help", provider.scope_note));
  const policy = element("section", "analytics-review-list");
  policy.append(element("h3", "", "Доступ і умови provider-а"));
  const policyMetrics = element("dl", "analytics-metrics");
  [
    ["Режим", { disabled: "Вимкнено", restricted_trial: "Обмежений trial", standard_internal: "Внутрішній стандартний" }[provider.access_mode] || "Не налаштовано"],
    ["Trial діє до", dateTime(provider.trial_expires_at) || "Не застосовується"],
    ["Денний ліміт", provider.daily_request_limit || "Не застосовується"],
    ["Призначено адміністраторів", provider.assigned_admin_count],
    ["Остання зміна умов", provider.last_policy_event_at ? `${dateTime(provider.last_policy_event_at)} · ${provider.last_policy_event_action}` : "Подій ще немає"],
  ].forEach(([label, value]) => policyMetrics.append(element("dt", "", label), element("dd", "", String(value))));
  policy.append(policyMetrics, element("p", "account-help", "Це read-only факт конфігурації. Керування умовами доступне лише в «Ринкових даних» для admin-а, який увімкнув відповідний доступ у профілі."));
  fragment.append(policy);
  if (coverage.covered_report_ids.length) {
    const links = element("p", "account-help", "Приклади покритих звітів: ");
    coverage.covered_report_ids.forEach((reportId, index) => {
      if (index) links.append(document.createTextNode(", "));
      const link = element("a", "", reportId); link.href = `/report-detail.html?id=${encodeURIComponent(reportId)}`; links.append(link);
    });
    fragment.append(links);
  }
  content.replaceChildren(fragment); dialog.showModal();
}

function renderProviders(container, providers, dialog, dialogContent) {
  renderTable(container, ["Провайдер", "Freshness", "Знімки", "Спроби", "Coverage чернеток"], providers.map((provider) => {
    const button = element("button", "analytics-expert-button", provider.display_name);
    button.type = "button"; button.addEventListener("click", () => openProviderDialog(dialog, dialogContent, provider));
    const coverage = provider.coverage;
    return [button, providerFreshnessLabel(provider.freshness_status), `${provider.snapshots_approved}/${provider.snapshots_total} затверджено`, `${provider.failed_operations} failed · ${provider.retry_operations} retry`, `${coverage.covered_draft_reports}/${coverage.candidate_draft_reports} покрито`];
  }), "Активних ринкових provider-ів поки немає.");
}

function renderCurrencySources(container, snapshots, dialog, dialogContent) {
  const formatCurrencyDateTime = (value) => {
    const parsed = new Date(value);
    return {
      date: new Intl.DateTimeFormat("uk-UA", { dateStyle: "medium" }).format(parsed),
      time: new Intl.DateTimeFormat("uk-UA", { timeStyle: "short" }).format(parsed),
    };
  };
  renderNbuCurrencySource(container, snapshots, dialog, dialogContent, formatCurrencyDateTime);
}

function numericValue(value) {
  if (value === null || value === undefined) return "—";
  return new Intl.NumberFormat("uk-UA", { maximumFractionDigits: 2 }).format(value);
}

function renderNarrativeSampleList(title, samples) {
  const section = element("section", "analytics-review-list");
  section.append(element("h3", "", title));
  if (!samples.length) {
    section.append(element("p", "account-help", "Непорожніх значень у цьому зрізі поки немає."));
    return section;
  }
  const list = document.createElement("ol");
  samples.forEach((sample) => {
    const row = document.createElement("li");
    const link = element("a", "", sample.report_id);
    link.href = `/report-detail.html?id=${encodeURIComponent(sample.report_id)}`;
    row.append(link, document.createTextNode(`: ${sample.word_count} слів · ${sample.non_whitespace_char_count} символів без пробілів · ${dateTime(sample.occurred_at)}`));
    list.append(row);
  });
  section.append(list);
  return section;
}

function renderNarrativeAnalytics(container, snapshot) {
  const cards = element("div", "analytics-narrative-list");
  snapshot.fields.forEach((field) => {
    const card = element("article", "analytics-admin-card analytics-narrative-card");
    card.append(element("h3", "", field.label));
    const metrics = element("dl", "analytics-metrics");
    [
      ["Непорожніх значень", field.non_empty_count], ["Медіана слів", numericValue(field.median_word_count)],
      ["Середнє слів", numericValue(field.average_word_count)], ["Медіана символів без пробілів", numericValue(field.median_non_whitespace_char_count)],
      ["Середнє символів без пробілів", numericValue(field.average_non_whitespace_char_count)],
    ].forEach(([label, value]) => metrics.append(element("dt", "", label), element("dd", "", String(value))));
    card.append(metrics, element("p", "account-help", field.source_semantics));
    card.append(renderNarrativeSampleList("Три найкоротші", field.shortest), renderNarrativeSampleList("Три найдовші", field.longest));
    cards.append(card);
  });
  container.replaceChildren(cards);
}

export async function initAnalytics() {
  const page = document.querySelector("[data-analytics-page]");
  if (!page) return;
  const status = document.getElementById("analytics-status");
  const token = localStorage.getItem("token");
  const expertResults = document.getElementById("analytics-expert-results");
  const adminResults = document.getElementById("analytics-admin-results");
  const narrativeResults = document.getElementById("analytics-narrative-results");
  const providerResults = document.getElementById("analytics-provider-results");
  const currencyResults = document.getElementById("analytics-currency-results");
  const expertDialog = document.getElementById("analytics-expert-dialog");
  const expertDialogContent = document.getElementById("analytics-expert-dialog-content");
  const periodForm = document.getElementById("analytics-period-form");
  const periodReset = document.getElementById("analytics-period-reset");
  const periodSummaryNode = document.getElementById("analytics-period-summary");
  const periodControls = document.getElementById("analytics-period-controls");
  const providerDialog = document.getElementById("analytics-provider-dialog");
  const providerDialogContent = document.getElementById("analytics-provider-dialog-content");
  const panels = Object.fromEntries([...page.querySelectorAll(".analytics-panel")].map((panel) => [panel.id.replace("analytics-", ""), panel]));

  page.querySelectorAll("[data-analytics-tab]").forEach((tab) => tab.addEventListener("click", () => {
    const selected = tab.dataset.analyticsTab;
    page.querySelectorAll("[data-analytics-tab]").forEach((item) => {
      const active = item === tab;
      item.classList.toggle("is-active", active);
      item.setAttribute("aria-selected", String(active));
    });
    Object.entries(panels).forEach(([name, panel]) => { panel.hidden = name !== selected; });
    periodControls.hidden = selected === "stones";
  }));
  expertDialog?.addEventListener("cancel", () => expertDialogContent.replaceChildren());
  expertDialog?.addEventListener("close", () => expertDialogContent.replaceChildren());
  providerDialog?.addEventListener("close", () => providerDialogContent.replaceChildren());
  const loadAnalytics = async () => {
    const period = Object.fromEntries(new FormData(periodForm).entries());
    if (period.date_from && period.date_to && period.date_from > period.date_to) {
      status.textContent = "Дата «Від» не може бути пізнішою за дату «До».";
      status.hidden = false;
      return;
    }
    status.hidden = true;
    try {
      const [experts, narratives, admins, providers, currency] = await Promise.all([
        getExpertStatistics(period, token), getNarrativeQualityAnalytics(period, token),
        getAdminReviewStatistics(period, token),
        getOperationalProviderAnalytics(period, token), getFxDataSnapshots(period, token),
      ]);
      renderExperts(expertResults, experts, expertDialog, expertDialogContent);
      renderNarrativeAnalytics(narrativeResults, narratives);
      renderAdmins(adminResults, admins);
      renderProviders(providerResults, providers.providers, providerDialog, providerDialogContent);
      renderCurrencySources(currencyResults, currency, providerDialog, providerDialogContent);
      periodSummaryNode.textContent = periodSummary(period);
    } catch (error) {
      if (error instanceof ApiRequestError && error.status === 401) { logout("/login.html"); return; }
      status.textContent = error instanceof ApiRequestError && error.status === 403
        ? "Аналітика доступна лише адміністратору."
        : "Не вдалося завантажити аналітику. Спробуйте оновити сторінку пізніше.";
      status.hidden = false;
    }
  };
  periodForm.addEventListener("submit", (event) => { event.preventDefault(); loadAnalytics(); });
  periodReset.addEventListener("click", () => { periodForm.reset(); loadAnalytics(); });
  await loadAnalytics();
}
