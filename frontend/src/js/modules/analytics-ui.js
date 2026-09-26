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
