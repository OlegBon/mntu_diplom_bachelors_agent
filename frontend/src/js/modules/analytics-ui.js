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
  return new Intl.DateTimeFormat("uk-UA", { dateStyle: "medium" }).format(new Date(`${value}T00:00:00`));
}

export function periodSummary(period) {
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

export function renderNarrativeAnalytics(container, snapshot, { reportHref, formatDateTime }) {
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

export function renderOperationalQuality(container, snapshot, { formatDateTime }) {
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

export function renderNbuCurrencySource(container, snapshots, dialog, dialogContent, formatDateTime, tableClass = "") {
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
