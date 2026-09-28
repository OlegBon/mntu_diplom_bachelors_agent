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
