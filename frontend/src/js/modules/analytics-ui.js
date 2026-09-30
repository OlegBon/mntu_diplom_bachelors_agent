import { formatDate, formatNumber, t } from "./i18n.js";

export function element(tagName, className, text) {
  const node = document.createElement(tagName);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

export function duration(value) {
  if (value === null || value === undefined) return "—";
  const hours = Math.floor(value / 3600);
  const minutes = Math.floor((value % 3600) / 60);
  const seconds = value % 60;
  if (hours) return `${hours} год ${minutes} хв`;
  if (minutes) return `${minutes} хв ${seconds} с`;
  return `${seconds} с`;
}

export function formatPeriodDate(value) {
  return formatDate(new Date(`${value}T00:00:00`), { dateStyle: "medium" });
  return new Intl.DateTimeFormat("uk-UA", { dateStyle: "medium" }).format(new Date(`${value}T00:00:00`));
}

export function periodSummary(period) {
  if (period.date_from && period.date_to) return t("analytics.periodRange", { from: formatPeriodDate(period.date_from), to: formatPeriodDate(period.date_to) });
  if (period.date_from) return t("analytics.periodFrom", { from: formatPeriodDate(period.date_from) });
  if (period.date_to) return t("analytics.periodTo", { to: formatPeriodDate(period.date_to) });
  return t("analytics.periodAll");
  if (period.date_from && period.date_to) return `Поточний зріз: з ${formatPeriodDate(period.date_from)} до ${formatPeriodDate(period.date_to)}`;
  if (period.date_from) return `Поточний зріз: від ${formatPeriodDate(period.date_from)}`;
  if (period.date_to) return `Поточний зріз: до ${formatPeriodDate(period.date_to)}`;
  return "Поточний зріз: за весь доступний час.";
}

export function renderTable(container, headers, rows, emptyMessage = "Даних за цим зрізом поки немає.") {
  if (!rows.length) {
    container.replaceChildren(element("p", "account-help", emptyMessage));
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
    row.forEach((value) => {
      const cell = document.createElement("td");
      if (value?.nodeType) cell.append(value);
      else cell.textContent = value;
      tableRow.append(cell);
    });
    tbody.append(tableRow);
  });
  table.append(thead, tbody);
  wrapper.append(table);
  container.replaceChildren(wrapper);
}

function narrativeNumber(value) {
  if (value !== null && value !== undefined) return formatNumber(value, { maximumFractionDigits: 2 });
  if (value === null || value === undefined) return "—";
  return new Intl.NumberFormat("uk-UA", { maximumFractionDigits: 2 }).format(value);
}

function renderNarrativeSamples(title, samples, reportHref, formatDateTime) {
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
    link.href = reportHref(sample.report_id);
    const description = sample.word_count === 0 && sample.non_whitespace_char_count === 0
      ? `: порожнє значення · ${formatDateTime(sample.occurred_at)}`
      : `: ${sample.word_count} слів · ${sample.non_whitespace_char_count} символів без пробілів · ${formatDateTime(sample.occurred_at)}`;
    row.append(link, document.createTextNode(description));
    list.append(row);
  });
  section.append(list);
  return section;
}

function renderNarrativeAnalyticsLegacy(container, snapshot, { reportHref, formatDateTime }) {
  const cards = element("div", "analytics-narrative-list");
  snapshot.fields.forEach((field) => {
    const card = element("article", "analytics-admin-card analytics-narrative-card");
    card.append(element("h3", "", field.label));
    const metrics = element("dl", "analytics-metrics");
    [
      ["Усього у зрізі", field.candidate_count], ["Непорожніх значень", field.non_empty_count],
      ["Порожніх значень", field.empty_count], ["Медіана слів", narrativeNumber(field.median_word_count)],
      ["Середнє слів", narrativeNumber(field.average_word_count)], ["Медіана символів без пробілів", narrativeNumber(field.median_non_whitespace_char_count)],
      ["Середнє символів без пробілів", narrativeNumber(field.average_non_whitespace_char_count)],
    ].forEach(([label, value]) => metrics.append(element("dt", "", label), element("dd", "", String(value))));
    card.append(metrics, element("p", "account-help", field.source_semantics));
    card.append(
      renderNarrativeSamples("Три найкоротші", field.shortest, reportHref, formatDateTime),
      renderNarrativeSamples("Три найдовші", field.longest, reportHref, formatDateTime),
      renderNarrativeSamples("До трьох порожніх", field.empty_samples, reportHref, formatDateTime),
    );
    cards.append(card);
  });
  container.replaceChildren(cards);
}

function localizedSampleDate(value, formatDateTime) {
  const formatted = formatDateTime(value);
  return typeof formatted === "string" ? formatted : `${formatted.date} ${formatted.time}`;
}

function renderLocalizedNarrativeSamples(titleKey, samples, reportHref, formatDateTime) {
  const section = element("section", "analytics-review-list");
  section.append(element("h3", "", t(titleKey)));
  if (!samples.length) {
    section.append(element("p", "account-help", t("analytics.noValues")));
    return section;
  }
  const list = document.createElement("ol");
  for (const sample of samples) {
    const row = document.createElement("li");
    const link = element("a", "", sample.report_id);
    link.href = reportHref(sample.report_id);
    const date = localizedSampleDate(sample.occurred_at, formatDateTime);
    const description = sample.word_count === 0 && sample.non_whitespace_char_count === 0
      ? `: ${t("analytics.emptyValue")} · ${date}`
      : `: ${t("analytics.sampleMetrics", { words: sample.word_count, characters: sample.non_whitespace_char_count, date })}`;
    row.append(link, document.createTextNode(description));
    list.append(row);
  }
  section.append(list);
  return section;
}

export function renderNarrativeAnalytics(container, snapshot, { reportHref, formatDateTime }) {
  const cards = element("div", "analytics-narrative-list");
  for (const field of snapshot.fields) {
    const card = element("article", "analytics-admin-card analytics-narrative-card");
    card.append(element("h3", "", field.label));
    const metrics = element("dl", "analytics-metrics");
    [
      ["analytics.totalInRange", field.candidate_count], ["analytics.nonEmptyValues", field.non_empty_count],
      ["analytics.emptyValues", field.empty_count], ["analytics.medianWords", narrativeNumber(field.median_word_count)],
      ["analytics.averageWords", narrativeNumber(field.average_word_count)], ["analytics.medianCharacters", narrativeNumber(field.median_non_whitespace_char_count)],
      ["analytics.averageCharacters", narrativeNumber(field.average_non_whitespace_char_count)],
    ].forEach(([labelKey, value]) => metrics.append(element("dt", "", t(labelKey)), element("dd", "", String(value))));
    card.append(metrics, element("p", "account-help", field.source_semantics));
    card.append(
      renderLocalizedNarrativeSamples("analytics.shortest", field.shortest, reportHref, formatDateTime),
      renderLocalizedNarrativeSamples("analytics.longest", field.longest, reportHref, formatDateTime),
      renderLocalizedNarrativeSamples("analytics.emptySamples", field.empty_samples, reportHref, formatDateTime),
    );
    cards.append(card);
  }
  container.replaceChildren(cards);
}

function renderCoverageTable(title, rows) {
  const section = element("section", "analytics-quality-section");
  section.append(element("h3", "", title));
  const tableHost = element("div", "analytics-quality-table");
  renderTable(tableHost, ["Поле", "Заповнено", "Немає"], rows.map((row) => [
    row.label, `${row.filled_count} із ${row.applicable_count}`, String(row.missing_count),
  ]));
  section.append(tableHost);
  return section;
}

function renderOperationalQualityLegacy(container, snapshot, { formatDateTime }) {
  const isDemo = snapshot.scope === "demo";
  const fragment = document.createDocumentFragment();
  const workflow = element("section", "analytics-quality-section");
  workflow.append(element("h3", "", isDemo ? "Synthetic workflow у вибраному періоді" : "Workflow у вибраному періоді"));
  const metrics = element("dl", "analytics-metrics");
  [
    [isDemo ? "Завершено synthetic чернетку" : "Створено", snapshot.workflow_created_count],
    [isDemo ? "Передано до synthetic review" : "Передано на перевірку", snapshot.workflow_sent_to_review_count],
    ["Повернено у чернетку", snapshot.workflow_returned_to_draft_count], ["Видано", snapshot.workflow_issued_count],
    ["Анульовано", snapshot.workflow_voided_count], ["Повторні повернення", snapshot.workflow_repeat_return_count],
  ].forEach(([label, value]) => metrics.append(element("dt", "", label), element("dd", "", String(value))));
  workflow.append(metrics, element("p", "account-help", isDemo
    ? "Події — детермінований synthetic lifecycle dataset, а не робота реальних людей. Причини переходів і тексти не показуються."
    : "Події рахуються за часом lifecycle event. Причини переходів і тексти не показуються."));

  const current = element("section", "analytics-quality-section");
  current.append(element("h3", "", "Поточний стан когорти"));
  const currentMetrics = element("dl", "analytics-metrics");
  [
    [isDemo ? "Demo-звітів у зрізі" : "Звітів створено у зрізі", snapshot.report_cohort_count], ["Чернетки", snapshot.current_status_counts.draft],
    ["На перевірці", snapshot.current_status_counts.review], ["Видано", snapshot.current_status_counts.issued],
    ["Анульовано", snapshot.current_status_counts.void], [isDemo ? "Поточна synthetic черга" : "Поточна черга всіх operational звітів", snapshot.current_review_count],
    ["Найдавніший початок поточної перевірки", formatDateTime(snapshot.oldest_current_review_started_at) || "Не моделюється"],
  ].forEach(([label, value]) => currentMetrics.append(element("dt", "", label), element("dd", "", String(value))));
  current.append(currentMetrics, element("p", "account-help", isDemo
    ? "Статус належить synthetic звітам, датованим у зрізі. Historical queue age для demo не моделюється."
    : "Статус належить звітам, створеним у зрізі. Черга перевірки — поточний глобальний стан, а не історичний лічильник."));

  const delivery = element("section", "analytics-quality-section");
  delivery.append(element("h3", "", "Готовність delivery"));
  const deliveryMetrics = element("dl", "analytics-metrics");
  if (snapshot.delivery_is_modeled) {
    [["Звіти з приватними media", snapshot.reports_with_media_count], ["Активні публічні паспорти", snapshot.active_public_passport_count], ["Видані без активного паспорта", snapshot.issued_without_active_passport_count]]
      .forEach(([label, value]) => deliveryMetrics.append(element("dt", "", label), element("dd", "", String(value))));
  } else {
    [["Private media", "Не моделюється"], ["Публічний паспорт", "Не моделюється"], ["Готовність delivery", "Не моделюється"]]
      .forEach(([label, value]) => deliveryMetrics.append(element("dt", "", label), element("dd", "", value)));
  }
  delivery.append(deliveryMetrics, element("p", "account-help", snapshot.delivery_is_modeled
    ? "Показано технічну готовність приватних media та поточного публічного паспорта; перегляди або відвідувачі не відстежуються."
    : "Synthetic dataset не моделює private storage, public URL, QR, PDF чи відвідувачів."));
  fragment.append(workflow, current, renderCoverageTable("Обов’язкові поля", snapshot.required_field_coverage), renderCoverageTable("Додаткові поля", snapshot.optional_field_coverage), delivery);
  container.replaceChildren(fragment);
}

function renderNbuCurrencySourceLegacy(container, snapshots, dialog, dialogContent, formatDateTime, tableClass = "") {
  container.replaceChildren();
  if (!snapshots.length) {
    container.append(element("p", "account-help", "Знімків офіційного курсу НБУ за цим зрізом поки немає."));
    return;
  }
  const latest = snapshots[0];
  const rate = Number(latest.rate).toLocaleString("uk-UA", { minimumFractionDigits: 2, maximumFractionDigits: 4 });
  const sourceButton = element("button", "analytics-expert-button", "Національний банк України (НБУ)");
  sourceButton.type = "button";
  sourceButton.addEventListener("click", () => {
    const metrics = element("dl", "analytics-metrics");
    [
      ["Тип джерела", "Офіційний валютний провайдер"], ["Походження даних", "Офіційний сервіс НБУ"],
      ["Тип значень", `${latest.base_currency_code}/${latest.quote_currency_code} official FX rate`],
      ["Кількість знімків", snapshots.length], ["Останній курс", `1 ${latest.base_currency_code} = ${rate} ${latest.quote_currency_code}`],
      ["Офіційна дата курсу", formatDateTime(`${latest.rate_date}T00:00:00`).date],
      ["Останнє отримання", `${formatDateTime(latest.retrieved_at).date}, ${formatDateTime(latest.retrieved_at).time}`],
    ].forEach(([label, value]) => metrics.append(element("dt", "", label), element("dd", "", String(value))));
    dialogContent.replaceChildren(
      element("h3", "analytics-dialog-name", "Національний банк України (НБУ)"), metrics,
      element("p", "account-help", "FX-знімки зберігаються immutable. Вони застосовуються лише для окремої USD/UAH-конвертації дозволених орієнтирів і не є ціною, оцінкою або аналітикою каменю."),
    );
    dialog.showModal();
  });
  const tableHost = element("div", tableClass || "analytics-currency-sources");
  renderTable(tableHost, ["Валютне джерело", "Пара", "Останній курс", "Офіційна дата", "Отримано", "Знімків"], [[
    sourceButton, `${latest.base_currency_code}/${latest.quote_currency_code}`,
    `1 ${latest.base_currency_code} = ${rate} ${latest.quote_currency_code}`,
    formatDateTime(`${latest.rate_date}T00:00:00`).date,
    `${formatDateTime(latest.retrieved_at).date}, ${formatDateTime(latest.retrieved_at).time}`,
    String(snapshots.length),
  ]]);
  container.append(tableHost);
}

function localizedCoverageTable(titleKey, rows) {
  const section = element("section", "analytics-quality-section");
  section.append(element("h3", "", t(titleKey)));
  const tableHost = element("div", "analytics-quality-table");
  renderTable(tableHost, [t("analytics.field"), t("analytics.filled"), t("analytics.missing")], rows.map((row) => [
    row.label, `${row.filled_count} / ${row.applicable_count}`, String(row.missing_count),
  ]));
  section.append(tableHost);
  return section;
}

export function renderOperationalQuality(container, snapshot, { formatDateTime }) {
  const isDemo = snapshot.scope === "demo";
  const buildSection = (titleKey, rows, helpKey) => {
    const section = element("section", "analytics-quality-section");
    const metrics = element("dl", "analytics-metrics");
    rows.forEach(([labelKey, value]) => metrics.append(element("dt", "", t(labelKey)), element("dd", "", String(value))));
    section.append(element("h3", "", t(titleKey)), metrics, element("p", "account-help", t(helpKey)));
    return section;
  };
  const workflow = [
    [isDemo ? "analytics.completedSyntheticDraft" : "analytics.created", snapshot.workflow_created_count],
    [isDemo ? "analytics.sentToSyntheticReview" : "analytics.sentToReview", snapshot.workflow_sent_to_review_count],
    ["analytics.returnedToDraft", snapshot.workflow_returned_to_draft_count], ["analytics.issued", snapshot.workflow_issued_count],
    ["analytics.void", snapshot.workflow_voided_count], ["analytics.repeatReturns", snapshot.workflow_repeat_return_count],
  ];
  const cohort = [
    [isDemo ? "analytics.demoReportsInRange" : "analytics.reportsCreatedInRange", snapshot.report_cohort_count],
    ["analytics.drafts", snapshot.current_status_counts.draft], ["analytics.underReview", snapshot.current_status_counts.review],
    ["analytics.issued", snapshot.current_status_counts.issued], ["analytics.void", snapshot.current_status_counts.void],
    [isDemo ? "analytics.currentSyntheticQueue" : "analytics.currentQueue", snapshot.current_review_count],
    ["analytics.oldestCurrentReview", formatDateTime(snapshot.oldest_current_review_started_at) || t("analytics.notModeled")],
  ];
  const delivery = snapshot.delivery_is_modeled
    ? [["analytics.reportsWithPrivateMedia", snapshot.reports_with_media_count], ["analytics.activePublicPassports", snapshot.active_public_passport_count], ["analytics.issuedWithoutPassport", snapshot.issued_without_active_passport_count]]
    : [["analytics.reportsWithPrivateMedia", t("analytics.notModeled")], ["analytics.activePublicPassports", t("analytics.notModeled")], ["analytics.deliveryReadiness", t("analytics.notModeled")]];
  const fragment = document.createDocumentFragment();
  fragment.append(
    buildSection(isDemo ? "analytics.syntheticWorkflowTitle" : "analytics.workflowTitle", workflow, isDemo ? "analytics.syntheticWorkflowHelp" : "analytics.workflowHelp"),
    buildSection("analytics.currentCohort", cohort, isDemo ? "analytics.syntheticCohortHelp" : "analytics.cohortHelp"),
    localizedCoverageTable("analytics.requiredFields", snapshot.required_field_coverage),
    localizedCoverageTable("analytics.optionalFields", snapshot.optional_field_coverage),
    buildSection("analytics.deliveryReadiness", delivery, snapshot.delivery_is_modeled ? "analytics.deliveryHelp" : "analytics.syntheticDeliveryHelp"),
  );
  container.replaceChildren(fragment);
}

export function renderNbuCurrencySource(container, snapshots, dialog, dialogContent, formatDateTime, tableClass = "") {
  container.replaceChildren();
  if (!snapshots.length) {
    container.append(element("p", "account-help", t("analytics.noCurrencySnapshots")));
    return;
  }
  const latest = snapshots[0];
  const rate = formatNumber(latest.rate, { minimumFractionDigits: 2, maximumFractionDigits: 4 });
  const sourceButton = element("button", "analytics-expert-button", t("analytics.nbu"));
  sourceButton.type = "button";
  sourceButton.addEventListener("click", () => {
    const metrics = element("dl", "analytics-metrics");
    [["analytics.sourceType", t("analytics.officialCurrencyProvider")], ["analytics.dataOrigin", t("analytics.officialNbuService")], ["analytics.valueType", `${latest.base_currency_code}/${latest.quote_currency_code} ${t("analytics.officialFxRate")}`], ["analytics.snapshotCount", snapshots.length], ["analytics.latestRate", `1 ${latest.base_currency_code} = ${rate} ${latest.quote_currency_code}`], ["analytics.officialRateDate", formatDateTime(`${latest.rate_date}T00:00:00`).date], ["analytics.retrieved", `${formatDateTime(latest.retrieved_at).date}, ${formatDateTime(latest.retrieved_at).time}`]].forEach(([label, value]) => metrics.append(element("dt", "", t(label)), element("dd", "", String(value))));
    dialogContent.replaceChildren(element("h3", "analytics-dialog-name", t("analytics.nbu")), metrics, element("p", "account-help", t("analytics.fxHelp")));
    dialog.showModal();
  });
  const tableHost = element("div", tableClass || "analytics-currency-sources");
  renderTable(tableHost, [t("analytics.currencySource"), t("analytics.pair"), t("analytics.latestRate"), t("analytics.officialRateDate"), t("analytics.retrieved"), t("analytics.snapshotCount")], [[sourceButton, `${latest.base_currency_code}/${latest.quote_currency_code}`, `1 ${latest.base_currency_code} = ${rate} ${latest.quote_currency_code}`, formatDateTime(`${latest.rate_date}T00:00:00`).date, `${formatDateTime(latest.retrieved_at).date}, ${formatDateTime(latest.retrieved_at).time}`, String(snapshots.length)]]);
  container.append(tableHost);
}
