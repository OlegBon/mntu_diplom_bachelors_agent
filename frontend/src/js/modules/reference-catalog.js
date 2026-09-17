import { getCurrentUser, getReferenceValues } from "./api.js";
import { registerVisibleDataRefresh } from "./page-refresh.js";

const CATEGORY_LABELS = {
  shape: "Форма", origin: "Походження", treatment_status: "Ознаки обробки",
  identification_status: "Рівень підтвердження", market_status: "Комерційний стан",
  report_status: "Статус звіту", girdle_thickness: "Товщина рундиста", culet_size: "Калета",
};

export async function initReferenceCatalog() {
  const page = document.querySelector("[data-reference-catalog-page]");
  if (!page) return;
  const token = localStorage.getItem("token");
  const status = document.getElementById("reference-catalog-status");
  const load = async () => {
    const user = await getCurrentUser(token);
    if (user.role !== "admin") throw new Error("Ця сторінка доступна лише адміністратору.");
    const values = await getReferenceValues(token);
    const catalog = document.getElementById("reference-catalog");
    catalog.replaceChildren();
    const groups = Map.groupBy(values, (value) => value.category);
    for (const [category, group] of groups) {
      const section = document.createElement("section"); section.className = "reference-category";
      const title = document.createElement("h2"); title.textContent = CATEGORY_LABELS[category] || category;
      const table = document.createElement("table"); table.className = "reference-category__table";
      const header = document.createElement("thead"); const headerRow = document.createElement("tr");
      for (const text of ["Код", "Значення"]) { const cell = document.createElement("th"); cell.textContent = text; headerRow.append(cell); }
      header.append(headerRow);
      const body = document.createElement("tbody");
      for (const value of group) {
        const row = document.createElement("tr");
        for (const text of [value.code, value.label]) { const cell = document.createElement("td"); cell.textContent = text; row.append(cell); }
        body.append(row);
      }
      table.append(header, body); section.append(title, table); catalog.append(section);
    }
  };
  try {
    await load();
    registerVisibleDataRefresh(load);
  } catch (error) {
    status.textContent = error.message;
    status.classList.add("is-error");
    status.hidden = false;
  }
}
