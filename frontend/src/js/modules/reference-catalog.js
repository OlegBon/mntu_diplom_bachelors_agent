import { getCurrentUser, getReferenceValues } from "./api.js";

export async function initReferenceCatalog() {
  const page = document.querySelector("[data-reference-catalog-page]");
  if (!page) return;
  const token = localStorage.getItem("token");
  const status = document.getElementById("reference-catalog-status");
  try {
    const user = await getCurrentUser(token);
    if (user.role !== "admin") throw new Error("Ця сторінка доступна лише адміністратору.");
    const values = await getReferenceValues(token);
    const body = document.getElementById("reference-catalog-body");
    body.replaceChildren();
    for (const value of values) {
      const row = document.createElement("tr");
      for (const text of [value.category, value.code, value.label]) {
        const cell = document.createElement("td"); cell.textContent = text; row.append(cell);
      }
      body.append(row);
    }
  } catch (error) {
    status.textContent = error.message;
    status.classList.add("is-error");
    status.hidden = false;
  }
}
