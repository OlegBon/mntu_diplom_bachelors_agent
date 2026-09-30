import { ApiRequestError, getAdminReviewStatistics, getExpertStatistics, getFxDataSnapshots, getNarrativeQualityAnalytics, getOperationalProviderAnalytics, getOperationalQualityAnalytics } from "./api.js";
import { logout } from "./auth.js";
import { duration, element, periodSummary, renderNarrativeAnalytics, renderNbuCurrencySource, renderOperationalQuality, renderTable } from "./analytics-ui.js";
import { formatDate, t } from "./i18n.js";

function localizeAnalyticsShell(page) {
  const textKeys = [
    [".page-title", "analytics.title"],
    [".page-subtitle", "analytics.subtitle"],
    ["#analytics-tab-stones", "analytics.stones"],
    ["#analytics-tab-experts", "analytics.experts"],
    ["#analytics-tab-narratives", "analytics.texts"],
    ["#analytics-tab-quality", "analytics.quality"],
    ["#analytics-tab-admins", "analytics.administrators"],
    ["#analytics-tab-providers", "analytics.providers"],
    ["#analytics-tab-currency", "analytics.currencySources"],
    ["#analytics-stones > h2", "analytics.stonesTitle"],
    ["#analytics-experts > h2", "analytics.expertsTitle"],
    ["#analytics-narratives > h2", "analytics.textsTitle"],
    ["#analytics-quality > h2", "analytics.qualityTitle"],
    ["#analytics-admins > h2", "analytics.administratorsTitle"],
    ["#analytics-providers > h2", "analytics.providersTitle"],
    ["#analytics-currency > h2", "analytics.currencyTitle"],
    ["#analytics-expert-dialog-title", "analytics.expertDialogTitle"],
    ["#analytics-provider-dialog-title", "analytics.providerDialogTitle"],
    ["label[for=analytics-date-from]", "analytics.from"],
    ["label[for=analytics-date-to]", "analytics.to"],
    ["#analytics-period-form button[type=submit]", "analytics.applyPeriod"],
    ["#analytics-period-reset", "analytics.allTime"],
  ];
  for (const [selector, key] of textKeys) {
    const element = page.querySelector(selector);
    if (element) element.textContent = t(key);
  }
  page.querySelector(".analytics-tabs")?.setAttribute("aria-label", t("analytics.tabs"));
  for (const closeButton of page.querySelectorAll(".account-dialog__close")) closeButton.setAttribute("aria-label", t("analytics.close"));
}

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
  return formatDate(new Date(value), { dateStyle: "medium", timeStyle: "short" });
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
      date: formatDate(parsed, { dateStyle: "medium" }),
      time: formatDate(parsed, { timeStyle: "short" }),
    };
  };
  renderNbuCurrencySource(container, snapshots, dialog, dialogContent, formatCurrencyDateTime);
}


export async function initAnalytics() {
  const page = document.querySelector("[data-analytics-page]");
  if (!page) return;
  localizeAnalyticsShell(page);
  document.addEventListener("diamant:locale-change", () => localizeAnalyticsShell(page));
  const status = document.getElementById("analytics-status");
  const token = localStorage.getItem("token");
  const expertResults = document.getElementById("analytics-expert-results");
  const adminResults = document.getElementById("analytics-admin-results");
  const narrativeResults = document.getElementById("analytics-narrative-results");
  const qualityResults = document.getElementById("analytics-quality-results");
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
      const [experts, narratives, quality, admins, providers, currency] = await Promise.all([
        getExpertStatistics(period, token), getNarrativeQualityAnalytics(period, token).catch(() => null),
        getOperationalQualityAnalytics(period, token).catch(() => null),
        getAdminReviewStatistics(period, token),
        getOperationalProviderAnalytics(period, token).catch(() => null), getFxDataSnapshots(period, token).catch(() => null),
      ]);
      renderExperts(expertResults, experts, expertDialog, expertDialogContent);
      if (narratives) {
        renderNarrativeAnalytics(narrativeResults, narratives, {
          reportHref: (reportId) => `/report-detail.html?id=${encodeURIComponent(reportId)}`,
          formatDateTime: dateTime,
        });
      } else narrativeResults.textContent = "Текстові метадані тимчасово недоступні.";
      if (quality) renderOperationalQuality(qualityResults, quality, { formatDateTime: dateTime });
      else qualityResults.textContent = "Операційні метадані тимчасово недоступні.";
      renderAdmins(adminResults, admins);
      if (providers) renderProviders(providerResults, providers.providers, providerDialog, providerDialogContent);
      else providerResults.textContent = "Метадані provider-ів тимчасово недоступні.";
      if (currency) renderCurrencySources(currencyResults, currency, providerDialog, providerDialogContent);
      else currencyResults.textContent = "Метадані валютних джерел тимчасово недоступні.";
      periodSummaryNode.textContent = periodSummary(period);
    } catch (error) {
      if (error instanceof ApiRequestError && error.status === 401) { logout("/login.html"); return; }
      status.textContent = error instanceof ApiRequestError && error.status === 403
        ? "Аналітика доступна лише адміністратору."
        : "Не вдалося завантажити аналітику. Спробуйте оновити сторінку пізніше.";
      status.hidden = false;
    }
  };
  document.addEventListener("diamant:locale-change", () => { void loadAnalytics(); });
  periodForm.addEventListener("submit", (event) => { event.preventDefault(); loadAnalytics(); });
  periodReset.addEventListener("click", () => { periodForm.reset(); loadAnalytics(); });
  await loadAnalytics();
}
